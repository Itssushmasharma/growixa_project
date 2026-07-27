# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-AUTH-002` — Password hashing + login/logout. Picked per explicit user direction: P0,
backend-only, continuing this session's backend momentum rather than branching into
frontend work (`GRX-TEST-002`) or a P1 task (`GRX-COMPANY-002`).

## Work completed

- **`apps/api/src/growixa_api/auth/security.py`** (new): Argon2id `hash_password`/
  `verify_password`. Cost parameters (`argon2_time_cost`/`memory_cost`/`parallelism`)
  added to `Settings` as real configuration, per AUTHENTICATION.md's explicit requirement
  that cost be raiseable without a code change — defaults match argon2-cffi's own
  OWASP-baseline `PasswordHasher` defaults.
- **`apps/api/src/growixa_api/auth/tokens.py`** (new): `create_access_token` — the
  **issuing** half of the JWT that `permissions.dependencies.get_current_user_id`
  (`GRX-RBAC-001`) has been verifying since that task. Same signing key/algorithm,
  closing the gap flagged at the time. Also refresh-token generation
  (`secrets.token_urlsafe`) and SHA-256 hashing (fast/deterministic is correct here —
  unlike a password, a refresh token is already high-entropy, not brute-forceable).
- **`refresh_tokens` table** (migration `ea25a5343142`): deferred from `GRX-AUTH-001`
  since that task's scope was schema for users/roles/permissions only; needed now because
  issuing a refresh token requires persisting its hash. Includes `replaced_by_token_id`,
  which stays `NULL` until `GRX-AUTH-003` (rotation) lands, but exists now as part of the
  fixed schema in DATABASE_SCHEMA.md.
- **`apps/api/src/growixa_api/users/repositories.py`** (new): `get_user_by_email` — the
  `users` module's first repository file. `auth` depends on `users` for identity lookup
  per MODULE_BOUNDARIES.md, so this belongs there, not duplicated inside `auth`.
- **`auth/services.py`**: `login()` raises one `InvalidCredentialsError` for unknown
  email, wrong password, *and* disabled accounts alike (THREAT_MODEL.md T11 — none
  distinguishable from the response), each still recording `user.login_failed` with
  `entity_id` set only when a user was actually found (so the *audit trail* still
  distinguishes them for incident response — just never the HTTP response). Success path
  updates `last_login_at`, issues both tokens, records `user.login`. `logout()` revokes
  the presented refresh token and records `user.logout`.
- **`auth/api.py`**: `POST /auth/login`, `POST /auth/logout` — added to the
  route-protection audit's public allowlist (they're the entry points before a session
  exists). Cookies: `HttpOnly` + `SameSite=Lax` unconditionally; `Secure` conditional on
  `settings.environment != "local"` (local dev is plain HTTP; a browser won't resend a
  `Secure` cookie without HTTPS).
- **`apps/api/tests/test_auth_login.py`** (new): valid login (cookies present, **no
  token values in the JSON body** — checked directly, not assumed), identical generic
  error for wrong-password vs. unknown-email (compared byte-for-byte), disabled-account
  rejection, logout (revokes the token row, clears both cookies, records the audit
  event). Extended the shared `user_factory` (`GRX-TEST-001`) to hash a real, known
  password (`DEFAULT_TEST_PASSWORD`) and accept an explicit `email` override.

## A real bug found that affects every coverage number recorded so far this session

`auth/services.py` showed 50% coverage despite all 4 new tests passing with assertions
that only make sense if the "uncovered" lines ran (audit rows created, `last_login_at`
set, tokens revoked). Root cause: SQLAlchemy's async engine bridges into the sync DBAPI
driver via `greenlet_spawn`, and coverage.py's default tracer does not follow into that
greenlet context — silently under-reporting any code running on the other side of an
`await session.execute(...)`/`commit()` call. Fixed by adding `concurrency = ["greenlet"]`
to `[tool.coverage.run]` in `pyproject.toml`. Total coverage jumped from 85% to **94%** on
rerun — the true baseline was always higher; this was a measurement bug, not new code.
`GRX-TEST-001`'s previously-recorded 87% baseline is now known to have been undercounted
for the same reason — not retroactively rewritten there (historical evidence is
point-in-time), but noted here since this is where it was found.

