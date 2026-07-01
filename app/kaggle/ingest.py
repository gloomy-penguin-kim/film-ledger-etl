import os
from datetime import datetime, timezone

import psycopg
from dotenv import load_dotenv, find_dotenv
from psycopg import ProgrammingError

load_dotenv(find_dotenv())

from pathlib import Path
import ast
import json
import re
import pprint

import pandas as pd


def connect(conn=None):
    if not conn:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.")
        conn = psycopg.connect(database_url)
    return conn


def execute_neon_query(db, sql="", args=None):
    """Run a SQL query and return the results as a list of dictionaries"""
    if not sql:
        raise ValueError("SQL query is empty. Please provide a valid SQL query.")
    try:
        with db.cursor() as cur:
            cur.execute(sql, (args or ()))
            db.commit()
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                return results
    except psycopg.Error as e:
        print(f"Database error: {e}")
        db.rollback()
        return []


db = connect()

BASE_DIR = Path("C:\\Users\\gloom\\PycharmProjects\\FilmLedger") # Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

DB_PATH = PROCESSED_DIR / "filmledger.duckdb"
PARQUET_PATH = PROCESSED_DIR / "movies.parquet"

COLUMN_RENAMES = {
    "Title": "title",
    "Year": "year",
    "Duration": "duration",
    "MPA": "mpa",
    "Rating": "rating",
    "Votes": "votes",
    "meta_score": "meta_score",
    "description": "description",
    "Movie Link": "movie_link",
    "link": "link",
    "writers": "writers",
    "directors": "directors",
    "stars": "stars",
    "budget": "budget",
    "opening_weekend_Gross": "opening_weekend_gross",
    "grossWorldWide": "gross_worldwide",
    "gross_US_Canada": "gross_us_canada",
    "release_date": "release_date",
    "countries_origin": "countrys",
    "filming_locations": "filming_locations",
    "production_company": "production_companys",
    "awards_content": "awards_content",
    "genres": "genres",
    "Languages": "languages",
}

from datetime import datetime

def normalize_date(date_str: str | None) -> str | None:
    """
    Normalize various human-readable dates into YYYY-MM-DD.

    Examples:
        "April 1920"      -> "1920-04-01"
        "1920"            -> "1920-01-01"
        "April 5, 1920"   -> "1920-04-05"
        "5 April 1920"    -> "1920-04-05"
        None              -> None
    """

    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    formats = [
        "%B %d, %Y",   # April 5, 1920
        "%d %B %Y",    # 5 April 1920
        "%B %Y",       # April 1920
        "%Y",          # 1920
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None

def parse_int(value):
    """
    Convert values like '1,234,567' into 1234567.
    Returns None when empty or invalid.
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "na", "-"}:
        return None

    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def parse_float(value):
    """
    Convert ratings like '8.7' into 8.7.
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "na", "-"}:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_money(value):
    """
    Convert money-ish values like '$123,456,789' into 123456789.
    This intentionally ignores currency symbols for MVP analytics.
    """
    return parse_int(value)


def parse_duration_minutes(value):
    """
    Handles common IMDb-ish forms:
    - '142 min'
    - '2h 22m'
    - '2 h 22 m'
    - '142'
    """
    if pd.isna(value):
        return None

    text = str(value).strip().lower()
    if not text or text in {"nan", "none", "n/a", "na", "-"}:
        return None

    hours_match = re.search(r"(\d+)\s*h", text)
    mins_match = re.search(r"(\d+)\s*m", text)

    if hours_match or mins_match:
        hours = int(hours_match.group(1)) if hours_match else 0
        mins = int(mins_match.group(1)) if mins_match else 0
        return hours * 60 + mins

    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def clean_title(value):
    """
    Remove leading list/rank numbers from movie titles.

    Examples:
    - '1. Il trittico dell\\'amore' -> 'Il trittico dell\\'amore'
    - '10. Pollyanna' -> 'Pollyanna'
    - '#12 The Movie' -> 'The Movie'
    """
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if not text:
        return ""

    # Handles:
    # 1. Title
    # 001. Title
    # #1 Title
    # #1. Title
    text = re.sub(r"^\s*#?\d+\s*\.?\s+", "", text)

    return text.strip()


def read_csv_safely(path: Path) -> pd.DataFrame:
    """
    IMDb/Kaggle CSVs sometimes have encoding quirks.
    Try UTF-8 first, then a forgiving fallback.
    """
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1")


