from app.etl.upsert_images import insert_image

from typing import Any

def upsert_similar_titles(conn, media_id: int, media: dict[str, Any]) -> None:
    for similar in (media.get("similar_titles") or []):
        similar_id = similar.get("id").strip()
        poster_url = similar.get("poster_url")

        if not similar_id: continue

        results = conn.execute(
            """
            INSERT INTO media_similar_titles (media_id,
                                              related_media_id,
                                              related_media_imdb_id)
            SELECT %(media_id)s,
                   m.media_id,
                   %(related_media_imdb_id)s
            FROM (SELECT %(related_media_imdb_id)s AS imdb_id) imdb
                     LEFT JOIN media m
                               ON m.media_imdb_id = imdb.imdb_id

            ON CONFLICT (media_id, related_media_imdb_id)
                DO UPDATE SET related_media_id = EXCLUDED.related_media_id

            RETURNING related_media_id;
            """,
            {
                "media_id": media_id,
                "related_media_imdb_id": similar.get("id"),
            },
        )

        if not results: continue

        related_media_id = results.fetchone()[0]

        if poster_url and related_media_id:
            insert_image(conn, {
                         "owner_id"   : related_media_id,
                         "owner_type" : "media",
                         "image_kind" : "poster",
                         "source_url" : poster_url,
                         "is_primary" : True
            })




