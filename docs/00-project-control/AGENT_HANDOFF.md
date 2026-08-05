# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-08-05
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

## Work completed (backend track — GRX-EMAIL-005)

- **Real gap found and fixed**: `THREAT_MODEL.md`'s `T14` specified webhook Basic Auth
  credentials "stored alongside the provider connection, encrypted at rest", but
  `email_provider_connections` never got those columns when Sprint 3 was planned.
  Migration `f5ecaa79863b` adds `webhook_username`/`webhook_password_encrypted`
  (nullable, fails closed if unset), auto-generated via `secrets.token_urlsafe` at
  connection-creation time and Fernet-encrypted like the SMTP password; the plaintext
  webhook password is returned exactly once, in the create-connection response, never
  persisted or retrievable again. Same migration adds `email_events` (insert-only,
  `event_type` CHECK'd) and `unsubscribe_events` per `DATABASE_SCHEMA.md`.
- New public `email_delivery.public_router`: `POST /webhooks/postmark` (HTTP Basic
  Auth checked against the active connection's own credentials via
  `secrets.compare_digest`) maps Postmark's `RecordType` to `event_type`, matches the
  delivery by `provider_message_id`, no-ops silently on an unmatched `MessageID`
  (Postmark expects 200 either way), and auto-suppresses on `BOUNCED`/`COMPLAINED` —
  wiring up `suppression_entries.reason` values that have existed since
  `GRX-CONTACT-005` but were never written until now.
- `GET /unsubscribe/{campaign_recipient_id}` is fully public and unauthenticated by
  design, identified only by the unguessable UUID (same shape as the invitation-accept
  token); records an `unsubscribe_events` row and suppresses the address with no
  `actor_id` (new `_upsert_suppression` helper bypasses `suppress_email`'s
  actor-requiring wrapper for this and the webhook's system-triggered case).
- The worker now appends a per-recipient unsubscribe footer link
  (`{api_public_url}/unsubscribe/{campaign_recipient_id}`) to every real send's
  `body_html`/`body_text` — plain append, no merge-tag infrastructure yet; new
  `api_public_url` worker setting (Compose default `http://localhost:${API_PORT}`).
- 8 new `apps/api` integration tests (`test_email_delivery.py`): webhook rejects
  no-credentials and wrong-credentials requests with zero `email_events` written (key
  negative test per `SPRINT_03`'s AC), a valid `Delivery` event updates
  `message_deliveries` and writes the event, a `Bounce` event auto-suppresses, an
  unmatched `MessageID` is a 200 no-op, a valid unsubscribe creates the event +
  suppression, an unknown `campaign_recipient_id` 404s.
- 1 new `apps/worker` integration test (`test_send_campaign.py`): the unsubscribe URL
  is present in both `body_html` and `body_text` passed to the mocked `send_email`.

## Real bugs found and fixed while debugging the new tests

None this time — `ruff`/`mypy`/`pytest` all passed on the first or near-first attempt
at every verification checkpoint, unlike `GRX-EMAIL-004`'s several real bugs.

## Files changed

- `apps/api/src/growixa_api/email_delivery/{models,schemas,services,api}.py` (extended)
- `apps/api/src/growixa_api/email_delivery/repositories.py` (new)
- `apps/api/src/growixa_api/integrations/{models,schemas,services,api}.py` (extended:
  webhook credential generation/storage)
- `apps/api/src/growixa_api/app.py` (wired `email_delivery_public_router`)
- `apps/api/migrations/versions/f5ecaa79863b_webhook_credentials_email_events_.py` (new)
- `apps/api/tests/test_email_delivery.py`, `test_protected_routes_audit.py` (extended)
- `apps/worker/src/growixa_worker/config.py` (added `api_public_url`)
- `apps/worker/src/growixa_worker/send_campaign.py` (extended: unsubscribe footer)
- `apps/worker/tests/test_send_campaign.py` (extended)
- `apps/worker/.env.example` (documented `API_PUBLIC_URL`)
- `compose.yaml` (worker service gets `API_PUBLIC_URL`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-EMAIL-005` → `DONE`,
  `GRX-EMAIL-006` → `READY`)
- `docs/00-project-control/PROJECT_STATUS.md`, `CHANGELOG.md` (this update)

## Commands executed

- `alembic upgrade head`, `alembic check` (clean, no drift)
- `ruff check`/`ruff format --check`/`mypy` — clean on both `apps/api` and `apps/worker`
- `pytest`: `apps/api` 142 passed, 3 skipped; `apps/worker` 9 passed
- `podman compose restart api worker` (no new dependency, code + migration only)
- Live verification against Compose (see below)

## Blockers

None. `GRX-EMAIL-006` (campaign report/analytics endpoint) is `READY`.

## Known issues / evidence gaps

- **No live Postmark account available**, same class of gap as `GRX-EMAIL-004`'s — the
  exact webhook JSON payload shape per `RecordType` is unverified.
  `PostmarkWebhookPayload` is deliberately permissive (`extra="allow"`, only
  `RecordType`/`MessageID` required), and the full raw payload is preserved in
  `email_events.metadata` for future reconciliation once a real payload is captured.
- Live-verified against Compose: created a connection and captured its one-time
  webhook credentials via curl; confirmed no-auth/wrong-auth both 401 before touching
  `email_events`; sent a real campaign (same `535` SMTP auth-rejection boundary as
  `GRX-EMAIL-004`) and manually set `provider_message_id` on the resulting
  `message_deliveries` row to simulate a Postmark-assigned ID, since the real send
  never receives one; a `Delivery` webhook flipped the row to `DELIVERED` and wrote
  the event; a `Bounce` webhook auto-suppressed the recipient; clicking the real
  `/unsubscribe/{id}` link returned the HTML confirmation and updated the suppression
  reason to `UNSUBSCRIBED`; an unknown unsubscribe id 404'd. Cleaned up all smoke-test
  rows afterward.
- Running the full backend `pytest` suite wipes `admin@growixa.local` again — recreated
  it before live verification. Known quirk, not a bug to fix.
- **Branch/doc coordination note**: this session's git branch was already
  `feature/FRONTEND/GRX-WEB-002` (a concurrent frontend session's branch) when this
  backend work started, so all `GRX-EMAIL-*` commits this session — including this
  one — landed there rather than on a dedicated backend branch. This file
  (`AGENT_HANDOFF.md`) is also now shared by both tracks: the frontend session's
  `GRX-WEB-002` handoff sits above this section rather than being replaced by it. Not
  fixed unilaterally (would mean a branch move/rebase); flagging for the user to
  decide whether to split branches going forward.
- Retry/backoff/dead-letter handling for `send_campaign` remains unimplemented
  (unchanged from `GRX-EMAIL-004`'s note, not newly introduced here).

## Current state

Sprint 1 and Sprint 2 are `DONE`. Sprint 3 (Email Marketing) is under way:
`GRX-EMAIL-001` through `GRX-EMAIL-005` are all `DONE`. `GRX-EMAIL-006` (campaign
report/analytics endpoint) is `READY`; `GRX-EMAIL-007`–`010` remain `BACKLOG` behind it.

## Exact next task

`GRX-EMAIL-006` — Campaign report/analytics endpoint. Aggregate
sent/delivered/opened/clicked/bounced/complained counts per campaign from
`message_deliveries`/`email_events`, exposed via an extended `campaigns` route. See
`MASTER_TASK_TRACKER.md`'s row for the exact acceptance criteria and required tests.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit

`9dbe9ee` — feat(email): Postmark webhook receiver + unsubscribe handling (GRX-EMAIL-005)
