# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-AUTH-005` — Password reset flow. Picked as the last P0 backend auth task remaining
(everything else `READY` at that point was frontend work); closes the final
account-recovery gap in the auth system.

## Work completed

- **`password_reset_ttl_minutes` setting** (`config.py`, default 30) and **`PasswordResetToken`
  model** (`auth/models.py`) matching `DATABASE_SCHEMA.md`'s `password_reset_tokens` table:
  `id`, `user_id` (FK `ON DELETE CASCADE`, indexed), unique `token_hash`, `expires_at`,
  `used_at`. Migration `bb25de08ba84`.
- **`auth/repositories.py`**: added `create_password_reset_token()` and
  `get_password_reset_token_by_hash()`, following the exact shape of the existing
  refresh-token repository functions.
- **`auth/services.py`**:
  - `InvalidPasswordResetTokenError` — missing/unknown/expired/already-used token.
  - `request_password_reset(session, *, email)`: looks up the user, **always** records a
    `user.password_reset_requested` audit event (mirrors `user.login_failed`'s
    always-record-regardless-of-outcome pattern for security-monitoring symmetry), and only
    creates+returns a raw token when the account exists; returns `None` otherwise.
  - `complete_password_reset(session, *, raw_token, new_password)`: validates the token,
    sets the new Argon2 hash, marks the token used, calls the existing (GRX-AUTH-003)
    `revoke_all_active_sessions(..., reason="password_reset")` to kill every session, and
    records `user.password_reset_completed`.
- **`auth/schemas.py`**: `PasswordResetRequestIn`, `PasswordResetRequestOut` (with an
  optional `token` field), `PasswordResetCompleteIn`.
- **`auth/api.py`**: `POST /auth/password-reset/request` and
  `POST /auth/password-reset/complete`, both public (added to the route-protection audit's
  allowlist in `tests/test_protected_routes_audit.py`).

## An explicit, flagged scope decision — not a silent shortcut

`POST /auth/password-reset/request`'s response always returns an identical generic message
regardless of whether the email is registered (THREAT_MODEL.md T11). It additionally
includes a `token` field that is populated with the raw reset token **only** when
`settings.environment == "local"` — there is still no email-delivery channel in Sprint 1
(same constraint flagged in `GRX-USER-001`'s invitation-token handoff). In any non-local
environment `token` is always `null` for both known and unknown emails, so T11 holds there
unconditionally; in local dev it necessarily leaks account existence via the token's
presence, which is acceptable only because local dev has no other way to retrieve the
token for manual testing. **Revisit the moment a notifications/email-delivery task
exists**: send the token out-of-band and drop it from the API response entirely, in every
environment.

## Files changed

- `apps/api/src/growixa_api/config.py` (`password_reset_ttl_minutes` setting)
- `apps/api/src/growixa_api/auth/models.py` (added `PasswordResetToken`)
- `apps/api/src/growixa_api/auth/repositories.py` (added `create_password_reset_token`,
  `get_password_reset_token_by_hash`)
- `apps/api/src/growixa_api/auth/services.py` (added `InvalidPasswordResetTokenError`,
  `request_password_reset`, `complete_password_reset`)
- `apps/api/src/growixa_api/auth/schemas.py` (added `PasswordResetRequestIn`,
  `PasswordResetRequestOut`, `PasswordResetCompleteIn`)
- `apps/api/src/growixa_api/auth/api.py` (added both new routes)
- `apps/api/migrations/versions/bb25de08ba84_password_reset_tokens_table.py` (new)
- `apps/api/tests/test_protected_routes_audit.py` (added both new paths to the public
  allowlist)
- `apps/api/tests/test_auth_password_reset.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-AUTH-005 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this
  update)

## Commands executed

```bash
cd apps/api
source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/alembic upgrade head    # sync to current head first
.venv/bin/alembic revision --autogenerate -m "password reset tokens table"
.venv/bin/ruff format migrations/versions/bb25de08ba84_password_reset_tokens_table.py
.venv/bin/alembic upgrade head

# models/repositories/services/schemas/api written, tests written
.venv/bin/ruff check --fix . && .venv/bin/ruff format . && .venv/bin/mypy .
.venv/bin/pytest -v   # 38 passed, 95% coverage

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # bb25de08ba84 (head)
curl -s http://localhost:8000/health

# created a smoke-test user directly via the ORM inside the container (no self-registration
# endpoint exists), then:
curl -X POST http://localhost:8000/auth/login -d '{"email":...,"password":"Old-Password-123!"}'
curl -X POST http://localhost:8000/auth/password-reset/request -d '{"email":...}'
curl -X POST http://localhost:8000/auth/password-reset/complete -d '{"token":...,"new_password":"New-Password-789!"}'
curl -X POST http://localhost:8000/auth/login -d '{"email":...,"password":"Old-Password-123!"}'   # 401
curl -X POST http://localhost:8000/auth/login -d '{"email":...,"password":"New-Password-789!"}'   # 200
podman compose exec postgres psql -U growixa -d growixa -c "SELECT action, actor_user_id, entity_id, metadata FROM audit_logs WHERE ...;"
podman compose exec postgres psql -U growixa -d growixa -c "SELECT id, revoked_at IS NOT NULL FROM refresh_tokens WHERE user_id = '...';"
podman compose exec postgres psql -U growixa -d growixa -c "SELECT used_at IS NOT NULL FROM password_reset_tokens WHERE user_id = '...';"
# cleaned up the smoke-test rows afterward
```

## Test results

`pytest` → 38 passed (34 pre-existing + 4 new). 95% coverage. `ruff`/`mypy` clean across 65
source files.

## Migrations

`bb25de08ba84` — creates `password_reset_tokens`. Depends on `f356da0136c3`.

## Decisions

None new — implements the flow already specified in
[AUTHENTICATION.md](../08-security/AUTHENTICATION.md) and
[THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T11. The local-dev-only token exposure is
a documented, flagged scope call (see above), not a `DECISIONS.md`-level architecture
decision — it's the same interim call already made once in `GRX-USER-001`.

## Blockers

None.

## Known issues

- Raw password-reset token is exposed in the `POST /auth/password-reset/request` response
  body, but only when `settings.environment == "local"` — see the flagged scope decision
  above. Revisit when email delivery exists.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); CORS for
  frontend calls (`GRX-FOUND-004`); `GRX-AUTH-004` (rate limiting) blocked on
  `GRX-FOUND-006`; no "list pending invitations"/"revoke invitation" endpoints
  (`GRX-USER-001`).

## Current state

Full password-reset request→complete lifecycle works and is tested end-to-end (automated
suite + live curl against Compose). This completes the fourth step of this session's
user-directed backend-continuity sequence: `GRX-AUTH-002` → `GRX-AUTH-003` →
`GRX-USER-001` → `GRX-AUTH-005`. Every P0 backend auth task in Sprint 1 that isn't blocked
on `GRX-FOUND-006` (Redis) is now `DONE`.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-TEST-002` (frontend test
foundation), `GRX-COMPANY-002` (company settings screen, frontend), `GRX-FOUND-008`
(dashboard shell, frontend), `GRX-USER-002` (user management screens, frontend). All
remaining `READY` Sprint 1 backend work is exhausted — everything left either needs
`GRX-FOUND-006` (Redis, for `GRX-AUTH-004`) or is frontend work.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`730519b` — feat(auth): password reset flow (GRX-AUTH-005)
