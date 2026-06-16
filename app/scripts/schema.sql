

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_session_jwt; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_session_jwt WITH SCHEMA public;


--
-- Name: EXTENSION pg_session_jwt; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION pg_session_jwt IS 'pg_session_jwt: manage authentication sessions using JWTs';


--
-- Name: neon_auth; Type: SCHEMA; Schema: -; Owner: neon_auth
--

CREATE SCHEMA neon_auth;


ALTER SCHEMA neon_auth OWNER TO neon_auth;

--
-- Name: pgrst; Type: SCHEMA; Schema: -; Owner: neon_service
--

CREATE SCHEMA pgrst;


ALTER SCHEMA pgrst OWNER TO neon_service;

--
-- Name: pre_config(); Type: FUNCTION; Schema: pgrst; Owner: neon_service
--

CREATE FUNCTION pgrst.pre_config() RETURNS void
    LANGUAGE sql
    SET search_path TO ''
    AS $$
  SELECT
      set_config('pgrst.db_schemas', 'public', true)
    , set_config('pgrst.db_aggregates_enabled', 'true', true)
    , set_config('pgrst.db_anon_role', 'anonymous', true)
    , set_config('pgrst.jwt_role_claim_key', '.role', true)
$$;


ALTER FUNCTION pgrst.pre_config() OWNER TO neon_service;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.account (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "accountId" text NOT NULL,
    "providerId" text NOT NULL,
    "userId" uuid NOT NULL,
    "accessToken" text,
    "refreshToken" text,
    "idToken" text,
    "accessTokenExpiresAt" timestamp with time zone,
    "refreshTokenExpiresAt" timestamp with time zone,
    scope text,
    password text,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL
);


ALTER TABLE neon_auth.account OWNER TO neon_auth;

--
-- Name: invitation; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.invitation (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "organizationId" uuid NOT NULL,
    email text NOT NULL,
    role text,
    status text NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "inviterId" uuid NOT NULL
);


ALTER TABLE neon_auth.invitation OWNER TO neon_auth;

--
-- Name: jwks; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.jwks (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "publicKey" text NOT NULL,
    "privateKey" text NOT NULL,
    "createdAt" timestamp with time zone NOT NULL,
    "expiresAt" timestamp with time zone
);


ALTER TABLE neon_auth.jwks OWNER TO neon_auth;

--
-- Name: member; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.member (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "organizationId" uuid NOT NULL,
    "userId" uuid NOT NULL,
    role text NOT NULL,
    "createdAt" timestamp with time zone NOT NULL
);


ALTER TABLE neon_auth.member OWNER TO neon_auth;

--
-- Name: organization; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.organization (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    logo text,
    "createdAt" timestamp with time zone NOT NULL,
    metadata text
);


ALTER TABLE neon_auth.organization OWNER TO neon_auth;

--
-- Name: project_config; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.project_config (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    endpoint_id text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    trusted_origins jsonb NOT NULL,
    social_providers jsonb NOT NULL,
    email_provider jsonb,
    email_and_password jsonb,
    allow_localhost boolean NOT NULL,
    plugin_configs jsonb,
    webhook_config jsonb
);


ALTER TABLE neon_auth.project_config OWNER TO neon_auth;

--
-- Name: session; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.session (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    token text NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL,
    "ipAddress" text,
    "userAgent" text,
    "userId" uuid NOT NULL,
    "impersonatedBy" text,
    "activeOrganizationId" text
);


ALTER TABLE neon_auth.session OWNER TO neon_auth;

--
-- Name: user; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth."user" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    email text NOT NULL,
    "emailVerified" boolean NOT NULL,
    image text,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    role text,
    banned boolean,
    "banReason" text,
    "banExpires" timestamp with time zone
);


ALTER TABLE neon_auth."user" OWNER TO neon_auth;

--
-- Name: verification; Type: TABLE; Schema: neon_auth; Owner: neon_auth
--

CREATE TABLE neon_auth.verification (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    identifier text NOT NULL,
    value text NOT NULL,
    "expiresAt" timestamp with time zone NOT NULL,
    "createdAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE neon_auth.verification OWNER TO neon_auth;

--
-- Name: connection; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.connection (
    connection_id bigint NOT NULL,
    connection_name text
);


ALTER TABLE public.connection OWNER TO neondb_owner;

--
-- Name: connection_connection_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.connection_connection_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.connection_connection_id_seq OWNER TO neondb_owner;

--
-- Name: connection_connection_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.connection_connection_id_seq OWNED BY public.connection.connection_id;


--
-- Name: errors; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.errors (
    error_id bigint NOT NULL,
    error_message text,
    payload_id bigint,
    media_id bigint,
    media_imdb_id text,
    sql_query text,
    error_timestamp timestamp with time zone DEFAULT now()
);


ALTER TABLE public.errors OWNER TO neondb_owner;

--
-- Name: errors_error_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.errors_error_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.errors_error_id_seq OWNER TO neondb_owner;

--
-- Name: errors_error_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.errors_error_id_seq OWNED BY public.errors.error_id;


--
-- Name: genre; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.genre (
    genre_id bigint NOT NULL,
    genre_name text NOT NULL
);


ALTER TABLE public.genre OWNER TO neondb_owner;

--
-- Name: genre_genre_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.genre_genre_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.genre_genre_id_seq OWNER TO neondb_owner;

--
-- Name: genre_genre_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.genre_genre_id_seq OWNED BY public.genre.genre_id;


--
-- Name: image_asset; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.image_asset (
    image_asset_id bigint NOT NULL,
    source_provider text,
    source_url text NOT NULL,
    source_width integer,
    source_height integer,
    source_content_type text,
    source_sha256 text,
    status text DEFAULT 'pending'::text NOT NULL,
    error_message text,
    attempt_count integer DEFAULT 0 NOT NULL,
    last_checked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT image_asset_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'processing'::text, 'cached'::text, 'failed'::text, 'skipped'::text])))
);


