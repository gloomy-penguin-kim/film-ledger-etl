from typing import Any

from app.etl.upsert_streaming import upsert_image_asset, attach_image_asset



def insert_image(conn, specs) -> int | None:
    owner_id = specs.get("owner_id")
    owner_type = specs.get("owner_type")
    image_kind = specs.get("image_kind")
    source_url = specs.get("source_url")
    width = specs.get("width")
    height = specs.get("height")
    is_primary = specs.get("is_primary") or False
    description = specs.get("description")
    source_provider = specs.get("source_provider") or 'imdb'
    status = "pending"

    if not source_url: return None

    results = conn.execute("""
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
            %(source_provider)s,
            %(source_url)s, 
            %(dims_width)s,
            %(dims_height)s,
            %(status)s,
            now(),
            now()
        )
        ON CONFLICT (source_url)
        DO UPDATE SET
            source_provider = EXCLUDED.source_provider,
            source_width = COALESCE(image_asset.source_width, EXCLUDED.source_width),
            source_height = COALESCE(image_asset.source_height, EXCLUDED.source_height),
            status = EXCLUDED.status,
            last_checked_at = now(),
            updated_at = now()
        RETURNING image_asset_id;
    """, {
        "source_provider": source_provider,
        "source_url": source_url,
        "dims_width": width,
        "dims_height": height,
        "status": status,
    })

    if not results: return None
    image_asset_id = results.fetchone()[0]

    # if it is going to be primary
    if is_primary:
        conn.execute("""
            update  image_asset_link 
               set  is_primary = false,
                    updated_at = now()  
             where  owner_type = %(owner_type)s and 
                    owner_id   = %(owner_id)s and 
                    image_kind = %(image_kind)s and
                    is_primary = true
            """, {
            "owner_type": owner_type,
            "owner_id": owner_id,
            "image_kind": image_kind
        })

    # make primary if one doesn't already exist
    conn.execute("""
        INSERT INTO image_asset_link (
            image_asset_id,
            owner_type,
            owner_id,
            image_kind, 
            description,
            is_primary,
            created_at,
            updated_at
        )
        select  constants.image_asset_id, 
                constants.owner_type, 
                constants.owner_id, 
                constants.image_kind,
                constants.description, 
                BOOL_OR(ial.image_asset_link_id is null) as is_primary, 
                now() as created_at, 
                now() as updated_at 
        from    (select  %(image_asset_id)s as image_asset_id,
                         %(owner_type)s as owner_type,
                         %(owner_id)s as owner_id,
                         %(image_kind)s as image_kind,  
                         %(description)s as description ) as constants 
                left outer join image_asset_link as ial 
                    on ial.owner_type = constants.owner_type and 
                        ial.owner_id = constants.owner_id and 
                        ial.image_kind = constants.image_kind and
                        ial.is_primary = true 
        group   by constants.image_asset_id, 
                constants.owner_type, 
                constants.owner_id, 
                constants.image_kind,
                constants.description 
            
        ON CONFLICT (owner_type, owner_id, image_kind, image_asset_id)
        DO UPDATE SET 
            description = case when length(EXCLUDED.description) > length(image_asset_link.description) then EXCLUDED.description else image_asset_link.description end,
            updated_at = now()         
            
    """, {
        "image_asset_id": image_asset_id,
        "owner_type": owner_type,
        "owner_id": owner_id,
        "image_kind": image_kind,
        "description": description,
    })

    return image_asset_id


def upsert_media_poster_image(
    conn,
    media_id: int,
    media: dict[str, Any],
) -> int | None:
    specs = media.get("good_image") or {}

    if not specs.get("url"):
        return None

    # image_asset_id = upsert_image_asset(
    #     conn=conn,
    #     source_provider="imdb" if media.get("imdb_url") else "unknown",
    #     source_url=specs.get("url"),
    #     width=specs.get("width"),
    #     height=specs.get("height")
    # )
    #
    # attach_image_asset(
    #     conn=conn,
    #     owner_type="media",
    #     owner_id=media_id,
    #     image_asset_id=image_asset_id,
    #     image_kind="poster",
    #     description=specs.get("caption")
    # )

    return insert_image(conn, {
        "owner_id": media_id,
        "owner_type": "media",
        "image_kind": "poster",
        "source_url": specs.get("url"),
        "width": specs.get("width"),
        "height": specs.get("height"),
        "is_primary": False,
        "description": specs.get("caption")
    })

