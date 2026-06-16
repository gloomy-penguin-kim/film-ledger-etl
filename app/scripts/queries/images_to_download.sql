WITH needed AS (
    SELECT DISTINCT
        ia.image_asset_id,
        ia.source_url,

        ial.owner_type,
        ial.owner_id,
        ial.image_kind,

        --COALESCE(m.media_title, p.person_name, pp.provider_name) as description,
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
        ) AS needs_variant,

        m.raw_json

    FROM image_asset ia
    JOIN image_asset_link ial
        ON ial.image_asset_id = ia.image_asset_id
    JOIN variant v
        ON v.image_kind = ial.image_kind
    LEFT JOIN image_variant iv
        ON iv.image_asset_id = ia.image_asset_id
       AND iv.variant_id = v.variant_id

    join media m
        on m.media_id = ial.owner_id and
            ial.owner_type = 'media'

--     left outer join media m
--         on m.media_id = ial.owner_id and
--             ial.owner_type = 'media'
--
--     left outer join person p
--         on p.person_id = ial.owner_id and
--             ial.owner_type = 'people'
--
--     left outer join provider pp
--         on pp.provider_id = ial.owner_id and
--             ial.owner_type = 'provider'

    WHERE
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
    source_url, raw_json,
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
GROUP BY owner_type, owner_id, description, source_url, image_kind, raw_json
ORDER BY owner_type, owner_id, description, source_url, image_kind, raw_json