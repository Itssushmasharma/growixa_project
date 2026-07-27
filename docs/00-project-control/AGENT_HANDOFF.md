# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-AUTH-003` — Refresh-token rotation + session revocation. Picked per explicit user
direction as "most needed first": closes a real security gap `GRX-AUTH-002` left open —
refresh tokens were issued but never rotated, with no reuse detection, meaning a stolen
refresh token could be replayed indefinitely.

## Work completed

- **`POST /auth/refresh`, `POST /auth/logout-all`** (new, in `auth/api.py`): both public
  routes (added to the route-protection audit's allowlist) that identify the acting user
  via the refresh token itself — consistent with the existing `/auth/logout`, not via
  `get_current_user_id`/`require_permission`.
- **`auth/services.refresh()`** (new): looks up the presented token by hash.
  - If already revoked by a *previous rotation* (not by logout) → reuse/compromise
    signal: calls `revoke_all_active_sessions()` to kill **every** session for that user,
    not just reject this one request, then raises.
  - If expired, or the user is no longer `ACTIVE` → rejects (the `ACTIVE` check is
    defense-in-depth on top of disable always revoking sessions elsewhere — don't rely on
    only one mechanism).
  - Otherwise: issues a new access + refresh token, marks the presented one
    `revoked_at` + `replaced_by_token_id` pointing at the new one — the
    `replaced_by_token_id` column that's existed since `GRX-AUTH-002`'s migration but
    stayed unused until now.
- **`auth/services.revoke_all_active_sessions(session, user_id, *, reason)`** (new):
  deliberately public (not `_`-prefixed) and does **not** commit itself — meant to compose
  into a larger transaction (e.g. a future disable-user action, which doesn't exist as its
  own endpoint yet and is out of `apps/api/auth/`'s own scope). Records a `session.revoked`
  audit event (Sprint 1's event set) with `reason`/`count`, only when something was
  actually revoked.
- **`auth/services.logout_all()`** (new): reuses the same revoke function, keyed off the
  presented refresh token — "log out everywhere" from any one of your own sessions.
- **`apps/api/tests/test_auth_refresh.py`** (new): rotation (new cookies, old token
  revoked with correct `replaced_by_token_id`), reuse detection (replaying the
  pre-rotation token 401s *and* revokes the entire chain, including the token it had
  already rotated to), `logout-all` across two simulated devices (two separate
  `AsyncClient`s — one client's cookie jar would silently overwrite the first session's
  refresh cookie on a second login), disable-revokes-sessions (proves the
  `revoke_all_active_sessions()` building block works, since no disable-user endpoint
  exists yet to exercise this end-to-end), and expired-token rejection.

## Verification beyond the automated suite

Rebuilt the `api` image, then ran a real login → refresh → replay-old-token flow via curl
against the live Compose stack, confirming via direct `psql` queries that *both* refresh
tokens ended up revoked and the `session.revoked` audit row was recorded with
`reason: "refresh_token_reuse_detected"`. Cleaned up the smoke-test user/rows afterward.

## Files changed

- `apps/api/src/growixa_api/auth/repositories.py` (added
  `list_active_refresh_tokens_for_user`)
- `apps/api/src/growixa_api/auth/services.py` (added `InvalidRefreshTokenError`,
  `revoke_all_active_sessions`, `refresh`, `logout_all`)
- `apps/api/src/growixa_api/auth/api.py` (added `/auth/refresh`, `/auth/logout-all`)
- `apps/api/tests/test_protected_routes_audit.py` (added both new routes to the public
  allowlist)
- `apps/api/tests/test_auth_refresh.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-AUTH-003 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .   # all clean

source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/pytest -v   # 28 passed, 94% coverage

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # ea25a5343142 (head — no schema change this task)
# created a smoke-test user inside the container, then:
curl -c cookies.txt -X POST http://localhost:8000/auth/login -d '...'
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8000/auth/refresh
curl -X POST http://localhost:8000/auth/refresh -H "Cookie: refresh_token=$OLD_TOKEN"  # 401
podman compose exec postgres psql -U growixa -d growixa -c "SELECT token_hash, revoked_at IS NOT NULL FROM refresh_tokens WHERE user_id = '...';"
podman compose exec postgres psql -U growixa -d growixa -c "SELECT action, metadata FROM audit_logs WHERE actor_user_id = '...';"
# cleaned up the smoke-test rows afterward
```

## Test results

`pytest` → 28 passed (23 pre-existing + 5 new). 94% coverage. `ruff`/`mypy` clean across
57 source files.

## Migrations

None — `refresh_tokens`'s full schema (including `replaced_by_token_id`) already existed
from `GRX-AUTH-002`'s migration; this task only started using the previously-unused column.

## Decisions

None new — implements the rotation/reuse-detection/revocation flows already specified in
[AUTHENTICATION.md](../08-security/AUTHENTICATION.md).

## Blockers

None.

## Known issues

- No disable-user HTTP endpoint exists yet to actually flip `users.status = 'DISABLED'` in
  production use — `revoke_all_active_sessions()` is built and tested as the reusable
  building block a future user-management task will call, but nothing calls it that way
  yet. Not a gap in this task's own scope (`apps/api/auth/` only).
- `GRX-AUTH-004` (rate limiting) still blocked on `GRX-FOUND-006` (Redis connectivity) —
  login and refresh both still have no brute-force protection.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); CORS for
  frontend calls (`GRX-FOUND-004`).

## Current state

The full refresh-token lifecycle (issue → rotate → detect reuse → revoke) is real, tested,
and verified end-to-end. Login, logout, refresh, and logout-all are all implemented and
working. No password reset, no rate limiting, no user invitation flow yet.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-AUTH-005` (password reset
flow), `GRX-USER-001` (internal user invitation + acceptance), `GRX-TEST-002` (frontend
test foundation), `GRX-COMPANY-002` (company settings screen, frontend), `GRX-FOUND-008`
(dashboard shell, frontend). `GRX-AUTH-004` (rate limiting) still needs `GRX-FOUND-006`.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`27a22af` — feat(auth): refresh-token rotation + session revocation (GRX-AUTH-003)
