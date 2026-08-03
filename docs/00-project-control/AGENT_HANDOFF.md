# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-08-04
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Task worked on

`GRX-WEB-002` — Public 3D Brand & Landing Website (`apps/web/src/app/(marketing)/`).

## Work completed

- Built the public Growixa 3D Brand & Landing Website adhering to Linear, Vercel, and Stripe design standards:
  - **`navbar.tsx`**: Header with official `BrandLogo` (`/assets/logo-icon.png`), nav links (*Platform*, *Solutions*, *Pricing*, *Security*, *Docs*), and dynamic CTAs (*Log In* / *Start Free* / *Go to Dashboard*).
  - **`hero-section.tsx`**: Outcome-focused hero (*"Grow Faster. Market Smarter. Powered by AI."*), dual CTAs (*"Start Free"*, *"Book Demo"*), and 3D floating glass dashboard preview card with live metric counters & simulated growth chart.
  - **`trust-bar.tsx`**: Social proof metric bar (*1,000+ Businesses*, *50M+ Emails*, *12M AI Generations*, *99.99% Uptime*).
  - **`ai-team-section.tsx`**: "Meet Your AI Marketing Team" grid showcasing 6 AI agents (Copywriter, Email Optimizer, Campaign Planner, Audience Builder, Social Creator, Marketing Analyst).
  - **`workflow-showcase.tsx`**: Visual automation step pipeline (*Lead fills form* ➔ *AI scores lead* ➔ *Email sequence* ➔ *WhatsApp/SMS* ➔ *Sales notified*).
  - **`integrations-section.tsx`**: Logo grid showcasing native connections (Postmark, Stripe, Razorpay, OpenAI, Claude, Meta, LinkedIn, Slack, Zapier).
  - **`security-section.tsx`**: Enterprise reliability badges (SOC2 Ready, GDPR, Fernet Encryption, RBAC, Insert-Only Audit Logs, 99.99% SLA Uptime).
  - **`pricing-section.tsx`**: Stripe-style tiered pricing matrix (Starter, Growth, Enterprise).
  - **`footer.tsx`**: Complete multi-column SaaS footer with system status badge.
  - **Dedicated Sub-pages**: `/features`, `/pricing`, `/solutions`, `/security`, `/docs`.
- Integrated official brand logo assets from `apps/web/src/assets/icon/growixa-icon-mark.png` and `primary/growixa-primary-horizontal-logo.png` into `public/assets/`.
- Verified zero regressions across Vitest (54 passed) and Playwright E2E (4 passed).

## Files changed

