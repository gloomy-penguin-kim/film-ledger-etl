# fetch → insert raw JSON → normalize → upsert rows
import argparse
import json
import pprint
import traceback

from app.etl.fetch_json import ImdbClient
from app.etl.db_conn import DatabaseConn
from app.etl.insert_raw_payload import save_raw_payload, mark_processed, get_last_processed_payload, update_movie
from app.etl.upsert_episodes import upsert_episode_list
from app.etl.upsert_images import insert_image
from app.etl.upsert_media import upsert_media
from app.etl.upsert_trending import upsert_trending_snapshot
from app.etl.upsert_people import upsert_people, upsert_enhanced
from app.etl.upsert_tables import upsert_keywords, upsert_languages, upsert_genres, upsert_connections, \
    upsert_countries
from app.etl.upsert_similar_titles import upsert_similar_titles
from app.etl.upsert_streaming import upsert_streaming_availability

imdb_client = ImdbClient()
db = DatabaseConn() 

VERSION = 3

DEBUG = False

def update_similar_connections_after(db):
    db.conn.execute("""
                    update media_similar_titles as mst
                    set related_media_id = m.media_id
                    from media m
                    where m.media_imdb_id = mst.related_media_imdb_id
                      and mst.related_media_id is null
                    """)
    db.conn.execute("""
                    update media_connection as mc
                    set related_media_id = m.media_id
                    from media m
                    where m.media_imdb_id = mc.related_media_imdb_id
                      and mc.related_media_id is null
                    """)
    with db.conn.execute("""
        select  m.media_id as episode_media_id, 
                episode_image_url,
                episode_plot 
        from    media_episode
                join media m 
                    on m.media_imdb_id = media_episode.episode_media_imdb_id
                left outer join image_asset ia 
                    on ia.source_url = episode_image_url
        where   ia.image_asset_id is null 
    """) as cur:
        for result in cur.fetchall():
            insert_image(db.conn, {
                "owner_id": result[0],
                "owner_type": "media",
                "image_kind": "poster",
                "source_url": result[1],
                "is_primary": True,
                "description": result[2]
            })
    db.conn.execute("""
                    update media_episode as ep
                    set episode_media_id = m.media_id
                    from media m
                    where m.media_imdb_id = ep.episode_media_imdb_id
                      and ep.episode_media_id is null
                    """)
    # db.conn.commit()


def update_similar_connections(db):
    count = 0
    excluded = []

    results = db.conn.execute("""
        select related_media_imdb_id, 'similar' as label from media_similar_titles where related_media_id is null
        union 
        select related_media_imdb_id, 'connection' as label from media_connection where related_media_id is null
        union 
        select episode_media_imdb_id as media_imdb_id, 'episode' as label from media_episode where episode_media_id is null
        """)

    rows = results.fetchall()

    print("")
    print(f"Updating similar connections - {len(rows)} rows")

    for result in rows:
        media_imdb_id = result[0]
        if media_imdb_id not in excluded:
            try:
                media_id = run_update(db,
                                      media_imdb_id=media_imdb_id,
                                      similar_titles=False,
                                      connections=False,
                                      episodes=False)
                count += 1
                print(f"{count}. Updated media {media_id}, imdb {media_imdb_id}, type {result[1]}")
                excluded.append(media_imdb_id)
                db.conn.commit()
            except Exception as e:
                print("error:", e)
                # db.conn.rollback()
                # update_similar_connections_after(db)
                # return
    update_similar_connections_after(db)
    print("DONE - Updating similar connections")


