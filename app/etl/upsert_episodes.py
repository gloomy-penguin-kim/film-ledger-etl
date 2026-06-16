import json
from datetime import date
from collections import Counter
import traceback


def upsert_episode_list(conn, series_media_id: int, series_media_imdb_id: str, episodes):
    if len(episodes) == 0: return

    conn.execute("""
        insert into media_series (series_media_id, series_media_imdb_id) 
        values (%s, %s)
        ON CONFLICT (series_media_imdb_id) DO NOTHING;
    """, (series_media_id, series_media_imdb_id))

    imdb_ids = []
    for episode in episodes:

        try:
            episode_number = ((episode.get("series") or {}).get("episodeNumber") or {}).get("episodeNumber")
            season_number = ((episode.get("series") or {}).get("episodeNumber") or {}).get("seasonNumber")
            episode_media_imdb_id = episode["id"]
            episode_title = episode["titleText"]["text"]
            episode_plot = ((episode.get("plot") or {}).get("plotText") or {}).get("plainText")
            release_date_day = (episode.get("releaseDate") or {}).get("day")
            release_date_mon = (episode.get("releaseDate") or {}).get("month")
            release_date_year = (episode.get("releaseDate") or {}).get("year")
            episode_release_date = date(int(release_date_year), int(release_date_mon), int(release_date_day)) if release_date_day and release_date_mon and release_date_year else None
            episode_review_rating = (episode.get("ratingsSummary") or {}).get("aggregateRating")
            episode_runtime = (episode.get("runtime") or {}).get("seconds")
            episode_image_url = (episode.get("primaryImage") or {}).get("url")
            episode_raw_json = json.dumps(episode)


            sql = """
                insert into media_episode (series_media_id, series_media_imdb_id, 
                                           season_number, 
                                           episode_number, episode_media_imdb_id, 
                                           episode_title, episode_plot, episode_rating, episode_runtime, 
                                           episode_release_date, episode_year,  
                                           episode_image_url, episode_media_id,
                                           raw_json)
                select x.series_media_id, 
                        x.series_media_imdb_id, 
                        case when x.season_number is null then 0 else cast(x.season_number as int) end,
                        case when x.episode_number is null then 0 else cast(x.episode_number as int) end, 
                        x.episode_media_imdb_id,
                        x.episode_title, 
                        x.episode_plot, 
                        cast(x.episode_rating as double precision), 
                        cast(x.episode_runtime as int), 
                        cast(x.episode_release_date as date), 
                        cast(x.episode_year as int), 
                        x.episode_image_url, 
                        m.media_id as episode_media_id,
                        x.raw_json
                from   (select 
                            %(series_media_id)s as series_media_id, 
                            %(series_media_imdb_id)s as series_media_imdb_id, 
                            %(season_number)s as season_number, 
                            %(episode_number)s as episode_number, 
                            %(episode_media_imdb_id)s as episode_media_imdb_id, 
                            %(episode_title)s as episode_title, 
                            %(episode_plot)s as episode_plot, 
                            %(episode_review_rating)s as episode_rating, 
                            %(episode_runtime)s as episode_runtime, 
                            %(episode_release_date)s as episode_release_date,
                            %(episode_year)s as episode_year, 
                            %(episode_image_url)s as episode_image_url,
                            %(episode_raw_json)s as raw_json 
                       ) as x 
                        left outer join media m 
                            on m.media_imdb_id = x.episode_media_imdb_id 
                limit  1 
                on conflict (series_media_imdb_id, season_number, episode_media_imdb_id) 
                do update 
                    set     episode_media_id = (select media_id from media where media_imdb_id = EXCLUDED.episode_media_imdb_id), 
                            episode_title = EXCLUDED.episode_title,
                            episode_plot = EXCLUDED.episode_plot,
                            episode_rating = EXCLUDED.episode_rating,
                            episode_runtime = EXCLUDED.episode_runtime,
                            episode_release_date = EXCLUDED.episode_release_date, 
                            episode_year = EXCLUDED.episode_year,
                            episode_image_url = EXCLUDED.episode_image_url,
                            raw_json = EXCLUDED.raw_json, 
                            updated_at = now()  
                returning episode_media_id;
            """
            results = conn.execute(sql, {
                "series_media_id": series_media_id,
                "series_media_imdb_id": series_media_imdb_id,
                "season_number": season_number,
                "episode_number": episode_number,
                "episode_media_imdb_id": episode_media_imdb_id,
                "episode_title": episode_title,
                "episode_plot": episode_plot,
                "episode_review_rating": episode_review_rating,
                "episode_runtime": episode_runtime,
                "episode_release_date": episode_release_date,
                "episode_year": release_date_year,
                "episode_image_url": episode_image_url,
                "episode_raw_json": episode_raw_json,
            })
            conn.commit()
            result = results.fetchone()[0]
            if not result:
                imdb_ids.append(episode_media_imdb_id)
        except Exception as e:
            print(e)
            print(episode)
            traceback.print_exc()
            quit()

    return imdb_ids
