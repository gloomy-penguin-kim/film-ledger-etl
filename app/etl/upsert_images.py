
def upsert_media_poster_image(conn, media_id: int, media: dict) -> int | None:
    dims = media.get("image_dimensions") or {}
    source_url = media.get("poster_url")

    if not source_url:
        return None

    with conn.execute("""
        INSERT INTO image_asset (
            source_provider,
            source_url,
            source_width,
            source_height, 
            status,
            last_checked_at,
            updated_at
        )
        VALUES (
            'imdb',
            %s, 
            %s,
            %s,
            'pending',
            now(),
            now()
        )
        ON CONFLICT (source_url)
        DO UPDATE SET
            source_width = COALESCE(image_asset.source_width, EXCLUDED.source_width),
            source_height = COALESCE(image_asset.source_height, EXCLUDED.source_height),
            last_checked_at = now(),
            updated_at = now()
        RETURNING image_asset_id;
    """, (
        source_url,
        dims.get("width"),
        dims.get("height"),
    )) as cur:
        image_asset_id = cur.fetchone()[0]

    conn.execute("""
        INSERT INTO image_asset_link (
            image_asset_id,
            owner_type,
            owner_id,
            image_kind,
            is_primary,
            sort_order,
            created_at,
            updated_at
        )
        VALUES (
            %(image_asset_id)s,
            'media',
            %(media_id)s,
            'poster',
            TRUE,
            0,
            now(),
            now()
        )
        ON CONFLICT (owner_type, owner_id, image_kind, image_asset_id)
        DO UPDATE SET
            is_primary = EXCLUDED.is_primary,
            updated_at = now();
    """, {
        "image_asset_id": image_asset_id,
        "media_id": media_id,
    })

    return image_asset_id