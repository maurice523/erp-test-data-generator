# syntax=docker/dockerfile:1

# Build from the backend directory so pyproject.toml, uv.lock, and src are in
# the Docker build context:
# docker build --file src/order_generator/Dockerfile --tag order-generator-api .

FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 4555


FROM base AS build

COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install locked dependencies before copying source code to preserve the
# dependency layer when only application code changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM base AS final

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd --gid 10001 ordergenerator \
    && useradd --uid 10001 --gid ordergenerator --no-create-home \
        --shell /usr/sbin/nologin ordergenerator

COPY --from=build --chown=ordergenerator:ordergenerator /app/.venv /app/.venv

USER ordergenerator

# Hosts such as Render assign the port through PORT; fall back to 4555 locally.
ENTRYPOINT ["sh", "-c", "uvicorn order_generator.api:app --host 0.0.0.0 --port ${PORT:-4555}"]
