# fetch → insert raw JSON → normalize → upsert rows
import argparse
import json

from app.etl.fetch_json import ImdbClient
from app.etl.db_conn import DatabaseConn
from app.etl.insert_raw_payload import save_raw_payload, mark_processed, get_last_processed_payload, update_movie
from app.etl.upsert_media import upsert_media
from app.etl.upsert_trending import upsert_trending_snapshot
from app.etl.upsert_people import upsert_people, upsert_enhanced
from app.etl.upsert_tables import upsert_keywords, upsert_languages, upsert_genres
from app.etl.upsert_streaming import upsert_streaming_availability

imdb_client = ImdbClient()
db = DatabaseConn() 

VERSION = 3

DEBUG = False

def ingest_trending(force: bool=False, count: int = 250):

    result = get_last_processed_payload(
        conn=db.conn,
        source="imdb_trending",
        version=VERSION)

    if result and not force:
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
            count=count,
        )  
    
    movies = imdb_client.extract_movie_info(data)

    count = 1
    for movie in movies:  
        conn = db.connect()

        try:
            media_imdb_id = movie.get("id")
            media_id, needs_a_refresh, missing_image = update_movie(conn, media_imdb_id)

            details = imdb_client.get_movie_details(media_imdb_id)

            if (DEBUG): print("-"*20, "upsert_media", "-"*20)
            media_id = upsert_media(conn, details)
            if (DEBUG): conn.commit()

            if needs_a_refresh:
                if (DEBUG): print("-"*20, "upsert_genres", "-"*20)
                upsert_genres(conn, media_id, details)
                if (DEBUG): conn.commit()

                if (DEBUG): print("-"*20, "upsert_people", "-"*20)
                upsert_people(conn, media_id, details)
                upsert_enhanced(conn, media_id, details)
                if (DEBUG): conn.commit()

                if (DEBUG): print("-"*20, "upsert_keywords", "-"*20)
                upsert_keywords(conn, media_id, details)
                upsert_languages(conn, media_id, details)
                if (DEBUG): conn.commit()

                if (DEBUG): print("-"*20, "get_streaming_availability", "-"*20)
                streaming = imdb_client.get_streaming_availability(media_imdb_id)
                upsert_streaming_availability(conn, media_id, streaming)
                if (DEBUG): conn.commit()

            if (DEBUG): print("-"*20, "upsert_trending_snapshot", "-"*20)
            upsert_trending_snapshot(conn, media_id, movie.get("rank"))
            conn.commit()

            print(f"{count}. Updated media {media_id}, imdb {media_imdb_id}")
            count += 1

        except Exception as e:
            sql_query = movie
            db.conn.rollback()
            db.conn.execute("""
                insert into errors (error_message, payload_id, media_id, media_imdb_id, sql_query)
                values (%(error)s, %(raw_id)s, %(media_id)s, %(media_imdb_id)s, %(query)s)
                """, {
                    "error": str(e),
                    "raw_id": raw_id,
                    "media_id": media_id,
                    "media_imdb_id": media_imdb_id,
                    "query": json.dumps(sql_query),
                })
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

    try:
        from app.download.images import run_images_download
        run_images_download(db, count=0)
    except Exception as e:
        db.conn.rollback()
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='ingest tending movie titles')

    # Add arguments
    parser.add_argument('-c','--count', dest='count', nargs='?', const=250, type=int, help='the number of titles to retrieve')
    parser.add_argument("-f","--force", dest='force', action='store_true', help='force the tables to load')
    parser.add_argument("-d","--drop", dest='drop', action='store_true', help='drop the tables, reload the data')
    parser.add_argument("-s","--schema", dest='schema', action='store_true', help='run schema.sql')
    parser.add_argument("-v","--view", dest='view', action='store_true', help='create media_full_view')
    # Parse the arguments
    args = parser.parse_args()

    # if args.drop:
    #     args.schema = True
    #     args.view = True
    #
    # if args.drop:
    #     db.drop_tables()

    if args.schema:
        db.create_default_schema()

    if args.view:
        db.create_view()

    ingest_trending(count=args.count,force=args.force)
