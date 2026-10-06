"""Durable spend cap for the public API.

The per-client limits in ``rate_limit`` live in memory, which is fine: they
exist to stop bursts, and a reset just grants one visitor a few extra requests.
The global cap is different — it bounds what this demo can cost in OpenAI
calls, so it has to survive restarts, redeploys and scale-to-zero. It is
counted in the D1 database that is already in the request path.
"""

import os

from order_generator import d1


HOURLY_LIMIT = int(os.getenv("LIMIT_GLOBAL_HOURLY", "100"))
DAILY_LIMIT = int(os.getenv("LIMIT_GLOBAL_DAILY", "500"))

RETENTION_SECONDS = 2 * 24 * 60 * 60

# called_at is unix seconds (SQLite has no timestamp type).
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_usage (
    called_at integer NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX IF NOT EXISTS api_usage_called_at_idx ON api_usage (called_at);
"""

PRUNE_SQL = "DELETE FROM api_usage WHERE called_at < unixepoch() - ?1"

# Count both windows and insert only if both pass, returning a row when the
# request is allowed. D1 runs one write at a time, and the statement is sent in
# the same batch (one transaction) as the prune, so two concurrent requests
# cannot both take the last slot.
CHECK_AND_RECORD_SQL = """
INSERT INTO api_usage (called_at)
SELECT unixepoch()
FROM (
    SELECT
        count(*) FILTER (WHERE called_at > unixepoch() - 3600) AS last_hour,
        count(*) FILTER (WHERE called_at > unixepoch() - 86400) AS last_day
    FROM api_usage
) AS windows
WHERE last_hour < ?1
  AND last_day < ?2
RETURNING called_at;
"""


class UsageLimitExceeded(Exception):
    """The global hourly or daily cap is spent."""


def ensure_usage_table() -> None:
    d1.query(CREATE_TABLE_SQL)


def check_and_record() -> None:
    """Record one API call, or raise if that would exceed the global caps.

    Raises ``UsageLimitExceeded`` when the cap is spent. Any other failure
    propagates: the caller treats it as a refusal, because a request that
    cannot reach the database cannot be served anyway, and letting it through
    would spend a model call on a request that is going to fail.
    """
    try:
        recorded = _record_one()
    except d1.D1Error as error:
        if "no such table" not in str(error):
            raise
        # Startup could not prepare the table (database unreachable at boot);
        # create it now rather than refusing every request.
        ensure_usage_table()
        recorded = _record_one()

    if not recorded:
        raise UsageLimitExceeded


def _record_one() -> bool:
    _pruned, inserted = d1.batch(
        [
            (PRUNE_SQL, [RETENTION_SECONDS]),
            (CHECK_AND_RECORD_SQL, [HOURLY_LIMIT, DAILY_LIMIT]),
        ]
    )
    return bool(inserted.rows)


def current_usage() -> dict[str, int]:
    """Counts for the two windows, for logging and manual checks."""
    result = d1.query(
        """
        SELECT
            count(*) FILTER (WHERE called_at > unixepoch() - 3600),
            count(*) FILTER (WHERE called_at > unixepoch() - 86400)
        FROM api_usage
        """
    )
    last_hour, last_day = result.rows[0]

    return {"last_hour": last_hour, "last_day": last_day}