ALTER TABLE public.image_asset OWNER TO neondb_owner;

--
-- Name: image_asset_image_asset_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.image_asset_image_asset_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.image_asset_image_asset_id_seq OWNER TO neondb_owner;

--
-- Name: image_asset_image_asset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.image_asset_image_asset_id_seq OWNED BY public.image_asset.image_asset_id;


--
-- Name: image_asset_link; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.image_asset_link (
    image_asset_link_id bigint NOT NULL,
    image_asset_id bigint NOT NULL,
    owner_type text NOT NULL,
    owner_id bigint NOT NULL,
    image_kind text NOT NULL,
    is_primary boolean DEFAULT true NOT NULL,
    sort_order integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT image_asset_link_image_kind_check CHECK ((image_kind = ANY (ARRAY['poster'::text, 'backdrop'::text, 'logo'::text, 'provider_logo'::text, 'headshot'::text]))),
    CONSTRAINT image_asset_link_owner_type_check CHECK ((owner_type = ANY (ARRAY['media'::text, 'provider'::text, 'people'::text])))
);


ALTER TABLE public.image_asset_link OWNER TO neondb_owner;

--
-- Name: image_asset_link_image_asset_link_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.image_asset_link_image_asset_link_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.image_asset_link_image_asset_link_id_seq OWNER TO neondb_owner;

--
-- Name: image_asset_link_image_asset_link_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.image_asset_link_image_asset_link_id_seq OWNED BY public.image_asset_link.image_asset_link_id;


--
-- Name: image_variant; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.image_variant (
    image_variant_id bigint NOT NULL,
    image_asset_id bigint NOT NULL,
    variant_id bigint references variant(variant_id),
    storage_provider text DEFAULT 'r2'::text NOT NULL,
    storage_bucket text,
    object_key text,
    public_url text,
    content_type text,
    width integer,
    height integer,
    byte_size integer,
    sha256 text,
    status text DEFAULT 'pending'::text NOT NULL,
    error_message text,
    attempt_count integer DEFAULT 0 NOT NULL,
    last_checked_at timestamp with time zone,
    cached_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT image_variant_status_check CHECK ((status = ANY (ARRAY['pending'::text, 'cached'::text, 'failed'::text, 'skipped'::text])))
);


ALTER TABLE public.image_variant OWNER TO neondb_owner;

--
-- Name: variant; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.variant (
    variant_id bigint NOT NULL,
    variant_name text NOT NULL,
    image_kind text,
    target_width integer,
    target_height integer,
    is_cropped boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    owner_type text,
    variant_str text DEFAULT 'testing tacos are soft tacos'::text NOT NULL,
    path_str text DEFAULT 'not null'::text NOT NULL,
    active boolean DEFAULT true,
    CONSTRAINT variant_image_kind_check CHECK ((image_kind = ANY (ARRAY['poster'::text, 'backdrop'::text, 'provider_logo'::text, 'logo'::text, 'headshot'::text]))),
    CONSTRAINT variant_owner_type_check CHECK ((owner_type = ANY (ARRAY['media'::text, 'provider'::text, 'people'::text])))
);


ALTER TABLE public.variant OWNER TO neondb_owner;

--
-- Name: image_choice_media; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.image_choice_media AS
 SELECT ial.owner_id AS media_id,
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
    v.path_str,
    v.variant_str,
    v.variant_name AS variant_key,
    v.target_width,
    v.target_height,
    v.is_cropped
   FROM (((public.image_asset_link ial
     JOIN public.image_asset ia ON ((ia.image_asset_id = ial.image_asset_id)))
     LEFT JOIN public.image_variant iv ON ((iv.image_asset_id = ia.image_asset_id)))
     LEFT JOIN public.variant v ON ((v.variant_id = iv.variant_id)))
  WHERE (ial.owner_type = 'media'::text);


ALTER VIEW public.image_choice_media OWNER TO neondb_owner;

--
-- Name: image_choice_people; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.image_choice_people AS
 SELECT ial.owner_id AS people_id,
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
    v.path_str,
    v.variant_str,
    v.variant_name AS variant_key,
    v.target_width,
    v.target_height,
    v.is_cropped
   FROM (((public.image_asset_link ial
     JOIN public.image_asset ia ON ((ia.image_asset_id = ial.image_asset_id)))
     LEFT JOIN public.image_variant iv ON ((iv.image_asset_id = ia.image_asset_id)))
     LEFT JOIN public.variant v ON ((v.variant_id = iv.variant_id)))
  WHERE (ial.owner_type = 'people'::text);


ALTER VIEW public.image_choice_people OWNER TO neondb_owner;

