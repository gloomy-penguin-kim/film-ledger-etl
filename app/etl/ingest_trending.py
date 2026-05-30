# fetch → insert raw JSON → normalize → upsert rows
import pprint
import json
from datetime import date
from app.etl.fetch_json import ImdbClient
from app.etl.db_conn import DatabaseConn
from app.etl.insert_raw_payload import save_raw_payload, mark_processed, get_last_processed_payload, update_movie
from app.etl.upsert_tables import upsert_media, upsert_trending_snapshot, upsert_genres
from app.etl.upsert_tables import upsert_people, upsert_keywords, upsert_languages, upsert_enhanced
from app.etl.upsert_tables import upsert_streaming_availability

imdb_client = ImdbClient()
db = DatabaseConn() 

# import app.etl.insert_raw_json as insert_raw_json
# import app.etl.normalize as normalize
# import app.etl.upsert_rows as upsert_rows

VERSION = 1 

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

    for movie in movies:  
        conn = db.connect() 

        media_imdb_id = movie.get("id")
        media_id = update_movie(conn, media_imdb_id) 

        if not media_id: 
            details = imdb_client.get_movie_details(media_imdb_id)

            media_id = upsert_media(conn, details) 

            upsert_genres(conn, media_id, details)
            
            upsert_people(conn, media_id, details)
            upsert_enhanced(conn, media_id, details)

            upsert_keywords(conn, media_id, details)
            upsert_languages(conn, media_id, details)

            streaming = imdb_client.get_streaming_availability(media_imdb_id)
            upsert_streaming_availability(conn, media_id, streaming)
        
        upsert_trending_snapshot(conn, media_id, movie.get("rank"))
 
 
    # for rank, item in iter_trending_items(payload):
    #     media_id = upsert_media(item)
    #     upsert_trending_snapshot(media_id, rank)
    #     upsert_genres(media_id, item)
    #     upsert_people(media_id, item)

    mark_processed(db, raw_id)

ingest_trending() 