from typing import Any


def upsert_streaming_availability(
    conn,
    media_id: int,
    streaming_data: list[dict[str, Any]],
) -> None:

    for provider in streaming_data:
        provider_code = provider.get("provider_code")
        provider_name = provider.get("provider_name")
        provider_title = provider.get("provider_title")
        provider_desc = provider.get("provider_desc")
        provider_link = provider.get("provider_link")
        provider_image = provider.get("provider_image")
        provider_category = provider.get("provider_category")
        provider_image_height = provider.get("provider_image_height")
        provider_image_width = provider.get("provider_image_width")

        if not provider_code or not provider_category:
            print(f"Skipping provider with missing code/category: {provider}")
            continue

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
        """, (
            provider_code,
            provider_name,
            provider_title,
            provider_category,
        )) as cur:
            result = cur.fetchone()

        if not result:
            print(f"Failed to upsert provider with code {provider_code}")
            continue

        provider_id = result[0]

        conn.execute("""
            INSERT INTO media_provider (
                media_id,
                provider_id,
                provider_desc,
                provider_link
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (media_id, provider_id)
            DO UPDATE SET
                provider_desc = EXCLUDED.provider_desc,
                provider_link = EXCLUDED.provider_link;
        """, (
            media_id,
            provider_id,
            provider_desc,
            provider_link,
        ))

        if provider_image:
            image_asset_id = upsert_image_asset(
                conn=conn,
                source_provider="imdb",
                source_url=provider_image,
                width=provider_image_width,
                height=provider_image_height,
            )

            attach_image_asset(
                conn=conn,
                owner_type="provider",
                owner_id=provider_id,
                image_asset_id=image_asset_id,
                image_kind="provider_logo",
                is_primary=True,
            )

def upsert_image_asset(
    conn,
    source_provider: str | None,
    source_url: str,
    width: int | None = None,
    height: int | None = None,
) -> int:
    if not source_url:
        raise ValueError("source_url is required for image_asset")

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
        VALUES (%s, %s, %s, %s, 'pending', now(), now())
        ON CONFLICT (source_url)
        DO UPDATE SET
            source_provider = COALESCE(image_asset.source_provider, EXCLUDED.source_provider),
            source_width = COALESCE(image_asset.source_width, EXCLUDED.source_width),
            source_height = COALESCE(image_asset.source_height, EXCLUDED.source_height),
            last_checked_at = now(),
            updated_at = now()
        RETURNING image_asset_id;
    """, (
        source_provider,
        source_url,
        width,
        height,
    )) as cur:
        result = cur.fetchone()

    if not result:
        raise RuntimeError(f"Failed to upsert image asset for {source_url}")

    return result[0]

def attach_image_asset(
    conn,
    owner_type: str,
    owner_id: int,
    image_asset_id: int,
    image_kind: str,
    is_primary: bool = True,
    sort_order: int = 0,
) -> None:
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
        VALUES (%s, %s, %s, %s, %s, %s, now(), now())
        ON CONFLICT (owner_type, owner_id, image_kind, image_asset_id)
        DO UPDATE SET
            is_primary = EXCLUDED.is_primary,
            sort_order = EXCLUDED.sort_order,
            updated_at = now();
    """, (
        image_asset_id,
        owner_type,
        owner_id,
        image_kind,
        is_primary,
        sort_order,
    ))


def upsert_media_poster_image(
    conn,
    media_id: int,
    media: dict[str, Any],
) -> int | None:
    dims = media.get("image_dimensions") or {}
    source_url = media.get("poster_url")

    if not source_url:
        return None

    image_asset_id = upsert_image_asset(
        conn=conn,
        source_provider="imdb" if media.get("imdb_url") else "unknown",
        source_url=source_url,
        width=dims.get("width"),
        height=dims.get("height"),
    )

    attach_image_asset(
        conn=conn,
        owner_type="media",
        owner_id=media_id,
        image_asset_id=image_asset_id,
        image_kind="poster",
        is_primary=True,
    )

    return image_asset_id