--
-- Name: image_choice_provider; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.image_choice_provider AS
 SELECT ial.owner_id AS provider_id,
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
    v.path_str,
    v.variant_str,
    v.variant_name AS variant_key,
    v.target_width,
    v.target_height,
    v.is_cropped
   FROM (((public.image_asset_link ial
     JOIN public.image_asset ia ON ((ia.image_asset_id = ial.image_asset_id)))
     LEFT JOIN public.image_variant iv ON ((iv.image_asset_id = ia.image_asset_id)))
     LEFT JOIN public.variant v ON ((v.variant_id = iv.variant_id)))
  WHERE (ial.owner_type = 'provider'::text);


ALTER VIEW public.image_choice_provider OWNER TO neondb_owner;

--
-- Name: image_people_media; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.image_people_media AS
 SELECT ial.owner_id AS people_id,
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
    v.path_str,
    v.variant_str,
    v.variant_name AS variant_key,
    v.target_width,
    v.target_height,
    v.is_cropped
   FROM (((public.image_asset_link ial
     JOIN public.image_asset ia ON ((ia.image_asset_id = ial.image_asset_id)))
     LEFT JOIN public.image_variant iv ON ((iv.image_asset_id = ia.image_asset_id)))
     LEFT JOIN public.variant v ON ((v.variant_id = iv.variant_id)))
  WHERE (ial.owner_type = 'people'::text);


ALTER VIEW public.image_people_media OWNER TO neondb_owner;

--
-- Name: image_provider_media; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.image_provider_media AS
 SELECT ial.owner_id AS provider_id,
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
    v.path_str,
    v.variant_str,
    v.variant_name AS variant_key,
    v.target_width,
    v.target_height,
    v.is_cropped
   FROM (((public.image_asset_link ial
     JOIN public.image_asset ia ON ((ia.image_asset_id = ial.image_asset_id)))
     LEFT JOIN public.image_variant iv ON ((iv.image_asset_id = ia.image_asset_id)))
     LEFT JOIN public.variant v ON ((v.variant_id = iv.variant_id)))
  WHERE (ial.owner_type = 'provider'::text);


ALTER VIEW public.image_provider_media OWNER TO neondb_owner;

--
-- Name: image_variant_image_variant_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.image_variant_image_variant_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.image_variant_image_variant_id_seq OWNER TO neondb_owner;

--
-- Name: image_variant_image_variant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.image_variant_image_variant_id_seq OWNED BY public.image_variant.image_variant_id;


--
-- Name: keyword; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.keyword (
    keyword_id bigint NOT NULL,
    keyword_name text NOT NULL
);


ALTER TABLE public.keyword OWNER TO neondb_owner;

--
-- Name: keyword_keyword_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.keyword_keyword_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.keyword_keyword_id_seq OWNER TO neondb_owner;

--
-- Name: keyword_keyword_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.keyword_keyword_id_seq OWNED BY public.keyword.keyword_id;


--
-- Name: language; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.language (
    language_id bigint NOT NULL,
    language_name text NOT NULL
);


ALTER TABLE public.language OWNER TO neondb_owner;

--
-- Name: language_language_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.language_language_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.language_language_id_seq OWNER TO neondb_owner;

--
-- Name: language_language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.language_language_id_seq OWNED BY public.language.language_id;


--
-- Name: media; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media (
    media_id bigint NOT NULL,
    media_imdb_id text NOT NULL,
    media_title text NOT NULL,
    media_original_title text,
    media_type text,
    media_release_year integer,
    media_release_date date,
    media_runtime_seconds integer,
    media_review_rating numeric(3,1),
    media_vote_count integer,
    media_plot text,
    media_certificate text,
    media_production_status text,
    raw_json jsonb,
    fetched_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    access_count integer DEFAULT 0,
    media_metascore integer
);


ALTER TABLE public.media OWNER TO neondb_owner;

