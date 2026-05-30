DROP VIEW IF EXISTS media_full_view;

CREATE OR REPLACE VIEW media_full_view AS
SELECT
  m.media_id,
  m.media_imdb_id,
  m.media_title,
  m.media_type,
  m.media_release_year,
  m.media_release_date,
  m.media_runtime_seconds,
  m.media_review_rating,
  m.media_vote_count,
  m.media_plot,

  COALESCE(
    CASE
      WHEN poster.status = 'cached' THEN poster.public_url
      ELSE NULL
    END,
    poster.public_url,
    poster.source_url,
    m.media_image
  ) AS media_image,

  COALESCE(poster.width, m.media_image_width) AS media_image_width,
  COALESCE(poster.height, m.media_image_height) AS media_image_height,

  CASE
    WHEN poster.image_asset_id IS NULL THEN NULL
    ELSE jsonb_build_object(
      'image_asset_id', poster.image_asset_id,
      'image_kind', poster.image_kind,
      'variant', poster.variant,
      'source_provider', poster.source_provider,
      'source_url', poster.source_url,
      'storage_provider', poster.storage_provider,
      'storage_bucket', poster.storage_bucket,
      'object_key', poster.object_key,
      'public_url', poster.public_url,
      'content_type', poster.content_type,
      'width', poster.width,
      'height', poster.height,
      'byte_size', poster.byte_size,
      'sha256', poster.sha256,
      'status', poster.status,
      'is_primary', poster.is_primary,
      'sort_order', poster.sort_order,
      'last_checked_at', poster.last_checked_at,
      'cached_at', poster.cached_at
    )
  END AS poster_image_asset,

  COALESCE(
    CASE
      WHEN backdrop.status = 'cached' THEN backdrop.public_url
      ELSE NULL
    END,
    backdrop.public_url,
    backdrop.source_url
  ) AS backdrop_image,

  CASE
    WHEN backdrop.image_asset_id IS NULL THEN NULL
    ELSE jsonb_build_object(
      'image_asset_id', backdrop.image_asset_id,
      'image_kind', backdrop.image_kind,
      'variant', backdrop.variant,
      'source_provider', backdrop.source_provider,
      'source_url', backdrop.source_url,
      'storage_provider', backdrop.storage_provider,
      'storage_bucket', backdrop.storage_bucket,
      'object_key', backdrop.object_key,
      'public_url', backdrop.public_url,
      'content_type', backdrop.content_type,
      'width', backdrop.width,
      'height', backdrop.height,
      'byte_size', backdrop.byte_size,
      'sha256', backdrop.sha256,
      'status', backdrop.status,
      'is_primary', backdrop.is_primary,
      'sort_order', backdrop.sort_order,
      'last_checked_at', backdrop.last_checked_at,
      'cached_at', backdrop.cached_at
    )
  END AS backdrop_image_asset,

  m.media_certificate,
  m.media_production_status,

  COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'genre_id', g.genre_id,
          'genre_name', g.genre_name
        )
        ORDER BY g.genre_name
      )
      FROM media_genre mg
      JOIN genre g ON g.genre_id = mg.genre_id
      WHERE mg.media_id = m.media_id
    ),
    '[]'::jsonb
  ) AS genres,

  COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'language_id', l.language_id,
          'language_name', l.language_name
        )
        ORDER BY l.language_name
      )
      FROM media_language ml
      JOIN language l ON l.language_id = ml.language_id
      WHERE ml.media_id = m.media_id
    ),
    '[]'::jsonb
  ) AS languages,

  COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'person_id', p.person_id,
          'person_imdb_id', p.person_imdb_id,
          'person_name', p.person_name,
          'person_image', p.person_image,
          'credit_category', mp.credit_category,
          'character_names', COALESCE(to_jsonb(mp.character_names), '[]'::jsonb),
          'enhanced_actor', mp.enhanced_actor
        )
        ORDER BY mp.credit_category, p.person_name
      )
      FROM media_person mp
      JOIN person p ON p.person_id = mp.person_id
      WHERE mp.media_id = m.media_id
    ),
    '[]'::jsonb
  ) AS credits,

  COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'keyword_id', k.keyword_id,
          'keyword_name', k.keyword_name
        )
        ORDER BY k.keyword_name
      )
      FROM media_keyword mk
      JOIN keyword k ON k.keyword_id = mk.keyword_id
      WHERE mk.media_id = m.media_id
    ),
    '[]'::jsonb
  ) AS keywords,

  COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'provider_id', pr.provider_id,
          'provider_code', pr.provider_code,
          'provider_name', pr.provider_name,
          'provider_title', pr.provider_title,
          'provider_title_alt', pr.provider_title_alt,
          'provider_category', pr.provider_category,
          'provider_desc', mpv.provider_desc,
          'provider_link', mpv.provider_link,

          'provider_image', COALESCE(
            CASE
              WHEN provider_logo.status = 'cached' THEN provider_logo.public_url
              ELSE NULL
            END,
            provider_logo.public_url,
            provider_logo.source_url
          ),

          'provider_image_asset', CASE
            WHEN provider_logo.image_asset_id IS NULL THEN NULL
            ELSE jsonb_build_object(
              'image_asset_id', provider_logo.image_asset_id,
              'image_kind', provider_logo.image_kind,
              'variant', provider_logo.variant,
              'source_provider', provider_logo.source_provider,
              'source_url', provider_logo.source_url,
              'storage_provider', provider_logo.storage_provider,
              'storage_bucket', provider_logo.storage_bucket,
              'object_key', provider_logo.object_key,
              'public_url', provider_logo.public_url,
              'content_type', provider_logo.content_type,
              'width', provider_logo.width,
              'height', provider_logo.height,
              'byte_size', provider_logo.byte_size,
              'sha256', provider_logo.sha256,
              'status', provider_logo.status,
              'is_primary', provider_logo.is_primary,
              'sort_order', provider_logo.sort_order,
              'last_checked_at', provider_logo.last_checked_at,
              'cached_at', provider_logo.cached_at
            )
          END
        )
        ORDER BY pr.provider_category, pr.provider_name, pr.provider_title
      )
      FROM media_provider mpv
      JOIN provider pr ON pr.provider_id = mpv.provider_id

      LEFT JOIN LATERAL (
        SELECT
          ia.*,
          pia.image_kind,
          pia.is_primary,
          pia.sort_order
        FROM provider_image_asset pia
        JOIN image_asset ia
          ON ia.image_asset_id = pia.image_asset_id
        WHERE pia.provider_id = pr.provider_id
          AND pia.image_kind IN ('provider_logo', 'logo')
        ORDER BY
          pia.is_primary DESC,
          pia.sort_order ASC,
          (ia.status = 'cached') DESC,
          (ia.public_url IS NOT NULL) DESC,
          (ia.variant = 'original') DESC,
          ia.cached_at DESC NULLS LAST,
          ia.updated_at DESC NULLS LAST
        LIMIT 1
      ) provider_logo ON TRUE

      WHERE mpv.media_id = m.media_id
    ),
    '[]'::jsonb
  ) AS providers,

  m.fetched_at,
  m.updated_at,
  m.access_count

