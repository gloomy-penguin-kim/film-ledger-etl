# fetch → insert raw JSON → normalize → upsert rows
import pprint
import json
from app.etl.fetch_json import ImdbClient
from app.etl.db_conn import DatabaseConn
from app.etl.insert_raw_payload import save_raw_payload, mark_processed, get_last_processed_payload, update_movie
from app.etl.upsert_media import upsert_media
from app.etl.upsert_trending import upsert_trending_snapshot
from app.etl.upsert_images import upsert_image_redo
from app.etl.upsert_tables import upsert_people, upsert_keywords, upsert_languages, upsert_enhanced, upsert_genres
from app.etl.upsert_streaming import upsert_streaming_availability

imdb_client = ImdbClient()
db = DatabaseConn() 

VERSION = 3

def ingest_trending(count: int = 250):

    result = get_last_processed_payload(
        conn=db.conn,
        source="imdb_trending",
        version=VERSION)

    if result:
        if result.get("processed_at"): 
            print("Last payload already processed")
            return 
        else: 
            print("Using last fetched payload that has not been processed yet.")
            data = result.get("payload")
            raw_id = result.get("id")
    else: 
        data = imdb_client.get_trending_movies(count=count) 
        raw_id = save_raw_payload(
            conn=db, 
            source="imdb_trending", 
            version=VERSION, 
            payload=json.dumps(data),
        )  
    
    movies = imdb_client.extract_movie_info(data)

    count = 1
    for movie in movies:  
        conn = db.connect()

        try:
            media_imdb_id = movie.get("id")
            media_id, needs_a_refresh, missing_image = update_movie(conn, media_imdb_id)

            details = imdb_client.get_movie_details(media_imdb_id)

            media_id = upsert_media(conn, details)

            if needs_a_refresh:
                upsert_genres(conn, media_id, details)

                upsert_people(conn, media_id, details)
                upsert_enhanced(conn, media_id, details)

                upsert_keywords(conn, media_id, details)
                upsert_languages(conn, media_id, details)

                streaming = imdb_client.get_streaming_availability(media_imdb_id)
                upsert_streaming_availability(conn, media_id, streaming)

            if missing_image:
                upsert_image_redo(conn,
                                  media_id=media_id,
                                  media=details)

            upsert_trending_snapshot(conn, media_id, movie.get("rank"))
            conn.commit()

            print(f"{count}. Updated media {media_id}, imdb {media_imdb_id}, raw_id {raw_id}")
            count += 1

        except Exception as e:
            sql_query = movie
            db.conn.rollback()
            db.conn.execute("""
                insert into errors (error_message, payload_id, media_id, media_imdb_id, sql_query)
                values (%s, %s, %s, %s, %s)
                """, (str(e), raw_id, media_id, media_imdb_id, json.dumps(sql_query)))
            db.conn.commit()
            if raw_id:
                db.conn.execute("""
                    update raw_imdb_payloads
                        set error_count = error_count + 1,
                            status = 'error'
                      where id = %s
                    """, (raw_id,))
                db.conn.commit()
            print(f"Error with media {media_id}, imdb {media_imdb_id}, raw_id {raw_id}")
            if sql_query: print(f"Json Data: {sql_query}")
            print(e)

    mark_processed(db, raw_id)



ingest_trending() 