DROP VIEW IF EXISTS media_full_view;
DROP VIEW IF EXISTS image_choice_media;
DROP VIEW IF EXISTS image_choice_provider;

CREATE OR REPLACE VIEW image_choice_media AS
SELECT
    ial.owner_id AS media_id,
    ial.image_kind,

    ia.image_asset_id,
    ia.source_provider,
    ia.source_url,
    ia.source_width,
    ia.source_height,
    ia.status AS asset_status,

    iv.image_variant_id,
    iv.public_url,
    iv.object_key,
    iv.storage_provider,
    iv.storage_bucket,
    iv.content_type,
    iv.width,
    iv.height,
    iv.byte_size,
    iv.sha256,
    iv.status AS variant_status,
    iv.cached_at,

    v.variant_id,
    v.variant_name,
    v.path_str,
    v.target_width,
    v.target_height,
    v.is_cropped

FROM image_asset_link ial
JOIN image_asset ia
    ON ia.image_asset_id = ial.image_asset_id
LEFT JOIN image_variant iv
    ON iv.image_asset_id = ia.image_asset_id
LEFT JOIN variant v
    ON v.variant_id = iv.variant_id
WHERE ial.owner_type = 'media';


CREATE OR REPLACE VIEW image_choice_people AS
SELECT
    ial.owner_id AS people_id,
    ial.image_kind,

    ia.image_asset_id,
    ia.source_provider,
    ia.source_url,
    ia.source_width,
    ia.source_height,
    ia.status AS asset_status,

    iv.image_variant_id,
    iv.public_url,
    iv.object_key,
    iv.storage_provider,
    iv.storage_bucket,
    iv.content_type,
    iv.width,
    iv.height,
    iv.byte_size,
    iv.sha256,
    iv.status AS variant_status,
    iv.cached_at,

    v.variant_id,
    v.variant_name,
    v.path_str,
    v.target_width,
    v.target_height,
    v.is_cropped

FROM image_asset_link ial
JOIN image_asset ia
    ON ia.image_asset_id = ial.image_asset_id
LEFT JOIN image_variant iv
    ON iv.image_asset_id = ia.image_asset_id
LEFT JOIN variant v
    ON v.variant_id = iv.variant_id
WHERE ial.owner_type = 'people';



CREATE OR REPLACE VIEW image_choice_provider AS
SELECT
    ial.owner_id AS provider_id,
    ial.image_kind,
    ial.is_primary,
    ial.sort_order,

    ia.image_asset_id,
    ia.source_provider,
    ia.source_url,
    ia.source_width,
    ia.source_height,
    ia.status AS asset_status,

    iv.image_variant_id,
    iv.public_url,
    iv.object_key,
    iv.storage_provider,
    iv.storage_bucket,
    iv.content_type,
    iv.width,
    iv.height,
    iv.byte_size,
    iv.sha256,
    iv.status AS variant_status,
    iv.cached_at,

    v.variant_id,
    v.variant_name,
    v.path_str,
    v.target_width,
    v.target_height,
    v.is_cropped

FROM image_asset_link ial
JOIN image_asset ia
    ON ia.image_asset_id = ial.image_asset_id
LEFT JOIN image_variant iv
    ON iv.image_asset_id = ia.image_asset_id
LEFT JOIN variant v
    ON v.variant_id = iv.variant_id