--
-- Name: media_connection; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_connection (
    media_id bigint NOT NULL,
    related_media_id bigint NOT NULL,
    related_media_year integer,
    related_media_imdb_id text,
    connection_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.media_connection OWNER TO neondb_owner;

--
-- Name: media_genre; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_genre (
    media_id bigint NOT NULL,
    genre_id bigint NOT NULL
);


ALTER TABLE public.media_genre OWNER TO neondb_owner;

--
-- Name: media_person; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_person (
    media_id bigint NOT NULL,
    person_id bigint NOT NULL,
    credit_category text NOT NULL,
    character_names text[],
    enhanced boolean DEFAULT false
);


ALTER TABLE public.media_person OWNER TO neondb_owner;

--
-- Name: media_provider; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_provider (
    media_id bigint NOT NULL,
    provider_id bigint NOT NULL,
    provider_desc text,
    provider_link text NOT NULL
);


ALTER TABLE public.media_provider OWNER TO neondb_owner;

--
-- Name: person; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.person (
    person_id bigint NOT NULL,
    person_imdb_id text NOT NULL,
    person_name text NOT NULL,
    person_image text
);


ALTER TABLE public.person OWNER TO neondb_owner;

--
-- Name: provider; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.provider (
    provider_id bigint NOT NULL,
    provider_code character varying(255) NOT NULL,
    provider_name character varying(255),
    provider_title text,
    provider_title_alt text,
    provider_category character varying(255) NOT NULL
);


ALTER TABLE public.provider OWNER TO neondb_owner;

--
-- Name: media_full_view; Type: VIEW; Schema: public; Owner: neondb_owner
--

CREATE VIEW public.media_full_view AS
 SELECT m.media_id,
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
            WHEN (poster.variant_status = 'cached'::text) THEN poster.public_url
            ELSE NULL::text
        END, poster.public_url, poster.source_url) AS media_image,
    COALESCE(poster.width, poster.source_width) AS media_image_width,
    COALESCE(poster.height, poster.source_height) AS media_image_height,
        CASE
            WHEN (poster.image_asset_id IS NULL) THEN NULL::jsonb
            ELSE jsonb_build_object('image_asset_id', poster.image_asset_id,
                                    'image_variant_id', poster.image_variant_id,
                                    'image_kind', poster.image_kind,
                                    'variant_id', poster.variant_id,
                                    'variant_key', poster.variant_key,
                                    'path_str', poster.path_str,
                                    'variant_str', poster.variant_str,
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
                                    'cached_at', poster.cached_at)
        END AS poster_image_asset,
    COALESCE(
        CASE
            WHEN (backdrop.variant_status = 'cached'::text) THEN backdrop.public_url
            ELSE NULL::text
        END, backdrop.public_url, backdrop.source_url) AS backdrop_image,
        CASE
            WHEN (backdrop.image_asset_id IS NULL) THEN NULL::jsonb
            ELSE jsonb_build_object('image_asset_id', backdrop.image_asset_id, 'image_variant_id', backdrop.image_variant_id, 'image_kind', backdrop.image_kind, 'variant_id', backdrop.variant_id, 'variant_key', backdrop.variant_key, 'path_str', backdrop.path_str, 'variant_str', backdrop.variant_str, 'source_url', backdrop.source_url, 'public_url', backdrop.public_url, 'width', backdrop.width, 'height', backdrop.height, 'asset_status', backdrop.asset_status, 'variant_status', backdrop.variant_status,
                                    backdrop.sort_order)
        END AS backdrop_image_asset,
    m.media_certificate,
    m.media_production_status,
    COALESCE(( SELECT jsonb_agg(jsonb_build_object('genre_id', g.genre_id, 'genre_name', g.genre_name) ORDER BY g.genre_name) AS jsonb_agg
           FROM (public.media_genre mg
             JOIN public.genre g ON ((g.genre_id = mg.genre_id)))
          WHERE (mg.media_id = m.media_id)), '[]'::jsonb) AS genres,
    COALESCE(( SELECT jsonb_agg(jsonb_build_object('person_id', p.person_id, 'person_imdb_id', p.person_imdb_id, 'person_name', p.person_name, 'person_image', COALESCE(
                CASE
                    WHEN (person_img.variant_status = 'cached'::text) THEN person_img.public_url
                    ELSE NULL::text
                END, person_img.public_url, person_img.source_url, p.person_image), 'person_image_asset',
                CASE
                    WHEN (person_img.image_asset_id IS NULL) THEN NULL::jsonb
                    ELSE jsonb_build_object('image_asset_id', person_img.image_asset_id, 'image_variant_id', person_img.image_variant_id, 'image_kind', person_img.image_kind, 'variant_id', person_img.variant_id, 'variant_key', person_img.variant_key, 'path_str', person_img.path_str, 'variant_str', person_img.variant_str, 'source_url', person_img.source_url, 'public_url', person_img.public_url, 'width', person_img.width, 'height', person_img.height, 'asset_status', person_img.asset_status, 'variant_status', person_img.variant_status)
                END, 'credit_category', mp.credit_category, 'character_names', COALESCE(to_jsonb(mp.character_names), '[]'::jsonb), 'enhanced', mp.enhanced) ORDER BY mp.credit_category, p.person_name) AS jsonb_agg
           FROM ((public.media_person mp
             JOIN public.person p ON ((p.person_id = mp.person_id)))
             LEFT JOIN LATERAL ( SELECT pim.people_id,
                    pim.image_kind,
                    pim.is_primary,
                    pim.sort_order,
                    pim.image_asset_id,
                    pim.source_provider,
                    pim.source_url,
                    pim.source_width,
                    pim.source_height,
                    pim.asset_status,
                    pim.image_variant_id,
                    pim.public_url,
                    pim.object_key,
                    pim.storage_provider,
                    pim.storage_bucket,
                    pim.content_type,
                    pim.width,
                    pim.height,
                    pim.byte_size,
                    pim.sha256,
                    pim.variant_status,
                    pim.cached_at,
                    pim.variant_id,
                    pim.path_str,
                    pim.variant_str,
                    pim.variant_key,
                    pim.target_width,
                    pim.target_height,
                    pim.is_cropped
                   FROM public.image_choice_people pim
                  WHERE ((pim.people_id = p.person_id) AND (pim.image_kind = ANY (ARRAY['headshot'::text, 'profile'::text, 'person_image'::text])))
                  ORDER BY pim.is_primary DESC, pim.sort_order, (pim.variant_status = 'cached'::text) DESC, (pim.public_url IS NOT NULL) DESC, (pim.variant_key = 'people_300x450'::text) DESC, (pim.variant_key = 'people_original'::text) DESC, pim.cached_at DESC NULLS LAST
                 LIMIT 1) person_img ON (true))
          WHERE (mp.media_id = m.media_id)), '[]'::jsonb) AS credits,
    COALESCE(( SELECT jsonb_agg(jsonb_build_object('provider_id', pr.provider_id, 'provider_code', pr.provider_code, 'provider_name', pr.provider_name, 'provider_title', pr.provider_title, 'provider_title_alt', pr.provider_title_alt, 'provider_category', pr.provider_category, 'provider_desc', mpv.provider_desc, 'provider_link', mpv.provider_link, 'provider_image', COALESCE(
                CASE
                    WHEN (provider_logo.variant_status = 'cached'::text) THEN provider_logo.public_url
                    ELSE NULL::text
                END, provider_logo.public_url, provider_logo.source_url), 'provider_image_asset',
                CASE
                    WHEN (provider_logo.image_asset_id IS NULL) THEN NULL::jsonb
                    ELSE jsonb_build_object('image_asset_id', provider_logo.image_asset_id, 'image_variant_id', provider_logo.image_variant_id, 'image_kind', provider_logo.image_kind, 'variant_id', provider_logo.variant_id, 'variant_key', provider_logo.variant_key, 'path_str', provider_logo.path_str, 'variant_str', provider_logo.variant_str, 'source_url', provider_logo.source_url, 'public_url', provider_logo.public_url, 'width', provider_logo.width, 'height', provider_logo.height, 'asset_status', provider_logo.asset_status, 'variant_status', provider_logo.variant_status)
                END) ORDER BY pr.provider_category, pr.provider_name, pr.provider_title) AS jsonb_agg
           FROM ((public.media_provider mpv
             JOIN public.provider pr ON ((pr.provider_id = mpv.provider_id)))
             LEFT JOIN LATERAL ( SELECT primg.provider_id,
                    primg.image_kind,
                    primg.is_primary,
                    primg.sort_order,
                    primg.image_asset_id,
                    primg.source_provider,
                    primg.source_url,
                    primg.source_width,
                    primg.source_height,
                    primg.asset_status,
                    primg.image_variant_id,
                    primg.public_url,
                    primg.object_key,
                    primg.storage_provider,
                    primg.storage_bucket,
                    primg.content_type,
                    primg.width,
                    primg.height,
                    primg.byte_size,
                    primg.sha256,
                    primg.variant_status,
                    primg.cached_at,
                    primg.variant_id,
                    primg.path_str,
                    primg.variant_str,
                    primg.variant_key,
                    primg.target_width,
                    primg.target_height,
                    primg.is_cropped
                   FROM public.image_choice_provider primg
                  WHERE ((primg.provider_id = pr.provider_id) AND (primg.image_kind = ANY (ARRAY['provider_logo'::text, 'logo'::text])))
                  ORDER BY primg.is_primary DESC, primg.sort_order, (primg.variant_status = 'cached'::text) DESC, (primg.public_url IS NOT NULL) DESC, (primg.variant_key = 'provider_logo_150x225'::text) DESC, (primg.variant_key = 'provider_logo_original'::text) DESC, primg.cached_at DESC NULLS LAST
                 LIMIT 1) provider_logo ON (true))
          WHERE (mpv.media_id = m.media_id)), '[]'::jsonb) AS providers,
    m.fetched_at,
    m.updated_at,
    m.access_count
   FROM ((public.media m
     LEFT JOIN LATERAL ( SELECT img.media_id,
            img.image_kind,
            img.is_primary,
            img.sort_order,
            img.image_asset_id,
            img.source_provider,
            img.source_url,
            img.source_width,
            img.source_height,
            img.asset_status,
            img.image_variant_id,
            img.public_url,
            img.object_key,
            img.storage_provider,
            img.storage_bucket,
            img.content_type,
            img.width,
            img.height,
            img.byte_size,
            img.sha256,
            img.variant_status,
            img.cached_at,
            img.variant_id,
            img.path_str,
            img.variant_str,
            img.variant_key,
            img.target_width,
            img.target_height,
            img.is_cropped
           FROM public.image_choice_media img
          WHERE ((img.media_id = m.media_id) AND (img.image_kind = 'poster'::text))
          ORDER BY img.is_primary DESC, img.sort_order, (img.variant_status = 'cached'::text) DESC, (img.public_url IS NOT NULL) DESC, (img.variant_key = 'poster_200x300'::text) DESC, (img.variant_key = 'poster_1000x1500'::text) DESC, (img.variant_key = 'poster_original'::text) DESC, img.cached_at DESC NULLS LAST
         LIMIT 1) poster ON (true))
     LEFT JOIN LATERAL ( SELECT img.media_id,
            img.image_kind,
            img.is_primary,
            img.sort_order,
            img.image_asset_id,
            img.source_provider,
            img.source_url,
            img.source_width,
            img.source_height,
            img.asset_status,
            img.image_variant_id,
            img.public_url,
            img.object_key,
            img.storage_provider,
            img.storage_bucket,
            img.content_type,
            img.width,
            img.height,
            img.byte_size,
            img.sha256,
            img.variant_status,
            img.cached_at,
            img.variant_id,
            img.path_str,
            img.variant_str,
            img.variant_key,
            img.target_width,
            img.target_height,
            img.is_cropped
           FROM public.image_choice_media img
          WHERE ((img.media_id = m.media_id) AND (img.image_kind = 'backdrop'::text))
          ORDER BY img.is_primary DESC, img.sort_order, (img.variant_status = 'cached'::text) DESC, (img.public_url IS NOT NULL) DESC, (img.variant_key = 'backdrop_1280x720'::text) DESC, (img.variant_key = 'backdrop_original'::text) DESC, img.cached_at DESC NULLS LAST
         LIMIT 1) backdrop ON (true));


