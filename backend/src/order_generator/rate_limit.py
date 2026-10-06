"""Per-client rate limiting for the public API.

Burst control only, counted in memory: a restart just grants one visitor a few
extra requests. It is also best effort, because behind the Cloudflare and Fly
proxies the caller's address comes from ``X-Forwarded-For``, which a client can
forge.

The cap that bounds spend lives in ``usage_limit``, counted in D1 so it
survives restarts no matter who is asking.
"""

import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


# Overridable through the environment so the limit can be tuned on the host,
# or tightened locally when testing the 429 path without spending model calls.
PER_CLIENT_LIMITS = os.getenv("RATE_LIMIT_PER_CLIENT", "10/minute;30/hour")


def client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_key)
