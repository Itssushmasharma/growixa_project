# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-USER-001` — Internal user invitation + acceptance. Picked per explicit user direction
as "most needed": the only real way to add any user to the system besides the
still-unbuilt `seed_first_admin` CLI (flagged since `GRX-AUTH-001`) or direct DB
manipulation.

## Work completed

- **Generalized `auth/tokens.py`** (`generate_refresh_token`/`hash_refresh_token` →
  `generate_token`/`hash_token`): invitation tokens need the exact same "high-entropy
  opaque token, SHA-256 hash for lookup" treatment as refresh tokens per
  AUTHENTICATION.md's token model. Verified only `auth/services.py` used the old names
  before renaming (grepped first) — a safe, contained rename, not a speculative one.
  Updated its 2 call sites; all 28 pre-existing tests still passed afterward.
- **`user_invitations` table** (migration `f356da0136c3`): both indexes
  DATABASE_SCHEMA.md specifies — a plain one on `email`, and a partial one on
  `email WHERE accepted_at IS NULL`.
- **`roles/repositories.py`** (new, `get_role_by_name`): `roles`'s first repository file —
  needed to resolve an invitation's `role_name` (e.g. "Viewer") to the seeded role's UUID.
- **`users/services.py`** (new):
  - `invite_user()`: resolves the role, checks the email isn't already registered (fails
    fast for the admin rather than only at acceptance), generates+hashes a token, returns
    `(invitation, raw_token)` — the raw token only ever exists in memory, never persisted.
  - `accept_invitation()`: re-validates not-yet-accepted / not-expired / email-still-free
    (closes a race between two acceptances, or the person registering some other way in
    between), creates the `User`, assigns the `UserRole`, marks the invitation accepted,
    records `invitation.accepted` with `actor_user_id` set to the **new** user (they're
    the one taking the accepting action, even though an admin initiated the invite).
- **`users/api.py`** (new): `POST /users/invitations` (permission-gated, `users.manage`),
  `POST /users/invitations/accept` (public — the invitee has no session yet, added to the
  route-protection audit's allowlist).

## An explicit, flagged scope decision — not a silent shortcut

`POST /users/invitations` returns the raw invitation token directly in its JSON response.
Sprint 1 has no email-delivery channel at all — no task for it exists anywhere in the
tracker — so there is currently no other way for the invitee to receive it. This is the
correct interim behavior given that constraint, not the intended end state. **Revisit the
moment a notifications/email-delivery task exists**: the token should be sent out-of-band
at that point and dropped from the API response entirely.

## Files changed

- `apps/api/src/growixa_api/auth/tokens.py` (renamed `generate_refresh_token`/
  `hash_refresh_token` → `generate_token`/`hash_token`)
- `apps/api/src/growixa_api/auth/services.py` (updated call sites for the rename)
- `apps/api/src/growixa_api/users/models.py` (added `UserInvitation`)
- `apps/api/src/growixa_api/users/repositories.py` (added `create_user`,
  `create_invitation`, `get_invitation_by_token_hash`)
- `apps/api/src/growixa_api/users/services.py`, `schemas.py`, `api.py` (new)
- `apps/api/src/growixa_api/roles/repositories.py` (new)
- `apps/api/src/growixa_api/config.py` (`invitation_ttl_days` setting)
- `apps/api/src/growixa_api/app.py` (mounts the new users router)
- `apps/api/migrations/env.py` (no new import needed — `UserInvitation` lives in the
  already-imported `users.models`)
- `apps/api/migrations/versions/f356da0136c3_user_invitations_table.py` (new)
- `apps/api/tests/test_protected_routes_audit.py` (added `/users/invitations/accept` to
  the public allowlist)
- `apps/api/tests/test_users_invitations.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-USER-001 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
# renamed auth/tokens.py functions, updated auth/services.py call sites
.venv/bin/pytest -v   # confirmed all 28 pre-existing tests still pass after the rename

# models written, wired into migrations/env.py (no new import — same users.models module)
source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/alembic revision --autogenerate -m "user invitations table"
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/alembic upgrade head

.venv/bin/pytest -v   # 34 passed, 94% coverage

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # f356da0136c3 (head)
# created a smoke-test Admin inside the container, then:
curl -c cookies.txt -X POST http://localhost:8000/auth/login -d '...'
curl -b cookies.txt -X POST http://localhost:8000/users/invitations -d '{"email":...,"role_name":"Viewer"}'
curl -X POST http://localhost:8000/users/invitations/accept -d '{"token":...,"password":...,"full_name":...}'
podman compose exec postgres psql -U growixa -d growixa -c "SELECT r.name FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE ur.user_id = '...';"
podman compose exec postgres psql -U growixa -d growixa -c "SELECT action FROM audit_logs WHERE actor_user_id = '...';"
# cleaned up the smoke-test rows afterward
```

## Test results

`pytest` → 34 passed (28 pre-existing + 6 new). 94% coverage. `ruff`/`mypy` clean across
63 source files.

## Migrations

`f356da0136c3` — creates `user_invitations`. Depends on `ea25a5343142`.

## Decisions

None new — implements the flow already specified in
[AUTHENTICATION.md](../08-security/AUTHENTICATION.md). The raw-token-in-response
interim behavior is a documented, flagged scope call (see above), not a `DECISIONS.md`-
level architecture decision.

## Blockers

None.

## Known issues

- Raw invitation token is exposed in the `POST /users/invitations` response body — see the
  flagged scope decision above. Revisit when email delivery exists.
- No "list pending invitations" or "revoke invitation" endpoint — out of this task's
  literal acceptance criteria (create + accept only); a natural addition for
  `GRX-USER-002`'s admin UI or its own small backend task if the UI needs it.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); CORS for
  frontend calls (`GRX-FOUND-004`); `GRX-AUTH-004` (rate limiting) blocked on
  `GRX-FOUND-006`.

## Current state

Full invite → accept lifecycle works and is tested end-to-end (automated suite + live
curl against Compose). An Admin can now provision new internal users without touching the
database directly. This completes the third step of this session's user-directed "most
needed" sequence: `GRX-AUTH-002` → `GRX-AUTH-003` → `GRX-USER-001`.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-AUTH-005` (password reset
flow), `GRX-TEST-002` (frontend test foundation), `GRX-COMPANY-002` (company settings
screen, frontend), `GRX-FOUND-008` (dashboard shell, frontend), `GRX-USER-002` (user
management screens, frontend, newly unblocked). `GRX-AUTH-004` (rate limiting) still needs
`GRX-FOUND-006`.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`87d2110` — feat(users): internal user invitation + acceptance (GRX-USER-001)