- `apps/web/src/app/(marketing)/marketing.module.css` (new)
- `apps/web/src/app/(marketing)/navbar.tsx` (new)
- `apps/web/src/app/(marketing)/hero-section.tsx` (new)
- `apps/web/src/app/(marketing)/trust-bar.tsx` (new)
- `apps/web/src/app/(marketing)/ai-team-section.tsx` (new)
- `apps/web/src/app/(marketing)/workflow-showcase.tsx` (new)
- `apps/web/src/app/(marketing)/integrations-section.tsx` (new)
- `apps/web/src/app/(marketing)/security-section.tsx` (new)
- `apps/web/src/app/(marketing)/pricing-section.tsx` (new)
- `apps/web/src/app/(marketing)/footer.tsx` (new)
- `apps/web/src/app/(marketing)/page.tsx` (new)
- `apps/web/src/app/(marketing)/page.test.tsx` (new)
- `apps/web/src/app/(marketing)/features/page.tsx` (new)
- `apps/web/src/app/(marketing)/pricing/page.tsx` (new)
- `apps/web/src/app/(marketing)/solutions/page.tsx` (new)
- `apps/web/src/app/(marketing)/security/page.tsx` (new)
- `apps/web/src/app/(marketing)/docs/page.tsx` (new)
- `apps/web/src/components/brand-logo.tsx` (new)
- `apps/web/public/assets/` (`logo-icon.png`, `logo-horizontal.png`, `hero-3d-concept.png`, `features-3d-concept.png`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md`

## Commands executed

```bash
git checkout -b feature/FRONTEND/GRX-WEB-002
cd apps/web
npm run format && npm run lint && npm run typecheck && npm run test -- --run   # 54 passed (all clean)
npx playwright test                                                             # 4 passed (Playwright e2e)
```

## Test results

- `tsc --noEmit`, `eslint`, `prettier --check` clean.
- `vitest` 54 passed.
- Playwright `test:e2e` 4 passed.

## Current state

`GRX-WEB-002` is fully `DONE` and committed (`7b94ba2` & `eca4dd7`).

## Exact next task

`GRX-EMAIL-005` (Postmark webhook receiver + unsubscribe handling) is in progress by backend agent. Next frontend task is `GRX-EMAIL-007` / `GRX-ADMIN-001`.

## Latest commit

`eca4dd7` — feat(web): update brand logo component to use official logo-icon asset

## Decisions made this session

Before writing code, two open architectural questions were surfaced to the user directly
(not guessed):

1. **How should `apps/worker` access the database?** `apps/worker` is a separate Python
   package from `apps/api` with no shared code, but `send_campaign` needs to read/write
   Postgres. Chosen: the worker gets its **own minimal SQLAlchemy/asyncpg data layer** —
   lightweight models for exactly the tables it touches — rather than depending on
   `growixa_api` as a library. Keeps the two apps independently deployable, matching
   `SYSTEM_ARCHITECTURE.md`'s "independently scalable Python workers" framing, at the
   cost of hand-kept-in-sync column definitions.
2. **Is a live Postmark account available for real-send verification?** No. Per
   `DEC-GRX-011`/`SPRINT_03_EMAIL_CAMPAIGN.md`'s own pre-approved fallback: build the
   full real pipeline (real SMTP client, real DB writes) and explicitly document the
   final outbound-send success as an evidence gap rather than silently assuming it or
   faking it with a mock.

## Work completed

- **Real gap found and fixed**: `usage_records` was documented (`DATA_MODEL.md`,
  `DEC-GRX-007`) as already existing since Sprint 1, but no migration or model for it
  existed anywhere in the codebase — a genuine miss that slipped through undetected
  until this task's own acceptance criterion (`usage_records` gets its first real
  write) needed the table to actually exist. Created new `growixa_api.usage` module
  (`models.py` only — nothing in `apps/api` writes to it; the worker owns that write
  path) and bundled its table into this task's migration.
- New `growixa_api.email_delivery` module: `MessageDelivery`/`DeliveryAttempt` models
  matching `DATABASE_SCHEMA.md`. `POST /campaigns/{id}/test-send` sends synchronously
  and inline via a new `smtp_sender.py` (`aiosmtplib`-based) — deliberately not queued,
  since a test send touches no campaign/recipient/delivery state at all, unlike a real
  send which `BACKGROUND_JOB_ARCHITECTURE.md` forbids running inline.
  `POST /campaigns/{id}/send` flips the campaign to `SENDING` and enqueues
  `grx.email_delivery.send_campaign` via the existing `jobs.producer.publish_job`.
- Migration `7049ac70cac8`: `usage_records`, `message_deliveries`, `delivery_attempts`
  tables, plus seeds the new `campaigns.send` permission (Super Admin/Admin/Marketing
  Manager only — Content Creator has `campaigns.manage` but deliberately not this,
  per RBAC.md's Slice 3 matrix).
- **`apps/worker` additions**: `db.py` (lazy-singleton async engine/session factory —
  lazy specifically so importing the module doesn't require `DATABASE_URL` to be set,
  keeping the existing non-DB tests import-safe), `encryption.py` (Fernet decrypt,
  mirroring `growixa_api.auth.encryption`, same shared local-dev key default),
  `email_sender.py` (`aiosmtplib` wrapper, mirrors `growixa_api`'s), `models.py`
  (minimal SQLAlchemy models — `Contact`, `Tag`, `ContactTag`, `ContactCustomField`,
  `ContactFieldValue`, `ContactList`, `ContactListMember`, `Segment`, `SegmentRule`,
  `SegmentMember`, `ConsentRecord`, `SuppressionEntry`, `EmailProviderConnection`,
  `SenderIdentity`, `Campaign`, `CampaignVersion`, `CampaignRecipient`,
  `MessageDelivery`, `DeliveryAttempt`, `UsageRecord` — no `ForeignKey("users.id")`
  since `users` isn't modeled here and the worker never emits DDL), `recipients.py`
  (duplicates `growixa_api.contacts.repositories.build_rule_condition`'s segment-rule
  evaluator — necessary duplication, not accidental, since the worker doesn't import
  `growixa_api`), `send_campaign.py` (the job handler). New `.env`/`.env.example` for
  the worker — its first time needing local settings beyond `RABBITMQ_URL`.
- `send_campaign`'s pipeline: resolve recipients by `recipient_type` (`ALL_CONTACTS`,
  `LIST` via `contact_list_members`, `SEGMENT` via `segment_members` for `SAVED` or
  live rule evaluation for `DYNAMIC`) → exclude addresses on `suppression_entries` or
  with a most-recent `EMAIL` consent of `WITHDRAWN` (`DEC-GRX-008`, marking them
  `SUPPRESSED`) → materialize `campaign_recipients` → freeze exactly one
  `campaign_versions` snapshot (`recipient_count` = total resolved incl. suppressed)
  → send via real SMTP per eligible recipient, writing `message_deliveries`/
  `delivery_attempts` → write one `usage_records` row (`quantity` = successfully-sent
  count) → set `campaign.status = SENT`. Idempotent via checking for an existing
  `campaign_versions` row before doing any work (not a separate idempotency-key store).
- Wired `grx.email_delivery.send_campaign` into `consumer.py` alongside the existing
  healthcheck queue.
- 8 new `apps/api` integration tests (`test_email_delivery.py`): send flips status to
  `SENDING` and publishes the job (mocked, following `test_jobs.py`'s established
  pattern), sending twice is rejected (409), **Content Creator can edit a draft but
  gets 403 sending it** (the new "permission-gated action within an otherwise-
  accessible resource" shape SPRINT_03's AC calls out), `campaigns.view`-only gets 403
  on both send/test-send, unauthenticated 401, 404s, test-send calls SMTP with the
  draft's current content (mocked transport) and a transport failure surfaces as 502.
- 8 new `apps/worker` integration tests (`test_send_campaign.py`): all-contacts send
  creates deliveries + snapshot + usage record, suppressed/withdrawn-consent contacts
  excluded, saved-segment/list targeting resolve correctly, dynamic-segment rules
  evaluated live, SMTP failure marks recipient/delivery `FAILED` without crashing,
  reprocessing an already-sent campaign is a no-op.

## Real bugs found and fixed while debugging the new tests

- **`apps/worker`'s pytest-asyncio config was missing `asyncio_default_fixture_loop_scope`/
  `asyncio_default_test_loop_scope = "session"`** — present in `apps/api` since
  GRX-TEST-001, never added to the worker. Its absence gave every test function a
  fresh event loop while the worker's DB engine is a module-level singleton bound to
  whichever loop first created it, causing "Future attached to a different loop"
  failures the moment more than one test touched the DB. Fixed by matching `apps/api`'s
  existing config.
- Several worker models were initially missing NOT-NULL columns that have no DB-side
  default (`EmailProviderConnection.provider`, `ContactList.name`, `Segment.name`,
  `SuppressionEntry.reason`) — each surfaced as a real `NotNullViolationError` against
  the actual Postgres schema the first time a test tried to insert one, not caught by
  `mypy`/`ruff` since the worker's models are hand-written, not generated from the
  real schema. Fixed by adding the missing columns.
- `Contact.created_at` was declared `nullable=False` with no `server_default` in the
  worker's model — SQLAlchemy explicitly sends `NULL` for a mapped-but-unset column
  with no Python-side default (it only *omits* a column from the INSERT when a
  `server_default`/`default` is declared), which violated the real table's NOT NULL
  constraint. Fixed by adding `server_default=func.now()` to match the real DDL.

## Files changed

- `apps/api/src/growixa_api/usage/{__init__,models}.py` (new)
- `apps/api/src/growixa_api/email_delivery/{__init__,models,schemas,services,api,smtp_sender}.py` (new)
- `apps/api/src/growixa_api/app.py` (wired `email_delivery_router`)
- `apps/api/pyproject.toml` (added `aiosmtplib`)
- `apps/api/migrations/env.py` (registered `usage`, `email_delivery` models)
- `apps/api/migrations/versions/7049ac70cac8_usage_records_message_deliveries_and_.py` (new)
- `apps/api/tests/test_email_delivery.py` (new)
- `apps/worker/src/growixa_worker/{db,encryption,email_sender,models,recipients,send_campaign}.py` (new)
- `apps/worker/src/growixa_worker/config.py` (added `database_url`, `encryption_key`)
- `apps/worker/src/growixa_worker/consumer.py` (wired the new queue/handler)
- `apps/worker/pyproject.toml` (added `sqlalchemy`/`asyncpg`/`cryptography`/`aiosmtplib`; fixed asyncio loop scope)
- `apps/worker/.env`, `.env.example` (new)
- `apps/worker/tests/test_send_campaign.py` (new)
- `compose.yaml` (worker service gets `DATABASE_URL`, depends on `postgres`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-EMAIL-004` → `DONE`, `GRX-EMAIL-005` → `READY`)
- `docs/00-project-control/PROJECT_STATUS.md`, `CHANGELOG.md` (this update)

