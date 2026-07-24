# Changelog

- Document ID: DOC-CHANGELOG
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [PROJECT_STATUS](PROJECT_STATUS.md), [DECISIONS](DECISIONS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md)

Reverse-chronological log of material changes to the Growixa repository (documentation and,
from Sprint 1 onward, code). Each entry names what changed and the commit(s) it landed in.

## 2026-07-24 — GRX-FOUND-005: PostgreSQL connectivity + Alembic foundation

- Added `apps/api/src/growixa_api/db.py`: SQLAlchemy 2.0 `DeclarativeBase` (`Base`), a
  module-level async engine (`pool_pre_ping=True`) built from `Settings.database_url`, an
  `async_sessionmaker`, and a `get_session()` FastAPI dependency (async generator) for
  future modules (`GRX-AUDIT-001`, `GRX-AUTH-001`, etc.) to depend-inject.
- Initialized Alembic with the async template (`alembic init -t async migrations`):
  `apps/api/alembic.ini` and `apps/api/migrations/{env.py,script.py.mako,versions/}`.
  `migrations/env.py` is wired to read `DATABASE_URL` from `growixa_api.config.get_settings()`
  (overriding `alembic.ini`'s placeholder URL at runtime, so there is one source of truth for
  the connection string) and sets `target_metadata = Base.metadata` for future autogeneration.
  Customized `script.py.mako` to match this project's ruff config (`collections.abc.Sequence`,
  `X | Y` union syntax) so every future generated migration passes lint without manual edits.
- Added the first migration (`migrations/versions/9ca09405a2b3_initial_empty_migration.py`):
  genuinely empty `upgrade`/`downgrade` (`pass`) — establishes the `alembic_version`
  tracking table baseline only; no application tables exist yet (those are `GRX-AUDIT-001`/
  `GRX-AUTH-001`/`GRX-COMPANY-001`, per [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md)).
