"""Minimal client for Cloudflare D1 over its REST API.

The API runs on Fly.io, outside Cloudflare, so it cannot use a Worker binding;
every statement is an HTTPS call instead. One shared client keeps the TLS
connection to Cloudflare open between requests.

D1 is SQLite. Parameters are positional (``?1``, ``?2``, ...): D1 does not
accept named parameters.
"""

import os
from dataclasses import dataclass

import httpx
from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())

API_BASE = "https://api.cloudflare.com/client/v4"
TIMEOUT_SECONDS = 15.0

_client = httpx.Client(timeout=TIMEOUT_SECONDS)


class D1Error(RuntimeError):
    """D1 rejected a statement or could not be reached."""


@dataclass(frozen=True)
class Result:
    columns: list[str]
    rows: list[list[object]]


def get_settings() -> tuple[str, str, str]:
    names = ("CF_ACCOUNT_ID", "CF_D1_DATABASE_ID", "CF_API_TOKEN")
    values = tuple(os.getenv(name, "") for name in names)
    missing = [name for name, value in zip(names, values) if not value]
    if missing:
        raise RuntimeError(
            f"{', '.join(missing)} not set in the environment or .env file."
        )
    return values


def query(sql: str, params: list[object] | tuple[object, ...] = ()) -> Result:
    """Run one statement and return its columns and rows."""
    return _raw({"sql": sql, "params": list(params)})[-1]


def batch(statements: list[tuple[str, list[object]]]) -> list[Result]:
    """Run several statements in one round trip, as a single transaction."""
    return _raw(
        {"batch": [{"sql": sql, "params": list(params)} for sql, params in statements]}
    )


def _raw(body: dict) -> list[Result]:
    account_id, database_id, token = get_settings()
    url = f"{API_BASE}/accounts/{account_id}/d1/database/{database_id}/raw"

    try:
        response = _client.post(
            url, json=body, headers={"Authorization": f"Bearer {token}"}
        )
    except httpx.HTTPError as error:
        raise D1Error(f"D1 request failed: {error}") from error

    try:
        payload = response.json()
    except ValueError:
        raise D1Error(f"D1 returned HTTP {response.status_code}: {response.text[:200]}")

    if not payload.get("success"):
        messages = "; ".join(
            error.get("message", "") for error in payload.get("errors", [])
        )
        raise D1Error(messages or f"D1 returned HTTP {response.status_code}")

    return [
        Result(
            columns=item["results"].get("columns", []),
            rows=item["results"].get("rows", []),
        )
        for item in payload["result"]
    ]
