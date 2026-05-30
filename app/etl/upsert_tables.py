
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


def upsert_people(conn, media_id: int, media: dict[str, Any]) -> None:
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




# From API data:
#   media_id
#   image_kind
#   source_provider
#   source_url
#   width
#   height
#   status = pending
#
# After download:
#   content_type
#   byte_size
#   sha256
#
# After upload:
#   storage_provider
#   storage_bucket
#   object_key
#   public_url
#   status = cached
#   cached_at