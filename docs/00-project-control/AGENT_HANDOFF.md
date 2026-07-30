# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-30
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-CONTACT-001` — Contacts schema + CRUD. First implementation task of Sprint 2
(Contacts), picked immediately after this session's Sprint 2 planning pass (data model,
RBAC, sprint doc, tracker rows) per the user's explicit "GO" to start building.

## Work completed

- New `apps/api/src/growixa_api/contacts/` module: `models.py` (`Contact`,
  `ContactCustomField`, `ContactFieldValue`), `schemas.py`, `repositories.py`,
  `services.py`, `api.py`.
- Migration `209d29349ccf`: creates the three tables and seeds `contacts.manage`/
  `contacts.view` permission codes + role grants (reusing the fixed role UUIDs from
  `d330e8b64b48`).
- Endpoints: `POST /contacts` (create-or-update-by-email), `GET /contacts`, `GET
  /contacts/{id}`, `PATCH /contacts/{id}`, `PATCH /contacts/{id}/status`, `GET`/`POST
  /contacts/custom-fields`.
- Email is the sole dedup key (no fuzzy matching) — `POST /contacts` with an existing
  email updates that row in place rather than creating a duplicate.
- Contact activity reuses the existing `audit_logs` table (`entity_type = 'contact'`)
  instead of a new activity table, per this session's Slice 2 data-model design.

## A real bug found and fixed

`Contact.updated_at` has `server_default=func.now(), onupdate=func.now()`. SQLAlchemy's
ORM expires an `onupdate`-managed column after the UPDATE that triggers it commits, so
reading `contact.updated_at` synchronously afterward (which the API layer's `_to_out()`
does when building the response) raised `sqlalchemy.exc.MissingGreenlet` — a sync
attribute access can't perform the implicit reload without an active greenlet context.
Fixed by calling `await session.refresh(contact)` immediately after each mutating
`session.commit()` in `contacts/services.py`, while still inside an awaited call.

**Worth checking elsewhere**: `company_profile.updated_at` has the identical
`onupdate=func.now()` shape, and its existing test suite (`test_company_settings.py`)
only ever does one `PUT` per test — it's never exercised a second `PUT` against an
already-saved row, which is exactly the path that would trigger this. This may be a
latent, currently-unobserved instance of the same bug. Not fixed in this session (out of
scope for `GRX-CONTACT-001`) — flagged as a background task instead.

## Files changed

- `apps/api/src/growixa_api/contacts/{__init__,models,schemas,repositories,services,api}.py` (new)
- `apps/api/migrations/versions/209d29349ccf_contacts_schema.py` (new)
- `apps/api/migrations/env.py` (registered `contacts` models for autogenerate)
- `apps/api/src/growixa_api/app.py` (wired `contacts_router`)
- `apps/api/tests/test_contacts.py` (new, 12 tests)
- `apps/api/tests/test_auth_schema_seed.py` (extended exact-match permission assertions
  for the two new codes)
- `docs/00-project-control/MASTER_TASK_TRACKER.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`
  (this update)

## Commands executed

```bash
cd apps/api
.venv/bin/alembic revision --autogenerate -m "contacts schema"
# hand-edited the generated migration to add the permission/role-grant seed
.venv/bin/alembic upgrade head
.venv/bin/ruff check . && .venv/bin/ruff format . && .venv/bin/mypy .
.venv/bin/pytest -q   # 69 passed, 3 skipped (94% coverage)
.venv/bin/alembic check   # no drift

cd ../..
podman compose up -d --build api
podman compose exec api alembic current   # 209d29349ccf (head)
# live curl: login -> create custom field -> create contact with custom field value ->
# re-create with same email (dedup: same id, list stays at 1) -> archive -> reactivate
# (audit event confirmed via psql) -> Analyst 200/403 split -> Viewer 403/403 split
# recreated admin@growixa.local (wiped by the full pytest run's migration round-trip
# test, which drops/recreates all tables against the same DB Compose uses)
# cleaned up all smoke-test rows afterward
```

## Test results

`ruff`/`mypy` clean. `pytest` 69 passed, 3 skipped (94% coverage, 12 new tests for
contacts). `alembic check` → no drift. Live-verified end-to-end against rebuilt Compose
containers, including the dedup, archive/audit, and permission-split behaviors.

## Migrations

`209d29349ccf` — `contacts`, `contact_custom_fields`, `contact_field_values` tables;
seeds `contacts.manage`/`contacts.view` permissions and role grants. Downgrade removes
the permission/role-grant rows before dropping the tables.

## Decisions

None new beyond what Sprint 2 planning already recorded. Confirmed live that the
email-dedup design works as specified (update-in-place, not duplicate).

## Blockers

None.

## Known issues

- Possible latent `MissingGreenlet` bug in `company_profile`'s update path (see above) —
  not confirmed, not fixed, flagged for separate investigation.
- `GRX-DEVOPS-001` still `IN_REVIEW` — needs a push to confirm a green Actions run.
- `GRX-DOC-003` blocked on that same push.
- Everything else carried over from earlier sessions (`seed_first_admin` CLI, no
  invitation list/revoke endpoints, raw password-reset token in local dev only)
  unchanged.

## Current state

`GRX-CONTACT-001` is `DONE`. Sprint 2's next `READY` task is `GRX-CONTACT-002` (tags &
lists), which depends on it.

## Exact next task

`GRX-CONTACT-002` — Tags & lists (`tags`, `contact_tags`, `contact_lists`,
`contact_list_members` tables + API). No explicit user direction beyond continuing
Sprint 2; awaiting confirmation before picking it up.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
podman compose up -d
```

## Latest commit

`7ec6c93` — feat(contacts): contacts schema + CRUD with email dedup (GRX-CONTACT-001)
