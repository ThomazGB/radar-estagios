"""Runs the whole pipeline: collect -> clean -> load.  Usage: python -m etl.pipeline"""
import os

from dotenv import load_dotenv

from db.init_db import init_db
from etl.clean import clean
from etl.collect import collect
from etl.load import load


def main() -> None:
    load_dotenv()
    database_url = os.environ["DATABASE_URL"]
    init_db(database_url)  # makes sure the tables exist (first run on Neon, CI...)
    raw = collect()
    print(f"raw postings: {len(raw)}")
    df = clean(raw)
    print(f"after cleaning: {len(df)}")
    saved = load(df, database_url)
    print(f"saved to database: {saved}")


if __name__ == "__main__":
    main()