def build_lookup_and_bridge(
        movies: pd.DataFrame,
        source_col: str,
        lookup_id_col: str,
        lookup_name_col: str,
):
    """
    Turn a multi-value movie column into:

    1. A lookup table:
       language_id | language_name

    2. A bridge table:
       movie_id | language_id
    """

    lookup_name_col = "name"

    exploded = (
        movies[["imdb_id", source_col]]
        .assign(value=movies[source_col].apply(split_multi_value))
        .explode("value")
    )

    exploded = exploded.dropna(subset=["value"])
    exploded["value"] = exploded["value"].astype(str).str.strip()
    exploded = exploded[exploded["value"] != ""]

    lookup = (
        exploded[["value"]]
        .drop_duplicates()
        .sort_values("value")
        .reset_index(drop=True)
    )

    lookup.insert(0, lookup_id_col, range(1, len(lookup) + 1))
    lookup = lookup.rename(columns={"value": lookup_name_col})

    bridge = exploded.merge(
        lookup,
        left_on="value",
        right_on=lookup_name_col,
        how="left",
    )

    bridge = (
        bridge[["imdb_id", lookup_name_col]]
        .drop_duplicates()
        .sort_values(["imdb_id", lookup_name_col])
        .reset_index(drop=True)
    )

    return lookup, bridge


def add_to_lookup_table(lookup, single):

    sql = f"select {single}_id, {single}_name from {single} order by {single}_name"
    results = execute_neon_query(db, sql)
    print(f"before adding records to {single}:", len(results))

    sql = f"insert into {single} ({single}_name) values (%s) on conflict do nothing returning {single}_id"
    with db.cursor() as cur:
        cur.executemany(sql, [(row.name,) for row in lookup.itertuples()])
    db.commit()

    sql = f"select {single}_id, {single}_name from {single} order by {single}_name"
    results = execute_neon_query(db, sql)
    print(f"after adding records to {single}:", len(results))


def add_to_person_table(lookup):

    sql = f"select person_id, person_imdb_id, person_name from person order by person_name"
    results = execute_neon_query(db, sql)
    print(f"before adding records to person:", len(results))

    sql = """insert into person (person_name)  
                select  inserted.person_name
                from    (select %s as person_name) as inserted
                        left outer join person p 
                            on p.person_name = inserted.person_name
                where   p.person_id is null  
             on conflict do nothing"""
    with db.cursor() as cur:
        cur.executemany(sql, [(row.name,) for row in lookup.itertuples()])
    db.commit()

    sql = f"select person_id, person_imdb_id, person_name from person order by person_name"
    results = execute_neon_query(db, sql)
    print(f"after adding records to person:", len(results))


def update_person_link_table(bridge, role):
    role = role.capitalize()

    sql = f"select * from media_person"
    results = execute_neon_query(db, sql)
    print(f"before adding records to media_person:", len(results))

    sql = """insert into media_person (media_id, person_id, credit_category) 
              select   m.media_id, g.person_id, %s as credit_category 
              from     media as m 
                       LEFT JOIN LATERAL (select * 
                             from person 
                             where person_name = %s
                             order by person_imdb_id ASC NULLS LAST
                             limit 1 ) as g  
                        on true 
              where    m.media_imdb_id = %s 
             on conflict do nothing"""
    with db.cursor() as cur:
        cur.executemany(sql, [(role, row.name, row.imdb_id, ) for row in bridge.itertuples()])
    db.commit()

    sql = f"select * from media_person"
    results = execute_neon_query(db, sql)
    print(f"after adding records to media_person:", len(results))


def update_link_table(bridge, single):

    sql = f"select * from media_{single}"
    results = execute_neon_query(db, sql)
    print(f"before adding records to media_{single}:", len(results))

    sql = (f"insert into media_{single} (media_id, {single}_id) "
           f"   select   m.media_id, g.{single}_id "
           f"   from     media as m "
           f"            join (select * from {single} where {single}_name = %s) as g "
           f"               on true " 
           f"   where m.media_imdb_id = %s"
           f"on conflict do nothing returning {single}_id")
    with db.cursor() as cur:
        cur.executemany(sql, [(row.name,row.imdb_id) for row in bridge.itertuples()])
    db.commit()

    sql = f"select * from media_{single}"
    results = execute_neon_query(db, sql)
    print(f"after adding records to media_{single}:", len(results))


def clean_lookup_value(value):
    """
    Clean one extracted lookup value.

    Turns None/null/nan-ish values into None.
    Turns normal text into stripped text.
    """
    if value is None:
        return None

    if pd.isna(value):
        return None

    text = str(value).strip().strip("'\"")

    if not text:
        return None

    if text.lower() in {"nan", "none", "null", "n/a", "na", "-"}:
        return None

    return text


