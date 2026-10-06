"""Create the order tables in Cloudflare D1 and fill them with fake data.

Usage (from backend/, with CF_ACCOUNT_ID, CF_D1_DATABASE_ID and CF_API_TOKEN
set in .env):

    uv run python db/load.py

Re-runnable: schema.sql drops and recreates the order tables. The spend-cap
table, api_usage, is managed by the API and is not touched.
"""

import sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DB_DIR))

from order_generator import d1  # noqa: E402
from seed import INSERT_ORDER, seed_statements  # noqa: E402


def main() -> None:
    d1.query((DB_DIR / "schema.sql").read_text(encoding="utf-8"))
    print("ran schema.sql")

    statements = seed_statements()
    for statement in statements:
        d1.query(statement)
    print(f"ran {len(statements)} seed statements")

    for table in INSERT_ORDER:
        count = d1.query(f"SELECT count(*) FROM {table}").rows[0][0]
        print(f"{table:28} {count:>6}")


if __name__ == "__main__":
    main()
