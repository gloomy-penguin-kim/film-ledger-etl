from typing import Any
import json
import pprint

from datetime import datetime, timezone

from app.etl.upsert_images import insert_image


def upsert_media(conn, media: dict[str, Any], full_download=False) -> int | None:
    sql = """
        INSERT INTO media (
            media_imdb_id,
            media_title,
            media_original_title,
            media_type,
            media_release_year,
            media_release_date,
            media_runtime_seconds,
            media_review_rating,
            media_vote_count,
            media_plot, 
            media_certificate, 
            media_production_status,
            media_metascore, 
            full_download, 
            raw_json,
            updated_at
        )
        VALUES (
            %(media_imdb_id)s,
            %(media_title)s,
            %(media_original_title)s,
            %(media_type)s,
            %(media_release_year)s,
            %(media_release_date)s,
            %(media_runtime_seconds)s,
            %(media_review_rating)s,
            %(media_vote_count)s,
            %(media_plot)s, 
            %(media_certificate)s,
            %(media_production_status)s,
            %(media_metascore)s, 
            %(full_download)s,
            %(raw_json)s::jsonb,
            now()
        )
        ON CONFLICT (media_imdb_id)
        DO UPDATE SET
            media_title = EXCLUDED.media_title,
            media_original_title = EXCLUDED.media_original_title,
            media_type = EXCLUDED.media_type,
            media_release_year = EXCLUDED.media_release_year,
            media_release_date = EXCLUDED.media_release_date,
            media_runtime_seconds = EXCLUDED.media_runtime_seconds,
            media_review_rating = EXCLUDED.media_review_rating,
            media_vote_count = EXCLUDED.media_vote_count,
            media_plot = EXCLUDED.media_plot, 
            media_certificate = EXCLUDED.media_certificate,
            media_production_status = EXCLUDED.media_production_status,
            media_metascore = EXCLUDED.media_metascore,
            full_download = EXCLUDED.full_download,
            raw_json = EXCLUDED.raw_json,
            updated_at = now()
        RETURNING media_id;
    """

    current_time = datetime.now(timezone.utc)
    params = {
        "media_imdb_id": media.get("id"),
        "media_title": media.get("title"),
        "media_original_title": media.get("original_title"),
        "media_type": media.get("title_type"),
        "media_release_year": media.get("release_year"),
        "media_release_date": media.get("release_date"),
        "media_runtime_seconds": media.get("runtime_seconds"),
        "media_review_rating": media.get("rating"),
        "media_vote_count": media.get("vote_count"),
        "media_plot": media.get("plot"),
        "media_certificate": media.get("certificate"),
        "media_production_status": media.get("production_status"),
        "media_metascore": media.get("metascore"),
        "full_download": current_time if full_download else media.get("full_download"),
        "raw_json": json.dumps(media),
    }

    with conn.execute(sql, params) as cur:
        results = cur.fetchone()
        if results:
            #upsert_media_poster_image(conn, media_id, media)
            insert_image(conn, {
                "owner_id": results[0],
                "owner_type": "media",
                "image_kind": "poster",
                "source_url": media.get("good_image").get("url"),
                "width": media.get("good_image").get("width"),
                "height": media.get("good_image").get("height"),
                "is_primary": False,
                "description": media.get("good_image").get("caption")
            })

            #print(f"{media.get('title')} - {media.get('title_type')} - {media.get('good_image').get('url')}")
            return results[0]
        return None

