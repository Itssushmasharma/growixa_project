# Project Status

- Document ID: DOC-PROJECT-STATUS
- Status: ACTIVE
- Version: 1.53
- Last updated: 2026-08-17
- Owner: Coding agent (on behalf of product owner)
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [WORKTREE_TRACKER](WORKTREE_TRACKER.md), [DECISIONS](DECISIONS.md), [DEVELOPMENT_READINESS](DEVELOPMENT_READINESS.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Product identity (confirmed)

- Product name: **Growixa**
- Product type: **AI-powered growth and marketing automation platform.** It begins with
  email and social media automation, then expands into SEO, AEO, GEO, website intelligence,
  content optimization, and integrated growth workflows.
- Tenancy model: the MVP (Slices 1–4) was built **single-tenant**, one company
  installation, multiple internal users, per the now-superseded `DEC-GRX-002`. As of
  [DEC-GRX-017](DECISIONS.md) (2026-08-07), Growixa is opening for **self-service
  customer registration**, with each customer's data isolated by an internal
  `account_id` key (no visible organizations/workspaces) and a separate IITDEVELOPER
  Platform Admin control plane above all customer accounts — see
  [Sprint 5](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md).
  Slices 1–4's existing data model is correct for what it was built for; Sprint 5 Phase A
  (`GRX-SAAS-001`) retrofits `account_id` isolation across it before any new
  account-facing feature is built.
- MVP focus (this release only): contact management, email marketing, one social platform,
  AI content assistant with mandatory human approval, campaign scheduling, basic analytics
- **Deferred to future releases (V1.5–V3), not cancelled:** SEO automation, AEO, GEO,
  website crawler, website audits, metadata recommendations, WordPress integration, GitHub
  integration, Search Console integration, content optimization agents, website improvement
  workflows, full multi-agent growth system. See
  [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md).
- **No longer deferred:** full multi-tenancy, customer-facing SaaS signup, and tenant
  billing — formerly deferred indefinitely under `DEC-GRX-013`, now superseded by
  `DEC-GRX-017`. Staged as Sprint 5. White-label platform remains deferred indefinitely
  (no trigger condition named).

The original SEO/AEO/GEO discovery document (`docs/archive/source-prd-seo-aeo-geo-website-intelligence/`)
is **not** a different or cancelled product — it is valid source material for those future
releases. See [DEC-GRX-001](DECISIONS.md) for the full scope-correction decision record.

## Current phase

**Phase 0 (repository & documentation foundation) and Phase 1 (product definition) — done.
Phase 4 (architecture), Phase 5 (data), and Phase 6 (security, Sprint-1-relevant subset) —
done for Slice 1 scope.**

**Development Readiness Gate for Slice 1 (Sprint 1: Foundation): PASS — every mandatory
item is a standalone document, no distributed-only gaps remain.** See
[DEVELOPMENT_READINESS.md](DEVELOPMENT_READINESS.md). **Sprint 1 implementation has begun.**
`GRX-FOUND-001` (repository and development tooling), `GRX-FOUND-002` (Docker Compose local
environment), `GRX-FOUND-003` (FastAPI application foundation), `GRX-FOUND-004` (Next.js
application foundation), `GRX-FOUND-005` (PostgreSQL connectivity + Alembic foundation),
`GRX-AUTH-001` (users/roles/permissions schema + seed), `GRX-RBAC-001` (centralized
permission-check dependency), `GRX-AUDIT-001` (audit log module), `GRX-TEST-001` (backend
test foundation), `GRX-COMPANY-001` (company profile + brand settings), `GRX-AUTH-002`
(password hashing + login/logout), `GRX-AUTH-003` (refresh-token rotation + session
revocation), `GRX-USER-001` (internal user invitation + acceptance), `GRX-AUTH-005`
(password reset flow), `GRX-FOUND-006` (Redis connectivity), `GRX-AUTH-004` (login rate
limiting), `GRX-TEST-002` (frontend test foundation), `GRX-FOUND-008` (dashboard
shell), `GRX-COMPANY-002` (company settings screen), `GRX-USER-002` (user management
screens), `GRX-FOUND-007` (RabbitMQ connectivity + worker skeleton), `GRX-DEVOPS-001`
(CI pipeline — pushed by the user and confirmed green on GitHub Actions), and `GRX-DOC-003`
(Sprint 1 documentation + handoff update, incl. the new
[FEATURE_STATUS_MATRIX.md](FEATURE_STATUS_MATRIX.md)), and `GRX-AUDIT-002` (audit log
viewing — `GET /audit` endpoint + frontend page) are all `DONE`. **Sprint 1 is now fully
`DONE` with no open gaps** — `GRX-DOC-003`'s feature audit found that `GRX-FEAT-027`
(Audit Logs) only satisfied the *recording* half of Sprint 1's acceptance criteria (no
way to view events), which `GRX-AUDIT-002` then closed the same session. See
[FEATURE_STATUS_MATRIX.md](FEATURE_STATUS_MATRIX.md) for the full per-feature breakdown. Per
[AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md), only one is worked
on at a time. See [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for session-by-session
detail.

**Development Readiness Gate for Slice 2 (Sprint 2: Contacts): PASS.** See
[DEVELOPMENT_READINESS.md](DEVELOPMENT_READINESS.md) and
[SPRINT_02_CONTACTS.md](../14-sprints/SPRINT_02_CONTACTS.md). Data model
([DATA_MODEL.md](../05-data/DATA_MODEL.md), [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md),
[ERD.md](../05-data/ERD.md)) and RBAC ([RBAC.md](../08-security/RBAC.md)) extended for
`contacts`, `tags`, `contact_lists`, `segments`, `contact_imports`,
`consent_records`/`suppression_entries`. Nine tasks added to
[MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) (`GRX-CONTACT-001`–`009`).
**All nine Sprint 2 tasks are now `DONE`: `GRX-CONTACT-001` (contacts schema + CRUD),
`GRX-CONTACT-002` (tags & lists), `GRX-CONTACT-003` (segments), `GRX-CONTACT-004`
(CSV contact import), `GRX-CONTACT-005` (consent & suppression), `GRX-CONTACT-006`
(contacts frontend), `GRX-CONTACT-007` (tags/lists/segments frontend), `GRX-CONTACT-008`
(CSV import frontend), and `GRX-CONTACT-009` (consent/suppression frontend). Sprint 2
(Contacts) is complete.**

**Development Readiness Gate for Slice 3 (Sprint 3: First Email Campaign): PASS.** See
[DEVELOPMENT_READINESS.md](DEVELOPMENT_READINESS.md) and
[SPRINT_03_EMAIL_CAMPAIGN.md](../14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md). This gate needed
one genuinely new prerequisite Slice 1/2 didn't: [OQ-002](OPEN_QUESTIONS.md) (email
provider) had to be resolved before planning could even start — now closed via
[DEC-GRX-015](DECISIONS.md): **Postmark, integrated via its SMTP relay endpoint** (the
user's own preference for an SMTP-based integration, reconciled with keeping Postmark's
bounce/open/click webhook tracking rather than losing it to a generic personal-mailbox
SMTP server). Data model, RBAC, and a new threat-model addendum (T13–T19, the first since
Sprint 1's) extended for `email_provider_connections`, `sender_identities`,
`email_templates`/`email_template_versions`, `campaigns`/`campaign_versions`,
`campaign_recipients`, `message_deliveries`/`delivery_attempts`, `email_events`,
`unsubscribe_events`. Ten tasks added to
[MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) (`GRX-EMAIL-001`–`010`); the first,
`GRX-EMAIL-001` (provider connection + sender identity), is `READY`.

**Ad hoc addition to Sprint 3:** `GRX-EMAIL-011` (Custom SMTP as a second email
provider) is `DONE` — `email_provider_connections` now allows one active connection
*per provider* (DB-enforced via a partial unique index), so Postmark and Custom SMTP
can both be connected at once, logged as [DEC-GRX-016](DECISIONS.md). Live-testing it
against the user's own real SMTP server found and fixed two real transport bugs: the
SMTP sender only supported STARTTLS, so port-465 (implicit TLS) servers hung
indefinitely; and TLS/certificate errors weren't caught by the sender's exception
wrapper, surfacing as an unhandled 500 instead of a clean error. The user's own server
has an expired certificate — an external blocker on their end, unrelated to this fix.

`GRX-EMAIL-012` (a "Test connection" button, requested directly by the user right after
`GRX-EMAIL-011`'s live testing) is also `DONE` — validates SMTP credentials via a real
connect+login before a connection is saved. Building it required moving
`smtp_sender.py` from `email_delivery` into `integrations` as `smtp_transport.py`, since
`MODULE_BOUNDARIES.md` only allows `email_delivery` to depend on `integrations`, not the
reverse.

**Ad hoc UX addition (not tied to a sprint plan):** `GRX-FOUND-009` (collapsible/
responsive sidebar navigation — hamburger toggle for desktop collapse + mobile overlay
drawer, plus an independent per-section accordion for each nav heading), requested
directly by the user mid-session, is `DONE`.

**Web Architecture & Brand Website Planning Pass:** `GRX-WEB-001` (Next.js App Router Groups refactoring: `(marketing)`, `(auth)`, `(dashboard)`, `(admin)`) added to [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) as `READY`. `GRX-WEB-002` (3D Brand & Landing Website: Linear/Vercel/Stripe aesthetic) and `GRX-ADMIN-001` (Admin Portal / Control Plane) added as `BACKLOG`.

**Development Readiness Gate for Slice 5 (Sprint 6: Social Publishing): PASS.** See
[DEVELOPMENT_READINESS.md](DEVELOPMENT_READINESS.md) and
[SPRINT_06_SOCIAL_PUBLISHING.md](../14-sprints/SPRINT_06_SOCIAL_PUBLISHING.md) — the sixth
sprint *file*, implementing the fifth product *slice* (Sprint 5's filename was already
consumed by the unplanned multi-tenancy retrofit). Resolved
[OQ-003](OPEN_QUESTIONS.md) (Instagram Business, [DEC-GRX-023](DECISIONS.md)) and
[OQ-005](OPEN_QUESTIONS.md) (Supabase Storage, [DEC-GRX-024](DECISIONS.md)) per direct
product-owner confirmation, plus [DEC-GRX-025](DECISIONS.md) (OAuth tokens reuse the
existing Fernet encryption, no new KMS). Scoped, at the user's explicit direction, to the
customer-facing feature only — platform-admin oversight tooling for social is deferred
until the product itself is finished. **All eleven Slice 5 tasks
(`GRX-SOCIAL-001`–`011`) are `DONE`**: readiness-gate docs; `social_connections` schema +
`social.manage`/`social.publish`/`social.view` RBAC seed; Instagram OAuth connect flow;
`social_posts`/`social_post_media` schema; post CRUD + Supabase Storage media upload
(single JPEG only, by explicit scope decision); publish-now; schedule/cancel/retry
dispatch pipeline (mirroring the Slice 4 campaigns pipeline's queue topology almost
exactly); the worker-side Instagram publish handler with permanent-vs-transient error
classification; a full backend+worker test suite (which found and fixed two real schema
bugs — a missing `provider` column on the worker's lightweight connection model, and a
missing DB-level default on `social_posts.idempotency_key`); the frontend (Instagram
connect card, post composer, social-only content calendar); and env/settings docs
(which found and fixed a real gap — `compose.yaml` wasn't passing the new Instagram/
Supabase env vars through to the `api`/`worker` containers at all). Two evidence gaps
remain, per [DEC-GRX-011](DECISIONS.md)'s no-DONE-on-mocked-provider-evidence rule as
applied at the level of *individual external calls*, not whole tasks: no live OAuth
round-trip against a real Meta Developer App, and no live image upload/publish against a
real Supabase bucket / Instagram account, since the user has not yet added
`INSTAGRAM_APP_ID`/`INSTAGRAM_APP_SECRET`/`SUPABASE_STORAGE_URL`/
`SUPABASE_STORAGE_SERVICE_KEY` to `.env`. Everything reachable without those — full
CRUD, validation, scheduling, cancellation, RBAC gating, cross-tenant isolation — was
live-verified via `curl` against the real running Compose stack.

**Development Readiness Gate for Slice 6 (Sprint 7: AI Assistant): PASS.** See
[DEVELOPMENT_READINESS.md](DEVELOPMENT_READINESS.md) and
[SPRINT_07_AI_ASSISTANT.md](../14-sprints/SPRINT_07_AI_ASSISTANT.md) — the last unbuilt
slice of the original 6-slice MVP roadmap. User's explicit scoping: multi-provider
(OpenAI/Azure OpenAI/Anthropic/Ollama), a platform-admin-configured default plus a
per-account bring-your-own override, and code structured for a future multi-agent slice
without adopting LangGraph yet ([DEC-GRX-012](DECISIONS.md) still holds — MVP AI stays
assistive single-shot). Resolved [OQ-004](OPEN_QUESTIONS.md) via
[DEC-GRX-026](DECISIONS.md) (multi-provider adapter + two-level config) and
[DEC-GRX-027](DECISIONS.md) (SSRF-safe `base_url` validation, applied uniformly to
platform-admin and customer input, re-checked at call time to defeat DNS rebinding).
**All eleven Slice 6 tasks (`GRX-AI-001`–`011`) are `DONE`**: readiness-gate docs;
`ai_generations`/`ai_provider_connections`/`platform_ai_provider_config` schema (3
tables, not the `DATA_MODEL.md` placeholder's speculative 4 — prompts are code-defined,
not a customer-editable DB table) + `ai.manage`/`ai.view`/`platform.ai.manage` RBAC seed;
four `httpx`-only provider adapters (OpenAI, Azure OpenAI, Anthropic, Ollama); account
BYO connections + platform-admin default config, both SSRF-validated at save and call
time; six capability modules (`ai/capabilities/`) each a `run(input, provider, model)`
function with prompt-building kept separate from the provider call, the concrete answer
to "structured for future multi-agent"; the generation endpoint (writing an
`ai_generations` row plus, on success, a `usage_records` row — fixing a real
pre-existing gap, that table had a reader since Sprint 1 but zero writers) and history
endpoint; a Test Connection feature (mirrors `GRX-EMAIL-012`'s SMTP precedent) added
mid-slice at the user's request while live-testing; a full backend test suite (283
passed, up from 244 — found and fixed a real empty-content-after-success bug in all four
provider adapters, discovered live-testing a reasoning model that exhausted its token
budget mid-chain-of-thought); the frontend (a reusable `AIGenerateButton` wired into the
campaign/post composers, a generation-history page, a platform-admin AI-config page, and
an account-level BYO provider card — 191 passed, up from 172); and env/settings docs
(this is the only integration in the codebase configured entirely via a DB-backed admin
UI with zero new env vars, by design). Live-verified end-to-end against a real Krutrim
(OpenAI-compatible third-party) API key the user provided directly — real successful
generations, real cost/token tracking, real `usage_records` writes — routed through the
platform-admin default config. Anthropic was reachability/error-path-verified only (no
real Anthropic key available), logged honestly per [DEC-GRX-011](DECISIONS.md) rather
than blanket-marked `DONE` on partial evidence. One narrower gap remains: no interactive
logged-in browser click-through of the provider-configuration forms' save/test-connection
flows (same action-classifier block on typing a login password encountered in Slice 5),
and a deliberate choice not to call the config-save endpoints via `curl` with fabricated
credentials against the live environment, since that would have overwritten the user's
real working Krutrim default with a keyless row.

**Development Readiness Gate for Slice 7 (Sprint 8: Billing): PASS.** See
[DEVELOPMENT_READINESS.md](DEVELOPMENT_READINESS.md) and
[SPRINT_08_BILLING.md](../14-sprints/SPRINT_08_BILLING.md) — the first slice that moves
real money. Resolved via [DEC-GRX-029](DECISIONS.md) (Razorpay, not Stripe, dual-currency)
and [DEC-GRX-030](DECISIONS.md) (Subscriptions API as the billing primitive, non-expiring
top-up credits, no per-batch FIFO). **All ten `GRX-BILL-*` tasks plus the three umbrella/
platform-admin/coupon rows (`GRX-SAAS-004`/`006`/`012`) are `DONE`**: readiness-gate docs;
`subscription_plans`/`account_subscriptions`/`account_credit_balances`/
`account_credit_purchases`/`coupon_codes`/`coupon_redemptions` schema (every account gets
a `Free`-tier subscription row automatically at registration) + `billing.manage`/
`billing.view`/`platform.billing.manage` RBAC seed; a signature-verified, idempotent
Razorpay webhook receiver (`POST /billing/razorpay`); real Razorpay Checkout for
subscribe/upgrade and one-time top-up Orders; an atomic (`SELECT ... FOR UPDATE`-locked)
quota evaluator for the two period-resetting metered dimensions (email sends, AI runs)
that falls back to non-expiring credit balances before blocking with `402` — and never
meters an account's own bring-your-own AI key; an in-process cancellation-downgrade
ticker (same pattern as the campaigns/social schedulers, confirmed live via code reading
to correct the architecture doc's draft claim that it ran worker-side); a platform-admin
override panel (manual plan assignment incl. Enterprise activation, credit grants, status
override, plan/credit-pack catalog CRUD) that bypasses Razorpay entirely; a coupon/
discount engine (percentage/fixed-amount coupons scoped to top-ups only — verified
against Razorpay's own docs that Checkout.js has no subscription-discount parameter —
plus free-credit-grant coupons redeemed directly); the customer billing page (plan/usage/
credits, upgrade, top-up, coupon redemption); a dedicated `test_billing_*.py` suite (23
tests: webhook signature/replay, quota race-condition, BYO-vs-platform metering split,
coupon validation) that found and fixed a real bug — coupon `applicable_plan_slugs`
eligibility was silently dead code, never actually enforced by either call site; and
env/settings docs (found and fixed a second real gap — `RAZORPAY_*` env vars were never
in `.env.example` at all, and `BILLING_DOWNGRADE_POLL_INTERVAL_SECONDS` was never wired
into `compose.yaml`'s passthrough despite having a real default in `config.py`).
Live-verified end-to-end against real Razorpay Test Mode throughout: real `Plan`/
`Subscription`/`Order` objects created via genuine API calls, a real Checkout.js modal
opened in a browser with the correct (and correctly coupon-discounted) amount, real
coupon redemption via both `curl` and the live UI with the credit balance visibly
updating. USD payments remain blocked pending Razorpay's own account-level international-
payments approval (an external, non-code blocker, not a bug) — INR-only for now, exactly
as `BILLING_SYSTEM_ARCHITECTURE.md §8` already documented. **All seven MVP-scope product
slices plus the Sprint 5 multi-tenancy retrofit are now complete.**

## Documents created so far

| Document | Status |
|---|---|
| `README.md` (root) | DONE |
| `docs/README.md` | DONE |
| `docs/00-project-control/PROJECT_STATUS.md` | DONE (this file) |
| `docs/00-project-control/ASSUMPTIONS.md` | DONE |
| `docs/00-project-control/OPEN_QUESTIONS.md` | DONE (OQ-001 resolved) |
| `docs/00-project-control/DECISIONS.md` | DONE (14 decisions incl. DEC-GRX-001 scope correction, DEC-GRX-014 auth) |
| `docs/00-project-control/DEFINITION_OF_DONE.md` | DONE |
| `docs/00-project-control/DEVELOPMENT_READINESS.md` | DONE (Slice 1 gate: PASS) |
| `docs/00-project-control/MASTER_TASK_TRACKER.md` | DONE (Sprint 1 tasks seeded) |
| `docs/01-product/PRODUCT_VISION.md` | DONE |
| `docs/01-product/PRD.md` | DONE (41-section structure, MVP-focused with links out to future scope) |
| `docs/01-product/MVP_SCOPE.md` | DONE |
| `docs/01-product/ROADMAP.md` | DONE (MVP → 1.1 → 1.2 → V1.5 → V2 → V3) |
| `docs/01-product/FUTURE_SCOPE_SEO_AEO_GEO.md` | DONE (old-PRD → new-ID → release mapping) |
| `docs/02-features/FEATURE_CATALOG.md` | DONE (stub: MVP feature list + deferred feature list) |
| `docs/02-features/FEATURE_SMS_MARKETING.md` | DONE (`GRX-FEAT-SMS-001` Twilio & SMS spec) |
| `docs/04-architecture/SYSTEM_ARCHITECTURE.md`, `MODULE_BOUNDARIES.md`, `BACKGROUND_JOB_ARCHITECTURE.md` | DONE |
| `docs/05-data/DATA_MODEL.md`, `ERD.md`, `DATABASE_SCHEMA.md` | DONE (Sprint 1 + Slice 2 + Slice 3 entities in full detail) |
| `docs/08-security/SECURITY_ARCHITECTURE.md`, `AUTHENTICATION.md`, `RBAC.md`, `THREAT_MODEL.md` | DONE (RBAC + threat model extended through Slice 3) |
| `docs/12-development/AGENT_EXECUTION_RULES.md` | DONE |
| `docs/14-sprints/SPRINT_01_FOUNDATION.md` | DONE (implementation complete) |
| `docs/14-sprints/SPRINT_02_CONTACTS.md` | DONE (implementation complete) |
| `docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md` | DONE (planning — implementation not started) |
| `docs/diagrams/container-architecture.mmd`, `er-diagram.mmd` | DONE |
| `docs/archive/source-prd-seo-aeo-geo-website-intelligence/` | DONE (relabeled from "legacy/superseded" to "future source material") |
| `docs/10-testing/TEST_STRATEGY.md` | DONE |
| `docs/11-devops/LOCAL_DEVELOPMENT.md` | DONE |
| `docs/00-project-control/CHANGELOG.md` | DONE |
| `docs/00-project-control/AGENT_HANDOFF.md` | DONE (updated at the end of every work session) |
| `apps/api/` tooling (pyproject.toml, ruff/mypy config, .env.example) | DONE (`GRX-FOUND-001`) |
| `apps/web/` tooling (package.json, eslint/prettier/tsconfig, .env.example) | DONE (`GRX-FOUND-001`) |
| `.pre-commit-config.yaml` | DONE (`GRX-FOUND-001`) |
| `compose.yaml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, root `.env.example` | DONE (`GRX-FOUND-002`) |
| `apps/api/src/growixa_api/{app,health,main}.py`, `apps/api/tests/test_health.py` | DONE (`GRX-FOUND-003`) |
| `apps/api/src/growixa_api/db.py`, `apps/api/alembic.ini`, `apps/api/migrations/`, `apps/api/tests/test_migrations.py` | DONE (`GRX-FOUND-005`) |
| `apps/web/src/app/{page,not-found}.tsx`, `apps/web/src/lib/{env,api-client}.ts` | DONE (`GRX-FOUND-004`) |
| `apps/api/src/growixa_api/{roles,permissions,users}/models.py`, migration `d330e8b64b48`, `apps/api/tests/test_auth_schema_seed.py` | DONE (`GRX-AUTH-001`) |
| `apps/api/src/growixa_api/permissions/{repositories,dependencies}.py`, `apps/api/tests/{test_require_permission,test_protected_routes_audit}.py` | DONE (`GRX-RBAC-001`) |
| `apps/api/src/growixa_api/audit/{models,repositories,services}.py`, migration `6575d09949f9`, `apps/api/tests/{test_audit_log,test_audit_insert_only}.py` | DONE (`GRX-AUDIT-001`) |
| `apps/api/tests/conftest.py` (`user_factory`), pytest-cov + `integration` marker in `apps/api/pyproject.toml` | DONE (`GRX-TEST-001`) |
| `apps/api/src/growixa_api/{company,brand}/{models,schemas,repositories,services,api}.py`, migration `1abf62872712`, `apps/api/tests/test_company_settings.py` | DONE (`GRX-COMPANY-001`) |
| `apps/api/src/growixa_api/auth/{models,security,tokens,repositories,services,schemas,api}.py`, migration `ea25a5343142`, `apps/api/src/growixa_api/users/repositories.py`, `apps/api/tests/test_auth_login.py` | DONE (`GRX-AUTH-002`) |
| `apps/api/src/growixa_api/auth/{repositories,services,api}.py` (rotation/reuse/logout-all extensions), `apps/api/tests/test_auth_refresh.py` | DONE (`GRX-AUTH-003`) |
| `apps/api/src/growixa_api/users/{models,repositories,services,schemas,api}.py`, `apps/api/src/growixa_api/roles/repositories.py`, migration `f356da0136c3`, `apps/api/tests/test_users_invitations.py` | DONE (`GRX-USER-001`) |
| `apps/api/src/growixa_api/auth/{models,repositories,services,schemas,api}.py` (password reset extensions), migration `bb25de08ba84`, `apps/api/tests/test_auth_password_reset.py` | DONE (`GRX-AUTH-005`) |
| `apps/api/src/growixa_api/redis.py` (new), `apps/api/src/growixa_api/health.py` (pooled-client reuse), `apps/api/tests/test_redis.py` | DONE (`GRX-FOUND-006`) |
| `apps/api/src/growixa_api/auth/rate_limit.py` (new), `apps/api/src/growixa_api/auth/api.py` (login/password-reset-request extensions), `apps/api/tests/test_auth_rate_limit.py` | DONE (`GRX-AUTH-004`) |
| `apps/web/vitest.config.ts`, `apps/web/vitest.setup.ts`, `apps/web/playwright.config.ts`, `apps/web/src/app/page.test.tsx`, `apps/web/tests/e2e/smoke.spec.ts` | DONE (`GRX-TEST-002`) |
| `apps/web/src/app/{login,dashboard}/`, `apps/web/src/lib/auth.ts`, `apps/api/src/growixa_api/{app,config}.py` (CORS), `apps/api/src/growixa_api/auth/api.py` (`GET /auth/me`), `apps/web/tests/e2e/dashboard.spec.ts` | DONE (`GRX-FOUND-008`) |
| `.github/workflows/ci.yml` | IN_REVIEW (`GRX-DEVOPS-001` — built and locally verified, awaiting a live GitHub Actions run) |
| `apps/web/src/app/dashboard/company-settings/` | DONE (`GRX-COMPANY-002`) |
| `apps/web/src/app/dashboard/team/`, `apps/api/src/growixa_api/roles/{api,schemas}.py` (new), `apps/api/src/growixa_api/users/` (extended) | DONE (`GRX-USER-002`) |
| `apps/api/src/growixa_api/jobs/` (new), `apps/worker/` (new app) | DONE (`GRX-FOUND-007`) |
| `apps/web/src/app/dashboard/contacts/suppression/` (new), `contacts-page.tsx`/`types.ts` (consent extensions) | DONE (`GRX-CONTACT-009`) |
| `docs/00-project-control/FEATURE_STATUS_MATRIX.md` | DONE (`GRX-DOC-003`) |
| `apps/api/src/growixa_api/audit/{api,schemas}.py` (new), `apps/web/src/app/dashboard/audit/` (new) | DONE (`GRX-AUDIT-002`) |
| `apps/web/src/app/dashboard/{dashboard-shell,sidebar,layout}.tsx` (collapsible/responsive nav) | DONE (`GRX-FOUND-009`) |
| `docs/00-project-control/RISKS.md`, `BLOCKERS.md` | NOT_STARTED (not required by any `GRX-DOC-*` task yet) |
| `docs/03-ux-ui/DESIGN_REFERENCES.md` | DONE (reference material only — see its own scope caveat; not a Sprint 1 spec) |
| `docs/01-product/FUTURE_SCOPE_MULTI_BRAND.md` | DONE (idea capture only — multi-brand profiles + subscription tiers; contradicts DEC-GRX-002/013 as proposed, not scheduled into any release) |
| `docs/01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md` | DONE — **approved and scheduled** as of `DEC-GRX-017` (2026-08-07); no longer idea-capture-only. Self-service customer registration + `account_id`-isolated customer accounts + IITDEVELOPER Platform Admin control plane. See [Sprint 5](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md) |
| `docs/01-product/FUTURE_SCOPE_LEAD_INTELLIGENCE.md` | DONE (idea capture only — AI voice qualification, licensed audience data, contact enrichment from a reference product; not scheduled into any release) |
| `docs/03-ux-ui/DESIGN_REFERENCE_REVSPOT.md` | DONE (reference material only — extracted design tokens from a reference product; proposes adopting its token architecture, not its color palette) |
| Full per-feature specs under `02-features/`, all of `06-api/`, `07-ai/`, `09-integrations/`, `13-business/` | NOT_STARTED |

## Immediate next steps

1. Session sequence so far, each picked as "most needed" given dependencies/priority (full
   rationale per task in [CHANGELOG.md](CHANGELOG.md)): `GRX-AUTH-002` → `GRX-AUTH-003` →
   `GRX-USER-001` → `GRX-AUTH-005` → `GRX-FOUND-006` → `GRX-AUTH-004` → `GRX-TEST-002` →
   `GRX-FOUND-008` → `GRX-DEVOPS-001` → `GRX-COMPANY-002` → `GRX-USER-002` →
   `GRX-FOUND-007` → Sprint 2: `GRX-CONTACT-001` → `GRX-CONTACT-002` → `GRX-CONTACT-003` →
   `GRX-CONTACT-004` → `GRX-CONTACT-005` → `GRX-CONTACT-006` → `GRX-CONTACT-007` →
   `GRX-CONTACT-008` → `GRX-CONTACT-009` → `GRX-DOC-003` → `GRX-AUDIT-002` →
   `GRX-FOUND-009` (ad hoc, user-requested sidebar UX, not part of any sprint plan) →
   Sprint 3 planning (`DEC-GRX-015` resolving OQ-002, data model, RBAC, threat model,
   `SPRINT_03_EMAIL_CAMPAIGN.md`, readiness gate, `GRX-EMAIL-001`–`010`) →
   `GRX-EMAIL-001` → `GRX-EMAIL-002` → `GRX-EMAIL-003` → `GRX-EMAIL-004` → `GRX-EMAIL-005`
   → `GRX-EMAIL-006` → `GRX-EMAIL-007` → `GRX-EMAIL-011` (ad hoc, Custom SMTP as a
   second provider + SMTP TLS fixes) → `GRX-EMAIL-012` (ad hoc, SMTP "test connection"
   button) → `GRX-EMAIL-008` → `GRX-EMAIL-009` → `GRX-EMAIL-010`.
   **Sprint 1 and Sprint 2 (Contacts) are both fully `DONE`**, including `GRX-DEVOPS-001`
   (user pushed and confirmed a green CI run), `GRX-DOC-003` (Sprint 1 doc/handoff
   update, which filed `GRX-AUDIT-002` for the audit-viewing gap it found), and
   `GRX-AUDIT-002` itself (closed the same session it was filed). **Sprint 3 (Email
   Marketing) is now fully `DONE`**: `GRX-EMAIL-001` through `GRX-EMAIL-007` (provider
   connection, templates, campaigns CRUD, the send pipeline, the Postmark webhook
   receiver + unsubscribe handling, the campaign report/analytics endpoint, and the
   provider connection + sender identity settings UI), the ad hoc `GRX-EMAIL-011`/
   `GRX-EMAIL-012` additions, `GRX-EMAIL-008` (email templates frontend — a list page
   plus dedicated create/edit pages at `/dashboard/templates/new` and
   `/dashboard/templates/[id]/edit`, with search, sort, delete, and duplicate),
   `GRX-EMAIL-009` (campaign builder + send frontend — one shared form/detail component
   at `/dashboard/campaigns/new` and `/dashboard/campaigns/[id]` covering drafting,
   recipient targeting, test send, and immediate send), and `GRX-EMAIL-010` (campaign
   report frontend — a "Delivery report" card on the same detail page, showing
   sent/delivered/opened/clicked/bounced/complained counts and rates once a campaign
   leaves `DRAFT`) are all `DONE`, none needing any backend changes beyond what
   Sprint 3's backend tasks already shipped. **Sprint 4 (Scheduled Campaigns) is now
   fully `DONE`**: `GRX-SCHED-001` (schema + schedule/cancel endpoints, built in parallel
   by two sessions and reconciled) and `GRX-SCHED-002` through `006` (scheduler ticker,
   worker dispatch consumer, Redis idempotency, TTL+DLX retry backoff, and DLQ, plus
   their tests — see `MASTER_TASK_TRACKER.md`). Backend-only: the `/{id}/schedule` and
   `/{id}/cancel` endpoints exist and now actually dispatch on time, but
   `campaign-form-page.tsx` has no UI to call them yet — a real, undone gap, not part of
   any `GRX-SCHED-*` row's scope, tracked here for whoever picks up Sprint 4's frontend.
   `GRX-EMAIL-004` also fixed a real gap found along the way — `usage_records` was
   documented as existing since Sprint 1 (`DEC-GRX-007`) but was never actually built —
   and carries one documented evidence gap: no live Postmark account is available in
   this environment, so the real outbound send was verified up to a genuine `535`
   auth rejection from Postmark's actual relay, not a successful delivery.
   `GRX-EMAIL-005` closed a second real gap: `THREAT_MODEL.md`'s `T14` called for webhook
   Basic Auth credentials "stored alongside the provider connection, encrypted at rest",
   but `email_provider_connections` never actually got those columns when Sprint 3 was
   planned — added them here. It carries the same class of evidence gap as
   `GRX-EMAIL-004`: no live Postmark account exists to confirm the exact webhook JSON
   payload shape, so `PostmarkWebhookPayload` is deliberately permissive (`extra="allow"`,
   only `RecordType`/`MessageID` required) and the full raw payload is preserved in
   `email_events.metadata`.
   `GRX-EMAIL-006` corrected its own tracker row's planning-time file location: rather
   than extending `campaigns` (which `MODULE_BOUNDARIES.md` doesn't permit to depend on
   `email_delivery`), it created the dedicated `analytics` module the boundaries doc
   already names for exactly this ("read-side aggregation/reporting over campaigns...").
   `GRX-EMAIL-007` (the first frontend task of Sprint 3) found a real permission-check
   bug during live browser verification, not caught by its own first-written component
   tests: the connection/sender-identity GET routes are themselves `integrations.manage`-
   gated on the backend, so a real non-Super-Admin's 403s on those calls masked the
   intended access-denied message with a generic load-error one — fixed by checking
   permissions before issuing the gated fetches, and the test suite's mock was corrected
   to reproduce the real 403s so this regression class is now caught automatically.
2. `RISKS.md`/`BLOCKERS.md` remain not required by any task yet; create them if/when a
   task's scope actually calls for one.
3. Write full feature specs in `02-features/` for Slice 3 features (`EMAIL_PROVIDERS.md`,
   `EMAIL_TEMPLATES.md`, `EMAIL_CAMPAIGNS.md`) as each task is picked up, not all upfront
   — same practice as Sprints 1–2.
4. Do not begin any V1.5+/SEO-AEO-GEO work until Slices 1–6 (MVP) are stable in production.
5. Do not resolve OQ-003/004/006/007/009/012 early — they don't block Slice 3 (explicit
   instruction; OQ-002 is the one exception, resolved because Slice 3 genuinely needed it).
6. Do not start more than one Sprint 1 task concurrently (explicit instruction).
7. Sprint 6 (Social Publishing, product Slice 5) is fully `DONE` (`GRX-SOCIAL-001`–`011`),
   built after the user chose it over Slice 6 (AI Assistant) and explicitly scoped it to
   the customer-facing feature only, deferring platform-admin oversight.
8. Sprint 7 (AI Assistant, product Slice 6) is now also fully `DONE` (`GRX-AI-001`–`011`)
   — all six MVP slices were complete as of that session.
9. Sprint 8 (Billing, product Slice 7) is now fully `DONE` (`GRX-BILL-001`–`010`, plus
   `GRX-SAAS-006`/`012`) — **the MVP roadmap plus the first monetization slice are both
   complete.** Next up: the platform-admin social oversight panel deferred under item 7,
   the "LLM Token Usage Metrics" aggregation endpoint + charts flagged (not built) during
   Slice 6's frontend work, `campaign-form-page.tsx`'s still-missing schedule/cancel UI
   gap noted under item 1 above, USD payments once Razorpay grants international-payments
   approval, or a new direction the user picks now that both the MVP and billing are
   built out.
10. **The application went live in production this session** — actual deployed stack is
    **Hugging Face Space `iitdeveloper/growixa`** (single Docker Space running both the
    FastAPI API and the worker consumer loop) **+ Netlify** (`growixa.netlify.app`,
    Next.js web), not Render — `render.yaml`/`RENDER_DEPLOYMENT.md` were deleted as no
    longer applicable. Live debugging surfaced and fixed two real production bugs (a
    whitespace-in-env-var SMTP crash and a ~67s registration-blocking hang) and one real
    architecture gap (the platform's default SMTP relay is unreachable from HF's network)
    that motivated building `GRX-SAAS-013` (platform-admin email provider config, DB-
    backed, no-redeploy-needed) — see `CHANGELOG.md`'s 2026-08-14 entry for the full
    incident writeup. Also surfaced a real Netlify-specific gotcha worth remembering: the
    site has its own native GitHub git integration with an environment-variable set
    *separate from* the GitHub Actions deploy workflow's variables, which can silently
    diverge (it did — the live site was calling Render's old URL after the workflow was
    already pointed at HF) and requires a "Clear cache and deploy site" after changing
    `NEXT_PUBLIC_API_URL` there, since it's a Next.js build-time value, not read live.
11. **Same-origin API proxy fix**: separately from the incidents in item 10, browser
    login/register was found to be completely blocked by CORS — Hugging Face's own Space
    ingress answers the browser's preflight `OPTIONS` request itself, before it reaches
    the container, without `Access-Control-Allow-Credentials`. Not fixable from
    `apps/api`'s own `CORSMiddleware` config (confirmed via direct comparison against
    local Compose, where the identical request is correct). Fixed by proxying `/api/*`
    through Netlify's own edge (`netlify.toml`), removing the need for cross-origin
    credentialed requests entirely. Requires a manual env var change
    (`NEXT_PUBLIC_API_URL=/api` in both the GitHub Actions repo variables and Netlify's
    dashboard) the coding agent can't apply directly — pending user action as of this
    update. New `docs/11-devops/PRODUCTION_DEPLOYMENT.md` documents the real deploy
    topology, previously undocumented.
12. **`GRX-SAAS-014` (Dashboards)**: both `/dashboard` and `/platform` were empty
    placeholders (the latter had no root page at all). Built a Phase-1-scoped overview
    for each — real KPIs/quota gauges/contact-growth chart/recent campaigns on the
    customer side, active-accounts/MRR/plan-distribution on the platform side — see
    `CHANGELOG.md`'s 2026-08-14 entry. The plan's full 4 role-adaptive customer views
    (Marketing Manager/Content Creator/Analyst) remain unbuilt, staged as Release 1.1 by
    the plan itself.
13. **`GRX-SAAS-015` (Suppression-list fixes)**: user-directed after live-checking the
    Suppression page found the "Remove" button silently did nothing — it called a
    `DELETE /contacts/suppression/{id}` route that never existed on the backend, a real
    previously-shipped bug, now fixed. Also added RFC 8058 one-click unsubscribe (a
    `List-Unsubscribe` header plus a new POST-capable unsubscribe endpoint, so Gmail/Yahoo
    show their native inbox-level "Unsubscribe" button), whole-domain suppression
    (`*@competitor.com`-style blocks via a nullable `domain` column + XOR CHECK constraint
    on `suppression_entries`), and CSV bulk import/export of the suppression list — see
    `CHANGELOG.md`'s 2026-08-15 entry. No new RBAC permission codes; all new routes reuse
    the existing `contacts.manage`/`contacts.view`.
14. **`GRX-SAAS-016` (Email Validation, free tier)**: picked up from `need_review_docs/
    EMAIL_VALIDATION_FEATURE_PLAN.md`. The plan's default was a paid provider
    (Clearout.io); asked the user whether one was actually needed given the app already
    has outbound SMTP, explained why that relay can't double as a mailbox-probing tool,
    and the user chose the free build instead — syntax, MX/A record, disposable-domain
    list, and role-account detection only, no SMTP mailbox probe or catch-all scoring (both
    genuinely require infrastructure a paid provider invests in). New `/dashboard/contacts/
    verify-email` page with single-check and bulk-CSV tools, no new DB table, no credit
    metering, no new RBAC code (reuses `contacts.view`) — see `CHANGELOG.md`'s 2026-08-15
    entry. Frontend was redesigned mid-build after the user shared a competitor's Verifier
    page as a layout reference, with an explicit instruction to keep Growixa's own color
    theme and only borrow the layout idea.
15. **`GRX-SAAS-017` (Email Validation, multi-vendor real-time provider config)**: direct
    same-session follow-up to `GRX-SAAS-016`. New `platform_email_validation_provider_config`
    table + admin page, mirroring the AI/email provider config pattern, gated to paid-plan
    accounts only with a per-check opt-out checkbox; Free-tier accounts are never affected.
    Self-hosting real mailbox probing was ruled out live (a real `RCPT TO` test attempt
    tripped this session's own safety classifier as reconnaissance). The user then
    configured a real Clearout.io key, which surfaced and fixed two real bugs (an
    object-shaped `sub_status` rendering as a raw Python dict repr; the vendor's name
    leaking into customer-facing text) plus a code-organization fix (a shared
    fallback-reason dictionary moved out of the vendor-specific adapter file into
    `providers/base.py`) — see `CHANGELOG.md`'s 2026-08-15 entry. Real credit-ledger
    deduction is deliberately not wired up yet; the checkbox is informational only for now.

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the full reverse-chronological history.