def split_multi_value(value):
    """
    Split fields like:
    - 'English, French'
    - 'English | French'
    - 'English; French'
    - '["English"]'
    - '["French", "English"]'
    - '[null, "English"]'

    Returns a clean list like:
    ["French", "English"]
    """
    if value is None:
        return []

    if pd.isna(value):
        return []

    text = str(value).strip()

    if not text:
        return []

    if text.lower() in {"nan", "none", "null", "n/a", "na", "-"}:
        return []

    # The Kaggle data may contain JSON-looking lists:
    # ["English"], ["French","English"], [null,"German"]
    if text.startswith("[") and text.endswith("]"):
        parsed = None

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None

        if isinstance(parsed, list):
            cleaned = [clean_lookup_value(item) for item in parsed]
            return [item for item in cleaned if item is not None]

    # Fallback for comma/pipe/semicolon-separated text.
    parts = re.split(r"\s*,\s*|\s*\|\s*|\s*;\s*", text)
    cleaned = [clean_lookup_value(part) for part in parts]

    return [item for item in cleaned if item is not None]




def modify_link_tables(movies, single, plural=""):
    if not plural:  plural = single + "s"

    print("-"*80)
    print(single)

    genres, movie_genres = build_lookup_and_bridge(
        movies=movies,
        source_col=plural,
        lookup_id_col=single + "_id",
        lookup_name_col=single + "_name",
    )
    add_to_lookup_table(genres, single)
    update_link_table(movie_genres, single)


def modify_person_tables(movies, role):
    print("-"*80)
    print(role)

    for m in movies.itertuples():
        print(m)
        break

    persons, movie_persons = build_lookup_and_bridge(
        movies=movies,
        source_col=role,
        lookup_id_col="person_name",
        lookup_name_col="person_name",
    )
    add_to_person_table(persons)
    update_person_link_table(movie_persons, role)

def divide_by_60(value):
    if not value or value == 0:
        return 0
    else: return value * 60

def get_imdb_id(value):
    return Path(value).parent.name