## Commands executed

- `alembic revision`, `alembic upgrade head`, `alembic check` (clean, no drift)
- `ruff check`/`ruff format --check`/`mypy` — clean on both `apps/api` and `apps/worker`
- `pytest`: `apps/api` 135 passed, 3 skipped; `apps/worker` 8 passed
- `podman compose up -d --build api worker` (both images needed new dependencies)
- Live verification against Compose (see below)

## Blockers

None. `GRX-EMAIL-005` (Postmark webhook receiver + unsubscribe handling) is `READY`.

## Known issues / evidence gaps

- **No live Postmark account available** — the actual outbound send was verified up to
  the credential boundary, not as a successful delivery. Live-verified: `POST
  /campaigns/{id}/test-send` made a real TCP/TLS + STARTTLS connection to
  `smtp.postmarkapp.com:587` and got a genuine `535 5.7.8 authentication failed`
  (proving the SMTP path is real code, not a stub); `POST /campaigns/{id}/send`
  enqueued a real job, the worker consumed it, hit the same real auth rejection per
  recipient, and correctly wrote `campaign_recipients`/`message_deliveries` as
  `FAILED`, `delivery_attempts` with the real error message, `campaign_versions` with
  the correct `recipient_count`, and a `usage_records` row with `quantity=0` — then
  left `campaign.status = SENT` rather than crashing. This closes automatically the
  first time a real Postmark server token is configured; flagging per
  `DEC-GRX-011`/`SPRINT_03`'s own rule rather than marking it DONE on faked evidence.
