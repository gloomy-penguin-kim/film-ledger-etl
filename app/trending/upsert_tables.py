
from typing import Any

from app.trending.upsert_images import insert_image


def upsert_keywords(conn, media_id: int, media: dict[str, Any]) -> None:
    keywords = media.get("keywords") or []

    for keyword_name in keywords:
        keyword_name = keyword_name.strip()

        if not keyword_name: continue

        results = conn.execute(
            """
            INSERT INTO keyword (keyword_name)
            VALUES (%s)
            ON CONFLICT (keyword_name)
            DO UPDATE SET keyword_name = EXCLUDED.keyword_name 
            RETURNING keyword_id;
            """,
            (keyword_name,),
        )

        if not results: continue
        keyword_id = results.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_keyword (media_id, keyword_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, keyword_id)
            DO NOTHING;
            """,
            (media_id, keyword_id),
        )


def upsert_countries(conn, media_id: int, media: dict[str, Any]) -> None:
    countries = media.get("countries") or []

    for country_name in countries:
        country_name = country_name.strip()

        if not country_name: continue

        results = conn.execute(
            """
            INSERT INTO country (country_name)
            VALUES (%s)
            ON CONFLICT (country_name)
            DO UPDATE SET country_name = EXCLUDED.country_name  
            RETURNING country_id;
            """,
            (country_name,),
        )

        if not results: continue
        country_id = results.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_country (media_id, country_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, country_id)
            DO UPDATE SET 
                media_id = EXCLUDED.media_id, 
                country_id = EXCLUDED.country_id;
            """,
            (media_id, country_id),
        )


def upsert_genres(conn, media_id: int, media: dict[str, Any]) -> None: 
    genres = media.get("genres") or []

    for genre_name in genres:
        genre_name = genre_name.strip()

        if not genre_name: continue

        results = conn.execute(
            """
            INSERT INTO genre (genre_name)
            VALUES (%s)
            ON CONFLICT (genre_name)
            DO UPDATE SET genre_name = EXCLUDED.genre_name
            RETURNING genre_id;
            """,
            (genre_name,),
        )

        if not results: continue
        genre_id = results.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_genre (media_id, genre_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, genre_id)
            DO NOTHING;
            """,
            (media_id, genre_id),
        )


def upsert_languages(conn, media_id: int, media: dict[str, Any]) -> None:
    languages = media.get("languages") or []
 
    for language_name in languages:
        language_name = language_name.strip()

        if not language_name: continue

        results = conn.execute(
            """
            INSERT INTO language (language_name)
            VALUES (%s)
            ON CONFLICT (language_name)
            DO UPDATE SET language_name = EXCLUDED.language_name 
            RETURNING language_id;
            """,
            (language_name,),
        )

        if not results: continue
        language_id = results.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_language (media_id, language_id)
            VALUES (%s, %s)
            ON CONFLICT (media_id, language_id)
            DO NOTHING;
            """,
            (media_id, language_id),
        )

