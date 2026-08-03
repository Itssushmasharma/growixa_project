# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-08-03
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Task worked on

`GRX-EMAIL-001` — email provider connection + sender identity, the first task of Sprint 3
(Email Marketing). Picked up on the user's "GO to next" after Sprint 3 planning closed with
`GRX-EMAIL-001` at `READY`.

## Work completed

- New `growixa_api.integrations` module: `models.py` (`EmailProviderConnection`,
  `SenderIdentity`), `repositories.py`, `services.py`, `schemas.py`, `api.py`. Named
  `integrations`, not `email_integrations`, on purpose — per `MODULE_BOUNDARIES.md` this is
  the designated home for all future provider connections (social, SMS, etc.), not an
  email-only module; the user asked about this directly mid-session and this is the answer.
- Fernet symmetric encryption for SMTP credentials at rest (`DEC-GRX-009`): new
  `auth/encryption.py` (`encrypt_secret`/`decrypt_secret`, mirrors `auth/security.py`'s
  `@lru_cache` hasher pattern) and a new `encryption_key` setting — a genuinely generated
  `Fernet.generate_key()` value for local dev (not hand-typed), distinct from
  `jwt_signing_key` because it must be reversible: the future worker needs to decrypt SMTP
  credentials to actually send mail.
- New `integrations.manage` permission, Super Admin only — the project's first
  Admin-excluded permission, per RBAC.md's Slice 3 permission codes.
  `EmailProviderConnectionOut` never returns the password or its encrypted form under any
  route. Creating a new connection deactivates any existing active one rather than
  mutating it in place, preserving credential history.
- Migration `393c4222c8af`: `email_provider_connections` + `sender_identities` tables
  (matching `DATABASE_SCHEMA.md`'s spec exactly), the partial `(is_active) WHERE is_active`
  index (also declared on the SQLAlchemy model so `alembic check` sees no drift), and seeds
  `integrations.manage` granted to Super Admin.
- Wired the new router into `create_app()`; registered `integrations.models` in
  `migrations/env.py` for autogenerate.
- 7 new integration tests in `tests/test_integrations.py`: connection create + encryption
  round-trip, new-connection-deactivates-old, Admin gets 403 (the key negative test given
  this is the first Admin-excluded permission), unauthenticated 401, sender identity
  create/list/status-update, unknown-connection 404, invalid-status 400.

## Real bug found and fixed

The sender-identity status-update route raised `MissingGreenlet` on `updated_at` right
after `session.commit()`. Root cause: `updated_at`'s `onupdate=func.now()` expires that
attribute after an UPDATE, so reading it afterward (e.g. in the API layer's response model)
triggers an un-awaited lazy reload. This exact issue and fix already exist in
`contacts/services.py` (see its comment on `create_or_update_contact`) — moved the
`commit()` + `session.refresh(identity)` into the service function to match that
established pattern, rather than leaving commit to `api.py` as the `company`/`create`-path
routes do (those only ever INSERT, where eager defaults avoid this problem).

Also corrected the invalid-verification-status error from `422` to `400` — `422` isn't
used anywhere else in this codebase, and every other "invalid value" error (users, contacts,
imports) uses `400`.

## Files changed

- `apps/api/pyproject.toml` (added `cryptography>=43.0`)
- `apps/api/src/growixa_api/config.py` (new `encryption_key` setting)
- `apps/api/src/growixa_api/auth/encryption.py` (new)
- `apps/api/src/growixa_api/integrations/{__init__,models,repositories,services,schemas,api}.py` (new)
- `apps/api/src/growixa_api/app.py` (wired `integrations_router`)
- `apps/api/migrations/env.py` (registered `integrations` models)
- `apps/api/migrations/versions/393c4222c8af_email_provider_connections_and_sender_.py` (new)
- `apps/api/tests/test_integrations.py` (new)
- `apps/api/tests/test_auth_schema_seed.py` (extended `EXPECTED_PERMISSIONS`/`EXPECTED_MATRIX` for `integrations.manage`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-EMAIL-001` → `DONE`, `GRX-EMAIL-002` → `READY`)
- `docs/00-project-control/PROJECT_STATUS.md`, `CHANGELOG.md` (this update)

## Commands executed

- `uv pip install -e ".[dev]" --python .venv/bin/python` (this venv has no `pip` binary at
  all — confirmed via `ls .venv/bin/` and `python -m pip` failing with "No module named
  pip"; `uv pip install ... --python .venv/bin/python` is the working form for all future
  dependency changes here)
- `alembic revision`, `alembic upgrade head`, `alembic check` (clean, no drift)
- `ruff check`, `ruff format --check` (+ `ruff format` to fix two files), `mypy` — all clean
- `pytest tests/test_integrations.py` then the full suite: 111 passed, 3 skipped
- `podman compose up -d --build api` (rebuild required: `cryptography` is a new dependency
  baked into the image at build time, a plain `restart` would not have picked it up)
- Live curl verification against the rebuilt Compose stack (see below)

## Decisions

None new this task — followed the module boundary, encryption approach (`DEC-GRX-009`),
and permission split already decided during Sprint 3 planning.

## Blockers

None. `GRX-EMAIL-002` (email templates + versioning) is `READY` to start next.

## Known issues

- Possible latent `MissingGreenlet` in `company_profile` (background task filed,
  unresolved, carried over from earlier sessions) — same class of bug as the one fixed in
  this task for `sender_identities`, but a different code path; not touched here.
- Running the full backend `pytest` suite wipes `admin@growixa.local` (and any other
  manually-created accounts) as a side effect of `test_migrations.py`'s table-drop
  round-trip against the same database Compose uses — recreated it after this session's
  full suite run, before live verification, and cleaned up all smoke-test rows (the
  connection/identity created via curl, plus a throwaway Admin-role user and its audit log
  rows) afterward. Known quirk, not a bug to fix.
- [OQ-009](OPEN_QUESTIONS.md) (rich-text vs. drag-and-drop template editor) remains open —
  deferred to `GRX-EMAIL-002`/`008`, whichever actually builds the template editor UI.

## Current state

Sprint 1 and Sprint 2 are `DONE`. Sprint 3 (Email Marketing) is under way:
`GRX-EMAIL-001` (provider connection + sender identity) is `DONE`. `GRX-EMAIL-002`
(email templates + versioning) is `READY`; `GRX-EMAIL-003`–`010` remain `BACKLOG` behind it.

## Exact next task

`GRX-EMAIL-002` — email templates + versioning. `email_templates`/`email_template_versions`
tables + migration + a new `templates` module (repositories, services, schemas, api);
insert-only version history where editing a template produces a new version and never
mutates a past one. Gated on `campaigns.manage` (per RBAC.md's Slice 3 matrix — templates
are a drafting concern, not a separate permission). OQ-009 (editor choice) is deferred to
this task per the Slice 3 readiness gate.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit

`f545ad0` — feat(email): provider connection + sender identity API (GRX-EMAIL-001)
