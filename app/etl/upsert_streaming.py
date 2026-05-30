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

        with conn.execute(
            """
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
            """,
            (
                provider_code,
                provider_name,
                provider_title,
                provider_category,
            ),
        ) as cur:
            result = cur.fetchone()

        if not result:
            print(f"Failed to upsert provider with code {provider_code}")
            continue

        provider_id = result[0]

        conn.execute(
            """
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
            """,
            (
                media_id,
                provider_id,
                provider_desc,
                provider_link,
            ),
        )

        if provider_image:
            image_asset_id = upsert_image_asset(
                conn=conn,
                source_provider="imdb",
                source_url=provider_image,
                variant="original",
                width=provider_image_width,
                height=provider_image_height,
            )

            attach_provider_image_asset(
                conn=conn,
                provider_id=provider_id,
                image_asset_id=image_asset_id,
                image_kind="provider_logo",
                is_primary=True,
            )


def upsert_image_asset(
    conn,
    source_provider: str | None,
    source_url: str,
    variant: str = "original",
    width: int | None = None,
    height: int | None = None,
) -> int:
    """
    One row per unique source_url + variant.
    No media_id.
    No provider_id.
    Just the reusable image record.
    """

    with conn.execute(
        """
        INSERT INTO image_asset (
            source_provider,
            source_url,
            variant,
            width,
            height,
            status,
            last_checked_at
        )
        VALUES (%s, %s, %s, %s, %s, 'pending', now())
        ON CONFLICT (source_url, variant)
        DO UPDATE SET
            source_provider = COALESCE(image_asset.source_provider, EXCLUDED.source_provider),
            width = COALESCE(image_asset.width, EXCLUDED.width),
            height = COALESCE(image_asset.height, EXCLUDED.height),
            last_checked_at = now(),
            updated_at = now()
        RETURNING image_asset_id;
        """,
        (
            source_provider,
            source_url,
            variant,
            width,
            height,
        ),
    ) as cur:
        result = cur.fetchone()

    if not result:
        raise RuntimeError(f"Failed to upsert image asset for {source_url}")

    return result[0]


def attach_provider_image_asset(
    conn,
    provider_id: int,
    image_asset_id: int,
    image_kind: str = "provider_logo",
    is_primary: bool = True,
    sort_order: int = 0,
) -> None:
    """
    This says: this provider uses this reusable image_asset.
    """

    conn.execute(
        """
        INSERT INTO provider_image_asset (
            provider_id,
            image_asset_id,
            image_kind,
            is_primary,
            sort_order
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (provider_id, image_asset_id, image_kind)
        DO UPDATE SET
            is_primary = EXCLUDED.is_primary,
            sort_order = EXCLUDED.sort_order,
            updated_at = now();
        """,
        (
            provider_id,
            image_asset_id,
            image_kind,
            is_primary,
            sort_order,
        ),
    )


def upsert_image_assets(conn,
                        media_id: int = None,
                        provider_id: int = None,
                        image_kind: str = None,
                        variant: str = None,
                        media: dict[str, Any] = None) -> int:

    dims = media.get("image_dimensions") or {}
    source_url = media.get("poster_url")

    if not source_url:
        insert = {
            "media_id": media_id,
            "provider_id": provider_id,
            "image_kind": image_kind,
            "variant": variant,
            "source_provider": "imdb" if media.get("imdb_url") else None,
            "source_url": None,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "status": "skipped",
            "error_message": "No poster_url found",
        }
    else:
        insert = {
            "media_id": media_id,
            "provider_id": provider_id,
            "image_kind": image_kind,
            "variant": variant,
            "source_provider": "imdb" if media.get("imdb_url") else "unknown",
            "source_url": source_url,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "status": "pending",
        }

    with conn.execute(
        """
        insert into image_asset (
            media_id,   
            provider_id, 
            image_kind, 
            variant, 
            source_provider, 
            source_url, 
            width,
            height, 
            status) 
        values  (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (media_id, provider_id, image_kind, variant) 
        do update set 
            image_kind = EXCLUDED.image_kind,
            variant = EXCLUDED.image_kind,
            source_provider = EXCLUDED.source_provider,
            source_url = EXCLUDED.source_url,
            width = EXCLUDED.width,
            height = EXCLUDED.height,
            status = EXCLUDED.status
        returning image_asset_id;
        """, (
                media_id, provider_id, insert.get("image_kind"), insert.get("variant"), insert.get("source_provider"),
                insert.get("source_url"), insert.get("width"), insert.get("height"), insert.get("status")
            )) as cur:
        return cur.fetchone()[0]