def run_update(db,
               media_imdb_id=None,
               force=False,
               similar_titles=True,
               connections=True,
               episodes=True
               ) -> int | None:
    if not media_imdb_id: return None
    conn = db.connect()
    media_id = None

    full_download = False if not similar_titles or not connections else True

    error = ""
    try:
        error = f"media_imdb_id = {media_imdb_id}\n"
        media_id, needs_a_refresh = update_movie(conn, media_imdb_id)

        error += f"media_id = {media_id}\n"
        details = imdb_client.get_movie_details(media_imdb_id)

        error += f"details = {details}\n"
        media_id = upsert_media(conn, details, full_download)

        if needs_a_refresh or force:
            error += f"step: upsert_people\n"
            upsert_people(conn, media_id, details)
            error += f"step: upsert_countries\n"
            upsert_countries(conn, media_id, details)
            error += f"step: upsert_genres\n"
            upsert_genres(conn, media_id, details)
            error += f"step: upsert_keywords\n"
            upsert_keywords(conn, media_id, details)
            error += f"step: upsert_languages\n"
            upsert_languages(conn, media_id, details)

            error += f"step: get_streaming_availability\n"
            streaming = imdb_client.get_streaming_availability(media_imdb_id)
            upsert_streaming_availability(conn, media_id, streaming)

            conn.commit()

            error += f"step: connections\n"
            if connections: upsert_connections(conn, media_id, details)
            error += f"step: similar_titles\n"
            if similar_titles: upsert_similar_titles(conn, media_id, details)

            if episodes and details.get("is_series"):
                error += f"step: episodes\n"
                episodes = imdb_client.get_episode_data(media_imdb_id)
                imdb_ids = upsert_episode_list(conn, media_id, media_imdb_id, episodes)
                for imdb_id in imdb_ids:
                    db.connect()
                    print("\tepisode:", imdb_id)
                    run_update(db,
                               imdb_id,
                               similar_titles=False,
                               connections=False)
                db.conn.execute("""
                                update media_episode as ep
                                set episode_media_id = m.media_id
                                from media m
                                where m.media_imdb_id = ep.episode_media_imdb_id
                                  and ep.episode_media_id is null
                                """)
                db.conn.commit()

            #upsert_media_pvoster_image(conn, media_id, details)
    except Exception as e:
        print("e:", e)
        print("error:", error)
        traceback.print_exc()

    return media_id


def ingest_trending(force: bool=False,
                    trending: bool = False,
                    count: int = 250):

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
    # movies = [{ "id": "tt0118276", "rank": 1 }]

    update_similar_connections_after(db)

    trending_arr = []
    count = 1
    for movie in movies:
        media_imdb_id = None
        media_id = None

        try:
            media_imdb_id = movie.get("id")

            media_id = run_update(db=db,
                                  media_imdb_id=media_imdb_id,
                                  force=force,
                                  similar_titles=False,
                                  connections=False,
                                  )

            trending_arr.append({"media_id": media_id, "rank": movie.get("rank")})

            print(f"{count}. Updated media {media_id}, imdb {media_imdb_id}")
            count += 1

        except Exception as e:
            sql_query = movie
            db.conn.rollback()
            db.conn.execute("""
                insert into errors (error_message, payload_id, media_id, media_imdb_id, sql_query)
                values (%(error)s, %(raw_id)s, %(media_id)s, %(media_imdb_id)s, %(sql_query)s)
                """, {
                    "error": str(e),
                    "raw_id": raw_id,
                    "media_id": media_id,
                    "media_imdb_id": media_imdb_id,
                    "sql_query": json.dumps(sql_query),
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

    try:
        db.conn.commit()
        update_similar_connections(db)
        db.conn.commit()

    except Exception as e:
        print("Exception caught!")
        print(e)

    if trending:
        upsert_trending_snapshot(db, trending_arr)

    mark_processed(db, raw_id)


    # try:
    #     from app.download.images import run_images_download
    #     run_images_download(db, count=0)
    # except Exception as e:
    #     db.conn.rollback()
    #     print(f"Exception: {e}")

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='ingest tending movie titles')

    # Add arguments
    parser.add_argument('-c','--count', dest='count', nargs='?', const=250, type=int, help='the number of titles to retrieve')
    parser.add_argument("-f","--force", dest='force', action='store_true', help='force the tables to load')
    parser.add_argument("-d","--drop", dest='drop', action='store_true', help='drop the tables, reload the data')
    parser.add_argument("-s","--schema", dest='schema', action='store_true', help='run schema.sql')
    parser.add_argument("-v","--view", dest='view', action='store_true', help='create media_full_view')
    parser.add_argument("-t","--trending", dest='trending', action='store_true', help='run trending snapshot')
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

    ingest_trending(count=args.count,
                    trending=args.trending,
                    force=args.force)
