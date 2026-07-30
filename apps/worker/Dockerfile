# Local development image. Not optimized for production (no multi-stage slim/distroless
# build, no non-root user hardening yet) — revisit under a dedicated deployment task.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["python", "-m", "growixa_worker.main"]