## Verification beyond the automated suite

Rebuilt the `api` image, confirmed `alembic current` reports the new head inside the
container, then ran a real login → wrong-password → logout flow via curl against the live
Compose stack — inspected the actual `Set-Cookie` headers directly (`HttpOnly`,
`SameSite=lax`, correct `Max-Age` matching config, no `Secure` locally) and confirmed
logout's `Set-Cookie` headers clear both cookies (`Max-Age=0`). Cleaned up the smoke-test
user and rows afterward.

## Files changed

- `apps/api/src/growixa_api/auth/__init__.py`, `models.py`, `security.py`, `tokens.py`,
  `repositories.py`, `services.py`, `schemas.py`, `api.py` (new)
- `apps/api/src/growixa_api/users/repositories.py` (new)
- `apps/api/src/growixa_api/config.py` (argon2 cost settings)
- `apps/api/src/growixa_api/app.py` (mounts the new auth router)
- `apps/api/migrations/env.py` (imports the new auth models module)
- `apps/api/migrations/versions/ea25a5343142_refresh_tokens_table.py` (new)
- `apps/api/tests/conftest.py` (`user_factory` now hashes a real password, accepts `email`)
- `apps/api/tests/test_auth_login.py` (new)
- `apps/api/tests/test_protected_routes_audit.py` (added `/auth/login`, `/auth/logout` to
  the public allowlist)
- `apps/api/pyproject.toml` (`concurrency = ["greenlet"]` coverage fix)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-AUTH-002 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
# models written, wired into migrations/env.py
source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/alembic revision --autogenerate -m "refresh tokens table"
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/alembic upgrade head

.venv/bin/pytest -v   # 23 passed
# investigated suspiciously-low auth/services.py coverage, found the greenlet gap, fixed
# pyproject.toml, reran:
.venv/bin/pytest -v   # 23 passed, 94% coverage (corrected)

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # ea25a5343142 (head)
# created a smoke-test user with a real argon2 hash inside the container, then:
curl -i -c cookies.txt -X POST http://localhost:8000/auth/login -d '...'   # inspected Set-Cookie
curl -X POST http://localhost:8000/auth/login -d '{"password":"wrong",...}'  # generic error
curl -i -b cookies.txt -X POST http://localhost:8000/auth/logout            # cookies cleared
# cleaned up the smoke-test rows afterward
```

## Test results

`pytest` → 23 passed (19 pre-existing + 4 new). 94% coverage (corrected from a
measurement bug found in this task — see above). `ruff`/`mypy` clean across 56 source
files.

## Migrations

`ea25a5343142` — creates `refresh_tokens`. Depends on `1abf62872712`.

## Decisions

None new — implements the flows already specified in
[AUTHENTICATION.md](../08-security/AUTHENTICATION.md) and
[THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T11.

## Blockers

None.

## Known issues

- `replaced_by_token_id` on `refresh_tokens` is unused until `GRX-AUTH-003` (rotation)
  lands — expected, not a gap in this task's own scope.
- `GRX-AUTH-004` (rate limiting on login) is not implemented yet — still blocked on
  `GRX-FOUND-006` (Redis connectivity), which hasn't been started. Login currently has no
  brute-force protection; this is a known, tracked gap, not an oversight.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`) — now more
  relevant than ever, since there's finally a real login endpoint to use it with; CORS for
  frontend calls (`GRX-FOUND-004`) — needed before any browser-based frontend can actually
  call `/auth/login` cross-origin in local dev.

## Current state

Login and logout are real, tested, and verified end-to-end (automated suite + live curl
against Compose). Password hashing, access-token issuance, and refresh-token issuance/
storage all work. No rate limiting, no refresh-token rotation, no password reset yet.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-AUTH-003` (refresh-token
rotation + session revocation), `GRX-AUTH-005` (password reset flow), `GRX-USER-001`
(internal user invitation + acceptance), `GRX-TEST-002` (frontend test foundation),
`GRX-COMPANY-002` (company settings screen, frontend), `GRX-FOUND-008` (dashboard shell,
frontend). `GRX-AUTH-004` (rate limiting) still needs `GRX-FOUND-006` first.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

Recorded below after this handoff is committed alongside the `GRX-AUTH-002` change set.
