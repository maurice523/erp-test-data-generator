from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from typing import Any
from pydantic import BaseModel

from slowapi.errors import RateLimitExceeded

from order_generator.pipeline import text_to_orders
from order_generator.rate_limit import PER_CLIENT_LIMITS, limiter
from order_generator.usage_limit import (
    UsageLimitExceeded,
    check_and_record,
    ensure_usage_table,
)

class GenerateOrdersResponse(BaseModel):
    orders: list[dict[str, Any]]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_usage_table()
    except Exception as error:
        # An unreachable database must not crash-loop the service; the table is
        # created lazily on the first request instead.
        print(f"Could not prepare the usage table at startup: {error}")
    yield


app = FastAPI(title="Order Generator API", lifespan=lifespan)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                "Too many order requests right now. This demo generates each "
                "order with an AI model, so requests are limited. Try again "
                "in a minute."
            )
        },
    )


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)


def enforce_global_cap() -> None:
    """Runs before the handler, so a refused request costs no model call."""
    try:
        check_and_record()
    except UsageLimitExceeded:
        raise HTTPException(
            status_code=429,
            detail=(
                "This demo has hit its daily limit on AI-generated orders. "
                "Please try again later."
            ),
        )
    except Exception:
        # Fail closed: without the database the request cannot be served, and
        # letting it through would spend a model call on a doomed request.
        raise HTTPException(
            status_code=503,
            detail="The order database is unavailable right now. Try again shortly.",
        )


@app.post("/api/order-generator", response_model=list[dict[str, Any]])
@limiter.limit(PER_CLIENT_LIMITS)
def generate_orders_endpoint(
    request: Request,
    text: str,
    _cap: None = Depends(enforce_global_cap),
) -> list[dict[str, Any]]:
    return text_to_orders(text)

@app.get("/test/version")
def show_version(version: int):
    return f"v.{version}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4555)
