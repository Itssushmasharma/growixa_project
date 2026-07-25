# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-25
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-AUDIT-001` — Audit log module. (This was the deferred half of the ordering issue
flagged during `GRX-AUTH-001` — proceeded now that `GRX-AUTH-001` is done.)

## Work completed

- **`apps/api/src/growixa_api/audit/models.py`** (new): `AuditLog` matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly. DB column `metadata` is
  mapped to Python attribute `event_metadata` (SQLAlchemy's `DeclarativeBase` reserves
  `.metadata` for the ORM's own `MetaData`). Indexes on `(entity_type, entity_id)`,
  `actor_user_id`, `created_at`.
- **Migration `6575d09949f9`**: clean autogenerate creating `audit_logs`.
- **`apps/api/src/growixa_api/audit/repositories.py`**: `create_audit_log`,
  `list_audit_logs` — raw persistence only, no business logic.
- **`apps/api/src/growixa_api/audit/services.py`**: `record_event` (redacts known-sensitive
  metadata keys — `password`, `password_hash`, `token`, `token_hash`, `refresh_token`,
  `access_token`, `secret` — to `"[REDACTED]"` before persisting; this is the
  "structured-log redaction" part of the task description and defense-in-depth for
  [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T7), `list_events` (thin wrapper). No
  `update`/`delete` function exists anywhere — insert-only by omission.
- **`apps/api/tests/test_audit_log.py`** (new): write→list round-trip, a system-actor event
  (`actor_user_id=None`), and a redaction test.
- **`apps/api/tests/test_audit_insert_only.py`** (new): introspects both modules via
  `inspect.getmembers`, asserts no public function name contains
  update/delete/modify/edit — the tracker's "negative test for missing update/delete
  routes," adapted since there's no HTTP layer in this module yet.

## Two real bugs found and fixed while validating this task

1. **Test fixture FK violation.** The write/list test's teardown deleted its throwaway test
   user while an audit row still referenced it as `actor_user_id` — which correctly has no
   `ON DELETE CASCADE` (an audit trail must survive the actor being removed). Fixed the
   fixture to delete its audit rows before the user.
2. **asyncpg type-cache poisoning (more interesting one).** `test_require_permission.py`
   started intermittently failing with `cache lookup failed for type ...` when run
   alongside `test_migrations.py`. Root cause: `test_migrations.py`'s downgrade→upgrade
   round trip was dropping and recreating the `citext` extension (in `GRX-AUTH-001`'s
   migration downgrade), and each `CREATE EXTENSION` gives the type a new Postgres OID —
   poisoning asyncpg's per-connection type cache for any already-pooled connection (recall
   `growixa_api.db`'s engine/pool is a session-wide singleton, per the `GRX-RBAC-001`
   session-loop fix) that later touches a `citext` column. Fixed by no longer dropping
   `citext` in that migration's `downgrade()` — table-level state is still fully reversible;
   leaving an installed extension behind after downgrade is standard, low-risk practice, and
   it eliminates the whole failure class rather than patching one symptom.

## Files changed

- `apps/api/src/growixa_api/audit/__init__.py`, `models.py`, `repositories.py`,
  `services.py` (new)
- `apps/api/migrations/env.py` (imports the new audit models module)
- `apps/api/migrations/versions/6575d09949f9_audit_logs_table.py` (new)
- `apps/api/migrations/versions/d330e8b64b48_users_roles_permissions_schema.py` (downgrade
  no longer drops the `citext` extension — see bug #2 above)
- `apps/api/tests/test_audit_log.py`, `test_audit_insert_only.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-AUDIT-001 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
# models written, wired into migrations/env.py
source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/alembic revision --autogenerate -m "audit logs table"
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/alembic upgrade head   # succeeds against Compose Postgres

.venv/bin/pytest -v   # 14 passed (after both bugfixes above)

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # 6575d09949f9 (head)
curl http://localhost:8000/health         # unaffected, still ok
```

## Test results

`pytest` → 14 passed: 10 pre-existing + 4 new (write/list round-trip, system-actor event,
redaction, insert-only audit). `ruff`/`mypy` clean across 30 source files.

## Migrations

`6575d09949f9` — creates `audit_logs`. Depends on `d330e8b64b48` (also touched this
session: its `downgrade()` no longer drops the `citext` extension — see bug #2). Verified
upgrade/downgrade/upgrade round-trip against real Compose Postgres.

## Decisions

None new — implements the schema already specified in
[DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md).

## Blockers

None.

## Known issues

None new. The `seed_first_admin` CLI gap (flagged in `GRX-AUTH-001`'s handoff) is still
open — relevant again now that `GRX-AUTH-002` is unblocked.

## Current state

Audit logging foundation (schema, insert-only repository/service, redaction) is done and
tested. Nothing calls `record_event` yet — no feature that should emit an audit event
(login, role change, etc.) is built yet. That starts with whichever of `GRX-AUTH-002`/
`GRX-USER-001` is picked up.

## Exact next task

Per explicit user direction: `GRX-TEST-001` (backend test foundation), then
`GRX-COMPANY-001` (company profile + brand settings). Also `READY` in the meantime:
`GRX-TEST-002` (frontend test foundation), `GRX-AUTH-002` (password hashing +
login/logout, newly unblocked), `GRX-USER-001` (internal user invitation + acceptance,
newly unblocked).

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`2b1dd7e` — feat(audit): insert-only audit log module (GRX-AUDIT-001)
