
from typing import Any


def upsert_keywords(conn, media_id: int, media: dict[str, Any]) -> None:
    keywords = media.get("keywords") or []

    for keyword_name in keywords:
        keyword_name = keyword_name.strip()

        if not keyword_name:
            continue

        with conn.execute(
            """
            INSERT INTO keyword (keyword_name)
            VALUES (%s)
            ON CONFLICT (keyword_name)
            DO UPDATE SET keyword_name = EXCLUDED.keyword_name
            RETURNING keyword_id;
            """,
            (keyword_name,),
        ) as cur:
            keyword_id = cur.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_keyword (media_id, keyword_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, keyword_id)
            DO NOTHING;
            """,
            (media_id, keyword_id),
        )


def upsert_genres(conn, media_id: int, media: dict[str, Any]) -> None: 
    genres = media.get("genres") or []

    for genre_name in genres:
        genre_name = genre_name.strip()

        if not genre_name:
            continue

        with conn.execute(
            """
            INSERT INTO genre (genre_name)
            VALUES (%s)
            ON CONFLICT (genre_name)
            DO UPDATE SET genre_name = EXCLUDED.genre_name
            RETURNING genre_id;
            """,
            (genre_name,),
        ) as cur:
            genre_id = cur.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_genre (media_id, genre_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, genre_id)
            DO NOTHING;
            """,
            (media_id, genre_id),
        )


def upsert_languages(conn: psycopg.Connection, media_id: int, media: dict[str, Any]) -> None: 
    languages = media.get("languages") or []
 
    for language_name in languages:
        language_name = language_name.strip()

        if not language_name:
            continue

        with conn.execute(
            """
            INSERT INTO language (language_name)
            VALUES (%s)
            ON CONFLICT (language_name)
            DO UPDATE SET language_name = EXCLUDED.language_name
            RETURNING language_id;
            """,
            (language_name,),
        ) as cur:
            language_id = cur.fetchone()[0]  

        conn.execute(
            """
            INSERT INTO media_language (media_id, language_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, language_id)
            DO NOTHING;
            """,
            (media_id, language_id),
        )



