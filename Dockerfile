# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

# uv installs itself via the official static binary image (no pip bootstrap needed)
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install deps first (cache layer independent of source changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY user_api ./user_api
COPY alembic.ini ./alembic.ini

RUN uv sync --frozen --no-dev

RUN useradd --create-home --uid 1000 appuser
USER appuser

ENV PATH="/app/.venv/bin:${PATH}"

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz', timeout=2)" || exit 1

CMD ["uvicorn", "user_api.adapters.inbound.http.main:app", "--host", "0.0.0.0", "--port", "8000"]