ALTER VIEW public.media_full_view OWNER TO neondb_owner;

--
-- Name: media_keyword; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_keyword (
    media_id bigint NOT NULL,
    keyword_id bigint NOT NULL
);


ALTER TABLE public.media_keyword OWNER TO neondb_owner;

--
-- Name: media_language; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_language (
    media_id bigint NOT NULL,
    language_id bigint NOT NULL
);


ALTER TABLE public.media_language OWNER TO neondb_owner;

--
-- Name: media_media_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.media_media_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.media_media_id_seq OWNER TO neondb_owner;

--
-- Name: media_media_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.media_media_id_seq OWNED BY public.media.media_id;


--
-- Name: media_similar_titles; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.media_similar_titles (
    media_id bigint NOT NULL,
    related_media_id bigint NOT NULL,
    related_media_imdb_id text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.media_similar_titles OWNER TO neondb_owner;

--
-- Name: person_person_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.person_person_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.person_person_id_seq OWNER TO neondb_owner;

--
-- Name: person_person_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.person_person_id_seq OWNED BY public.person.person_id;


--
-- Name: provider_provider_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.provider_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.provider_provider_id_seq OWNER TO neondb_owner;

--
-- Name: provider_provider_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.provider_provider_id_seq OWNED BY public.provider.provider_id;


--
-- Name: raw_imdb_payloads; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.raw_imdb_payloads (
    id bigint NOT NULL,
    source text NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    payload jsonb NOT NULL,
    error_count integer DEFAULT 0,
    fetched_at timestamp with time zone DEFAULT now(),
    processed_at timestamp with time zone,
    status text DEFAULT 'new'::text,
    count integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.raw_imdb_payloads OWNER TO neondb_owner;

--
-- Name: raw_imdb_payloads_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.raw_imdb_payloads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.raw_imdb_payloads_id_seq OWNER TO neondb_owner;

--
-- Name: raw_imdb_payloads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.raw_imdb_payloads_id_seq OWNED BY public.raw_imdb_payloads.id;


--
-- Name: trending_snapshot; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.trending_snapshot (
    id bigint NOT NULL,
    media_id bigint,
    rank integer NOT NULL,
    snapshot_date timestamp without time zone DEFAULT CURRENT_DATE,
    source text DEFAULT 'imdb'::text
);


ALTER TABLE public.trending_snapshot OWNER TO neondb_owner;

--
-- Name: trending_snapshot_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.trending_snapshot_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.trending_snapshot_id_seq OWNER TO neondb_owner;

--
-- Name: trending_snapshot_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.trending_snapshot_id_seq OWNED BY public.trending_snapshot.id;


--
-- Name: variant_variant_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.variant_variant_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.variant_variant_id_seq OWNER TO neondb_owner;

--
-- Name: variant_variant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.variant_variant_id_seq OWNED BY public.variant.variant_id;


--
-- Name: connection connection_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.connection ALTER COLUMN connection_id SET DEFAULT nextval('public.connection_connection_id_seq'::regclass);


--
-- Name: errors error_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.errors ALTER COLUMN error_id SET DEFAULT nextval('public.errors_error_id_seq'::regclass);


--
-- Name: genre genre_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.genre ALTER COLUMN genre_id SET DEFAULT nextval('public.genre_genre_id_seq'::regclass);


--
-- Name: image_asset image_asset_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_asset ALTER COLUMN image_asset_id SET DEFAULT nextval('public.image_asset_image_asset_id_seq'::regclass);


--
-- Name: image_asset_link image_asset_link_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_asset_link ALTER COLUMN image_asset_link_id SET DEFAULT nextval('public.image_asset_link_image_asset_link_id_seq'::regclass);


--
-- Name: image_variant image_variant_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_variant ALTER COLUMN image_variant_id SET DEFAULT nextval('public.image_variant_image_variant_id_seq'::regclass);


--
-- Name: keyword keyword_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.keyword ALTER COLUMN keyword_id SET DEFAULT nextval('public.keyword_keyword_id_seq'::regclass);


--
-- Name: language language_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.language ALTER COLUMN language_id SET DEFAULT nextval('public.language_language_id_seq'::regclass);


--
-- Name: media media_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media ALTER COLUMN media_id SET DEFAULT nextval('public.media_media_id_seq'::regclass);


--
-- Name: person person_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.person ALTER COLUMN person_id SET DEFAULT nextval('public.person_person_id_seq'::regclass);


--
-- Name: provider provider_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.provider ALTER COLUMN provider_id SET DEFAULT nextval('public.provider_provider_id_seq'::regclass);


--
-- Name: raw_imdb_payloads id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.raw_imdb_payloads ALTER COLUMN id SET DEFAULT nextval('public.raw_imdb_payloads_id_seq'::regclass);


--
-- Name: trending_snapshot id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.trending_snapshot ALTER COLUMN id SET DEFAULT nextval('public.trending_snapshot_id_seq'::regclass);


--
-- Name: variant variant_id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.variant ALTER COLUMN variant_id SET DEFAULT nextval('public.variant_variant_id_seq'::regclass);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: invitation invitation_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT invitation_pkey PRIMARY KEY (id);


--
-- Name: jwks jwks_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.jwks
    ADD CONSTRAINT jwks_pkey PRIMARY KEY (id);


--
-- Name: member member_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT member_pkey PRIMARY KEY (id);


--
-- Name: organization organization_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (id);


--
-- Name: organization organization_slug_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.organization
    ADD CONSTRAINT organization_slug_key UNIQUE (slug);


--
-- Name: project_config project_config_endpoint_id_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.project_config
    ADD CONSTRAINT project_config_endpoint_id_key UNIQUE (endpoint_id);


--
-- Name: project_config project_config_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.project_config
    ADD CONSTRAINT project_config_pkey PRIMARY KEY (id);


--
-- Name: session session_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT session_pkey PRIMARY KEY (id);


--
-- Name: session session_token_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT session_token_key UNIQUE (token);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: verification verification_pkey; Type: CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.verification
    ADD CONSTRAINT verification_pkey PRIMARY KEY (id);


--
-- Name: connection connection_connection_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.connection
    ADD CONSTRAINT connection_connection_name_key UNIQUE (connection_name);


--
-- Name: connection connection_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.connection
    ADD CONSTRAINT connection_pkey PRIMARY KEY (connection_id);


--
-- Name: errors errors_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (error_id);


--
-- Name: genre genre_genre_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.genre
    ADD CONSTRAINT genre_genre_name_key UNIQUE (genre_name);


--
-- Name: genre genre_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.genre
    ADD CONSTRAINT genre_pkey PRIMARY KEY (genre_id);


--
-- Name: image_asset_link image_asset_link_owner_type_owner_id_image_kind_image_asset_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_asset_link
    ADD CONSTRAINT image_asset_link_owner_type_owner_id_image_kind_image_asset_key UNIQUE (owner_type, owner_id, image_kind, image_asset_id);


--
-- Name: image_asset_link image_asset_link_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_asset_link
    ADD CONSTRAINT image_asset_link_pkey PRIMARY KEY (image_asset_link_id);


--
-- Name: image_asset image_asset_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_asset
    ADD CONSTRAINT image_asset_pkey PRIMARY KEY (image_asset_id);


--
-- Name: image_asset image_asset_unique_source_url; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_asset
    ADD CONSTRAINT image_asset_unique_source_url UNIQUE (source_url);


--
-- Name: image_variant image_variant_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_variant
    ADD CONSTRAINT image_variant_pkey PRIMARY KEY (image_variant_id);


--
-- Name: image_variant image_variant_unique_asset_variant_storage; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_variant
    ADD CONSTRAINT image_variant_unique_asset_variant_storage UNIQUE (image_asset_id, variant_id, storage_provider, storage_bucket);


--
-- Name: keyword keyword_keyword_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.keyword
    ADD CONSTRAINT keyword_keyword_name_key UNIQUE (keyword_name);


--
-- Name: keyword keyword_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.keyword
    ADD CONSTRAINT keyword_pkey PRIMARY KEY (keyword_id);


--
-- Name: language language_language_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT language_language_name_key UNIQUE (language_name);


--
-- Name: language language_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT language_pkey PRIMARY KEY (language_id);


--
-- Name: media_connection media_connection_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_connection
    ADD CONSTRAINT media_connection_pkey PRIMARY KEY (media_id, related_media_id, connection_id);


--
-- Name: media_genre media_genre_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_genre
    ADD CONSTRAINT media_genre_pkey PRIMARY KEY (media_id, genre_id);


--
-- Name: media_keyword media_keyword_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_keyword
    ADD CONSTRAINT media_keyword_pkey PRIMARY KEY (media_id, keyword_id);


--
-- Name: media_language media_language_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_language
    ADD CONSTRAINT media_language_pkey PRIMARY KEY (media_id, language_id);


--
-- Name: media media_media_imdb_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_media_imdb_id_key UNIQUE (media_imdb_id);


--
-- Name: media_person media_person_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_person
    ADD CONSTRAINT media_person_pkey PRIMARY KEY (media_id, person_id, credit_category);


--
-- Name: media media_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media
    ADD CONSTRAINT media_pkey PRIMARY KEY (media_id);


--
-- Name: media_provider media_provider_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_provider
    ADD CONSTRAINT media_provider_pkey PRIMARY KEY (media_id, provider_id);


--
-- Name: media_similar_titles media_similar_titles_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_similar_titles
    ADD CONSTRAINT media_similar_titles_pkey PRIMARY KEY (media_id, related_media_id);


--
-- Name: person person_person_imdb_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.person
    ADD CONSTRAINT person_person_imdb_id_key UNIQUE (person_imdb_id);


--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (person_id);


--
-- Name: provider provider_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.provider
    ADD CONSTRAINT provider_pkey PRIMARY KEY (provider_id);


--
-- Name: raw_imdb_payloads raw_imdb_payloads_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.raw_imdb_payloads
    ADD CONSTRAINT raw_imdb_payloads_pkey PRIMARY KEY (id);


--
-- Name: trending_snapshot trending_snapshot_media_id_snapshot_date_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.trending_snapshot
    ADD CONSTRAINT trending_snapshot_media_id_snapshot_date_key UNIQUE (media_id, snapshot_date);


--
-- Name: trending_snapshot trending_snapshot_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.trending_snapshot
    ADD CONSTRAINT trending_snapshot_pkey PRIMARY KEY (id);


--
-- Name: provider unique_provider_category_code; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.provider
    ADD CONSTRAINT unique_provider_category_code UNIQUE (provider_category, provider_code);


--
-- Name: variant variant_path_str_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.variant
    ADD CONSTRAINT variant_path_str_key UNIQUE (path_str);


--
-- Name: variant variant_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.variant
    ADD CONSTRAINT variant_pkey PRIMARY KEY (variant_id);


--
-- Name: variant variant_variant_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.variant
    ADD CONSTRAINT variant_variant_name_key UNIQUE (variant_name);


--
-- Name: account_userId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "account_userId_idx" ON neon_auth.account USING btree ("userId");


--
-- Name: invitation_email_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX invitation_email_idx ON neon_auth.invitation USING btree (email);


--
-- Name: invitation_organizationId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "invitation_organizationId_idx" ON neon_auth.invitation USING btree ("organizationId");


--
-- Name: member_organizationId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "member_organizationId_idx" ON neon_auth.member USING btree ("organizationId");


--
-- Name: member_userId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "member_userId_idx" ON neon_auth.member USING btree ("userId");


--
-- Name: organization_slug_uidx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE UNIQUE INDEX organization_slug_uidx ON neon_auth.organization USING btree (slug);


--
-- Name: session_userId_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX "session_userId_idx" ON neon_auth.session USING btree ("userId");


--
-- Name: verification_identifier_idx; Type: INDEX; Schema: neon_auth; Owner: neon_auth
--

CREATE INDEX verification_identifier_idx ON neon_auth.verification USING btree (identifier);


--
-- Name: uq_image_asset_source_url; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE UNIQUE INDEX uq_image_asset_source_url ON public.image_asset USING btree (source_url);


--
-- Name: account account_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.account
    ADD CONSTRAINT "account_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: invitation invitation_inviterId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT "invitation_inviterId_fkey" FOREIGN KEY ("inviterId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: invitation invitation_organizationId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.invitation
    ADD CONSTRAINT "invitation_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES neon_auth.organization(id) ON DELETE CASCADE;


--
-- Name: member member_organizationId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT "member_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES neon_auth.organization(id) ON DELETE CASCADE;


--
-- Name: member member_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.member
    ADD CONSTRAINT "member_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: session session_userId_fkey; Type: FK CONSTRAINT; Schema: neon_auth; Owner: neon_auth
--

ALTER TABLE ONLY neon_auth.session
    ADD CONSTRAINT "session_userId_fkey" FOREIGN KEY ("userId") REFERENCES neon_auth."user"(id) ON DELETE CASCADE;


--
-- Name: image_variant image_variant_image_asset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_variant
    ADD CONSTRAINT image_variant_image_asset_id_fkey FOREIGN KEY (image_asset_id) REFERENCES public.image_asset(image_asset_id) ON DELETE CASCADE;


--
-- Name: image_variant image_variant_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.image_variant
    ADD CONSTRAINT image_variant_variant_id_fkey FOREIGN KEY (variant_id) REFERENCES public.variant(variant_id) ON DELETE CASCADE;


--
-- Name: media_connection media_connection_connection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_connection
    ADD CONSTRAINT media_connection_connection_id_fkey FOREIGN KEY (connection_id) REFERENCES public.connection(connection_id);


--
-- Name: media_connection media_connection_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_connection
    ADD CONSTRAINT media_connection_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id);


--
-- Name: media_connection media_connection_related_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_connection
    ADD CONSTRAINT media_connection_related_media_id_fkey FOREIGN KEY (related_media_id) REFERENCES public.media(media_id);


--
-- Name: media_genre media_genre_genre_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_genre
    ADD CONSTRAINT media_genre_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES public.genre(genre_id) ON DELETE CASCADE;


--
-- Name: media_genre media_genre_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_genre
    ADD CONSTRAINT media_genre_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id) ON DELETE CASCADE;


