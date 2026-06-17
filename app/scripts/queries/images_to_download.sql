WITH needed AS (
    SELECT DISTINCT
        ia.image_asset_id,
        ia.source_url,
        ial.owner_type,
        ial.owner_id,
        ial.image_kind,
        provider_code as description,
        v.variant_id,
        v.path_str,
        v.target_width,
        v.target_height,
        v.is_cropped,
        iv.image_variant_id,
        iv.status,
        iv.cached_at,
        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        ) AS needs_variant
    FROM image_asset ia
    JOIN image_asset_link ial
        ON ial.image_asset_id = ia.image_asset_id
    JOIN variant v
        ON v.image_kind = ial.image_kind
    LEFT JOIN image_variant iv
        ON iv.image_asset_id = ia.image_asset_id
       AND iv.variant_id = v.variant_id
     join provider pp
        on pp.provider_id = ial.owner_id and
            ial.owner_type = 'provider'

    WHERE  v.active = true and
        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        )

UNION

    SELECT DISTINCT
        ia.image_asset_id,
        ia.source_url,

        ial.owner_type,
        ial.owner_id,
        ial.image_kind,

        p.person_name as description,

        v.variant_id,
        v.path_str,
        v.target_width,
        v.target_height,
        v.is_cropped,

        iv.image_variant_id,
        iv.status,
        iv.cached_at,

        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        ) AS needs_variant

    FROM image_asset ia
    JOIN image_asset_link ial
        ON ial.image_asset_id = ia.image_asset_id
    JOIN variant v
        ON v.image_kind = ial.image_kind
    LEFT JOIN image_variant iv
        ON iv.image_asset_id = ia.image_asset_id
       AND iv.variant_id = v.variant_id
     join
         (select p.*
          from person p
                   join media_person mp
                        on mp.person_id = p.person_id
                   join media m
                        on m.media_id = mp.media_id
                   join trending_snapshot_recent ts
                        on ts.media_id = m.media_id)  p
        on p.person_id = ial.owner_id and
            ial.owner_type = 'people'


    WHERE  v.active = true and
        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        )


UNION

    SELECT DISTINCT
        ia.image_asset_id,
        ia.source_url,
        ial.owner_type,
        ial.owner_id,
        ial.image_kind,
        m.media_title as description,
        v.variant_id,
        v.path_str,
        v.target_width,
        v.target_height,
        v.is_cropped,
        iv.image_variant_id,
        iv.status,
        iv.cached_at,
        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        ) AS needs_variant

    FROM image_asset ia
    JOIN image_asset_link ial
        ON ial.image_asset_id = ia.image_asset_id
    JOIN variant v
        ON v.image_kind = ial.image_kind
    LEFT JOIN image_variant iv
        ON iv.image_asset_id = ia.image_asset_id
       AND iv.variant_id = v.variant_id

     join (
            select    m.*
            from      media m
                      join trending_snapshot_recent ts
                        on ts.media_id = m.media_id
        ) m
        on m.media_id = ial.owner_id and
            ial.owner_type = 'media'


    WHERE  v.active = true and
        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        )


union


select distinct
        ia.image_asset_id,
        ia.source_url,

        ial.owner_type,
        ial.owner_id,
        ial.image_kind,

        m.related_media_title as description,

        v.variant_id,
        v.path_str,
        v.target_width,
        v.target_height,
        v.is_cropped,

        iv.image_variant_id,
        iv.status,
        iv.cached_at,

        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        ) AS needs_variant

    FROM image_asset ia
    JOIN image_asset_link ial
        ON ial.image_asset_id = ia.image_asset_id
    JOIN variant v
        ON v.image_kind = ial.image_kind
    LEFT JOIN image_variant iv
        ON iv.image_asset_id = ia.image_asset_id
       AND iv.variant_id = v.variant_id
    join (
          SELECT
            m.media_id,
            m.media_title,
            mc.related_media_id,
            c.connection_name,
            related.media_title AS related_media_title,
            related.media_type
          FROM
            media m
            JOIN trending_snapshot_recent ts ON ts.media_id = m.media_id
            JOIN media_connection mc ON m.media_id = mc.media_id
            JOIN connection c ON c.connection_id = mc.connection_id
            JOIN media related ON related.media_id = mc.related_media_id
          where related.media_type = 'Movie')  m
        on m.media_id = ial.owner_id and
            ial.owner_type = 'media'

    WHERE  v.active = true and
        (
            iv.image_variant_id IS NULL
            OR iv.status <> 'cached'
            OR iv.cached_at IS NULL
            OR iv.cached_at <= NOW() - INTERVAL '6 months'
        )

)

SELECT
    owner_type,
    owner_id,
    image_kind,
    description,
    source_url,
    jsonb_agg(
        jsonb_build_object(
            'description', description,
            'image_asset_id', image_asset_id,
            'owner_type', owner_type,
            'owner_id', owner_id,
            'image_kind', image_kind,
            'variant_id', variant_id,
            'path_str', path_str,
            'target_width', target_width,
            'target_height', target_height,
            'is_cropped', is_cropped,
            'image_variant_id', image_variant_id,
            'status', status,
            'cached_at', cached_at,
            'needs_variant', needs_variant
        )
        ORDER BY owner_type, owner_id, image_kind
    ) AS variants_needed
FROM needed
GROUP BY owner_type, owner_id, description, source_url, image_kind
ORDER BY owner_type, owner_id, description, source_url, image_kind