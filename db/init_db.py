"""Applies schema.sql to the database in DATABASE_URL.  Usage: python -m db.init_db

Safe to run many times: every statement uses IF NOT EXISTS.
"""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

SCHEMA = Path(__file__).with_name("schema.sql")


def init_db(database_url: str) -> None:
    with psycopg.connect(database_url) as conn:
        conn.execute(SCHEMA.read_text(encoding="utf-8"))


if __name__ == "__main__":
    load_dotenv()
    init_db(os.environ["DATABASE_URL"])
    print("schema applied")
