"""Create the order tables and fill them with fake data.

Usage (from backend/, with DATABASE_URL set in .env):

    uv run python db/load.py
"""

import os
from pathlib import Path

import psycopg
from dotenv import find_dotenv, load_dotenv


DB_DIR = Path(__file__).resolve().parent
SCRIPTS = ("schema.sql", "seed.sql")
COUNTED_TABLES = (
    "orders",
    "order_lines",
    "order_addresses",
    "customer_contacts",
    "contact_methods",
)


def main() -> None:
    load_dotenv(find_dotenv())
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is not set. Add it to backend/.env.")

    with psycopg.connect(database_url) as connection:
        for script_name in SCRIPTS:
            script = (DB_DIR / script_name).read_text(encoding="utf-8")
            with connection.cursor() as cursor:
                cursor.execute(script)
            connection.commit()
            print(f"ran {script_name}")

        with connection.cursor() as cursor:
            for table in COUNTED_TABLES:
                cursor.execute(f"SELECT count(*) FROM {table}")
                print(f"{table:28} {cursor.fetchone()[0]:>6}")


if __name__ == "__main__":
    main()
