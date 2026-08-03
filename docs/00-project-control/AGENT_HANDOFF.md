# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-08-03
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Task worked on

`GRX-EMAIL-002` — email templates + versioning, the second task of Sprint 3 (Email
Marketing). Picked up on the user's "continue next" after `GRX-EMAIL-001` closed.

## Work completed

- New `growixa_api.templates` module: `EmailTemplate`/`EmailTemplateVersion` models
  matching `DATABASE_SCHEMA.md`'s spec exactly, plus `repositories.py`, `services.py`,
  `schemas.py`, `api.py`.
- Routes gated on `campaigns.manage` (create/edit) and `campaigns.view` (read) per
  RBAC.md's Slice 3 matrix. Neither permission existed in the DB yet — Slice 3 planning
  deliberately deferred seeding them to whichever task first needed them — so migration
  `d36211c53aed` seeds both. `campaigns.send` stays deferred to `GRX-EMAIL-004`, where the
  actual send action lands.
- `POST /templates` creates a template and its version 1 together (a template can't exist
  without content). `POST /templates/{id}/versions` appends `version_number = max+1`; the
  previous version's row is never touched — matches `ConsentRecord`'s insert-only pattern,
  with "current" derived as the highest `version_number` rather than a mutable pointer.
  `GET /templates/{id}/versions` returns the full history, newest first.
- 6 new integration tests in `tests/test_templates.py`: create, edit-creates-new-version-
  without-mutating-old (asserts both rows survive with distinct content), a
  `campaigns.view`-only role (Analyst) can read but gets 403 on write, Viewer gets 403 on
  read, unauthenticated 401, 404 on an unknown template for get/list-versions/edit.
- Extended `test_auth_schema_seed.py`'s `EXPECTED_PERMISSIONS`/`EXPECTED_MATRIX` for the
  two new permission codes.

## Decisions

None new — followed the module/permission split already decided during Sprint 3 planning
and RBAC.md's existing `campaigns.manage`/`campaigns.view` descriptions.

## Files changed

- `apps/api/src/growixa_api/templates/{__init__,models,repositories,services,schemas,api}.py` (new)
- `apps/api/src/growixa_api/app.py` (wired `templates_router`)
- `apps/api/migrations/env.py` (registered `templates` models)
- `apps/api/migrations/versions/d36211c53aed_email_templates_and_versions.py` (new)
- `apps/api/tests/test_templates.py` (new)
- `apps/api/tests/test_auth_schema_seed.py` (extended for `campaigns.manage`/`campaigns.view`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-EMAIL-002` → `DONE`, `GRX-EMAIL-003` → `READY`)
- `docs/00-project-control/PROJECT_STATUS.md`, `CHANGELOG.md` (this update)

## Commands executed

- `alembic revision`, `alembic upgrade head`, `alembic check` (clean, no drift)
- `ruff check`/`ruff format --check`/`mypy` across the whole repo — all clean
- `pytest tests/test_templates.py` then the full suite: 117 passed, 3 skipped
- `podman compose restart api` (no new dependency this time, code + migration only —
  unlike `GRX-EMAIL-001` this didn't need a full image rebuild)
- Live curl verification against Compose (see below)

## Blockers

None. `GRX-EMAIL-003` (campaigns CRUD + targeting) is `READY` to start next.

## Known issues

- Possible latent `MissingGreenlet` in `company_profile` (background task filed,
  unresolved, carried over from earlier sessions) — not touched here. `templates` doesn't
  have this exposure: nothing ever UPDATEs an `email_templates`/`email_template_versions`
  row after insert (no rename endpoint, versions are insert-only), so `updated_at`'s
  `onupdate=func.now()` never fires and the refresh-after-commit issue fixed in
  `GRX-EMAIL-001` doesn't apply here.
- Running the full backend `pytest` suite wipes `admin@growixa.local` — recreated it
  after this session's full suite run, before live verification, and cleaned up all
  smoke-test rows (the template/versions created via curl, plus a throwaway Viewer user
  and its audit log rows) afterward. Known quirk, not a bug to fix.
- [OQ-009](OPEN_QUESTIONS.md) (rich-text vs. drag-and-drop template editor) remains open —
  this task deliberately didn't resolve it: `body_html`/`body_text` accept whatever a
  future editor produces, per `DATA_MODEL.md`'s note that OQ-009 doesn't require a schema
  change. Still deferred to `GRX-EMAIL-008` (email templates frontend), which is the task
  that will actually build the editor UI.

## Current state

Sprint 1 and Sprint 2 are `DONE`. Sprint 3 (Email Marketing) is under way:
`GRX-EMAIL-001` and `GRX-EMAIL-002` are `DONE`. `GRX-EMAIL-003` (campaigns CRUD +
targeting) is `READY`; `GRX-EMAIL-004`–`010` remain `BACKLOG` behind it.

## Exact next task

`GRX-EMAIL-003` — campaigns CRUD + targeting. `campaigns`/`campaign_versions`/
`campaign_recipients` tables + migration + a new `campaigns` module; a campaign draft can
target a segment, list, or all contacts (reusing Slice 2's `contacts` module), reference a
template (`templates.email_templates`) or ad hoc content, and stay editable until send.
`campaign_versions` gets exactly one row per campaign, written at send time (not per-edit
history) — that write itself is `GRX-EMAIL-004`'s job, not this task's. Gated on
`campaigns.manage` (already seeded by `GRX-EMAIL-002`) for drafting, `campaigns.view` for
read.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit

`1dac3ff` — feat(email): templates + versioning API (GRX-EMAIL-002)
