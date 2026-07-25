# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-24
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-RBAC-001` — Centralized permission-check dependency.

## Scope decision made before writing code (flagged to the user, then proceeded)

`require_permission()` cannot work without resolving "who is calling," but token
issuance/validation is `auth`-module territory per
[AUTHENTICATION.md](../08-security/AUTHENTICATION.md), and `apps/api/auth/` doesn't exist
yet (`GRX-AUTH-002`, not started). Resolved by giving `permissions` a narrowly-scoped
`get_current_user_id()` that only *verifies* an already-issued JWT cookie — real, working
code (a hand-crafted valid JWT authenticates correctly in tests), just nothing issues that
cookie yet. `GRX-AUTH-002`'s login endpoint will be what mints it. Same pattern as
`GRX-FOUND-004`'s `apiFetch` — real code, no caller yet.

## Work completed

- **`apps/api/src/growixa_api/permissions/repositories.py`** (new):
  `user_has_permission(session, user_id, code) -> bool` — the only place in this module
  touching the DB directly, joining `Permission`/`RolePermission`/`UserRole`. Note: this
  reads `growixa_api.users.models.UserRole` (owned by `users`), which
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)'s dependency table doesn't
  explicitly list for `permissions` (only `roles` is listed) — a permission check inherently
  needs both tables, so this is a deliberate, read-only cross-module dependency, not an
  oversight.
- **`apps/api/src/growixa_api/permissions/dependencies.py`** (new):
  - `get_current_user_id(request) -> uuid.UUID` — decodes the `access_token` cookie
    (PyJWT, HS256, `Settings.jwt_signing_key`), 401s on anything missing/invalid/expired.
  - `RequirePermission` — a callable **class** (not a closure) specifically so the audit
    test below can `isinstance()`-check a route's dependency tree for it. Depends on
    `get_current_user_id` + `get_session`; 403s via `user_has_permission`; returns the
    user id on success.
  - `require_permission(code)` — public factory, matches the exact name
    [AUTHENTICATION.md](../08-security/AUTHENTICATION.md) uses.
- **`apps/api/tests/test_require_permission.py`** (new): allowed / 403 / 401-missing /
  401-invalid cases, using the **real** seeded Viewer role from `GRX-AUTH-001`'s migration
  (has `company.settings.view`, lacks `users.manage`, per RBAC.md) — not a fixture-only fake
  role, the actual Sprint 1 seed data.
- **`apps/api/tests/test_protected_routes_audit.py`** (new): per
  [TEST_STRATEGY.md's RBAC section](../10-testing/TEST_STRATEGY.md#rbac-authorization-tests),
  walks every `APIRoute` in `create_app()` and asserts each one not in an explicit
  public-route allowlist is guarded by `RequirePermission`. Trivially true today (only
  `/health`, allowlisted) — starts catching real regressions the moment the first protected
  route ships.

## Two bugs found and fixed while validating this task (both test infra, not app code)

1. **Cross-event-loop asyncpg connection reuse.** `growixa_api.db`'s async engine/pool is a
   module-level singleton for the whole test process. pytest-asyncio's default
   function-scoped event loop meant the second async DB-touching test in a run could be
   handed a pooled connection opened under a different (already-closed) loop:
   `RuntimeError: ... attached to a different loop`. Fixed by setting
   `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope = "session"` in
   `pyproject.toml`.
2. **Route-audit found zero routes.** This FastAPI version (`0.139.2`) doesn't flatten
   `include_router()`'s routes directly into `app.routes`; it wraps them in an internal
   `_IncludedRouter`, with the real routes at `.original_router.routes`. Fixed the audit
   test to recurse through that wrapper via `getattr` (not by importing the private class),
   so it isn't hard-pinned to this specific internal shape.

## Files changed

- `apps/api/src/growixa_api/permissions/repositories.py` (new)
- `apps/api/src/growixa_api/permissions/dependencies.py` (new)
- `apps/api/tests/test_require_permission.py` (new)
- `apps/api/tests/test_protected_routes_audit.py` (new)
- `apps/api/pyproject.toml` (session-scoped asyncio loop for tests; ruff B008 FastAPI exemption)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-RBAC-001 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .   # all clean

set -a; source ../../.env; set +a
export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/pytest -v   # 9 passed

cd ../..
podman compose up -d --build api   # rebuild picks up the new permissions modules
curl http://localhost:8000/health  # unaffected, still ok
```

## Test results

`pytest` → 9 passed: the 5 pre-existing tests (health x2, migration round-trip, auth-schema
seed) plus 4 new (allowed, 403, 401-missing-token, 401-invalid-token) plus the route audit
(counted within the 9). `ruff`/`mypy` clean across 23 source files.

## Migrations

None — no schema change, this task only adds an authorization dependency.

## Decisions

None new — implements the mechanism already specified in
[AUTHENTICATION.md §Centralized authorization](../08-security/AUTHENTICATION.md#centralized-authorization).
The `get_current_user_id` scope call above is a task-sequencing/module-placement judgment
call, not a `DECISIONS.md`-level architecture decision — flagged to the user before
implementing, not silently guessed.

## Blockers

None.

## Known issues / gaps flagged, not fixed here

- `get_current_user_id`'s JWT verification will need to be reconciled with whatever
  `GRX-AUTH-002` builds for issuance — at minimum, confirm the claim shape (`sub`) and
  cookie name (`access_token`) match what login actually sets. If `GRX-AUTH-002` needs a
  different shape, update `get_current_user_id` to match rather than maintaining two
  incompatible token formats.
- The `seed_first_admin` CLI gap flagged in `GRX-AUTH-001`'s handoff is still open.

## Current state

`require_permission()` exists, is fully tested (including a real seeded role and a
route-protection audit), and is ready for every future protected route to depend on. No
route currently uses it in the real app yet — `/health` is the only route and is
(correctly) public. The first real consumer will be whichever of `GRX-AUTH-002`,
`GRX-COMPANY-001`, etc. is picked up next.

## Exact next task

Four tasks are now `READY`:

- `GRX-AUDIT-001` — Audit log module.
- `GRX-TEST-001` — Backend test foundation.
- `GRX-TEST-002` — Frontend test foundation.
- `GRX-COMPANY-001` — Company profile + brand settings (newly unblocked by this task).

Per [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md), only one Sprint
1 task is worked on at a time.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

Recorded below after this handoff is committed alongside the `GRX-RBAC-001` change set.
