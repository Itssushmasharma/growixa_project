# Changelog

- Document ID: DOC-CHANGELOG
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [PROJECT_STATUS](PROJECT_STATUS.md), [DECISIONS](DECISIONS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md)

Reverse-chronological log of material changes to the Growixa repository (documentation and,
from Sprint 1 onward, code). Each entry names what changed and the commit(s) it landed in.

## 2026-07-27 — GRX-AUTH-003: Refresh-token rotation + session revocation

- Picked next per explicit user direction as "most needed first": closes a real security
  gap `GRX-AUTH-002` left open by design (refresh tokens issued, but no rotation, no reuse
  detection — a stolen refresh token could otherwise be replayed indefinitely).
- Added `POST /auth/refresh` and `POST /auth/logout-all` — both public routes (added to
  the route-protection audit's allowlist) that identify the acting user via the refresh
  token itself, consistent with the existing `/auth/logout`, rather than via
  `get_current_user_id`/`require_permission`.
- `auth/services.refresh()`: looks up the presented token; if already revoked by a
  *previous rotation* (not by logout), treats this as a reuse/compromise signal and calls
  the new `revoke_all_active_sessions()` to kill every session for that user — not just
  reject the one request — before raising. Otherwise rotates: issues a new access +
  refresh token, marks the presented one `revoked_at` + `replaced_by_token_id` pointing at
  the new one (the `refresh_tokens` column that existed since `GRX-AUTH-002`'s migration
  but stayed unused until now), and re-validates `user.status == "ACTIVE"` on every
  refresh (defense in depth beyond relying solely on disable always successfully revoking
  sessions elsewhere).
- Added `auth/services.revoke_all_active_sessions(session, user_id, *, reason)` —
  deliberately public (not `_`-prefixed) and does not commit itself, so a future
  disable-user action (no such endpoint exists yet; out of `apps/api/auth/`'s own scope)
  can call it as one step in a larger transaction. Records a `session.revoked` audit event
  (Sprint 1's audit event set) with the reason and count, only when it actually revoked
  something.
- `auth/services.logout_all()` reuses the same revoke function, keyed off the presented
  refresh token — logging out "everywhere" from any one of your own sessions.
- Added `apps/api/tests/test_auth_refresh.py`: rotation (new cookies issued, old token
  revoked with the correct `replaced_by_token_id`), reuse detection (replaying the
  pre-rotation token 401s *and* revokes the entire chain including the token it had
  already rotated to), `logout-all` across two simulated devices (two separate
  `AsyncClient`s, since one client's cookie jar would silently overwrite the first
  session's refresh cookie on a second login), disable-revokes-sessions (proves the
  `revoke_all_active_sessions()` building block works, since no disable-user endpoint
  exists to exercise end-to-end yet), and expired-token rejection.
- Verified beyond the automated suite: rebuilt the `api` image, then ran a real
  login → refresh → replay-old-token flow via curl against the live Compose stack,
  confirming via direct `psql` queries that *both* refresh tokens ended up revoked and the
  `session.revoked` audit row was recorded with `reason: "refresh_token_reuse_detected"`.
  Cleaned up the smoke-test user/rows afterward.
- Verified: `ruff`/`format --check`/`mypy` clean across 57 source files; `pytest` 28
  passed, 94% coverage.
- `GRX-AUTH-003` marked `DONE`. No task became newly `READY` from this alone — nothing
  else in the tracker lists it as a dependency yet.
- Commit: `27a22af`.

## 2026-07-27 — GRX-AUTH-002: Password hashing + login/logout

- Picked next per explicit user direction: P0, backend-only, continuing the session's
  backend momentum rather than branching into frontend work (`GRX-TEST-002`) or a P1 task
  (`GRX-COMPANY-002`).
- Added `apps/api/src/growixa_api/auth/security.py`: Argon2id `hash_password`/
  `verify_password`, cost parameters (`argon2_time_cost`/`memory_cost`/`parallelism`) added
  to `Settings` as configuration per
  [AUTHENTICATION.md](../08-security/AUTHENTICATION.md) ("tuned parameters set as
  configuration... so cost can be raised as hardware improves"), defaulting to
  argon2-cffi's own OWASP-baseline `PasswordHasher` defaults.
- Added `apps/api/src/growixa_api/auth/tokens.py`: `create_access_token` — the **issuing**
  half of the JWT that `permissions.dependencies.get_current_user_id` (`GRX-RBAC-001`) has
  been verifying since that task, same signing key/algorithm, closing the gap flagged at
  the time. Also refresh-token generation (`secrets.token_urlsafe`) and hashing
  (SHA-256 — fast/deterministic is correct here since, unlike a password, a refresh token
  is already high-entropy, not a low-entropy brute-forceable input).
- Added the `refresh_tokens` table (migration `ea25a5343142`) — deferred from
  `GRX-AUTH-001` since that task's own scope was schema for users/roles/permissions only;
  needed now because issuing a refresh token requires persisting its hash. Includes
  `replaced_by_token_id`, populated only once `GRX-AUTH-003` (rotation) lands, but present
  now as part of the fixed schema in DATABASE_SCHEMA.md.
- Added `apps/api/src/growixa_api/users/repositories.py` (`get_user_by_email`) — the
  `users` module's first repository file; `auth` depends on `users` for identity lookup per
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md), so this lookup belongs
  there, not duplicated inside `auth`.
- `auth/services.py`: `login()` raises a single `InvalidCredentialsError` for unknown
  email, wrong password, *and* disabled accounts alike — deliberately indistinguishable
  per [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T11, each still recording a
  `user.login_failed` audit event (with `entity_id` set only when a user was actually
  found, so the audit trail itself still distinguishes them for legitimate incident
  response — that distinction just never reaches the HTTP response). Successful login
  updates `last_login_at`, issues both tokens, and records `user.login`. `logout()`
  revokes the presented refresh token and records `user.logout`.
- `auth/api.py`: `POST /auth/login` and `POST /auth/logout`, added to the
  route-protection audit's public allowlist (they are the entry points before a session
  exists). Cookies are `HttpOnly` + `SameSite=Lax` unconditionally; `Secure` is
  conditional on `settings.environment != "local"` — local dev runs over plain HTTP, and a
  browser will not resend a `Secure` cookie without HTTPS.
- Added `apps/api/tests/test_auth_login.py`: valid login (cookies present, **no token
  values in the JSON body** — verified directly per T2, not assumed), identical generic
  error for wrong-password vs. unknown-email (compared byte-for-byte, not just both-401),
  disabled-account rejection, and logout (revokes the token row, clears both cookies,
  records the audit event). Extended the shared `user_factory` (`GRX-TEST-001`) to hash a
  real, known password (`DEFAULT_TEST_PASSWORD`) and accept an explicit `email` override,
  rather than duplicating user-creation logic for this task's tests.
- **Real bug found and fixed — this one affects every coverage number recorded so far this
  session.** `auth/services.py` showed 50% coverage despite all 4 new tests passing with
  assertions that only make sense if the "uncovered" lines ran (audit rows created,
  `last_login_at` set, tokens revoked). Root cause: SQLAlchemy's async engine bridges into
  the sync DBAPI driver via `greenlet_spawn`, and coverage.py's default tracer does not
  follow into that greenlet context, silently under-reporting any code that runs on the
  other side of an `await session.execute(...)`/`commit()` call. Fixed by adding
  `concurrency = ["greenlet"]` to `[tool.coverage.run]`. Total coverage jumped from 85% to
  **94%** on rerun — the true baseline was always higher; this was purely a measurement
  bug, not new code appearing. `GRX-TEST-001`'s previously-recorded 87% baseline is now
  known to have been an undercount for the same reason; not retroactively rewritten there
  (historical evidence is point-in-time), but flagged here since this is where it was found.
- Verified beyond the automated suite: rebuilt the `api` image, confirmed `alembic current`
  reports the new head inside the container, then ran a real login → wrong-password →
  logout flow via curl against the live Compose stack — inspected the actual `Set-Cookie`
  headers (`HttpOnly`, `SameSite=lax`, correct `Max-Age` matching config, no `Secure` in
  local) and confirmed logout's `Set-Cookie` headers clear both cookies (`Max-Age=0`).
  Cleaned up the smoke-test user/rows afterward.
- Verified: `ruff`/`format --check`/`mypy` clean across 56 source files; `pytest` 23 passed,
  94% coverage (corrected).
- `GRX-AUTH-002` marked `DONE`. `GRX-AUTH-003` (refresh-token rotation + session
  revocation), `GRX-AUTH-005` (password reset flow), and `GRX-FOUND-008` (dashboard shell,
  frontend) are newly `READY`, alongside the already-`READY` `GRX-TEST-002`,
  `GRX-USER-001`, `GRX-COMPANY-002`. `GRX-AUTH-004` (rate limiting) still needs
  `GRX-FOUND-006` (Redis connectivity), not yet started.
- Commit: `b7cf4d8`.

## 2026-07-25 — GRX-COMPANY-001: Company profile + brand settings

- First task this session to ship real, RBAC-gated HTTP endpoints (previous tasks were
  schema/dependency foundations with no routes of their own besides `/health`).
- Added `apps/api/src/growixa_api/company/{models,schemas,repositories,services,api}.py`
  and the equivalent `brand/` module, following the full layered structure from
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md) for the first time
  (`models` → `repositories` → `services` → `api`, plus `schemas` for the Pydantic
  request/response shapes) since this is the first task that actually needs every layer.
- `company_profile`/`brand_profiles` are true singletons per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) — "exactly one row, enforced in the
  service, not a DB constraint." Implemented as get-then-upsert in `company/services.py`
  and `brand/services.py`, explicitly documented as **not race-safe** against two
  concurrent first-time saves (acceptable for Sprint 1's single-admin-at-a-time usage; a
  unique constraint or advisory lock would close that gap if it ever matters).
- `brand` depends on `company` per module boundaries — `brand.services` calls
  `company.repositories.get_company_profile` directly (the documented same-request
  cross-module call pattern) and raises a small domain error
  (`CompanyProfileRequiredError`) if no company profile exists yet, translated to a 400 at
  the API layer. No new permission codes were invented for brand — RBAC.md's existing
  `company.settings.view`/`company.settings.edit` cover both, matching RBAC.md's own
  framing of brand as part of company settings.
- Added migration `1abf62872712` (clean autogenerate: `company_profile` then
  `brand_profiles`, correct FK order).
- Added `apps/api/tests/test_company_settings.py`: admin edit+view, viewer view-only (403
  on edit) for *both* company and brand, unauthenticated 401, and the
  brand-requires-company-first 400 case. Since both tables are true singletons shared
  across the whole test run, every test clears both tables before and after itself via an
  autouse fixture — order-independent by construction, not by accident.
- Verified beyond the automated suite: rebuilt the `api` image, confirmed
  `alembic current` reports the new head inside the container, and ran a live end-to-end
  curl flow against the running Compose stack (mint a real Admin JWT inside the container,
  `PUT`/`GET /company/profile`, `PUT /brand/profile`) — real HTTP round-trip, not just the
  test suite's ASGI transport.
- Verified: `ruff`/`format --check`/`mypy` clean across 45 source files; `pytest` 19 passed
  (14 pre-existing + 5 new), 86% coverage.
- `GRX-COMPANY-001` marked `DONE`. `GRX-COMPANY-002` (company settings screen, frontend) is
  newly `READY`, alongside the already-`READY` `GRX-TEST-002`, `GRX-AUTH-002`,
  `GRX-USER-001`. This completes the user-specified sequence
  (`GRX-AUDIT-001` → `GRX-TEST-001` → `GRX-COMPANY-001`).
- Commit: `e40f6f8`.

## 2026-07-25 — GRX-TEST-001: Backend test foundation

- Added `apps/api/tests/conftest.py`: a `user_factory` fixture (async, factory-function
  pattern) that creates a real user, optionally assigns it an existing seeded role, and
  deletes every user it created at teardown. Kept deliberately simple — commit-and-cleanup
  per creation, not a transactional-rollback session — see the module's own docstring and
  [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for why the heavier pattern wasn't adopted now.
- Refactored `test_require_permission.py` (`GRX-RBAC-001`) and `test_audit_log.py`
  (`GRX-AUDIT-001`) to use the shared `user_factory` instead of their own near-identical
  ad hoc fixtures — the direct point of this task, not incidental cleanup.
- Added `pytest-cov` and `[tool.coverage.run]` config (`source = ["growixa_api"]`,
  tests excluded). Current baseline: **87%** line coverage (`pytest` with default addopts).
  No enforced minimum threshold yet — establishing the baseline measurement is this task's
  job; a specific enforced number is better decided once `GRX-DEVOPS-001` wires up CI and
  there's more code to judge a rational threshold against.
- Registered a `pytest.mark.integration` marker (in `pyproject.toml`, avoiding
  "unknown marker" warnings) and applied it to every test that touches a real backing
  service: `test_audit_log.py`, `test_auth_schema_seed.py`, `test_migrations.py`, and two of
  `test_require_permission.py`'s four tests (the other two — missing/invalid token — never
  reach `get_session` because `get_current_user_id` raises first, per FastAPI's
  parameter-order dependency resolution, and were left unmarked *and separately verified* to
  need no DB — see below).
- **Verified the split is real, not just labeled**: ran
  `pytest -m "not integration"` with `DATABASE_URL`/`REDIS_URL`/`RABBITMQ_URL` all pointed
  at unreachable hosts — all 7 unit-tier tests still passed. This is the actual proof (not
  an assumption) that the unit/integration boundary holds.
- No CI pipeline exists yet (`GRX-DEVOPS-001`, which depends on this task and
  `GRX-TEST-002`, hasn't started) — this task's own acceptance criterion
  ("`pytest` runs green ... in CI") is satisfied by `pytest` running green locally with the
  new foundation in place, matching how earlier foundation tasks satisfied "smoke test"
  criteria before their own supporting infrastructure existed.
- Verified: `ruff`/`format --check`/`mypy` clean across 31 source files; `pytest` 14 passed
  (same 14 as before this task — this task changed test *infrastructure*, not test *count*).
- `GRX-TEST-001` marked `DONE`. No task became newly `READY` from this alone (only
  `GRX-DEVOPS-001` depends on it, and that also needs `GRX-TEST-002`, not done). Per
  explicit user direction, `GRX-COMPANY-001` is next.
- Commit: `de55382`.

## 2026-07-25 — GRX-AUDIT-001: Audit log module

- **Task-ordering note**: this was the deferred half of the `GRX-AUDIT-001`/`GRX-AUTH-001`
  ordering issue flagged during `GRX-AUTH-001` — `audit_logs.actor_user_id` FKs to
  `users.id`, so this task genuinely needed `GRX-AUTH-001` done first. It was, so this
  proceeded cleanly.
- Added `apps/api/src/growixa_api/audit/models.py`: `AuditLog` matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly — indexes on
  `(entity_type, entity_id)`, `actor_user_id`, and `created_at`; the DB column `metadata` is
  mapped to a Python attribute named `event_metadata` since SQLAlchemy's `DeclarativeBase`
  already reserves `.metadata` for the ORM's own `MetaData` object.
- Added migration `6575d09949f9` (clean autogenerate, no hand-editing needed beyond
  ruff-driven line wrapping) creating `audit_logs`.
- Added `apps/api/src/growixa_api/audit/repositories.py` (`create_audit_log`,
  `list_audit_logs` — raw persistence only) and `services.py` (`record_event`,
  `list_events`). `record_event` redacts known-sensitive metadata keys (`password`,
  `password_hash`, `token`, `token_hash`, `refresh_token`, `access_token`, `secret`) to
  `"[REDACTED]"` before the row is ever written — the "structured-log redaction" half of
  this task's description, and defense-in-depth for
  [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T7 (secret leakage in logs). No
  `update`/`delete` function exists anywhere in either module — the "insert-only" property
  is enforced by omission, not a runtime guard.
- Added `apps/api/tests/test_audit_log.py`: write→list round-trip (real Postgres), a
  system-actor event (`actor_user_id=None`, explicitly allowed per the schema doc), and a
  redaction test asserting sensitive keys are stripped while unrelated keys survive intact.
- Added `apps/api/tests/test_audit_insert_only.py`: introspects `audit.repositories` and
  `audit.services` via `inspect.getmembers` and asserts no public function name contains
  "update"/"delete"/"modify"/"edit" — the tracker's required "negative test for missing
  update/delete routes," adapted to code-path auditing since no HTTP API layer exists yet
  in this module (matches the broader wording in
  [TEST_STRATEGY.md §Audit-log tests](../10-testing/TEST_STRATEGY.md#audit-log-tests): "no
  application code path... updates or deletes").
- **Real bug found and fixed while validating this task**: the write/list test's fixture
  teardown (deleting its throwaway test user) initially failed with a Postgres FK violation
  — `actor_user_id` correctly has no `ON DELETE CASCADE` (an audit trail must survive the
  actor being removed), so the test's own audit row was still referencing that user. Fixed
  by having the fixture delete its audit rows before the user.
- **Second, more interesting bug found and fixed**: `test_require_permission.py` started
  intermittently failing with `asyncpg.exceptions.InternalServerError: cache lookup failed
  for type ...` when run in the same session as `test_migrations.py`. Root cause:
  `test_migrations.py`'s downgrade-then-upgrade round trip was dropping and recreating the
  `citext` Postgres extension (added in `GRX-AUTH-001`'s migration, downgrade path) — each
  `CREATE EXTENSION` assigns the type a new internal OID, which poisons asyncpg's
  per-connection type cache for any already-pooled connection (recall `growixa_api.db`'s
  engine/pool is a session-wide singleton) that later touches a `citext` column. Fixed by no
  longer dropping the `citext` extension in that migration's `downgrade()` — a common,
  low-risk exception to full reversibility (table-level state is still fully reversible;
  leaving an installed extension behind is standard practice) that eliminates the whole
  class of failure rather than papering over one symptom of it.
- Verified: `ruff`/`format --check`/`mypy` clean across 30 source files; `pytest` 14 passed
  (10 pre-existing + 4 new); rebuilt the `api` image, `podman compose exec api alembic
  current` → new head, `/health` unaffected.
- `GRX-AUDIT-001` marked `DONE`. `GRX-AUTH-002` and `GRX-USER-001` (both depended on this
  and `GRX-AUTH-001`, both now done) are newly `READY`, alongside the already-`READY`
  `GRX-TEST-001`, `GRX-TEST-002`, `GRX-COMPANY-001`. Per explicit user direction, the next
  two tasks to pick up are `GRX-TEST-001` then `GRX-COMPANY-001`.
- Commit: `2b1dd7e`.

## 2026-07-25 — Design reference intake (not a tracker task)

- Product owner supplied brand assets (`apps/web/src/assets/`: primary, stacked, icon,
  wordmark, monochrome logo variants) and a self-contained HTML mockup covering the login
  screen and a full dashboard concept, plus a written design brief.
- Saved as [`docs/03-ux-ui/DESIGN_REFERENCES.md`](../03-ux-ui/DESIGN_REFERENCES.md) +
  [`docs/03-ux-ui/mockups/growixa-login-and-dashboard-mockup.html`](../03-ux-ui/mockups/growixa-login-and-dashboard-mockup.html)
  so this context survives outside chat history for whichever future session builds
  `GRX-AUTH-002`'s login UI or `GRX-FOUND-008`'s dashboard shell.
- **Explicit scope caveat recorded in that doc**: the brief describes the full eventual
  product (Contacts, Campaigns, Social, AI Assistant, Billing, ...), almost all of which is
  out of Sprint 1 per [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md) — this
  is reference material, not an approved implementation spec for any current task. No UI was
  built from it in this session.
- Added a `check-added-large-files` exclusion in `.pre-commit-config.yaml` for
  `apps/web/src/assets/` and `docs/03-ux-ui/mockups/` (several logo PNGs and the mockup HTML
  legitimately exceed the repo's default 1MB cap).
- Three additional files the brief references (`Growixa Dashboard v2.dc.html`,
  `Growixa Onboarding.dc.html`, `Growixa Style Options.dc.html`) were not available locally —
  noted as missing in the reference doc in case they're added later.
- Not tied to a `GRX-*` tracker row — this is reference intake, not an implementation task.

## 2026-07-24 — GRX-RBAC-001: Centralized permission-check dependency

- **Scope decision, made explicit up front**: `require_permission()` cannot function
  without some way to resolve "who is making this request," but token issuance/validation
  is conceptually `auth`-module territory per
  [AUTHENTICATION.md §Centralized authorization](../08-security/AUTHENTICATION.md#centralized-authorization)
  and the `AuthProvider` adapter-boundary language — and `apps/api/auth/` doesn't exist yet
  (`GRX-AUTH-002`). Resolved by adding a narrowly-scoped `get_current_user_id()` to the
  `permissions` module: it only *verifies* an already-issued JWT cookie and extracts the
  user id — genuine, working code (hand-craft a validly-signed JWT with the same
  `jwt_signing_key` and it correctly authenticates), not a stub — but it issues nothing.
  `GRX-AUTH-002`'s login endpoint is what will actually mint that cookie. This mirrors how
  `GRX-FOUND-004`'s `apiFetch` was real code nothing called yet.
- Added `apps/api/src/growixa_api/permissions/repositories.py`:
  `user_has_permission(session, user_id, code) -> bool`, an ORM query joining
  `Permission`/`RolePermission`/`UserRole` — the only place in this module that talks to
  the database directly, per [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md).
  Note: `permissions`'s dependency table only lists `roles`, but this query necessarily also
  reads `users.models.UserRole` (owned by `users`) since a permission check inherently spans
  both — a read-only cross-module dependency, not a boundary violation (comparable to how
  `analytics` is documented to read across all modules).
- Added `apps/api/src/growixa_api/permissions/dependencies.py`:
  - `get_current_user_id(request) -> uuid.UUID` — decodes the `access_token` cookie via
    PyJWT (`HS256`, `Settings.jwt_signing_key`), 401s on missing/invalid/expired.
  - `RequirePermission` — a callable class (not a closure) so a route-protection audit can
    `isinstance()`-check a route's dependency tree; depends on `get_current_user_id` and
    `get_session`, 403s if `user_has_permission` is false, otherwise returns the user id.
  - `require_permission(code)` — the public factory matching the exact name used in
    [AUTHENTICATION.md](../08-security/AUTHENTICATION.md).
- Added `apps/api/tests/test_require_permission.py`: allowed / 403 / 401-missing-token /
  401-invalid-token cases, using the **real** Viewer role seeded by `GRX-AUTH-001`'s
  migration (Viewer has `company.settings.view`, not `users.manage`, per RBAC.md) — no
  fixture-only fake roles, the actual Sprint 1 seed data.
- Added `apps/api/tests/test_protected_routes_audit.py`, per
  [TEST_STRATEGY.md §RBAC authorization tests](../10-testing/TEST_STRATEGY.md#rbac-authorization-tests):
  walks every `APIRoute` in `create_app()` and asserts each one not explicitly allowlisted
  as public is guarded by a `RequirePermission` dependency somewhere in its dependency tree.
  Trivially true today (only `/health`, allowlisted) but becomes a real regression trap the
  moment the first protected route ships.
- **Bug found and fixed (test infra, not app code)**: `growixa_api.db`'s async engine/pool
  is a module-level singleton shared for the whole test process; pytest-asyncio's default
  function-scoped event loop meant a second async DB-touching test could be handed a pooled
  asyncpg connection opened under a *different* (already-closed) loop, raising
  `RuntimeError: ... attached to a different loop`. Fixed by setting
  `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope = "session"` in
  `pyproject.toml` so the whole test session shares one loop.
- **Bug found and fixed (test infra)**: the route-protection audit initially found zero
  `APIRoute`s at all — this FastAPI version (`0.139.2`) doesn't flatten
  `include_router()`'s routes directly into `app.routes` the way older versions did; it
  wraps them in an internal `_IncludedRouter` object exposing the real routes via
  `.original_router.routes`. Fixed by recursing through that wrapper (via `getattr`, not by
  importing the private class) rather than assuming a flat route list.
- Also added `extend-immutable-calls = ["fastapi.Depends", ...]` to ruff's `flake8-bugbear`
  config — B008 otherwise flags FastAPI's own required `Depends(...)`-in-defaults pattern as
  a mutable-default-argument bug, which it isn't.
- Verified: `ruff`/`format --check`/`mypy` clean across 23 source files; `pytest` 9 passed
  (4 pre-existing + 1 seed-data + 4 new); rebuilt the `api` image, `/health` unaffected.
- `GRX-RBAC-001` marked `DONE`. `GRX-COMPANY-001` (depended on this and `GRX-FOUND-005`,
  both now done) is newly `READY`, alongside the already-`READY` `GRX-AUDIT-001`,
  `GRX-TEST-001`, `GRX-TEST-002`.
- Commit: `7e77444`.

## 2026-07-24 — GRX-AUTH-001: Users, roles, permissions schema + seed

- **Task-ordering note**: picked this task ahead of the other three tasks that became
  `READY` alongside it after `GRX-FOUND-005` (`GRX-AUDIT-001`, `GRX-TEST-001`,
  `GRX-TEST-002`), even though the tracker doesn't encode the dependency: `audit_logs`
  (`GRX-AUDIT-001`) has `actor_user_id uuid FK → users.id` per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md), so the `users` table has to exist
  first. The tracker's `GRX-AUDIT-001` row only lists `GRX-FOUND-005` as a dependency — this
  is a real gap worth fixing in a future tracker-hygiene pass, not something to silently
  work around by reordering without a note.
- Added `apps/api/src/growixa_api/{roles,permissions,users}/models.py`: SQLAlchemy 2.0
  models (`Role`; `Permission`, `RolePermission`; `User`, `UserRole`) matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly — UUID PKs generated
  application-side (`default=uuid.uuid4`, no `pgcrypto` dependency), `CITEXT` email (case-
  insensitive per the schema doc), the `status IN ('ACTIVE','DISABLED')` check constraint.
  Split module-by-module per [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)
  (`permissions` owns `role_permissions`; `users` owns `user_roles`, since it references
  `assigned_by_user_id`). Only `models.py` was added per module — no `api/`, `services/`,
  `repositories/` yet, since this task's scope is schema + seed only (those layers have no
  real logic to hold yet; endpoints are `GRX-AUTH-002`/`GRX-RBAC-001`).
  `migrations/env.py` now imports all three model modules so `Base.metadata` is fully
  populated for `--autogenerate`.
- Added migration `d330e8b64b48` (autogenerated table DDL, hand-edited to add
  `CREATE EXTENSION IF NOT EXISTS citext` and seed data): creates all 5 tables in FK-safe
  order, then seeds the 6 Sprint 1 roles, 6 permission codes, and the full 16-row
  `role_permissions` matrix, exactly per [RBAC.md](../08-security/RBAC.md)'s role →
  permission table. Seed rows use fixed (not per-run-random) UUIDs hardcoded in the
  migration, generated once, so the migration is reproducible. Uses `sa.table()`/
  `op.bulk_insert()` proxies rather than importing the ORM models directly, per Alembic's
  own guidance (so a future model change can't silently rewrite this migration's meaning).
  Downgrade drops the 5 tables and the `citext` extension — full round-trip to empty.
- Added `apps/api/tests/test_auth_schema_seed.py`: an integration-tier test (real Postgres,
  same reasoning as `GRX-FOUND-005`'s migration test) asserting the *exact* set of 6 role
  names, *exact* set of 6 permission codes, and the *exact* role→permission matrix (not just
  row counts) match RBAC.md after `alembic upgrade head`.
- Verified: `ruff check`/`format --check`/`mypy` clean; `pytest` 4 passed (2 health + the
  generic migration round-trip from `GRX-FOUND-005`, now covering both migrations, + this
  task's seed-data test); spot-checked seed data directly via `psql` in the `postgres`
  container (6 roles, 6 permission codes, 16 `role_permissions` rows); rebuilt the `api`
  image and confirmed `podman compose exec api alembic current` reports the new head.
- **Known gap, explicitly not addressed in this task**: `LOCAL_DEVELOPMENT.md` documents a
  `python -m growixa_api.cli.seed_first_admin` command "finalized when `GRX-AUTH-001` ... is
  implemented," but no tracker task actually owns it, and it needs Argon2id password
  hashing, which is `GRX-AUTH-002`'s explicit scope (`apps/api/auth/`). Building it here
  would mean creating `apps/api/auth/` ahead of the task that owns that module. Left as a
  gap to resolve when `GRX-AUTH-002` is picked up (or as its own tracker line item) rather
  than silently expanding this task's scope into another module's territory.
- `GRX-AUTH-001` marked `DONE`. `GRX-RBAC-001` (its only dependency was this task) is newly
  `READY`, alongside the already-`READY` `GRX-AUDIT-001`, `GRX-TEST-001`, `GRX-TEST-002`.
- Commit: `daf9bc7`.

## 2026-07-24 — GRX-FOUND-004: Next.js application foundation

- Added `apps/web/src/lib/api-client.ts`: a small typed `fetch` wrapper (`apiFetch<T>`) that
  prepends `getApiUrl()`, sends `credentials: "include"` (auth is HttpOnly-cookie-based per
  [DEC-GRX-014](DECISIONS.md), not bearer tokens), and throws a typed `ApiError` on any
  non-2xx response instead of leaving every caller to check `response.ok`. Not yet consumed
  by any UI — nothing calls the API from the frontend until `GRX-AUTH-002`/`GRX-USER-002` —
  but this is genuine, working infrastructure (foundation work, explicitly allowed to stand
  alone per [DEFINITION_OF_DONE.md §No placeholder completion](DEFINITION_OF_DONE.md#no-placeholder-completion)),
  not a stub.
- Added `apps/web/src/app/not-found.tsx` as the routing-baseline piece: Next.js App Router's
  convention for a real custom 404, verified to actually return 404 (not just exist).
- Reworded `apps/web/src/app/page.tsx`'s placeholder copy — it referenced `GRX-FOUND-002`
  ("Placeholder page for local Docker Compose validation"), which was accurate when it was
  added as a stopgap for that task's stack validation, but this task is what actually
  establishes the app shell, so the copy no longer references a specific task.
- No changes to `.env.example`/env config — `NEXT_PUBLIC_API_URL` and `getApiUrl()` were
  already established in `GRX-FOUND-001`/`GRX-FOUND-002` and remain the single env surface.
- Verified: `npm run lint`, `format:check`, `typecheck`, and `build` all pass. Local smoke
  test (`next start`): `/` → 200 (renders "Growixa"), an unknown route → 404. Rebuilt the
  `web` Docker image and re-verified through the full Compose stack: all 5 services healthy,
  `GET /` → 200, unknown route → 404, `api`'s `/health` unaffected.
- No automated test harness was added — `GRX-TEST-002` (test runner config, component test
  harness, one e2e smoke test) is a separate, already-tracked task that owns building that
  infrastructure; this task's "smoke test loads root route" requirement was satisfied via
  the manual/scripted verification above, consistent with how `GRX-FOUND-002`'s smoke-test
  requirement was satisfied before any test runner existed.
- `GRX-FOUND-004` marked `DONE`. `GRX-AUDIT-001`, `GRX-AUTH-001`, `GRX-TEST-001` (already
  `READY` from `GRX-FOUND-005`), and `GRX-TEST-002` (newly `READY` — its only dependency was
  this task) are all now `READY`.
- Commit: `8269436`.

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