def db_value(value):
    """Convert pandas NaN and 0 to None for PostgreSQL."""
    if pd.isna(value):
        return None

    if value == 0:
        return None

    return value

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(RAW_DIR.glob("**/merged_movies_data_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No merged CSV files found under {RAW_DIR}. "
            "Expected files like data/raw/2000/merged_movies_data_2000.csv"
        )

    print(f"Found {len(files)} merged CSV files.")

    frames = []

    for file_path in files:
        print(f"Reading {file_path}")
        df = read_csv_safely(file_path)

        # Preserve the source file/year for debugging.
        df["source_file"] = str(file_path.relative_to(BASE_DIR))

        year_match = re.search(r"merged_movies_data_(\d{4})", file_path.name)
        df["source_year"] = int(year_match.group(1)) if year_match else None

        frames.append(df)

    movies = pd.concat(frames, ignore_index=True)

    # Rename known columns into Python/SQL-friendly names.
    movies = movies.rename(columns=COLUMN_RENAMES)

    # Make sure all expected columns exist, even if one year's file is odd.
    expected_columns = set(COLUMN_RENAMES.values()) | {"source_file", "source_year"}
    for col in expected_columns:
        if col not in movies.columns:
            movies[col] = None

    # Clean useful fields.
    movies["year"] = movies["year"].apply(parse_int)
    movies["duration_minutes"] = movies["duration"].apply(parse_duration_minutes)
    movies["duration_seconds"] = movies["duration_minutes"].apply(divide_by_60)
    movies["rating"] = movies["rating"].apply(parse_float)
    movies["votes"] = movies["votes"].apply(parse_int)
    movies["meta_score"] = movies["meta_score"].apply(parse_int)
    movies["imdb_id"] = movies["movie_link"].apply(get_imdb_id)
    movies["release_date"] = movies["release_date"].apply(normalize_date)
    movies = movies.dropna(subset=["release_date"])
    movies = movies.dropna(subset=["description"])
    movies = movies[movies["release_date"] >= "1960-01-01"]

    for money_col in ["budget", "opening_weekend_gross", "gross_worldwide", "gross_us_canada"]:
        movies[f"{money_col}_usd"] = movies[money_col].apply(parse_money)

    # Basic cleanup.
    text_columns = [
        "title",
        "mpa",
        "description",
        "movie_link",
        "link",
        "writers",
        "directors",
        "stars",
        "release_date",
        "countrys",
        "filming_locations",
        "production_companys",
        "awards_content",
        "genres",
        "languages",
    ]
    for col in text_columns:
        movies[col] = movies[col].fillna("").astype(str).str.strip()

    # Remove leading IMDb/Kaggle ranking numbers from titles.
    movies["title"] = movies["title"].apply(clean_title)

    # Drop exact duplicate rows.
    before = len(movies)
    movies = movies.drop_duplicates()
    after = len(movies)

    movies = movies.reset_index(drop=True)
    movies.insert(0, "movie_id", range(1, len(movies) + 1))

    print(f"Rows before de-dupe: {before}")
    print(f"Rows after de-dupe:  {after}")

    # sql = """
    #     INSERT INTO media (
    #         media_imdb_id,
    #         media_title,
    #         media_type,
    #         media_release_year,
    #         media_release_date,
    #         media_runtime_seconds,
    #         media_review_rating,
    #         media_vote_count,
    #         media_plot,
    #         media_certificate,
    #         media_production_status,
    #         media_metascore,
    #         updated_at
    #     )
    #     VALUES (
    #         %(media_imdb_id)s,
    #         %(media_title)s,
    #         %(media_type)s,
    #         %(media_release_year)s,
    #         %(media_release_date)s,
    #         %(media_runtime_seconds)s,
    #         %(media_review_rating)s,
    #         %(media_vote_count)s,
    #         %(media_plot)s,
    #         %(media_certificate)s,
    #         %(media_production_status)s,
    #         %(media_metascore)s,
    #         now()
    #     )
    #     ON CONFLICT (media_imdb_id)
    #     DO UPDATE SET
    #         media_title = EXCLUDED.media_title,
    #         media_type = coalesce(media.media_type, EXCLUDED.media_type),
    #         media_release_year = EXCLUDED.media_release_year,
    #         media_release_date = EXCLUDED.media_release_date,
    #         media_runtime_seconds = EXCLUDED.media_runtime_seconds,
    #         media_review_rating = coalesce(media.media_review_rating, EXCLUDED.media_review_rating),
    #         media_vote_count = EXCLUDED.media_vote_count,
    #         media_plot = EXCLUDED.media_plot,
    #         media_certificate = EXCLUDED.media_certificate,
    #         media_production_status = EXCLUDED.media_production_status,
    #         media_metascore = coalesce(media.media_metascore, EXCLUDED.media_metascore),
    #         updated_at = now();
    # """
    #
    # with db.cursor() as cur:
    #     for media in movies.itertuples():
    #         p = {
    #             "media_imdb_id": media.imdb_id,
    #             "media_title": media.title,
    #             "media_type": "Movie",
    #             "media_release_year": media.year,
    #             "media_release_date": media.release_date,
    #             "media_runtime_seconds": db_value(media.duration_seconds),
    #             "media_review_rating": db_value(media.rating),
    #             "media_vote_count": db_value(media.votes),
    #             "media_plot": media.description,
    #             "media_certificate": media.mpa,
    #             "media_production_status": "Released",
    #             "media_metascore": db_value(media.meta_score),
    #         }
    #         try:
    #             cur.execute(sql, p)
    #             db.commit()
    #         except ProgrammingError as e:
    #             print(f"SQL Error: {e.pgcode} - {e.pgerror}")
    #         except Exception as e:
    #             print(e)
    #             pprint.pprint(p)
    #             quit()


    # modify_link_tables(movies, "genre")
    # modify_link_tables(movies, "language")
    # modify_link_tables(movies, "country")
    # modify_link_tables(movies, "production_company")
    # modify_tables(con, movies, "filming_location")


    # modify_person_tables(movies, "directors")
    modify_person_tables(movies, "stars")
    # modify_person_tables(movies, "writers")

    quit()

    # Rename known columns into Python/SQL-friendly names.
    movies = movies.rename(columns={"countries_origins": "countries_origin",
                                    "production_companys": "production_company"})

    # Write to Parquet using DuckDB, so we do not need pyarrow.
    con.execute(f"COPY movies TO '{PARQUET_PATH.as_posix()}' (FORMAT PARQUET)")

    # Quick sanity checks.
    total = con.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    year_range = con.execute("SELECT MIN(year), MAX(year) FROM movies").fetchone()
    top_movies = con.execute(
        """
        SELECT title, year, rating, votes
        FROM movies
        WHERE rating IS NOT NULL
        ORDER BY rating DESC, votes DESC NULLS LAST
        LIMIT 10
        """
    ).fetchdf()

    language_sample = con.execute(
        """
        SELECT l.language_name,
               COUNT(*) AS movie_count
        FROM languages l
                 JOIN movie_languages ml
                      ON l.language_id = ml.language_id
        GROUP BY l.language_name
        ORDER BY movie_count DESC, l.language_name
        LIMIT 20
        """
    ).fetchdf()

    print("\nTop languages:")
    print(language_sample)

    genre_sample = con.execute(
        """
        SELECT l.genre_name,
               COUNT(*) AS movie_count
        FROM genres l
                 JOIN movie_genres ml
                      ON l.genre_id = ml.genre_id
        GROUP BY l.genre_name
        ORDER BY movie_count DESC, l.genre_name
        LIMIT 10
        """
    ).fetchdf()

    print("\nTop genres:")
    print(genre_sample)

    con.close()

    print(f"Created database: {DB_PATH}")
    print(f"Created parquet:  {PARQUET_PATH}")
    print(f"Total movies:     {total}")
    print(f"Year range:       {year_range[0]} - {year_range[1]}")
    print("\\nTop sample:")
    print(top_movies)


if __name__ == "__main__":
    main()