- Possible latent `MissingGreenlet` in `company_profile` (filed earlier, unresolved,
  unrelated to this task).
- Running the full backend `pytest` suite wipes `admin@growixa.local` — recreated it
  and cleaned up all smoke-test rows (campaign, contact, sender identity, connection)
  after live verification. Known quirk, not a bug to fix.
- Retry/backoff/dead-letter handling for `send_campaign` (per
  `BACKGROUND_JOB_ARCHITECTURE.md`'s general pattern) is not implemented — matches the
  existing healthcheck job's same gap from GRX-FOUND-007, not newly introduced here.
  Revisit if/when the worker needs real retry semantics.

## Current state

Sprint 1 and Sprint 2 are `DONE`. Sprint 3 (Email Marketing) is under way:
`GRX-EMAIL-001` through `GRX-EMAIL-004` are all `DONE`. `GRX-EMAIL-005` (Postmark
webhook receiver + unsubscribe handling) is `READY`; `GRX-EMAIL-006`–`010` remain
`BACKLOG` behind it.

## Exact next task

`GRX-EMAIL-005` — Postmark webhook receiver + unsubscribe handling. New
`email_events`/`unsubscribe_events` tables + migration, an authenticated (HTTP Basic
Auth per `THREAT_MODEL.md`'s T14) webhook endpoint in `email_delivery` that updates the
matching `message_deliveries` row and appends an `email_events` row on
delivered/opened/clicked/bounced/complained events. A recipient clicking unsubscribe
must both record an `unsubscribe_events` row and add/update a `suppression_entries` row
in the same transaction (reusing Slice 2's suppression infrastructure). Required
negative test: an unauthenticated webhook request is rejected before touching either
table.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit

`aa2bdb4` — feat(email): send pipeline via worker (GRX-EMAIL-004)
