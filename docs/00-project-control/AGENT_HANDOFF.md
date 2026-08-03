# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-08-03
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Task worked on

`GRX-EMAIL-003` — campaigns CRUD + targeting, the third task of Sprint 3 (Email
Marketing). Picked up on the user's "ok" after `GRX-EMAIL-002` closed and I named
`GRX-EMAIL-003` as next.

## Work completed

- New `growixa_api.campaigns` module: `Campaign`, `CampaignVersion`, `CampaignRecipient`
  models matching `DATABASE_SCHEMA.md`'s spec, plus `repositories.py`, `services.py`,
  `schemas.py`, `api.py`.
- Migration `d7fa144e5c60` creates all three tables together (per `DATABASE_SCHEMA.md`'s
  migration-order note), but this task only implements CRUD for `campaigns` itself —
  `campaign_versions`/`campaign_recipients` are schema-only, to be populated by
  `GRX-EMAIL-004`'s send pipeline job. No new permissions: reused `campaigns.manage`
  (create/edit) and `campaigns.view` (read), already seeded by `GRX-EMAIL-002`.
- Recipient targeting validation (`_validate_recipient_target` in `services.py`): checks
  `recipient_type` is one of `SEGMENT`/`LIST`/`ALL_CONTACTS`, that exactly one of
  `recipient_segment_id`/`recipient_list_id` is set matching that type (a service-layer
  rule, not a DB CHECK constraint, per `DATABASE_SCHEMA.md`), and that the referenced
  segment/list actually exists — calling `contacts.repositories.get_segment_by_id`/
  `get_contact_list_by_id` directly, per `MODULE_BOUNDARIES.md`'s cross-module call
  convention. Same convention used to validate `sender_identity_id` (via
  `integrations.repositories.get_sender_identity`) and optional `template_id` (via
  `templates.repositories.get_template`).
- `PATCH /campaigns/{id}` uses `payload.model_dump(exclude_unset=True)` rather than the
  "`None` means don't touch" convention used elsewhere (contacts) — needed here because
  switching `recipient_type` must be able to explicitly null out the no-longer-relevant
  `recipient_segment_id`/`recipient_list_id`, which the simpler convention can't express.
  Editing is rejected with `409` once `campaign.status` has left `DRAFT`
  (`CampaignNotEditableError`), enforced at the service layer per `DATA_MODEL.md`.
- 10 new integration tests in `tests/test_campaigns.py`: create for each recipient_type
  (including from a template), invalid targeting shapes (missing segment, both set,
  unknown segment), unknown sender_identity 404, editing a draft updates fields and can
  switch targeting cleanly (old reference cleared), editing a non-DRAFT campaign is
  rejected (409), a `campaigns.view`-only role (Analyst) can read but not write,
  unauthenticated 401, 404 on an unknown campaign.

## Decisions

None new — followed the module/permission split and targeting rules already specified
in `DATA_MODEL.md`/`DATABASE_SCHEMA.md`/`RBAC.md` from Sprint 3 planning.

## Files changed

- `apps/api/src/growixa_api/campaigns/{__init__,models,repositories,services,schemas,api}.py` (new)
- `apps/api/src/growixa_api/app.py` (wired `campaigns_router`)
- `apps/api/migrations/env.py` (registered `campaigns` models)
- `apps/api/migrations/versions/d7fa144e5c60_campaigns_versions_and_recipients.py` (new)
- `apps/api/tests/test_campaigns.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-EMAIL-003` → `DONE`, `GRX-EMAIL-004` → `READY`)
- `docs/00-project-control/PROJECT_STATUS.md`, `CHANGELOG.md` (this update)

## Commands executed

- `alembic revision`, `alembic upgrade head`, `alembic check` (clean, no drift)
- `ruff check`/`ruff format --check`/`mypy` across the whole repo — all clean
- `pytest tests/test_campaigns.py` then the full suite: 127 passed, 3 skipped
- `podman compose restart api` (no new dependency, code + migration only)
- Live curl verification against Compose (see below)

## Blockers

None. `GRX-EMAIL-004` (send pipeline: worker + `email_delivery`) is `READY` to start next.

## Known issues

- Possible latent `MissingGreenlet` in `company_profile` (background task filed,
  unresolved, carried over from earlier sessions) — not touched here. `campaigns.status`
  and other onupdate-triggered columns on `Campaign` are correctly handled via the
  established commit+refresh pattern in `campaigns/services.py::update_campaign`.
- Running the full backend `pytest` suite wipes `admin@growixa.local` — recreated it
  after this session's full suite run (as Super Admin, per this project's established
  convention — briefly mis-created it as Marketing Manager first and corrected it before
  proceeding), and cleaned up all smoke-test rows (the campaign/segment/sender identity
  created via curl, plus a throwaway Viewer user and its audit log rows) afterward.
  Known quirk, not a bug to fix.
- `campaign_versions`/`campaign_recipients` tables exist but are empty by design until
  `GRX-EMAIL-004` writes to them — not a gap in this task, per its own scope.

## Current state

Sprint 1 and Sprint 2 are `DONE`. Sprint 3 (Email Marketing) is under way:
`GRX-EMAIL-001`, `GRX-EMAIL-002`, and `GRX-EMAIL-003` are all `DONE`. `GRX-EMAIL-004`
(send pipeline) is `READY`; `GRX-EMAIL-005`–`010` remain `BACKLOG` behind it.

## Exact next task

`GRX-EMAIL-004` — send pipeline (worker + `email_delivery`). New
`growixa_api.email_delivery` module plus `apps/worker/` extension: `message_deliveries`/
`delivery_attempts` tables + migration, a `grx.email_delivery.send_campaign` job
(following `BACKGROUND_JOB_ARCHITECTURE.md`'s envelope/idempotency/retry pattern already
used by `GRX-FOUND-007`). Sending must enqueue a worker job, not send inline; at send
time it resolves recipients into `campaign_recipients` (materializing the segment/list/
all-contacts targeting), suppression-checks each one against `suppression_entries`
(`DEC-GRX-008` — cannot be a fast-follow, needs a negative test), freezes exactly one
`campaign_versions` snapshot row, and writes `usage_records`' first real row. Gated on
`campaigns.send` (not yet seeded — this task's migration should seed it, per RBAC.md's
Slice 3 matrix: Super Admin/Admin/Marketing Manager only, Content Creator excluded).

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit

`52fa336` — feat(email): campaigns CRUD + targeting API (GRX-EMAIL-003)
