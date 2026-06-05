
create table if not exists errors (
    error_id BIGSERIAL PRIMARY KEY,
    error_message TEXT,
    payload_id BIGINT,
    media_id BIGINT,
    media_imdb_id TEXT,
    sql_query TEXT,
    error_timestamp TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE IF NOT EXISTS raw_imdb_payloads (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL, 
    version INT NOT NULL DEFAULT 1,
    payload JSONB NOT NULL,
    error_count INT DEFAULT 0,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ DEFAULT NULL,
    status TEXT DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS media (
    media_id BIGSERIAL PRIMARY KEY,
    media_imdb_id TEXT UNIQUE NOT NULL,
    media_title TEXT NOT NULL,
    media_original_title TEXT,
    media_type TEXT,
    media_release_year INT,
    media_release_date DATE,
    media_runtime_seconds INT,
    media_review_rating NUMERIC(3,1),
    media_vote_count INT,
    media_plot TEXT,
    media_certificate TEXT,
    media_production_status TEXT, 
    raw_json JSONB,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    access_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS trending_snapshot (
    id BIGSERIAL PRIMARY KEY,
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    rank INT NOT NULL,
    snapshot_date DATE DEFAULT current_date,
    source TEXT DEFAULT 'imdb',
    UNIQUE (media_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS genre (
    genre_id BIGSERIAL PRIMARY KEY,
    genre_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS media_genre (
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    genre_id BIGINT REFERENCES genre(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, genre_id)
);

CREATE TABLE IF NOT EXISTS person (
    person_id BIGSERIAL PRIMARY KEY,
    person_imdb_id TEXT UNIQUE NOT NULL,
    person_name TEXT NOT NULL,
    person_image TEXT 
);

CREATE TABLE IF NOT EXISTS media_person (
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    person_id BIGINT REFERENCES person(person_id) ON DELETE CASCADE,
    credit_category TEXT NOT NULL,
    character_names TEXT[],
    enhanced_actor BOOLEAN DEFAULT FALSE, 
    PRIMARY KEY (media_id, person_id, credit_category)
);

CREATE TABLE IF NOT EXISTS keyword (
    keyword_id BIGSERIAL PRIMARY KEY,
    keyword_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS media_keyword (
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    keyword_id BIGINT REFERENCES keyword(keyword_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, keyword_id)
);

CREATE TABLE IF NOT EXISTS language (
    language_id BIGSERIAL PRIMARY KEY,
    language_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS media_language (
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    language_id BIGINT REFERENCES language(language_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, language_id)
);
CREATE TABLE IF NOT EXISTS provider (
    provider_id BIGSERIAL PRIMARY KEY,
    provider_code VARCHAR(255) NOT NULL,
    provider_name VARCHAR(255),
    provider_title TEXT,
    provider_title_alt TEXT,
    provider_category VARCHAR(255) NOT NULL,

    CONSTRAINT unique_provider_category_code
        UNIQUE (provider_category, provider_code)
);

CREATE TABLE IF NOT EXISTS media_provider (
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    provider_id BIGINT REFERENCES provider(provider_id) ON DELETE CASCADE,
    provider_desc TEXT,
    provider_link TEXT NOT NULL,
    PRIMARY KEY (media_id, provider_id)
);

CREATE TABLE IF NOT EXISTS image_asset (
    image_asset_id BIGSERIAL PRIMARY KEY,

    -- The original/source image.
    source_provider TEXT,
    source_url TEXT NOT NULL,

    source_width INTEGER,
    source_height INTEGER,
    source_content_type TEXT,

    -- Optional fingerprint of the original.
    source_sha256 TEXT,

    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'processing', 'cached', 'failed', 'skipped')
    ),

    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,

    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT image_asset_unique_source_url UNIQUE (source_url)
);

CREATE TABLE IF NOT EXISTS image_variant (
    image_variant_id BIGSERIAL PRIMARY KEY,
    image_asset_id BIGINT NOT NULL REFERENCES image_asset(image_asset_id) ON DELETE CASCADE,

    -- original, thumb, card, large, w342, w500, etc.
    variant_id bigint not null references variant(variant_id) on delete cascade,

    storage_provider TEXT NOT NULL DEFAULT 'r2',
    storage_bucket TEXT,
    object_key TEXT,
    public_url TEXT,

    content_type TEXT,
    width INTEGER,
    height INTEGER,
    byte_size INTEGER,
    sha256 TEXT,

    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'cached', 'failed', 'skipped')
    ),

    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,

    last_checked_at TIMESTAMPTZ,
    cached_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT image_variant_unique_asset_variant_storage UNIQUE (
        image_asset_id,
        variant_id,
        storage_provider,
        storage_bucket
    )
);

CREATE TABLE if not exists path (
    path_id SERIAL PRIMARY KEY,
    path_name TEXT NOT NULL,
    parent_id INT REFERENCES path(path_id)
);


CREATE TABLE IF NOT EXISTS image_asset_link (
    image_asset_link_id BIGSERIAL PRIMARY KEY,

    image_asset_id BIGINT NOT NULL
        REFERENCES image_asset(image_asset_id) ON DELETE CASCADE,

    owner_type TEXT NOT NULL CHECK (
        owner_type IN ('media', 'provider')
    ),

    owner_id BIGINT NOT NULL,

    image_kind TEXT NOT NULL CHECK (
        image_kind IN ('poster', 'backdrop', 'logo', 'provider_logo')
    ),

    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (owner_type, owner_id, image_kind, image_asset_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_image_asset_source_url
ON image_asset(source_url);



CREATE TABLE IF NOT EXISTS variant (
    variant_id BIGSERIAL PRIMARY KEY,

    variant_name text not null,

    owner_type TEXT CHECK (
        owner_type in ('media','provider')
    ),
    image_kind TEXT CHECK (
        image_kind IN ('poster', 'backdrop', 'provider_logo', 'logo')
    ),
    variant_str TEXT,
    path_str TEXT NOT NULL,
    active boolean not null default true,

    target_width INTEGER,
    target_height INTEGER,

    is_cropped BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT unique_variant_slug
        UNIQUE (owner_type, image_kind, variant_str)
);

INSERT INTO variant (
    variant_name,

    owner_type,
    image_kind,
    variant_str,

    path_str,

    target_width,
    target_height,
    is_cropped
)
VALUES
    ('original_media',
     'media',
     'poster',
     'original',
     'media/poster/original',
     NULL,
     NULL,
     FALSE),

    ('original_provider_logo',
     'provider',
     'provider_logo',
     'original',
     'provider/provider_logo/original',
     NULL,
     NULL,
     FALSE),

    ('poster_200x300',
     'media',
     'poster',
     '200x300',
     'media/poster/200x300',
     200,
     300,
     TRUE),

    ('poster_1000x1500',
     'media',
     'poster',
     '1000x1500',
     'media/poster/1000x1500',
     1000,
     1500,
     TRUE),

    ('provider_logo_150x225',
     'provider',
     'provider_logo',
     '225x150',
     'provider/provider_logo/255x150',
     225,
     150,
     TRUE)

ON CONFLICT (variant_name) DO NOTHING;