WHERE ial.owner_type = 'provider';


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
    CASE WHEN poster.variant_status = 'cached' THEN poster.public_url END,
    poster.public_url,
    poster.source_url
  ) AS media_image,

  COALESCE(poster.width, poster.source_width) AS media_image_width,
  COALESCE(poster.height, poster.source_height) AS media_image_height,

  CASE
    WHEN poster.image_asset_id IS NULL THEN NULL
    ELSE jsonb_build_object(
      'image_asset_id', poster.image_asset_id,
      'image_variant_id', poster.image_variant_id,
      'image_kind', poster.image_kind,
      'variant_id', poster.variant_id,
      'path_str', poster.path_str,
      'source_provider', poster.source_provider,
      'source_url', poster.source_url,
      'public_url', poster.public_url,
      'object_key', poster.object_key,
      'storage_provider', poster.storage_provider,
      'storage_bucket', poster.storage_bucket,
      'content_type', poster.content_type,
      'width', poster.width,
      'height', poster.height,
      'byte_size', poster.byte_size,
      'sha256', poster.sha256,
      'asset_status', poster.asset_status,
      'variant_status', poster.variant_status,
      'is_primary', poster.is_primary,
      'sort_order', poster.sort_order,
      'cached_at', poster.cached_at
    )
  END AS poster_image_asset,

  COALESCE(
    CASE WHEN backdrop.variant_status = 'cached' THEN backdrop.public_url END,
    backdrop.public_url,
    backdrop.source_url
  ) AS backdrop_image,

  CASE
    WHEN backdrop.image_asset_id IS NULL THEN NULL
    ELSE jsonb_build_object(
      'image_asset_id', backdrop.image_asset_id,
      'image_variant_id', backdrop.image_variant_id,
      'image_kind', backdrop.image_kind,
      'variant_id', backdrop.variant_id,
      'path_str', backdrop.path_str,
      'source_url', backdrop.source_url,
      'public_url', backdrop.public_url,
      'width', backdrop.width,
      'height', backdrop.height,
      'asset_status', backdrop.asset_status,
      'variant_status', backdrop.variant_status,
      'is_primary', backdrop.is_primary,
      'sort_order', backdrop.sort_order
    )
  END AS backdrop_image_asset,

  m.media_certificate,
  m.media_production_status,

  COALESCE((
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
  ), '[]'::jsonb) AS genres,

  COALESCE((
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
          CASE WHEN provider_logo.variant_status = 'cached' THEN provider_logo.public_url END,
          provider_logo.public_url,
          provider_logo.source_url
        ),

        'provider_image_asset', CASE
          WHEN provider_logo.image_asset_id IS NULL THEN NULL
          ELSE jsonb_build_object(
            'image_asset_id', provider_logo.image_asset_id,
            'image_variant_id', provider_logo.image_variant_id,
            'image_kind', provider_logo.image_kind,
            'variant_id', provider_logo.variant_id,
            'path_str', provider_logo.path_str,
            'source_url', provider_logo.source_url,
            'public_url', provider_logo.public_url,
            'width', provider_logo.width,
            'height', provider_logo.height,
            'asset_status', provider_logo.asset_status,
            'variant_status', provider_logo.variant_status
          )
        END
      )
      ORDER BY pr.provider_category, pr.provider_name, pr.provider_title
    )
    FROM media_provider mpv
    JOIN provider pr ON pr.provider_id = mpv.provider_id

    LEFT JOIN LATERAL (
      SELECT *
      FROM image_choice_provider primg
      WHERE primg.provider_id = pr.provider_id
        AND primg.image_kind IN ('provider_logo', 'logo')
      ORDER BY
        primg.is_primary DESC,
        primg.sort_order ASC,
        (primg.variant_status = 'cached') DESC,
        (primg.public_url IS NOT NULL) DESC,
        (primg.variant_key = 'provider_logo_150x225') DESC,
        (primg.variant_key = 'provider_logo_original') DESC,
        primg.cached_at DESC NULLS LAST
      LIMIT 1
    ) provider_logo ON TRUE

    WHERE mpv.media_id = m.media_id
  ), '[]'::jsonb) AS providers,

  m.fetched_at,
  m.updated_at,
  m.access_count

FROM media m

LEFT JOIN LATERAL (
  SELECT *
  FROM image_choice_media img
  WHERE img.media_id = m.media_id
    AND img.image_kind = 'poster'
  ORDER BY
    img.is_primary DESC,
    img.sort_order ASC,
    (img.variant_status = 'cached') DESC,
    (img.public_url IS NOT NULL) DESC,
    (img.variant_key = 'poster_200x300') DESC,
    (img.variant_key = 'poster_1000x1500') DESC,
    (img.variant_key = 'poster_original') DESC,
    img.cached_at DESC NULLS LAST
  LIMIT 1
) poster ON TRUE

LEFT JOIN LATERAL (
  SELECT *
  FROM image_choice_media img
  WHERE img.media_id = m.media_id
    AND img.image_kind = 'backdrop'
  ORDER BY
    img.is_primary DESC,
    img.sort_order ASC,
    (img.variant_status = 'cached') DESC,
    (img.public_url IS NOT NULL) DESC,
    (img.variant_key = 'backdrop_1280x720') DESC,
    (img.variant_key = 'backdrop_original') DESC,
    img.cached_at DESC NULLS LAST
  LIMIT 1
) backdrop ON TRUE;