- Added `apps/api/tests/test_migrations.py`: an integration-tier smoke test (real Postgres
  required, per [TEST_STRATEGY.md §Database migration tests](../10-testing/TEST_STRATEGY.md#database-migration-tests))
  that runs `alembic upgrade head` → asserts the head revision is recorded → `alembic
  downgrade base` → asserts no revision is recorded → `upgrade head` again, using Alembic's
  Python API directly (a plain sync test, since Alembic's async `env.py` calls
  `asyncio.run(...)` internally and cannot be nested inside pytest-asyncio's event loop).
- **Bug found and fixed**: `greenlet` — required by SQLAlchemy's async engine — was missing
  from `apps/api/pyproject.toml`. It happened to resolve as a transitive dependency inside
  the Docker image's `pip install`, masking the gap, but was absent from the local `uv`-
  managed dev venv, so any async engine use (including the `/health` checks added in
  `GRX-FOUND-002`) would have failed outside Docker. Added `greenlet>=3.1` as an explicit
  dependency.
- **Bug found and fixed**: `apps/api/Dockerfile` only ever `COPY`'d `pyproject.toml`,
  `README.md`, and `src/` — `alembic.ini` and `migrations/` were never in the image or the
  `compose.yaml` bind mounts, so `docker compose exec api alembic upgrade head` (this task's
  literal acceptance criterion, and the command documented in
  [LOCAL_DEVELOPMENT.md](../11-devops/LOCAL_DEVELOPMENT.md)) would have failed. Added them to
  the Dockerfile `COPY` steps and added matching bind mounts in `compose.yaml` (consistent
  with the existing `src` mount) so migrations stay live-editable like application code.
- Verified: `ruff check` 0 errors, `ruff format --check` pass, `mypy` 0 issues (11 source
  files), `pytest` 3 passed (2 health + 1 migration round-trip against real Compose
  Postgres). `alembic upgrade head` / `alembic current` succeed both from the host (via
  `localhost:5433`) and via `podman compose exec api alembic upgrade head` against the
  running Compose Postgres.
- `GRX-FOUND-005` marked `DONE`. `GRX-AUDIT-001`, `GRX-AUTH-001`, and `GRX-TEST-001` (all
  depend only on `GRX-FOUND-005`) are now `READY`, alongside the still-open `GRX-FOUND-004`.
- Commit: `0cff500`.

## 2026-07-23 — GRX-FOUND-003: FastAPI application foundation

- Refactored the ad hoc FastAPI app added during `GRX-FOUND-002` validation into a proper
  app-factory structure: `growixa_api/app.py` (`create_app()`, sets title/version, mounts
  the health router), `growixa_api/health.py` (`GET /health` route plus three isolated,
  independently-testable `_check_postgres`/`_check_redis`/`_check_rabbitmq` functions),
  `growixa_api/main.py` (thin `app = create_app()` uvicorn entrypoint — unchanged Docker
  CMD reference).
- OpenAPI docs (`/docs`, `/redoc`, `/openapi.json`) are enabled — this is FastAPI's default
  when nothing disables it; verified reachable (200) rather than left as an unverified
  assumption.
- Added `apps/api/tests/test_health.py`: two tests (all-dependencies-ok, one-dependency-
  degraded) that assert full response-body shape, not just status code, per
  [TEST_STRATEGY.md §Rules preventing shallow tests](../10-testing/TEST_STRATEGY.md#rules-preventing-tasks-from-being-marked-done-with-shallow-tests).
  Tests monkeypatch the three check functions directly (no real DB/Redis/MQ connection) and
  set required `Settings` env vars via `monkeypatch.setenv` + `get_settings.cache_clear()`,
  so the unit suite runs without any backing service, per
  [TEST_STRATEGY.md §Backend unit-test approach](../10-testing/TEST_STRATEGY.md#backend-unit-test-approach).
- Fixed a stale `pyproject.toml` mypy override (`growixa_api.tests.*`, a module path that
  never matched the actual `apps/api/tests/` layout) to `tests.*`, and added
  `apps/api/tests/__init__.py`.
- Verified: `ruff check` 0 errors, `ruff format --check` pass, `mypy` 0 issues (7 source
  files), `pytest` 2 passed. Rebuilt the `api` Docker image and re-validated the full
  Compose stack: all 5 services healthy, `GET /health` → 200
  `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`,
  `GET /docs` and `GET /openapi.json` → 200.
- `GRX-FOUND-003` marked `DONE`. `GRX-FOUND-004` (Next.js application foundation) and
  `GRX-FOUND-005` (PostgreSQL connectivity + Alembic foundation) are both now `READY`
  (only one to be worked at a time per [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md)).
- Commit: `c69eb10`.

## 2026-07-23 — GRX-FOUND-002: Docker Compose local environment

- Added `compose.yaml` defining `postgres` (16-alpine), `redis` (7-alpine), `rabbitmq`
  (3-management-alpine), `api`, and `web` services on a shared bridge network, with
  healthchecks and `depends_on: condition: service_healthy` gating startup order.
- Added `apps/api/Dockerfile` (python:3.13-slim, editable install, `uvicorn --reload`) and
  `apps/web/Dockerfile` (node:22-alpine, `npm run dev`) — local-development images, not
  production-optimized (no multi-stage/distroless build or non-root hardening yet).
- Added a minimal `growixa_api` app (`main.py`, `config.py`) with a real `GET /health`
  endpoint that checks Postgres/Redis/RabbitMQ connectivity, so the compose stack has
  something functional to validate against ahead of `GRX-FOUND-003`.
- Added a minimal Next.js `apps/web/src/app/` (App Router `layout.tsx`/`page.tsx`) and
  `next.config.mjs` so `apps/web` builds/serves, ahead of `GRX-FOUND-004`.
- Added root `.env.example` documenting all Compose-level variables (DB/MQ credentials,
  host port mappings, JWT signing settings per [DEC-GRX-014](DECISIONS.md)).
- Validated end-to-end: `podman compose up -d` brings up all 5 services `healthy`;
  `GET /health` returns `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`;
  the web root returns HTTP 200.
- Fixed a podman-compose bug encountered during validation: a multi-word `CMD`-array
  healthcheck test (`api` service's `python -c "..."` health check) was being incorrectly
  re-split into separate argv tokens by podman-compose, breaking the check even though the
  app itself was healthy. Switched to `CMD-SHELL` form in `compose.yaml`, which
  podman-compose preserves as a single string correctly.
- Local-environment note (not a repo change): the default `POSTGRES_PORT=5432` in
  `.env.example` can collide with a natively-running Postgres on the host; `.env` is
  gitignored so this is a per-machine `.env` adjustment, not a schema/compose change.
- `GRX-FOUND-002` marked `DONE`; `GRX-FOUND-003` (FastAPI application foundation) now `READY`.
- Commit: `76354d2`.

## 2026-07-23 — GRX-FOUND-001: repository and development tooling

- First Sprint 1 implementation task. Added `apps/api/` (FastAPI/Python tooling: `ruff`,
  `mypy`, `pytest`, `.venv`, `.env.example`) and `apps/web/` (Next.js/TypeScript tooling:
  ESLint 9 flat config, Prettier, `tsc`, `.env.example`) — tooling and config only, no
  application code yet.
- Added `.pre-commit-config.yaml` wiring lint/format/type-check for both apps plus standard
  hygiene hooks; installed the git hook.
- Fixed 3 `npm audit` findings (moderate `postcss` XSS, high `sharp`/`libvips` CVEs, both
  pinned internally by Next.js on every current release) via a `package.json` `overrides`
  block. Verified 0 vulnerabilities after.
- All required checks verified passing: `ruff check`, `ruff format --check`, `mypy`,
  `eslint`, `prettier --check`, `tsc --noEmit`, `pre-commit run --all-files`.
- `GRX-FOUND-001` marked `DONE`; `GRX-FOUND-002` (Docker Compose) now `READY`.
- Commit: `42f8b37`.

## 2026-07-22 — Documentation gate closed; Sprint 1 authorized

- Added standalone [`docs/10-testing/TEST_STRATEGY.md`](../10-testing/TEST_STRATEGY.md) and
  [`docs/11-devops/LOCAL_DEVELOPMENT.md`](../11-devops/LOCAL_DEVELOPMENT.md), closing the
  last two distributed-only gaps in the Development Readiness Gate.
- [`DEVELOPMENT_READINESS.md`](DEVELOPMENT_READINESS.md) now shows every mandatory Slice 1
  gate item as `PASS` with a standalone document as evidence.
- Sprint 1 implementation authorized to begin at `GRX-FOUND-001`.

## 2026-07-22 — Slice 1 readiness: architecture, data, security baseline

- Resolved [OQ-001](OPEN_QUESTIONS.md) via [DEC-GRX-014](DECISIONS.md): application-managed
  FastAPI authentication (Argon2id, rotating refresh tokens, HttpOnly/Secure/SameSite
  cookies, centralized RBAC, OIDC/SSO adapter boundary for later). No Keycloak/third-party
  provider in MVP.
- Added `docs/04-architecture/` (SYSTEM_ARCHITECTURE, MODULE_BOUNDARIES,
  BACKGROUND_JOB_ARCHITECTURE), `docs/05-data/` (DATA_MODEL, ERD, DATABASE_SCHEMA), and
  `docs/08-security/` (SECURITY_ARCHITECTURE, AUTHENTICATION, RBAC, THREAT_MODEL) for Slice
  1 scope.
- Added [`MASTER_TASK_TRACKER.md`](MASTER_TASK_TRACKER.md) seeded with Sprint 1 tasks and
  [`SPRINT_01_FOUNDATION.md`](../14-sprints/SPRINT_01_FOUNDATION.md).
- Development Readiness Gate for Slice 1 reached PASS (with two items still in distributed
  form, closed in the entry above).
- Commit: `cc46e6d`.

## 2026-07-22 — Scope correction: Growixa remains the broader growth platform

- Corrected an earlier documentation pass that had read as a full product pivot. Logged as
  [DEC-GRX-001](DECISIONS.md): Growixa's positioning stays "AI-powered growth and marketing
  automation platform"; only the **first release** scope narrowed to email/social/contacts/
  AI-assist/scheduling/analytics. SEO/AEO/GEO/website-intelligence work from the original
  discovery PRD is preserved and mapped to future releases V1.5–V3 in
  [`FUTURE_SCOPE_SEO_AEO_GEO.md`](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md), not dropped.
- Relabeled `docs/archive/source-prd-seo-aeo-geo-website-intelligence/` (previously named as
  if it were an unrelated/superseded product) to reflect it as valid future-release source
  material.
- Added `docs/01-product/` (PRODUCT_VISION, PRD, MVP_SCOPE, ROADMAP,
  FUTURE_SCOPE_SEO_AEO_GEO), `docs/02-features/FEATURE_CATALOG.md` (stub), and
  `docs/00-project-control/` core docs (PROJECT_STATUS, ASSUMPTIONS, OPEN_QUESTIONS,
  DECISIONS, DEFINITION_OF_DONE, DEVELOPMENT_READINESS) and
  `docs/12-development/AGENT_EXECUTION_RULES.md`.
- Commit: `50b93cf`.

## 2026-07-22 — Repository initialized

- `git init`, `.gitignore`, root `README.md`.
- Original SEO/AEO/GEO discovery PRD (from an uploaded `.docx`) converted to Markdown and
  placed under `docs/archive/` (naming corrected in the entry above).
- Commit: `92bbdad`.