--
-- Name: media_keyword media_keyword_keyword_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_keyword
    ADD CONSTRAINT media_keyword_keyword_id_fkey FOREIGN KEY (keyword_id) REFERENCES public.keyword(keyword_id) ON DELETE CASCADE;


--
-- Name: media_keyword media_keyword_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_keyword
    ADD CONSTRAINT media_keyword_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id) ON DELETE CASCADE;


--
-- Name: media_language media_language_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_language
    ADD CONSTRAINT media_language_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.language(language_id) ON DELETE CASCADE;


--
-- Name: media_language media_language_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_language
    ADD CONSTRAINT media_language_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id) ON DELETE CASCADE;


--
-- Name: media_person media_person_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_person
    ADD CONSTRAINT media_person_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id) ON DELETE CASCADE;


--
-- Name: media_person media_person_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_person
    ADD CONSTRAINT media_person_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.person(person_id) ON DELETE CASCADE;


--
-- Name: media_provider media_provider_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_provider
    ADD CONSTRAINT media_provider_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id) ON DELETE CASCADE;


--
-- Name: media_provider media_provider_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_provider
    ADD CONSTRAINT media_provider_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.provider(provider_id) ON DELETE CASCADE;


--
-- Name: media_similar_titles media_similar_titles_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_similar_titles
    ADD CONSTRAINT media_similar_titles_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id);


--
-- Name: media_similar_titles media_similar_titles_related_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.media_similar_titles
    ADD CONSTRAINT media_similar_titles_related_media_id_fkey FOREIGN KEY (related_media_id) REFERENCES public.media(media_id);


--
-- Name: trending_snapshot trending_snapshot_media_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.trending_snapshot
    ADD CONSTRAINT trending_snapshot_media_id_fkey FOREIGN KEY (media_id) REFERENCES public.media(media_id) ON DELETE CASCADE;




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

    ('provider_logo_original',
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

    ('provider_logo_225x150',
     'provider',
     'provider_logo',
     '225x150',
     'provider/provider_logo/255x150',
     225,
     150,
     TRUE)

ON CONFLICT (variant_name) DO NOTHING;




