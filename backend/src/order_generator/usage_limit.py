"""Durable spend cap for the public API.

The per-client limits in ``rate_limit`` live in memory, which is fine: they
exist to stop bursts, and a reset just grants one visitor a few extra requests.
The global cap is different — it bounds what this demo can cost in OpenAI
calls, so it has to survive restarts, redeploys and scale-to-zero. It is
counted in the Postgres database that is already in the request path.
"""

import os

import psycopg

from order_generator.extract.extract_orders import get_database_url


HOURLY_LIMIT = int(os.getenv("LIMIT_GLOBAL_HOURLY", "100"))
DAILY_LIMIT = int(os.getenv("LIMIT_GLOBAL_DAILY", "500"))

RETENTION = "2 days"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_usage (
    called_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS api_usage_called_at_idx ON api_usage (called_at);
"""

# One statement, one round trip: count both windows, insert only if both pass,
# and return a row when the request is allowed. Doing it in a single statement
# keeps it atomic, so two concurrent requests cannot both take the last slot.
CHECK_AND_RECORD_SQL = f"""
WITH windows AS (
    SELECT
        count(*) FILTER (WHERE called_at > now() - interval '1 hour') AS last_hour,
        count(*) FILTER (WHERE called_at > now() - interval '1 day') AS last_day
    FROM api_usage
),
pruned AS (
    DELETE FROM api_usage WHERE called_at < now() - interval '{RETENTION}'
)
INSERT INTO api_usage (called_at)
SELECT now()
FROM windows
WHERE last_hour < %(hourly_limit)s
  AND last_day < %(daily_limit)s
RETURNING called_at;
"""


class UsageLimitExceeded(Exception):
    """The global hourly or daily cap is spent."""


def ensure_usage_table() -> None:
    with psycopg.connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)


def check_and_record() -> None:
    """Record one API call, or raise if that would exceed the global caps.

    Raises ``UsageLimitExceeded`` when the cap is spent. Any other failure
    propagates: the caller treats it as a refusal, because a request that
    cannot reach the database cannot be served anyway, and letting it through
    would spend a model call on a request that is going to fail.
    """
    try:
        recorded = _record_one()
    except psycopg.errors.UndefinedTable:
        # Startup could not prepare the table (database asleep or unreachable
        # at boot); create it now rather than refusing every request.
        ensure_usage_table()
        recorded = _record_one()

    if not recorded:
        raise UsageLimitExceeded


def _record_one() -> bool:
    with psycopg.connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                CHECK_AND_RECORD_SQL,
                {"hourly_limit": HOURLY_LIMIT, "daily_limit": DAILY_LIMIT},
            )
            return cursor.fetchone() is not None


def current_usage() -> dict[str, int]:
    """Counts for the two windows, for logging and manual checks."""
    with psycopg.connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    count(*) FILTER (WHERE called_at > now() - interval '1 hour'),
                    count(*) FILTER (WHERE called_at > now() - interval '1 day')
                FROM api_usage
                """
            )
            last_hour, last_day = cursor.fetchone()

    return {"last_hour": last_hour, "last_day": last_day}
