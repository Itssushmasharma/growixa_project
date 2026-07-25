# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-25
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-COMPANY-001` — Company profile + brand settings. Last task in the user-specified
sequence: `GRX-AUDIT-001` → `GRX-TEST-001` → `GRX-COMPANY-001`.

## Work completed

First task this session to ship real, RBAC-gated HTTP endpoints — everything before this
was schema/dependency foundations with no routes besides `/health`.

- **`apps/api/src/growixa_api/company/`** and **`brand/`** (new): both follow the full
  layered structure from [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)
  for the first time — `models.py` → `repositories.py` (raw persistence) →
  `services.py` (business logic) → `api.py` (FastAPI router), plus `schemas.py` for
  Pydantic request/response shapes.
- **Singleton handling**: `company_profile`/`brand_profiles` are true singletons per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) ("exactly one row, enforced in the
  service, not a DB constraint"). Implemented as get-then-upsert in both services, with an
  explicit docstring noting it's **not race-safe** against two concurrent first-time saves
  — acceptable for Sprint 1's single-admin-at-a-time usage; flagged rather than silently
  assumed safe.
- **`brand` → `company` dependency**: `brand.services` calls
  `company.repositories.get_company_profile` directly (the documented same-request
  cross-module call pattern), raising `CompanyProfileRequiredError` (translated to 400 at
  the API layer) if no company profile exists yet. No new permission codes invented — RBAC's
  existing `company.settings.view`/`edit` cover brand too, matching how RBAC.md frames brand
  as part of company settings.
- **Migration `1abf62872712`**: clean autogenerate, `company_profile` then
  `brand_profiles` in correct FK order.
- **`apps/api/tests/test_company_settings.py`** (new): admin edit+view, viewer view-only
  (403 on edit) for both tables, unauthenticated 401, and the brand-requires-company-first
  400 case. Both tables are shared singletons across the whole test run, so every test
  clears both via an autouse fixture before and after itself — order-independent by
  construction.

## Verification beyond the automated suite

Rebuilt the `api` image, confirmed `alembic current` reports the new head inside the
container, then ran a real end-to-end flow against the live Compose stack: minted a real
Admin JWT inside the running container (using the actual seeded Admin role), then
`PUT`/`GET /company/profile` and `PUT /brand/profile` via plain curl — a genuine HTTP
round-trip through uvicorn, not just the test suite's in-process ASGI transport. Cleaned up
the smoke-test data (company/brand rows, the throwaway user) afterward.

## Files changed

- `apps/api/src/growixa_api/company/__init__.py`, `models.py`, `schemas.py`,
  `repositories.py`, `services.py`, `api.py` (new)
- `apps/api/src/growixa_api/brand/__init__.py`, `models.py`, `schemas.py`,
  `repositories.py`, `services.py`, `api.py` (new)
- `apps/api/src/growixa_api/app.py` (mounts both new routers)
- `apps/api/migrations/env.py` (imports the two new model modules)
- `apps/api/migrations/versions/1abf62872712_company_profile_and_brand_profiles_.py` (new)
- `apps/api/tests/test_company_settings.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-COMPANY-001 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
# models written, wired into migrations/env.py
source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/alembic revision --autogenerate -m "company profile and brand profiles tables"
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/alembic upgrade head

.venv/bin/pytest -v   # 19 passed, 86% coverage

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # 1abf62872712 (head)
# minted a real Admin JWT inside the container, then:
curl -X PUT http://localhost:8000/company/profile -H "Cookie: access_token=$TOKEN" -d '...'
curl http://localhost:8000/company/profile -H "Cookie: access_token=$TOKEN"
curl -X PUT http://localhost:8000/brand/profile -H "Cookie: access_token=$TOKEN" -d '...'
# cleaned up the smoke-test rows afterward
```

## Test results

`pytest` → 19 passed (14 pre-existing + 5 new). 86% coverage. `ruff`/`mypy` clean across 45
source files.

## Migrations

`1abf62872712` — creates `company_profile`, `brand_profiles`. Depends on `6575d09949f9`.

## Decisions

None new — implements the schema and permission model already specified in
[DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) and [RBAC.md](../08-security/RBAC.md).
The get-then-upsert race-safety tradeoff is a documented judgment call, not a
`DECISIONS.md`-level architecture decision.

## Blockers

None.

## Known issues

- Get-then-upsert singleton pattern is not race-safe against two concurrent first-time
  saves — see the docstring in `company/services.py`. Not a problem for Sprint 1's
  single-admin usage; revisit if concurrent admin writes ever become a real scenario.
- Still-open gaps from earlier sessions (unrelated to this task): `seed_first_admin` CLI
  (`GRX-AUTH-001`), CORS for frontend calls (`GRX-FOUND-004`).

## Current state

This completes the user-specified sequence for this session:
`GRX-AUDIT-001` → `GRX-TEST-001` → `GRX-COMPANY-001`, all `DONE`. Company/brand settings
have real, tested, RBAC-gated endpoints. No frontend UI consumes them yet
(`GRX-COMPANY-002`).

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-TEST-002` (frontend test
foundation), `GRX-AUTH-002` (password hashing + login/logout), `GRX-USER-001` (internal
user invitation + acceptance), `GRX-COMPANY-002` (company settings screen, frontend, newly
unblocked).

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`e40f6f8` — feat(company): company profile + brand settings, RBAC-gated (GRX-COMPANY-001)
