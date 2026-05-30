import json
from datetime import date
from typing import Any

import psycopg
from psycopg.rows import dict_row


def upsert_media(conn: psycopg.Connection, media: dict[str, Any]) -> int:
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
            media_image,
            media_image_width,
            media_image_height,
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
            %(media_image)s,
            %(media_image_width)s,
            %(media_image_height)s,
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
            media_image = EXCLUDED.media_image,
            media_image_width = EXCLUDED.media_image_width,
            media_image_height = EXCLUDED.media_image_height,
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
        "media_image": media.get("poster_url"),
        "media_image_width": image_dimensions.get("width"),
        "media_image_height": image_dimensions.get("height"),
        "media_certificate": media.get("certificate"),
        "media_production_status": media.get("production_status"),
        "raw_json": json.dumps(media),
    }

    with conn.execute(sql, params) as cur: 
        results = cur.fetchone()
        print("Upserted media:", results)
        return results[0] if results else None

    

def upsert_trending_snapshot(
    conn,
    media_id: int,
    rank: int,
    snapshot_date: date | None = date.today(),
) -> None: 
    if not media_id or rank is None:
        raise ValueError("media_id and rank are required for upserting trending snapshot.")
    
    sql = """
        INSERT INTO trending_snapshot (
            media_id,
            rank,
            snapshot_date
        )
        VALUES (
            %(media_id)s,
            %(rank)s,
            COALESCE(%(snapshot_date)s, current_date)
        )
        ON CONFLICT (media_id, snapshot_date)
        DO UPDATE SET
            rank = EXCLUDED.rank;
    """

    conn.execute(
        sql,
        {
            "media_id": media_id,
            "rank": rank,
            "snapshot_date": snapshot_date,
        },
    )    
    conn.commit()


def upsert_keywords(conn: psycopg.Connection, media_id: int, media: dict[str, Any]) -> None: 
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
    conn.commit()


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
    conn.commit()


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
    conn.commit()


def upsert_people(conn: psycopg.Connection, media_id: int, media: dict[str, Any]) -> None: 
    credits = media.get("credits") or {}

    for category, people in credits.items():
        if not people:
            continue

        for credit in people:
            person_imdb_id = credit.get("id")
            person_name = credit.get("name")
            person_image = credit.get("profile_image")

            if not person_imdb_id or not person_name:
                continue

            with conn.execute(
                """
                INSERT INTO person (
                    person_imdb_id,
                    person_name,
                    person_image
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (person_imdb_id)
                DO UPDATE SET
                    person_name = EXCLUDED.person_name,
                    person_image = EXCLUDED.person_image
                RETURNING person_id;
                """,
                (person_imdb_id, person_name, person_image),
            ) as cur:
                person_id = cur.fetchone()[0]

            characters = credit.get("characters") or []

            conn.execute(
                """
                INSERT INTO media_person (
                    media_id,
                    person_id,
                    credit_category,
                    character_names
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (media_id, person_id, credit_category)
                DO UPDATE SET
                    character_names = EXCLUDED.character_names;
                """,
                (
                    media_id,
                    person_id,
                    category,
                    characters,
                ),
            )        
    conn.commit()



def upsert_enhanced(conn, media_id: int, media: dict[str, Any]) -> None: 
    enhanced_actors = media.get("enhanced_actors") or []

    for actor in enhanced_actors:  
        if not actor:
            continue 

        person_imdb_id = actor.get("url").split("/")[-2] if actor.get("url") else None
        person_name = actor.get("name")
        person_image = actor.get("profile_image") 

        if not person_imdb_id or not person_name:
            continue 

        with conn.execute(
            """
                INSERT INTO person (
                    person_imdb_id,
                    person_name,
                    person_image
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (person_imdb_id)
                DO UPDATE SET
                    person_name = EXCLUDED.person_name,
                    person_image = COALESCE(EXCLUDED.person_image, person.person_image)
                RETURNING person_id;
            """,
            (person_imdb_id, person_name, person_image),
        ) as cur:
            result = cur.fetchone()
            if result:
                person_id = result[0] 
                conn.execute(
                    """
                    update  media_person mp
                    set     enhanced_actor = true
                    from    person p
                        where   mp.person_id = p.person_id
                                and mp.person_id = %s
                                and mp.media_id = %s 
                        """,
                        (person_id, media_id),
                    ) 
    conn.commit()


def upsert_streaming_availability(conn, media_id: int, streaming_data: dict[str, Any]) -> None: 
    
    for provider in streaming_data:
        
        provider_code = provider.get("provider_code")
        provider_name = provider.get("provider_name")
        provider_title = provider.get("provider_title")
        provider_desc = provider.get("provider_desc")
        provider_link = provider.get("provider_link")    
        provider_image = provider.get("provider_image") 
        provider_category = provider.get("provider_category") 

        with conn.execute("""
            INSERT INTO provider (
                provider_code, 
                provider_name,
                provider_title,
                provider_category
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (provider_code, provider_category)
            DO UPDATE SET
                provider_name = EXCLUDED.provider_name,
                provider_title = EXCLUDED.provider_title
            RETURNING provider_id;
        """, (provider_code, provider_name, provider_title, provider_category)) as cur:
            result = cur.fetchone()
            if not result:
                print(f"Failed to upsert provider with code {provider_code}")
                continue
            provider_id = result[0]

            conn.execute(
                """
                INSERT INTO media_provider (media_id, provider_id, provider_desc, 
                                        provider_link, provider_image)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (media_id, provider_id) 
                DO UPDATE SET 
                    provider_desc = EXCLUDED.provider_desc,
                    provider_link = EXCLUDED.provider_link,
                    provider_image = EXCLUDED.provider_image 
                """,
                (media_id, provider_id, provider_desc, 
                    provider_link, provider_image),
        )
    conn.commit()
