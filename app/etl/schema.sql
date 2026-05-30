CREATE TABLE IF NOT EXISTS raw_imdb_payloads (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL, 
    version INT NOT NULL DEFAULT 1,
    payload JSONB NOT NULL, 
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
    media_image TEXT,
    media_image_width INT,
    media_image_height INT,
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
    provider_code VARCHAR(255) UNIQUE NOT NULL, 
    provider_name VARCHAR(255),
    provider_title TEXT NOT NULL,  
    provider_title_alt TEXT, 
    provider_category VARCHAR(255) NOT NULL,  
    CONSTRAINT unique_provider_code_name UNIQUE (provider_category, provider_code)
);
 
CREATE TABLE IF NOT EXISTS media_provider (
    media_id BIGINT REFERENCES media(media_id) ON DELETE CASCADE,
    provider_id BIGINT REFERENCES provider(provider_id) ON DELETE CASCADE,
    provider_desc TEXT, 
    provider_link TEXT NOT NULL, 
    provider_image TEXT NOT NULL, 
    PRIMARY KEY (media_id, provider_id)
);
 