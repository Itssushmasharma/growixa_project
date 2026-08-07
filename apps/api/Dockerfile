# Local development image. Not optimized for production (no multi-stage slim/distroless
# build, no non-root user hardening yet) — revisit under a dedicated deployment task.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini ./
COPY src ./src
COPY migrations ./migrations

RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000

# Use --reload only in development (controlled via RELOAD_ENABLED env var).
# Production deployments (like Render) should NOT use --reload to avoid file descriptor exhaustion.
CMD sh -c 'uvicorn growixa_api.main:app --host 0.0.0.0 --port 8000 ${RELOAD_ENABLED:+--reload}'
