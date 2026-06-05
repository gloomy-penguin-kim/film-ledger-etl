from typing import Any
import json

from app.etl.upsert_streaming import upsert_media_poster_image


def upsert_media(conn, media: dict[str, Any]) -> int | None:
    image_dimensions = media.get("image_dimensions") or {}

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
            raw_json = EXCLUDED.raw_json,
            updated_at = now()
        RETURNING media_id;
    """

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
        "raw_json": json.dumps(media),
    }

    with conn.execute(sql, params) as cur:
        results = cur.fetchone()
        if results:
            media_id = results[0]
            upsert_media_poster_image(conn, media_id, media)
            return media_id
        return None

