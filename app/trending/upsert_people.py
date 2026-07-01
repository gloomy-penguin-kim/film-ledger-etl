from typing import Any


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
                fetch_one = cur.fetchone()
                if not fetch_one or len(fetch_one) == 0:
                    continue
                person_id = fetch_one[0]

                if person_image:
                    with conn.execute("""
                        INSERT INTO image_asset (source_provider, source_url, status,
                                    created_at, updated_at)
                            VALUES ('imdb', %s, 'pending', NOW(), NOW())
                        ON CONFLICT (source_url) DO NOTHING
                        RETURNING image_asset_id;
                    """, (person_image,)) as curr:
                        fetch_two = curr.fetchone()
                        if not fetch_two or len(fetch_two) == 0:
                            continue
                        image_asset_id = fetch_two[0]
                        conn.execute("""
                            INSERT INTO image_asset_link (image_asset_id, owner_type, owner_id,
                                        image_kind, created_at, updated_at)
                                VALUES (%(image_asset_id)s, 'people', %(person_id)s, 'headshot',
                                          NOW(), NOW())
                            ON CONFLICT (image_asset_id, image_kind, owner_type, owner_id) DO NOTHING;
                        """, { "image_asset_id": image_asset_id,
                               "person_id": person_id})

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
    enhanced = ((media.get("enhanced_actors") or []) +
                (media.get("enhanced_directors") or []) +
                (media.get("enhanced_creators") or []))

    for person in enhanced:
        if not person:
            continue

        person_imdb_id = person.get("url").split("/")[-2] if person.get("url") else None
        person_name = person.get("name")
        person_image = person.get("profile_image")

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
                    set     enhanced = true
                    from    person p
                        where   mp.person_id = p.person_id
                                and mp.person_id = %s
                                and mp.media_id = %s 
                        """,
                        (person_id, media_id),
                    )