FROM media m

LEFT JOIN LATERAL (
  SELECT
    ia.*,
    mia.image_kind,
    mia.is_primary,
    mia.sort_order
  FROM media_image_asset mia
  JOIN image_asset ia
    ON ia.image_asset_id = mia.image_asset_id
  WHERE mia.media_id = m.media_id
    AND mia.image_kind = 'poster'
  ORDER BY
    mia.is_primary DESC,
    mia.sort_order ASC,
    (ia.status = 'cached') DESC,
    (ia.public_url IS NOT NULL) DESC,
    (ia.variant = 'w500') DESC,
    (ia.variant = 'original') DESC,
    ia.cached_at DESC NULLS LAST,
    ia.updated_at DESC NULLS LAST
  LIMIT 1
) poster ON TRUE

LEFT JOIN LATERAL (
  SELECT
    ia.*,
    mia.image_kind,
    mia.is_primary,
    mia.sort_order
  FROM media_image_asset mia
  JOIN image_asset ia
    ON ia.image_asset_id = mia.image_asset_id
  WHERE mia.media_id = m.media_id
    AND mia.image_kind = 'backdrop'
  ORDER BY
    mia.is_primary DESC,
    mia.sort_order ASC,
    (ia.status = 'cached') DESC,
    (ia.public_url IS NOT NULL) DESC,
    (ia.variant = 'w780') DESC,
    (ia.variant = 'original') DESC,
    ia.cached_at DESC NULLS LAST,
    ia.updated_at DESC NULLS LAST
  LIMIT 1
) backdrop ON TRUE;