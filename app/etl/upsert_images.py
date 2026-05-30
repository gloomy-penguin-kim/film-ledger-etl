def upsert_image_redo(conn, media_id, media):
    dims = media.get("image_dimensions") or {}
    source_url = media.get("poster_url")

    with conn.execute("""
        INSERT INTO image_asset (
            source_provider,
            source_url,
            variant,
            width,
            height,
            status,
            last_checked_at
        )
        VALUES (
            'imdb',
            %s,
            'original',
            %s,
            %s,
            'pending',
            now()
        )
        ON CONFLICT (source_url, variant)
        DO UPDATE SET
            width = COALESCE(image_asset.width, EXCLUDED.width),
            height = COALESCE(image_asset.height, EXCLUDED.height),
            last_checked_at = now(),
            updated_at = now()
        RETURNING image_asset_id;
    """, (source_url, dims.get("width"), dims.get("height"))) as cur:
        image_asset_id = cur.fetchone()[0]

        conn.execute("""
            INSERT INTO media_image_asset (
                media_id,
                image_asset_id,
                image_kind,
                is_primary
            )
            VALUES (
                %s,
                %s,
                'poster',
                TRUE
            )
            ON CONFLICT (media_id, image_asset_id, image_kind)
            DO NOTHING;
        """, (media_id, image_asset_id))
