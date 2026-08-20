# Changelog

- Document ID: DOC-CHANGELOG
- Status: ACTIVE
- Version: 1.0.0
- Last updated: 2026-08-18
- Owner: Coding agent
- Related documents: [PROJECT_STATUS](PROJECT_STATUS.md), [DECISIONS](DECISIONS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md)

Reverse-chronological log of material changes to the Growixa repository (documentation and,
from Sprint 1 onward, code). Each entry names what changed and the commit(s) it landed in.

## 2026-08-20 — v0.4.0-rc1 release candidate (UAT preview)

- **`v0.4.0-rc1`** — cut UAT release candidate tag containing template token insertion fix, real Brand Voice API integration, Quick Starters UX fix, and multi-variation rendering.
- Merged `feature/FRONTEND/GRX-TEMPLATE-TOKEN-FIX` fixing visual editor token synchronization and live preview.
- Merged `feature/FRONTEND/GRX-QA-001` removing dead notification badge CSS styles and unused `QualityMetrics` types.
- Merged `feature/FRONTEND/GRX-BUG-002-004` delivering real `GET /brand/profile` integration in Brand Voice drawer (`GRX-BUG-002`), honest Quick Starters parameter loading (`GRX-BUG-003`), and full 1-7 variation rendering with relative timestamps (`GRX-BUG-004`).

## 2026-08-20 — v0.3.0 production release

- **`v0.3.0`** — official production release promoted from `v0.3.0-rc2`.
- Merged `feature/FRONTEND/add-web-favicon` delivering brand `/icon.png` and `/apple-icon.png` (512x512 PNG).
- Merged `chore/DEVOPS/pre-commit-branch-guard` enforcing branch naming standards and preventing direct commits to `main`.
- Hardened `.github/workflows/deploy-production.yml` and `deploy-uat.yml` with automated directory permission checks and SCP synchronization.
- Isolated production PostgreSQL inside Docker network (`GRX-INFRA-005`), eliminating host port 5432 collision risks.

## 2026-08-18 — GRX-INFRA-005 production deploy port-collision hotfix

- **`GRX-INFRA-005`** — fixed the GHCR Compose production deploy path after `v0.2.0`
  rollout failed during migrations with `Bind for 127.0.0.1:5432 failed: port is already
  allocated`.
- Production Postgres is now Docker-network-internal only in `compose.prod.yaml`; API and
  worker still connect through `postgres:5432`, and operators use `docker compose exec`
  for DB access instead of a host port.
- `deploy_prod.sh`, `deploy_uat.sh` and `backup_db.sh` now use stable Compose project names
  (`growixa-prod`, `growixa-uat`) while explicit volume names preserve the existing
  `docker_*` data volumes during the project-name migration.
- `deploy_prod.sh` and `deploy_uat.sh` fail fast if legacy Compose project `docker`
  containers still exist, with operator instructions to inspect and remove containers
  without deleting volumes before retrying the renamed stack.
- The OVH runbook and Growixa infra playbook now document internal-only production DB
  access and the safe triage commands for a `5432` owner on the VPS.

## 2026-08-18 — v0.2.0 production release

- Promoted the validated `v0.2.0-rc4` payload to production via tag `v0.2.0`.
- Production workflow routing verified before tagging: `.github/workflows/deploy-production.yml`
  accepts `v*.*.*` release tags and excludes `v*.*.*-*`/`*rc*`; UAT remains on `v*-rc*`.
- Release notes finalized for `v0.2.0` with release date, production status, production URL,
  and UAT staging URL.

## 2026-08-18 — v0.2.0-rc4 UAT release: deploy rollback safety and campaign scheduling redirect

- **`GRX-INFRA-004`** — hardened `scripts/deploy_vps.sh` so `docker image prune -f` runs
  only after the post-deploy health check passes. Failed deployments now preserve dangling
  rollback images instead of deleting them before the new containers are proven healthy.
  Landed in `7bd9a82`, with tracker/review docs through `ba7290c`.
- **Campaign scheduling redirect fix** — after a successful schedule confirmation, the
  campaign form now redirects back to `/dashboard/campaigns` so users return to the
  all-campaigns view and can immediately see the scheduled campaign. Landed in `beb7b17`;
  approval and review record through `84bebaa`.
- **Tagged `v0.2.0-rc4`**:
  - Routes to UAT only through `.github/workflows/deploy-uat.yml` (`v*-rc*` tags).
  - Updates `RELEASE_NOTES.md` to reflect the active UAT preview tag.

## 2026-08-18 — v0.2.0-rc3 UAT release: Dependabot 7 CVE remediation & CI security audit gates

- **`GRX-SEC-002`** — triaged and remediated all 7 Dependabot alerts (6 high, 1 moderate) on `main`:
  - Documented technical triage in [`docs/08-security/DEPENDABOT_TRIAGE.md`](../08-security/DEPENDABOT_TRIAGE.md), confirming all CVEs were isolated to dev/build tooling with zero customer data or runtime API exposure.
  - Applied package overrides for `postcss@^8.5.26`, `nanoid@^3.3.18`, `js-yaml@^4.3.1`, and version-selector overrides for `brace-expansion@^1.1.0: ^1.1.18` + `brace-expansion@^5.0.0: ^5.0.9`.
  - Refreshed lockfile; **`npm audit` reports 0 vulnerabilities** across all dependencies.
  - Maintained Next.js `15.5.21` stability without forcing breaking major bumps.
  - Added automated security gates to `.github/workflows/ci.yml`: `pip-audit` for backend & worker, and `npm audit --audit-level=high` for frontend.
- **Codebase Quality & Lint Hygiene**:
  - Resolved `ruff` E501 line-length violations in `auth/api.py` and `platform_auth/api.py`.
  - Cleaned up unused import in `tests/infrastructure/test_migrations.py`.
  - Added trailing newline to `scripts/compile-docs.js` output and formatted `generated-docs.json`.
- **Tagged `v0.2.0-rc3`**:
  - Deployed automatically to the UAT environment on the OVH VPS via `.github/workflows/deploy-uat.yml`.
  - Landed in merge commit `c84b61d` and push `0d2bfa9`.


## 2026-08-18 — Task-tracker correction and the process gap that caused it

- Marked seven merged tasks `DONE` that were still showing as outstanding work:
  `GRX-TEST-ORG-001` (`f4d2b13`, was `IN_REVIEW`), `GRX-SAAS-007` (`434a464`, was
  `BACKLOG`), `GRX-SAAS-009` (`af733c4`, was `IN_REVIEW`), `GRX-CONTACT-016` (`95189af`),
  `GRX-DOCS-001` (`89624bd`), `GRX-INFRA-003` and `GRX-CHORE-001` (both `b11cbb2`, were
  `READY`).
- Marked `GRX-CONTACT-011` `DONE` — delivered by `GRX-CONTACT-015` and `GRX-CONTACT-016`
  rather than as its own branch. Verified against its own acceptance criteria on `main`
  (multi-select, select-all, bulk delete, bulk suppress, bulk restore, and the
  `contacts.manage` gate all covered by named tests), not merged by association.
- Corrected stale `GRX-CONTACT-010 (READY, not started)` dependency text on
  `GRX-CONTACT-011` and `GRX-CONTACT-014`; `GRX-CONTACT-010` merged as `a8419ff`.
  `GRX-CONTACT-014` remains `BLOCKED` — it depends on `OQ-008`/`OQ-028`, which are
  unresolved product decisions.
- **Why this mattered**: a project-manager agent read the tracker and reported three tasks
  as `READY` that were already shipped. The tracker is what every agent reads to pick up
  work, so a merged task left at `READY` sends the next agent to re-implement it.
  `GRX-SAAS-007` sat at `BACKLOG` while merged.
- Root cause was structural, not clerical: the developer sequence ended at handoff, so no
  role owned moving the row after merge. Added `DEFINITION_OF_DONE.md` item 23, and named
  the owner in `growixa-developer` step 9 and `growixa-reviewer` §5.
- Fixed table hygiene: `GRX-CONTACT-016` was missing its closing `|`, silently dropping its
  last column. Seven rows split wide because cells contain a literal `|` inside code spans
  (`str | None`); confirmed this never shifted the `Status` field, so it did not cause the
  misreport.
- Added `scripts/tracker_to_csv.py`, which generates `MASTER_TASK_TRACKER.csv` by splitting
  only on pipes outside code spans (`--check` fails when stale). The markdown remains the
  source of truth.
- Remaining not-`DONE` and all genuine: `GRX-SEC-002` (`READY`), `GRX-CONTACT-012`/`013`
  (`BACKLOG`, design-first), `GRX-CONTACT-014` (`BLOCKED`).
- Landed in commits `b07878d`, `000b30c`.

## 2026-08-17 — v0.2.0-rc2 UAT release, deploy hardening, and marketing rollback

- **`GRX-INFRA-003`** — hardened `scripts/deploy_vps.sh`: it now exits non-zero when the
  post-deploy health check fails (it previously printed a warning and still reported success),
  and takes a fresh database backup immediately before `alembic upgrade head` rather than
  relying on a cron backup up to 24h stale. Documented a restore procedure at
  `OVH_VPS_DEPLOYMENT.md` §8a and **rehearsed it against a real dump** — restored into a
  scratch database and compared against source (60 tables, `accounts` 75=75, `users` 79=79,
  matching `alembic_version`), then dropped the scratch database. Known remaining defect:
  `docker image prune -f` still runs before the health check, discarding the rollback image.
- **`GRX-CHORE-001`** — added `.claude-flow/` to `.gitignore`.
- Tagged **`v0.2.0-rc2`**, which routes to UAT only (`deploy-uat.yml` matches `*-rc*`;
  `deploy-production.yml` excludes `!*rc*`). Updated `RELEASE_NOTES.md`, correcting a stale
  reference to a `v0.2.0-rc1` tag that was never created, and added a Known Issues section
  covering the 7 open Dependabot alerts and the prune-before-health-check ordering.
- Removed all contributions from one contributor from `main` at the product owner's
  direction (`4e67eec`): the marketing FAQ section was reverted to its `v0.1.0-rc2` state
  byte-for-byte and the associated backend lint edits dropped. The `/docs` help centre was
  deliberately preserved — it is unrelated work.
- **`GRX-FAQ-UAT-REBASE`** (`520dfaf`) — corrected three false claims on the public
  marketing FAQ that had reached `main` via PR #7 (`eff1628`) while the branch carried a
  `CHANGES_REQUESTED` verdict: "every single database table is keyed with a tenant account
  ID" (11 tables have no `account_id`), a "14-day free trial" with no backend
  implementation, and in-panel cancellation that does not exist. Also fixed a WCAG 2.2 AA
  SC 2.4.7 failure (`outline: none` with no replacement focus indicator) and added
  `prefers-reduced-motion` handling. **Process finding**: a GitHub merge does not consult
  the `pr_reviews/` verdict, so an approved-looking PR can bypass a blocking review.
- **`GRX-LINT-RUFF-002`** (`4b22f53`) and `f5f3812` — restored backend ruff compliance and
  stopped Prettier style-checking `src/content/docs/generated-docs.json`, which is emitted
  by the docs compiler on every build and had been failing frontend CI repeatedly.
- **`GRX-AGENT-DEV-001`** (`a936228`) — added tool-neutral developer and reviewer playbooks
  at `.agents/skills/growixa-developer/` and `.agents/skills/growixa-reviewer/`.

## 2026-08-17 — GRX-DOCS-001: Customer Help Center (`/docs`) & In-App Contextual Help

- Added a customer-facing help centre at `/docs` (20 markdown articles compiled to a JSON
  manifest by `scripts/compile-docs.js`, 10 supporting components) plus contextual help
  entry points in the dashboard.
- Independently reviewed across two rounds with product-owner sign-off; handed off in
  `pr_reviews/feature-FRONTEND-GRX-DOCS-001.md`. Landed in commit `89624bd`.

## 2026-08-17 — GRX-CONTACT-016: Deleted Contacts View & Contact Restoration

- Added a dedicated Deleted view for soft-deleted contacts with single and bulk restore,
  backend restore endpoints, and quota handling on restore — completing the soft-deletion
  model established by `DEC-GRX-034` and `GRX-CONTACT-010`.
- Independently reviewed and approved; handed off in
  `pr_reviews/feature-BACKEND-GRX-CONTACT-016.md`. Landed in commit `95189af`.

## 2026-08-17 — GRX-INFRA-002: Unified Multi-Environment CI/CD (GitHub Actions, GHCR, Production & UAT on OVH VPS)

- Implemented automated, self-contained multi-environment CI/CD pipeline on OVH VPS (`149.56.101.2`), replacing legacy external hosting dependencies (Hugging Face and Netlify).
- Created `.github/workflows/deploy-production.yml` (triggered on `v*.*.*` release tags) and `.github/workflows/deploy-uat.yml` (triggered on `v*-rc*` release-candidate tags).
- Built modular Docker Compose configurations in `deploy/docker/` (`compose.prod.yaml`, `compose.uat.yaml`, `compose.local.yaml`) with isolated database ports (5432 vs 5433), RabbitMQ ports (5672 vs 5673), and web/API bindings (3000/8000 vs 3001/8001).
- Implemented automated rollout and backup scripts in `deploy/scripts/` (`deploy_prod.sh`, `deploy_uat.sh`, `backup_db.sh` with gzip compression and 14-day retention).
- Configured host-level Caddy reverse proxy dual-domain routing for `https://growixa.iitdeveloper.com` (Production) and `https://uat.growixa.iitdeveloper.com` (UAT Staging) with automatic Let's Encrypt TLS certificates.
- Upgraded CI runner Node.js engine to v22 to satisfy `undici` and `jsdom` test dependencies across all 243 frontend tests.
- Created universal AI coding agent skill at `.agents/skills/growixa-infra/SKILL.md` and referenced in `AGENTS.md`.
- Landed in commit `a12c8c1`, `39226ca`. Handed off in `pr_reviews/feature-BACKEND-GRX-INFRA-002.md`.

## 2026-08-17 — GRX-INFRA-001: OVH VPS Production Deployment Guide & Automated Scripts

- Created comprehensive production-grade deployment runbook (`docs/11-devops/OVH_VPS_DEPLOYMENT.md`) tailored for OVHcloud VPS (`149.56.101.2`, 6 vCores, 12GB RAM, 96GB NVMe SSD).
- Hardened server security: UFW firewall configuration isolating internal databases/brokers, 4GB swap space configuration, and Caddy reverse proxy setup.
- Created 1-click update script and database backup script with size validation.
- Landed in commit `79e7b8c`. Handed off in `pr_reviews/feature-BACKEND-GRX-INFRA-001.md`.

## 2026-08-17 — GRX-SAAS-007: Platform Admin Provider Management Hub (`/platform/providers`)

- Built unified Super Admin provider management hub at `/platform/providers` consolidating Email (Postmark, Resend, SendGrid, Custom SMTP), AI (OpenAI, Anthropic, Gemini), and Email Validation (Clearout) configurations into a unified tabbed interface.
- Added live provider connectivity tests (`POST /platform/ai-config/test-connection`, `/platform/email-config/test-connection`) with real-time UI status feedback.
- Landed in commit `434a464`. Handed off in `pr_reviews/feature-BACKEND-GRX-SAAS-007.md`.

## 2026-08-17 — GRX-CONTACT-015: Soft delete — customer-facing UI (delete, bulk delete, suppression, purge)

- Implemented customer-facing soft-delete UI for contacts table: row and header multi-select checkboxes, floating bulk action bar with item counter, Delete Confirmation Modal with optional suppression list checkbox, and Audience Purge with type-to-confirm safeguard (`DEC-GRX-034`).
- Permission-gated for `contacts.manage`.
- 18 component/unit tests passing in `contacts-page.test.tsx`.
- Landed in commit `a97bef2`. Handed off in `pr_reviews/feature-FRONTEND-GRX-CONTACT-015.md`.

## 2026-08-17 — GRX-CONTACT-010: Soft delete — schema, repository layer & query filtering

- Implemented database schema migration adding nullable `deleted_at` timestamp to `contacts` table and partial unique indexes (`(account_id, email) WHERE deleted_at IS NULL`).
- Updated repository queries to filter out soft-deleted contacts by default across list, count, segment, and campaign evaluation queries.
- Landed in commit `8d6ec7a`. Handed off in `pr_reviews/feature-BACKEND-GRX-CONTACT-010.md`.

## 2026-08-15 — GRX-SAAS-017: Email Validation — multi-vendor real-time provider config, paid plans (ad hoc)

- Direct follow-up to `GRX-SAAS-016` in the same session: after seeing a garbled fake
  address pass the free checks as "Valid," the user asked whether Growixa could
  self-host real mailbox verification instead of paying a provider. A live test
  confirmed outbound port 25 works from the dev environment, but an actual `RCPT TO`
  probe attempt was blocked by this session's own safety classifier as reconnaissance
  against a real third party's mail infrastructure — reinforcing the recommendation to
  use a real vendor rather than self-host. The user then asked for a **platform-admin
  configurable, multi-vendor** architecture (not hardcoded to Clearout), gated to
  **paid-plan accounts only**, plus a per-check **opt-out checkbox** so a paid account
  isn't forced to spend a credit on every check.
- New `platform_email_validation_provider_config` table (mirrors
  `platform_ai_provider_config`/`platform_email_provider_config`'s "one active row"
  pattern), a `ClearoutProvider` adapter (raw httpx, no vendor SDK), and
  `providers/factory.py`'s resolution rule: a real-time adapter is only returned when
  the account's plan isn't `free` AND the platform has an active vendor configured —
  otherwise every account gets `GRX-SAAS-016`'s free check, never an error.
- New `GET /email-validation/availability` and a `use_realtime` flag on
  `POST /email-validation/check`; new platform-admin page at
  `/platform/email-validation-config`; the customer verify-email page shows a
  `Real-time`/`Basic check` badge on every result and gracefully falls back to `BASIC`
  if the vendor call itself fails, with a visible reason.
- The user then configured a real Clearout.io API key live, closing the evidence gap:
  the exact garbled address that started this now correctly comes back `INVALID` with a
  real "Mailbox not found" reason. This surfaced two real bugs only a live call could
  catch — Clearout's `sub_status` is an object, not a string (was rendering as a raw
  Python dict repr in the UI), and the reason text was leaking the vendor's name
  ("Clearout: ...") to the end customer — both fixed. A separate code-review catch moved
  a shared fallback-reason dictionary out of the Clearout-specific adapter file into
  `providers/base.py`, since it describes this module's own status vocabulary, not
  anything Clearout-specific, and every future vendor adapter needs the same wording.
- No real credit-ledger deduction wired up yet (deliberately deferred, separate scope
  from this pass) — the checkbox is currently informational only.

## 2026-08-15 — GRX-SAAS-016: Email Validation — free tier (ad hoc)

- Picked up from a `need_review_docs/EMAIL_VALIDATION_FEATURE_PLAN.md` review. The plan's
  default recommendation was a paid third-party provider (Clearout.io/ZeroBounce); asked
  the user whether one was actually needed given the app already has an outbound SMTP
  relay — explained why that relay can't double as an SMTP-probing verification tool
  (probing arbitrary third-party mail servers needs raw port-25 connections, which most
  cloud hosts block/rate-limit, and real mail providers throttle probing IPs fast). User
  chose the free, no-provider build.
- New `email_validation` module: syntax check, MX/A record lookup (RFC 5321 implicit-MX
  fallback), a curated disposable-domain list, and a role-account (info@, admin@, ...)
  list. `POST /email-validation/check` (single) and `POST /email-validation/bulk-csv`
  (CSV upload, up to 2,000 rows, returns the same CSV with a `validation_status` column
  added), both gated by the existing `contacts.view` — no new RBAC code, no DB table, no
  credit metering. The bulk route is rate-limited (IP-keyed) since it can trigger many
  DNS lookups per call.
- New `/dashboard/contacts/verify-email` page: a tabbed Single Email / Bulk Upload tool
  with real drag-and-drop CSV upload and an honest "what we check" / "what we don't
  check" panel — built entirely from Growixa's own existing design tokens, not a new
  theme (the initial pass used a plainer layout; redesigned after review with the
  explicit instruction to borrow only the layout idea from a competitor reference, never
  its color scheme).
- Self-caught: `example.com` (RFC 2606's reserved documentation domain) had been added to
  the disposable-domain list as a placeholder, colliding with the same domain used as the
  neutral test fixture — removed before it could misclassify a real domain.
- Also fixed a small pre-existing bug found in passing: `--color-purple`, referenced by
  the Suppression page's "Complained" metric since `GRX-SAAS-015`, was never actually
  defined in `globals.css` — now defined.

## 2026-08-15 — GRX-SAAS-015: Suppression-list fixes — bug fix, one-click unsubscribe, domain blocking, CSV import/export (ad hoc)

- User-directed after live-checking the Suppression page. Three things fixed/added:
- **Bug fix**: the "Remove" button on `/dashboard/contacts/suppression` called
  `DELETE /contacts/suppression/{id}` — a route that never existed on the backend, so the
  button silently did nothing. Added the route plus `remove_suppression` service/repository
  layer.
- **RFC 8058 one-click unsubscribe**: outbound campaign emails now carry a
  `List-Unsubscribe`/`List-Unsubscribe-Post: List-Unsubscribe=One-Click` header, so
  Gmail/Yahoo show their native inbox-level "Unsubscribe" affordance. Required adding a
  new `POST /unsubscribe/{campaign_recipient_id}` alongside the existing `GET` — mail
  clients require the target URL to accept POST for one-click unsubscribe to work.
- **Domain-level suppression + CSV import/export**: `suppression_entries` extended with a
  nullable `domain` column and an XOR CHECK constraint (`email` XOR `domain`, never both) —
  a customer can now block every address at a domain in one action
  (`POST /contacts/suppression/domains`), and bulk import/export the whole suppression list
  as CSV (`POST /contacts/suppression/import`, `GET /contacts/suppression/export`). A
  partial unique index on `(account_id, domain) WHERE domain IS NOT NULL` enforces one
  active block per domain per account. All new routes reuse the existing
  `contacts.manage`/`contacts.view` permissions — no new RBAC code.
- 7 new backend tests, 2 new worker tests, 2 new frontend tests. Live-verified end-to-end
  against the real running Compose stack via both `curl` and a real browser session.
  See `MASTER_TASK_TRACKER.md`'s `GRX-SAAS-015` row for the full evidence writeup.

## 2026-08-14 — GRX-SAAS-014: Dashboards — customer + platform admin overview (ad hoc)

- Driven by a product-planning review of `need_review_docs/DASHBOARDS_METRICS_AND_UI_PLAN.md`.
  Both dashboards were previously empty: `/dashboard` showed a static "nothing here yet"
  placeholder; `/platform` had no root page at all (login redirected straight to Accounts).
  Scoped to the plan's own "Phase 1 (MVP)" tier — one unified overview per surface, not
  the full 4 role-adaptive customer views, which the plan itself stages as Release 1.1.
- New `GET /dashboard/overview` (auth-only, no new RBAC permission — same shape as
  `GET /auth/me`): total/active contacts, campaign status breakdown, scheduled social
  posts, account-wide email open/click rate, quota snapshot, 6-month contact-growth
  curve, 5 most recent campaigns with sent/open-rate. New
  `GET /platform/dashboard/summary` on the existing `platform.usage.manage` gate:
  active-account count, MRR (USD/INR), current-period email/AI usage, dynamic per-plan
  distribution. Direct SQL aggregation, no new pre-aggregated table or Redis cache layer
  in this pass (accepted-risk, revisit at scale).
- New shared frontend components (`<MetricCard/>`, `<QuotaGauge/>`, `<TrendChart/>` — a
  native SVG chart, no new charting-library dependency) power both dashboards.
- Self-caught: a latent sidebar active-state bug where `href="/platform"` would have
  matched every other platform page as also "active" — fixed alongside adding the new
  Overview nav entry.

## 2026-08-14 — Same-origin API proxy (ad hoc, production incident response)

- Live production incident: login/register (and every credentialed browser request) was
  completely broken. Root-caused via a live browser session — the actual `POST
  /auth/login` was blocked at the CORS preflight stage with `Access-Control-Allow-
  Credentials` missing from the `OPTIONS` response. Confirmed via direct comparison this
  was not an `apps/api` bug: the identical request against local Compose returns the
  correct header; against the live Hugging Face Space, the `OPTIONS` response is missing
  the app's own response markers entirely (`server: uvicorn`, `x-proxied-*`), meaning
  HF's own Space ingress answers the preflight itself before it reaches the container —
  not something fixable from `apps/api`'s `CORSMiddleware` config.
- Fixed by removing the need for cross-origin credentialed requests at all: `netlify.toml`
  now proxies `/api/*` to the HF backend server-side (`[[redirects]]`, status 200), so the
  browser sees `growixa.netlify.app/api/...` as same-origin — no CORS, no preflight.
  `NEXT_PUBLIC_API_URL` must be `/api` for this to be used; `API_INTERNAL_URL` (new) keeps
  server-side/SSR calls going directly to the backend, same shape as `compose.yaml`'s
  existing `API_INTERNAL_URL` for local Compose. `.github/workflows/
  deploy-frontend-netlify.yml` updated to match. New
  `docs/11-devops/PRODUCTION_DEPLOYMENT.md` documents the real deploy topology (this was
  previously undocumented — `RENDER_DEPLOYMENT.md` was deleted with no replacement).
- Requires two manual env var updates the coding agent can't make directly (no GitHub/
  Netlify API credentials in this environment): `NEXT_PUBLIC_API_URL=/api` in both the
  GitHub repo's Actions Variables and Netlify's dashboard env vars, then a
  "Clear cache and deploy site" (it's a Next.js build-time value).

## 2026-08-14 — GRX-SAAS-013: Platform-admin email provider config (ad hoc, production incident response)

- Driven by a live production incident: the `.env`-only `PLATFORM_SMTP_*` relay
  (`s81.gocheapweb.com:465`) was unreachable from the deployed environment
  (`SMTPConnectTimeoutError`), and a separate bug (`PLATFORM_SMTP_HOST` trailing
  newline) crashed registration with an unhandled `500` instead of degrading gracefully.
  Both root-caused via real HF Space container logs.
- Fixed the crash: `Settings` now strips whitespace from every string env var
  (`config.py`); `smtp_transport.py`'s except clause widened to also catch `ValueError`.
  Fixed the ~67s registration hang: `register_route` now fires
  `send_verification_email` via `BackgroundTasks` instead of `await`ing it inline, with
  an explicit `SEND_TIMEOUT_SECONDS=20` on the `aiosmtplib.send()` call — registration
  latency went from ~67s to 0.143s.
- New `platform_email_provider_config` table (migration `a1b2c3d4e5f6`) and
  `notifications/` module: lets a platform admin configure/rotate the platform's default
  outbound SMTP credentials without a redeploy, resolved before falling back to the
  legacy `.env` settings. New `platform.email.manage` platform RBAC
  (`platform.owner`/`platform.admin`). Mirrors `platform_ai_provider_config`'s pattern;
  reuses `email_provider_connections`' `POSTMARK`/`CUSTOM_SMTP` vocabulary and the
  existing `integrations/smtp_transport.py` send/test functions directly — no new
  Postmark HTTP-API adapter. New `GET/PUT /platform/email-config`,
  `POST /platform/email-config/test` routes; new `/platform/email-config` admin UI page.
  `THREAT_MODEL.md` gained T69–T70.
- Deleted `render.yaml`/`docs/11-devops/RENDER_DEPLOYMENT.md` — the actual deployed
  stack is Hugging Face (API+worker) + Netlify (web), not Render.

## 2026-08-14 — GRX-BILL-001–010, GRX-SAAS-006/012: Billing (Sprint 8 / Slice 7 complete — first monetization slice)

- The first slice that moves real money. Readiness gate resolved via
  [DEC-GRX-029](DECISIONS.md) (Razorpay, not Stripe, dual-currency USD/INR) and
  [DEC-GRX-030](DECISIONS.md) (Subscriptions API as the billing primitive — Razorpay
  owns the recurring charge, Growixa reacts to webhooks; non-expiring top-up credits,
  no per-batch FIFO; percentage/fixed-amount/free-credit-grant coupon types).
  `THREAT_MODEL.md` gained T60–T68. Sprint-file: `SPRINT_08_BILLING.md`.
- New `subscription_plans`/`account_subscriptions`/`account_credit_balances`/
  `account_credit_purchases`/`coupon_codes`/`coupon_redemptions` schema — every account
  gets a `Free`-tier `account_subscriptions` row automatically at registration, never
  zero. New `billing.manage`/`billing.view` customer RBAC and `platform.billing.manage`
  platform RBAC (`platform.owner`/`platform.finance` only).
- A signature-verified, idempotent Razorpay webhook receiver (`POST /billing/razorpay`,
  same "verify before touching any table" shape as the Postmark webhook) handling
  `subscription.activated`/`charged`/`halted`/`cancelled` and `payment.captured`;
  idempotency for top-up credits enforced at the DB level (`account_credit_purchases.
  razorpay_payment_id` unique constraint, not application locking).
- Real Razorpay Checkout for subscribe/upgrade (Subscriptions API) and one-time top-up
  purchases (Orders API) — `POST /billing/subscribe`/`/billing/topup`.
- An atomic quota evaluator (`check_and_consume_quota`, `SELECT ... FOR UPDATE`-locked)
  for the two period-resetting metered dimensions (email sends, AI runs): checks the
  plan's monthly allowance first, falls back to the non-expiring credit balance for any
  overage, then blocks with `402`. An account's own bring-your-own AI key is never
  metered — only platform-provided generations are (`ai/services.py`'s `source ==
  "PLATFORM_DEFAULT"` check).
- An in-process cancellation-downgrade ticker (`GRX-BILL-006`, runs inside the `api`
  service's FastAPI lifespan, same pattern as the campaigns/social schedulers —
  confirmed by reading `campaigns/scheduler.py` directly, correcting the architecture
  doc's draft claim that it ran worker-side) that downgrades a `CANCELED` subscription
  to Free once its `current_period_end` passes.
- A platform-admin override panel (`GRX-SAAS-006`): manual plan assignment including
  Enterprise activation, free credit grants, billing-status override, and a genuine
  create-not-just-edit plan/credit-pack catalog UI — all bypass Razorpay entirely,
  gated `platform.billing.manage`. Widened `subscription_plans.slug`'s CHECK from a
  fixed 4-value whitelist to a plain format check so a real new tier can be created
  (self-serve checkout eligibility for a new tier is a deliberate, documented separate
  follow-up, not wired automatically).
- A coupon/discount engine (`GRX-SAAS-012`): percentage and fixed-amount coupons apply
  to top-up purchases only — verified against Razorpay's own Checkout.js docs that
  Subscription checkout has no discount parameter, correcting the architecture doc's
  original draft claim — while free-credit-grant coupons redeem directly via `POST
  /billing/redeem-coupon`, never touching Razorpay. Platform-admin CRUD at
  `/platform/coupons` (create/toggle/redemption-analytics); customer redemption fields
  on `/dashboard/billing`. Coupon-touching routes are rate-limited by source IP
  (`THREAT_MODEL.md` T65), closing a gap where the threat model had already documented
  this mitigation before it was actually built.
- The customer billing page (`/dashboard/billing`, `GRX-BILL-007`): current plan card,
  live quota usage bars, credit balances + coupon redemption, plan comparison grid with
  real Razorpay Checkout.js, top-up purchase grid, currency toggle.
- A dedicated `test_billing_{webhook,quota,coupons}.py` suite (`GRX-BILL-008`, 23 new
  tests) plus a `test_cross_tenant_isolation.py` extension — **found and fixed a real
  bug while writing the plan-eligibility test**: `_validate_coupon_for_redemption`'s
  `applicable_plan_slugs` check was dead code, since both call sites unconditionally
  passed `plan_slug=None`; fixed by resolving the account's real current plan before
  validating. The route-protection-audit criterion needed no new test — the existing
  generic `test_protected_routes_audit.py` already covers every new route automatically.
- Settings/env docs (`GRX-BILL-009`) — **found and fixed a second real gap**:
  `RAZORPAY_KEY_ID`/`_SECRET`/`_WEBHOOK_SECRET` had never been added to
  `.env.example` despite existing since `GRX-BILL-002`/`003`, and
  `BILLING_DOWNGRADE_POLL_INTERVAL_SECONDS` had a real default in `config.py` but was
  never wired into `compose.yaml`'s passthrough, so setting it in `.env` silently did
  nothing. New "Billing (Razorpay) setup" section in `LOCAL_DEVELOPMENT.md`.
- Full verification (`GRX-BILL-010`): `ruff`/`mypy`/`alembic check` clean on `apps/api`
  (306 passed, 8 skipped, up from 283 baseline, zero regressions);
  `eslint`/`tsc`/`prettier`/`vitest`/`next build` clean on `apps/web` (204 passed).
  Live-verified end-to-end against real Razorpay Test Mode throughout this whole slice:
  real `Plan`/`Subscription`/`Order` objects via genuine API calls, a real Checkout.js
  modal in a browser showing the correct (and correctly coupon-discounted) amount, real
  coupon creation/redemption via both `curl` and the live UI. USD stays blocked pending
  Razorpay's own account-level international-payments approval — an external, non-code
  blocker already documented in `BILLING_SYSTEM_ARCHITECTURE.md §8`, not a bug.
- **All seven MVP-scope product slices plus the Sprint 5 multi-tenancy retrofit are now
  complete.**
- Commits: `2b005ff`, `09fdcb7`, `cf978c1`, `16407a5`, `1400b4f`, `e44e7c4`, `befeef5`,
  `b34657c`, `2378e70`, and this session's `GRX-BILL-008`/`009`/`010` closeout.

## 2026-08-13 — GRX-AI-001–011: AI Assistant (Sprint 7 / Slice 6 complete — all six MVP slices now built)

- User chose Slice 6 (AI Assistant, the last unbuilt MVP slice) next, with three explicit
  scoping instructions: configurable multi-provider support (OpenAI, Azure OpenAI,
  Anthropic, Ollama), a platform-admin-configured default plus a per-account
  bring-your-own override, and code structured so a future slice can build multiple
  agents on top of it — using LangGraph later if needed, not now.
- Readiness gate: [DEC-GRX-026](DECISIONS.md) resolves [OQ-004](OPEN_QUESTIONS.md) (the
  multi-provider adapter + two-level config strategy), [DEC-GRX-027](DECISIONS.md)
  (SSRF-safe validation for any custom `base_url`, applied uniformly to platform-admin
  and customer-supplied values, re-checked at call time to defeat DNS rebinding — covers
  the `169.254.169.254` cloud metadata address via the link-local range).
  `THREAT_MODEL.md` gained T52–T59. Sprint-file: `SPRINT_07_AI_ASSISTANT.md`, the
  seventh sprint file, implementing product Slice 6.
- New `ai_generations`/`ai_provider_connections`/`platform_ai_provider_config` schema —
  3 tables, not the `DATA_MODEL.md` placeholder's speculative 4: prompts are code-defined
  strings (`ai/prompts/templates.py`), not a customer-editable DB table, deliberately
  avoiding a repeat of the `usage_records` "built Sprint 1, zero writers" mistake. New
  `ai.manage`/`ai.view` customer RBAC (mirrors `social.manage`/`social.view`; BYO
  connection *management* reuses the existing Super-Admin-only `integrations.manage`)
  and `platform.ai.manage` platform RBAC (owner/admin only — this gates an encrypted
  credential, a higher trust bar than `platform.usage.manage`).
- Four provider adapters (`ai/providers/`), raw `httpx`, zero vendor SDKs — matching this
  codebase's existing Postmark/Supabase/Instagram convention: `OpenAIProvider` (with an
  optional SSRF-validated `base_url` override, added specifically to reach the user's
  real Krutrim OpenAI-compatible endpoint), `AzureOpenAIProvider`, `AnthropicProvider`,
  `OllamaProvider`. **Found and fixed a real bug live-testing**: a reasoning model
  (`gpt-oss-120b`) hit `max_tokens` mid-chain-of-thought and returned `content: null`
  with a "successful" HTTP response — all four adapters now raise `AIProviderError` on
  empty content after success instead of silently returning nothing, and every
  capability's token budget was raised accordingly.
- Account BYO provider connections and platform-admin default config — same
  deactivate-then-insert convention as `email_provider_connections`/
  `social_connections`, SSRF-validated at save time and re-validated at call time.
  Resolution order: the account's own active connection first, else the platform
  default, else a clean `AINotConfiguredError` (409) — never a 500 or a silent
  hardcoded fallback.
- Six capability modules (`ai/capabilities/`: subject line, body copy, social caption,
  rewrite, hashtags, posting time), each exporting one `run(input, provider, model)`
  function with prompt-string construction kept separate from the `provider.generate()`
  call — the concrete, working answer to "structured for future multiple agents": a
  future LangGraph slice can wrap these as tools/nodes without a rewrite, without
  adopting LangGraph now ([DEC-GRX-012](DECISIONS.md) still holds — MVP AI stays
  assistive single-shot generate/rewrite/suggest, not autonomous).
- `POST /ai/generate/{capability}` writes an `ai_generations` row
  (`COMPLETE`/`FAILED`) every call and, on success, a `usage_records` row too —
  **fixing a real pre-existing gap**: that table has had a reader (`platform_admin`)
  since Sprint 1 but zero writers until this slice. `GET /ai/generations` (history,
  filterable by capability/linked entity) gated `ai.view`.
- Test Connection feature (`POST /ai/connections/test`, `POST /platform/ai-config/test`),
  added mid-slice at the user's request while live-testing a real API key: builds an
  adapter from unsaved credentials and makes one real minimal generation call,
  persisting nothing — mirrors `GRX-EMAIL-012`'s SMTP test-connection precedent exactly.
- Full backend test suite (283 passed, 8 skipped, up from 244): SSRF validator
  (private/loopback/link-local/metadata-IP rejection, save-time + call-time +
  DNS-rebinding re-check), BYO-vs-platform-default resolution precedence, cross-tenant
  isolation extension, route-protection audit re-run clean.
- Frontend: a reusable `AIGenerateButton` component (one component, not duplicated per
  page) wired into `campaign-form-page.tsx` (subject, body copy) and
  `post-form-page.tsx` (caption, hashtags) — click-to-insert only, AI output is never
  auto-applied, matching `DEC-GRX-006`'s mandatory-human-approval rule structurally (AI
  output can only ever land in a draft; the existing `campaigns.send`/`social.publish`
  permissions still gate the actual send). New `/dashboard/ai` generation-history page.
  A platform-admin AI-config page (`/platform/ai-config`, the real platform-staff route
  group — corrected mid-session after initially mis-planning it under the unrelated
  `(admin)` shell) follows the platform panel's already-shipped light theme rather than
  the user's dark-themed mockup, for visual consistency, while keeping the mockup's
  functional layout. An account-level "AI Model Provider" bring-your-own card on the
  Integrations page mirrors the existing Instagram card pattern. 191 passed (up from
  172), `next build` clean.
- Settings/env docs: `.env.example`'s `ENCRYPTION_KEY` note now covers AI credentials
  too; `LOCAL_DEVELOPMENT.md` gains an "AI Assistant setup" section — deliberately the
  only integration in this codebase with **zero new env vars**, since the provider,
  key, and model are all DB-configured via the admin UI at runtime, not `.env`, so a
  platform admin can switch providers without a redeploy.
- Live-verified end-to-end against a real Krutrim (OpenAI-compatible third-party) API
  key the user provided directly, routed through the platform-admin default config:
  real successful generations, real cost/token tracking, real `usage_records` writes,
  and (deliberately fake credentials) the Test Connection routes' correct 502
  error-surfacing without persisting anything. Anthropic was reachability/
  error-path-verified only (no real Anthropic key available) — logged honestly per
  [DEC-GRX-011](DECISIONS.md) rather than blanket-marked `DONE`. Did not complete an
  interactive logged-in browser click-through of the two provider-configuration forms'
  save/test-connection flows: the same action-classifier block on typing a password
  into a login form encountered in Slice 5 recurred, and — separately — saving the
  live platform config via `curl` with fabricated credentials was deliberately avoided,
  since it would have overwritten the user's real working Krutrim default with a
  keyless row.
- **All six MVP slices (Foundation, Contacts, Email Campaigns, Scheduled Email, Social
  Publishing, AI Assistant) are now built.** Remaining known gaps: the platform-admin
  social oversight panel deferred during Slice 5, and the "LLM Token Usage Metrics"
  charts from the user's AI-config mockup (would need a new backend aggregation
  endpoint, not built this slice).

## 2026-08-12 — GRX-SOCIAL-001–011: Social Publishing — Instagram Business (Sprint 6 / Slice 5 complete)

- User chose Slice 5 (Social Publishing) over Slice 6 (AI Assistant) as the next MVP
  feature, explicitly scoped to the self-serve customer-facing feature only —
  platform-admin oversight tooling for social is deferred until the product itself is
  finished.
- Readiness gate: [DEC-GRX-023](DECISIONS.md) resolves [OQ-003](OPEN_QUESTIONS.md)
  (Instagram Business/Meta Graph API), [DEC-GRX-024](DECISIONS.md) resolves
  [OQ-005](OPEN_QUESTIONS.md) (Supabase Storage, public-read bucket required since
  Instagram fetches media by plain URL), [DEC-GRX-025](DECISIONS.md) reuses the existing
  Fernet encryption for OAuth tokens (no new KMS). `THREAT_MODEL.md` gained T44–T51.
  Sprint-file numbering: this is `SPRINT_06_SOCIAL_PUBLISHING.md`, the sixth sprint file,
  implementing product Slice 5 — Sprint 5's filename was already taken by the unplanned
  multi-tenancy retrofit.
- New `social_connections` (per-account Instagram OAuth connection, Fernet-encrypted
  token, one-active-per-provider partial unique index — same shape as
  `email_provider_connections`) and `social.manage`/`social.publish`/`social.view` RBAC
  seed. `social.publish` is deliberately Marketing-Manager+-only, stricter than how
  Slice 4's shipped `campaigns.manage`-gated schedule route actually behaves — a
  deliberate correction, not a copy-paste of that gap.
- Instagram OAuth connect flow (`/integrations/instagram/oauth/{authorize,callback}`):
  Redis-backed single-use CSRF `state`, exchanges the short-lived code for a long-lived
  user token, resolves the linked IG Business Account through the connected Facebook
  Page, and stores the **Page's** own access token (what the Content Publishing API
  actually authenticates with).
- New `social_posts`/`social_post_media` schema (status state machine mirrors
  `campaigns.status`) and a new `files` module (`storage_client.py`) wrapping Supabase
  Storage's REST API directly via `httpx`, no SDK — matching this codebase's existing
  thin-provider-wrapper convention. Post CRUD + media upload enforces exactly one JPEG
  image ≤8MB per post, an explicit scope decision (the media table stays
  carousel/video-ready for a future slice).
- Publish-now (fire-once queue, mirrors `email_delivery`'s immediate-send queue) and a
  full schedule/cancel/retry dispatch pipeline: `social/scheduler.py` is a structural
  mirror of `campaigns/scheduler.py`'s atomic claim query, and the
  `grx.social.dispatch`/DLQ/retry-ladder queue topology mirrors the campaigns dispatch
  pipeline's TTL/dead-letter-exchange shape exactly. `retry_post` is genuinely new
  territory (campaigns has no manual retry route at all) — confirmed safe to reuse the
  post's fixed `idempotency_key` by reading how the campaigns worker's Redis "done"
  marker only gets set *after* success.
- Worker-side `instagram_client.py` (container-create/poll/publish) classifies Graph
  error code 190 (dead/expired token) as a `PermanentPublishError` that short-circuits
  the retry ladder straight to DLQ/FAILED, instead of burning all 3 attempts against a
  token that can never succeed.
- Full backend+worker test suite (17 new backend integration tests, 10 new worker
  tests, a 3-test cross-tenant isolation extension) **found and fixed two real schema
  bugs**: the worker's lightweight `SocialConnection` model was missing the `provider`
  column entirely, and `social_posts.idempotency_key` had no DB-level default (only a
  Python-side one), unlike `campaigns.idempotency_key` which deliberately has one for
  exactly this reason — fixed via a new migration matching that established precedent.
- Frontend: an Instagram card on the Integrations page (plain `<a href>` OAuth
  navigation, the one deliberate departure from every other Connect/Save action in this
  app, since the user has to reach Meta's own consent screen), a new post
  list/composer/social-only-calendar route group under `/dashboard/social`, and sidebar
  wiring. 19 new component tests; `next build` clean.
- Settings/env docs **found and fixed a real gap**: `compose.yaml` only passes through
  an explicit whitelist of environment variables to the `api`/`worker` containers, and
  the new Instagram/Supabase vars weren't on it — so even after adding them to `.env`,
  Compose would have silently never forwarded them (confirmed live via a `client_id=`
  empty OAuth redirect before the fix). Added them to both services' `environment:`
  blocks, plus matching `.env.example` (root, api, worker), `render.yaml`, and a new
  "Social Publishing (Instagram) setup" section in `LOCAL_DEVELOPMENT.md`.
- Live-verified everything reachable without real Instagram/Supabase credentials via
  `curl` against the running Compose stack: login, `/auth/me` permission grants, full
  post CRUD, publish/schedule validation (both correctly 400 with no media), unknown-
  media 404, OAuth authorize redirect shape. Two evidence gaps remain per
  [DEC-GRX-011](DECISIONS.md) — no live OAuth round-trip and no live media
  upload/publish — pending the user adding real
  `INSTAGRAM_APP_ID`/`INSTAGRAM_APP_SECRET`/`SUPABASE_STORAGE_URL`/
  `SUPABASE_STORAGE_SERVICE_KEY` to `.env` themselves.
- Did not complete an interactive logged-in browser click-through of the composer/
  calendar UI: typing the local smoke-test admin account's password into the login form
  was blocked by this environment's action classifier (treated as credential entry,
  with no carve-out for a self-created local dev account); the user chose to rely on
  the `curl` verification + 172 passing frontend tests + clean production build instead
  of logging in themselves to unblock a full visual pass.

## 2026-08-06 — GRX-SCHED-002/003/004/005/006: Scheduler ticker, worker dispatch, retry/DLQ (Sprint 4 complete)

- New `apps/api/src/growixa_api/campaigns/scheduler.py`: `claim_due_campaigns()` atomically
  flips due `SCHEDULED` campaigns to `DISPATCHING` via a single `UPDATE...RETURNING`;
  `run_scheduler_loop()` polls every `scheduler_poll_interval_seconds` (default 5s) as a
  FastAPI `lifespan` background task and publishes one `grx.campaigns.dispatch` job per
  claimed campaign.
- New worker dispatch handler in `apps/worker/src/growixa_worker/consumer.py`: reuses the
  existing `handle_send_campaign` unmodified (already status-agnostic and idempotent via a
  `CampaignVersion`-existence check). Redis (`redis_client.py`, new) marks a job's
  `idempotency_key` done *after* success — never before attempting, so a legitimate retry
  after a transient failure is never blocked.
- Retry backoff via RabbitMQ's TTL + dead-letter-exchange pattern: three durable wait
  queues (`grx.campaigns.dispatch.retry.{0,1,2}`, 1m/5m/15m TTL) dead-letter back into
  `grx.campaigns.dispatch`, no delay plugin needed. After 3 retries, the job is republished
  to `grx.campaigns.dlq` and the campaign is marked `FAILED`.
- `apps/worker` gained a `redis` dependency and `REDIS_URL` (wired into `compose.yaml`).
- 7 new integration tests against real Postgres (`test_campaign_scheduler_ticker.py`,
  `test_dispatch_consumer.py`).
- Two real bugs found and fixed: (1) `caf1c42204c9`'s and `4a92b8107c12`'s `downgrade()`
  both tried to drop the same-named unique constraint — harmless going up, fatal going
  down; `caf1c42204c9` is now a no-op on both sides (its job was already fully subsumed by
  `4a92b8107c12`). (2) The live `growixa-api-1` Compose container had zero volume mounts —
  created before `compose.yaml`'s bind mounts existed, and `restart` doesn't reapply
  config — so it had been silently serving a stale image all session; `docker compose up
  -d --build api` fixed it. Also added `logging.basicConfig` to `create_app()`, since
  nothing previously configured a handler for the `growixa_api` logger namespace.
- **Sprint 4 (Scheduled Campaigns) is now fully `DONE`** on the backend. No frontend UI
  exists yet to call `/{id}/schedule`/`/{id}/cancel` — a real, tracked gap.

## 2026-08-06 — GRX-EMAIL-010: Campaign report frontend (Sprint 3 complete)

- New "Delivery report" card on the campaign detail page, shown once a campaign
  leaves `DRAFT`. No backend changes — `GET /campaigns/{id}/report`
  (`GRX-EMAIL-006`) already returned everything needed.
- Sent shown as a raw count; Delivered/Bounced/Complained as rates of sent;
  Opened/Clicked as rates of delivered (can't open/click what wasn't
  delivered) — falls back to a bare count instead of a misleading `0%`/`NaN%`
  when the denominator is 0.
- The report fetch is isolated in its own try/catch so a report failure
  degrades to "no report section," not a full-page error — the campaign
  itself already loaded successfully by that point.
- `eslint`/`tsc --noEmit`/`prettier`/`next build` clean; `vitest` 101 passed
  (4 new). **Evidence gap**: the browser-automation tool became unavailable
  partway through this task, so no live screenshot was possible — verified
  instead via the component suite's exact percentage-math assertions and
  reuse of `GRX-EMAIL-009`'s already-live-verified fetch/render scaffolding.
- **Sprint 3 (Email Marketing) is now fully `DONE`.**

## 2026-08-06 — GRX-EMAIL-009: Campaign builder + send frontend

- New `campaigns` dashboard page (`campaigns.view`-gated), plus `/dashboard/campaigns/new`
  and `/dashboard/campaigns/[id]` — the `[id]` route doubles as both the editable-draft
  form and the read-only detail/send view once a campaign leaves `DRAFT`. No backend
  changes: every endpoint needed already existed from `GRX-EMAIL-003`/`004`/`006`/`007`/`008`.
- Recipient targeting (all contacts / a list / a segment), an optional "load content
  from a template" prefill, and a **Test & send** panel: test-send works at any
  status (matching the backend's own lack of a status guard), "Send now" is
  `DRAFT`-only and confirmed via `window.confirm`, then optimistically flips the
  status pill to `SENDING` rather than polling.
- Extracted the HTML re-indenter added ad hoc in `GRX-EMAIL-008` into
  `apps/web/src/lib/format-html.ts` so both the templates and campaigns HTML editors
  share one implementation instead of two copies.
- **Mid-task redesign from a user-supplied reference**: the list started as row-based
  (matching the templates list), then became a card grid with status-filter tabs.
  Scoped down from the reference via explicit choice: no open/click-rate per card
  (real data exists via the `GRX-EMAIL-006` report endpoint, but pulling it in here
  means N+1 fetches and duplicates `GRX-EMAIL-010`'s actual job) and no
  Scheduled/Paused tabs (not real statuses yet — `campaigns.status`'s CHECK
  constraint is `DRAFT`/`SENDING`/`SENT`/`FAILED` only; scheduled sending is the
  still-`BACKLOG` `GRX-SCHED-*` work).
- `eslint`/`tsc --noEmit`/`prettier`/`next build` clean; `vitest` 97 passed (18 new).

## 2026-08-06 — GRX-EMAIL-008: Email templates frontend

- New `templates` dashboard page (`campaigns.view`-gated, under a new "CAMPAIGNS"
  sidebar section) plus two dedicated routes: `/dashboard/templates/new` and
  `/dashboard/templates/[id]/edit`, sharing one `TemplateFormPage` component. Moved
  off an inline-on-the-list-page form after live user feedback found it confusing,
  and to match a two-pane reference (breadcrumb, form + sticky live-preview panel).
- Search (name/subject) and sort (last-updated/name) on the list — pure client-side
  filters over the already-fetched list, no backend change.
- Live HTML preview via a `<iframe sandbox="">` (no `allow-scripts`/
  `allow-same-origin`) — verified with a template containing both a `<style>` block
  and an embedded `<script>` tag: the CSS rendered, the script did not execute.
- **Delete + Duplicate**, added as a scoped-down follow-up to a fuller design
  reference (categories/tags and thumbnail cards deferred — no schema for them yet).
  New `DELETE /templates/{id}`; blocked with a 409 (not a raw 500) when a campaign
  still references the template, since `campaigns.template_id`'s FK has no `ON
  DELETE` behavior. Duplicate has no dedicated endpoint — the create page reads a
  `?duplicateFrom={id}` query param and pre-fills from that template's current
  version.
- **Also fixed**: both this page's and Company Settings' cards were capped at a
  fixed `max-width` (760px / 640px), leaving large empty space on wide viewports —
  changed both to `width: 100%`. Inputs/textareas were initially left capped at a
  readable width inside the now-wider cards; live user feedback on both pages asked
  for full-width fields instead, so that cap was removed too — every field in both
  forms now stretches to the card's full width.
- **Also fixed** (live feedback on the create/edit form): the HTML body textarea
  was too short (`min-height` 260px → 460px), and there was no way to copy the HTML
  or clean up its indentation. Added **Format** (a small dependency-free HTML
  re-indenter — void/self-closing elements don't nest, everything else does) and
  **Copy** (`navigator.clipboard.writeText`) buttons above the HTML body field.
- `apps/api` `pytest` (targeted): 11 passed. `apps/web`: `eslint`/`tsc --noEmit`/
  `prettier`/`next build` clean; `vitest` 79 passed.

## 2026-08-06 — GRX-EMAIL-012: "Test connection" button for SMTP provider setup

- New `POST /integrations/email-providers/test` — connects and authenticates via SMTP
  only (no message sent, nothing persisted), returning 204 on success or 502 with the
  real underlying error on failure. Gated by the existing `integrations.manage`
  permission.
- New "Test connection" button in the connection form, using the current (unsaved)
  field values — lets a user validate credentials before committing to Save.
- **Moved `smtp_sender.py` from `email_delivery` to `integrations/smtp_transport.py`**:
  `MODULE_BOUNDARIES.md` only allows `email_delivery` to depend on `integrations`, not
  the reverse, and this new endpoint belongs to `integrations` (connection setup).
  `email_delivery/services.py` and `api.py` updated to import from the new location.
- Factored the port-465-vs-STARTTLS decision out of `send_email` into a shared
  `_tls_kwargs()` helper, reused by the new `test_connection()` — avoids duplicating
  `GRX-EMAIL-011`'s TLS-mode fix in two places.
- `apps/api` targeted tests (not the full suite, to avoid `GRX-EMAIL-011`'s DB-wipe
  quirk): 40 passed. `vitest`: 62 passed (2 new). `ruff`/`mypy`/`alembic
  check`/`eslint`/`tsc --noEmit`/`prettier`/`next build` clean.
- Live-verified against Postmark's real SMTP relay with bad credentials: the button
  showed a real `535 authentication failed` response in the toast, not a canned
  message.

## 2026-08-06 — GRX-EMAIL-011: Custom SMTP as a second provider + SMTP TLS fixes

- `email_provider_connections` now allows one active connection *per provider*
  instead of one globally — DB-enforced via a new partial unique index
  `(provider) WHERE is_active` (migration `04cce299c2d1`), replacing the old
  non-unique index. `provider` CHECK expanded to `('POSTMARK', 'CUSTOM_SMTP')`.
  Logged as [DEC-GRX-016](DECISIONS.md), fulfilling the "second provider
  needs a new decision" clause from `DEC-GRX-015`.
- New `GET /integrations/email-providers` (plural) lists all connections,
  replacing the old singular GET; `POST /integrations/email-provider` is now
  provider-scoped when deactivating a prior active connection.
- Integrations page rebuilt as a 2-card grid (Postmark, Custom SMTP), each
  independently showing connection status, identity count, and its own
  scoped sender-identity list/add form.
- **Real bug found and fixed**: `test_campaigns.py`'s
  `test_unauthenticated_requests_are_rejected` created a sender-identity
  fixture but never cleaned it up — harmless before this task's new unique
  constraint, a genuine cross-test failure after it went in.
- **Two further real bugs found live-testing against a real SMTP server**
  (the user's own `mail.iitdeveloper.com`, using their real password —
  entered by the user themselves, never typed by the agent): (1)
  `smtp_sender.py`/`email_sender.py` hardcoded STARTTLS (`start_tls=True`)
  unconditionally, so a port-465 (implicit-TLS) server just hung waiting for
  a plaintext banner that never comes — fixed by selecting `use_tls` vs
  `start_tls` based on `smtp_port == 465`. (2) `ssl.SSLCertVerificationError`
  (e.g. an expired server certificate) is an `OSError`, not an
  `aiosmtplib.SMTPException`, so it escaped `EmailSendError`'s except clause
  and surfaced as an unhandled 500 instead of the intended 502 "Test send
  failed" — fixed by also catching `OSError`. The user's own server has an
  expired certificate, an external blocker on their end unrelated to this
  fix.
- `apps/api` `pytest`: 152 passed, 3 skipped. `apps/worker` `pytest`: 12
  passed. `ruff`/`mypy`/`alembic check` clean on both; `eslint`/`tsc
  --noEmit`/`prettier`/`vitest` (60 passed)/`next build` clean on
  `apps/web`.

## 2026-08-05 — GRX-EMAIL-007: provider connection + sender identity frontend

- New `apps/web/src/app/(dashboard)/dashboard/integrations/` page: a provider
  connection form (`POST /integrations/email-provider`) with a one-time
  webhook-credentials reveal banner, a read-only connection summary once one
  exists, and a sender-identity list + add form
  (`POST /integrations/sender-identities`) with a manual verification-status
  dropdown (`PATCH .../status`) — verification is a manual admin action in
  Sprint 3, not automated Postmark polling, per `SPRINT_03`'s scope.
- New "Integrations" sidebar item gated by `requiresPermission:
  "integrations.manage"`, matching every other SETTINGS item's pattern.
- **Real bug found and fixed during live verification, not caught by the
  component tests as first written**: the connection/sender-identity GET
  routes are themselves `integrations.manage`-gated on the backend (unlike
  e.g. `/users`, readable by any authenticated user), so the page's original
  load effect — which fetched `/auth/me` and both GETs in one `Promise.all`
  — let a real non-Super-Admin's 403s on those GETs reject the whole
  `Promise.all` and hit the generic load-error catch before the permission
  check was ever reached. The intended "You don't have access to configure
  integrations." message never actually rendered; a live browser check
  (login as a throwaway Admin, not Super Admin) surfaced a misleading
  "Could not load integration settings." instead. Fixed by checking
  `me.permissions` first and only issuing the gated fetches when access is
  confirmed; updated the access-denied test to reject those two calls with a
  real `ApiError(403, ...)` instead of resolving them, so this exact
  regression class is now caught by the suite — a reminder that a mocked
  component test can hide a bug if the mock doesn't reproduce the real
  backend's per-endpoint permission gating.
- `eslint`/`tsc --noEmit`/`prettier --check` clean. `vitest`: 59 passed (5
  new). `next build` clean, `/dashboard/integrations` route registered.
- Live-verified against Compose: created a real connection as Super Admin
  and captured the real one-time webhook credentials in the UI, added a
  sender identity, flipped its verification status to VERIFIED; created a
  throwaway Admin user directly in the database for the negative path —
  confirmed no "Integrations" sidebar item and, after the fix above, the
  correct access-denied message on direct navigation. Cleaned up the
  smoke-test connection/identity rows; the throwaway Admin account was
  disabled rather than deleted (deleting it would have violated
  `audit_logs`' insert-only invariant, since its login had already written
  an audit row referencing it).
- Note: this commit landed directly on `main` — the user merged the prior
  `feature/FRONTEND/GRX-WEB-002` branch via PR earlier in the session, so
  the branch-coordination note from `GRX-EMAIL-005`/`006`'s entries no
  longer applies going forward. Commit `fa0d924`

## 2026-08-05 — GRX-EMAIL-006: campaign report/analytics endpoint

- **Corrected the tracker's own planning-time file location**: the `MASTER_TASK_TRACKER.md`
  row said this task would extend `campaigns`, but `MODULE_BOUNDARIES.md` names a
  dedicated `analytics` module for exactly this ("read-side aggregation/reporting over
  campaigns...") and `campaigns`' own allowed-dependency list doesn't include
  `email_delivery`. Built a new `growixa_api.analytics` module instead — no models or
  migration, since `SPRINT_03_EMAIL_CAMPAIGN.md` explicitly excludes a pre-aggregated
  `analytics_events` table in favor of computing the report live.
- `GET /campaigns/{id}/report` mounted under the existing `/campaigns` prefix (same
  multi-module-same-prefix pattern `email_delivery` already uses), gated by the
  existing `campaigns.view` permission — `RBAC.md`'s own rationale for that grant
  already named this exact use case.
- Metric definitions: `sent` from `campaign_recipients.status` (stable — never touched
  by webhook handling, so it reflects the original send outcome even after a later
  bounce); `delivered`/`bounced`/`complained` from `message_deliveries.status` (a
  single mutable pointer, current terminal state); `opened`/`clicked` from **distinct**
  deliveries with a matching `email_events` row, not raw event rows — `email_events` is
  insert-only, so a redelivered webhook notification is a new row and counting rows
  directly would let one recipient's repeat notification inflate the number.
- `pytest`: 147 passed, 3 skipped (5 new: counts match a hand-built fixture incl. a
  duplicate-event no-double-count check, `campaigns.view`-only role reads successfully,
  a role lacking it gets 403, unauthenticated 401, unknown campaign 404). `alembic
  check` clean (no migration). `ruff`/`mypy` clean.
- Live-verified against Compose: an unsent campaign's report was all zeros; after a
  real send (same `535` SMTP evidence-gap boundary as `GRX-EMAIL-004`/`005`) the send
  genuinely failed, so `sent` correctly stayed `0` rather than a fabricated success;
  separately simulated a Postmark-assigned message ID and fired real
  `Delivery`/`Open`/`Open`/`Click` webhook events, after which the report showed
  `delivered=1, opened=1, clicked=1` — the duplicate `Open` did not double-count.
  Cleaned up all smoke-test rows afterward. Commit `ba12931`

## 2026-08-05 — GRX-EMAIL-005: Postmark webhook receiver + unsubscribe handling

- **Real gap found and fixed**: `THREAT_MODEL.md`'s `T14` called for webhook Basic Auth
  credentials "stored alongside the provider connection, encrypted at rest", but
  `email_provider_connections` never got those columns when Sprint 3 was planned.
  Migration `f5ecaa79863b` adds `webhook_username`/`webhook_password_encrypted`
  (nullable, fails closed if unset), auto-generated at connection-creation time and
  Fernet-encrypted like the SMTP password; the plaintext webhook password is returned
  exactly once, in the create-connection response, never persisted or retrievable
  again. Same migration adds `email_events` (insert-only) and `unsubscribe_events`.
- `POST /webhooks/postmark` (public, HTTP Basic Auth against the active connection's
  own credentials, constant-time comparison) maps Postmark's `RecordType` to our
  `event_type`, matches the delivery by `provider_message_id`, no-ops silently on an
  unmatched `MessageID` (Postmark expects 200 either way), and auto-suppresses on
  `BOUNCED`/`COMPLAINED` — wiring up `suppression_entries.reason` values that have
  existed since `GRX-CONTACT-005` but were never written until now.
- `GET /unsubscribe/{campaign_recipient_id}` is fully public, identified only by the
  unguessable UUID (same shape as the invitation-accept token); records an
  `unsubscribe_events` row and suppresses the address with no `actor_id` (new
  `_upsert_suppression` helper, bypassing `suppress_email`'s actor-requiring wrapper).
- The worker now appends a per-recipient unsubscribe link to every real send's
  `body_html`/`body_text` (plain footer append, no merge-tag infrastructure yet); new
  `api_public_url` worker setting.
- `apps/api` `pytest`: 142 passed, 3 skipped (8 new: webhook no-credentials/wrong-
  credentials rejection with zero `email_events` written, a valid `Delivery` event,
  auto-suppression on `Bounce`, unmatched-`MessageID` no-op, valid unsubscribe,
  unknown-id 404). `apps/worker` `pytest`: 9 passed (1 new: unsubscribe URL present in
  the sent body). `alembic check` clean; `ruff`/`mypy` clean on both apps.
- **Documented evidence gap (DEC-GRX-011 / SPRINT_03's pre-approved fallback), same
  class as `GRX-EMAIL-004`'s**: no live Postmark account is available, so the exact
  webhook JSON payload shape per `RecordType` is unverified. `PostmarkWebhookPayload`
  is deliberately permissive (`extra="allow"`), and the full raw payload is preserved
  in `email_events.metadata` for future reconciliation.
- Live-verified against Compose: captured one-time webhook credentials from a real
  connection-create call; confirmed no-auth/wrong-auth both 401 before touching
  `email_events`; sent a real campaign (same `535` SMTP auth-rejection evidence-gap
  boundary as `GRX-EMAIL-004`), manually set `provider_message_id` to simulate a
  Postmark-assigned ID (the real send never receives one), then fired real `Delivery`
  and `Bounce` webhook events and clicked the real unsubscribe link — all updated the
  database exactly as expected. Cleaned up all smoke-test rows afterward. Commit
  `9dbe9ee`

## 2026-08-04 — GRX-EMAIL-004: send pipeline (worker + email_delivery)

- **Real gap found and fixed**: `usage_records` was documented (`DATA_MODEL.md`,
  `DEC-GRX-007`) as already existing since Sprint 1, but no migration or model for it
  existed anywhere in the codebase. Created it now (new `growixa_api.usage` module)
  since this task's own acceptance criterion — `usage_records` gets its first real
  write — needed the table to actually exist.
- Per an explicit decision this session, `apps/worker` gained its own minimal
  SQLAlchemy/asyncpg data layer — models for exactly the tables `send_campaign` reads
  or writes (including a duplicated segment-rule evaluator) — rather than depending on
  `growixa_api` as a library, keeping the two apps independently deployable per
  `SYSTEM_ARCHITECTURE.md`.
- New `growixa_api.email_delivery` module: `POST /campaigns/{id}/test-send` sends
  synchronously and inline (explicitly fine — it touches no campaign/recipient/delivery
  state); `POST /campaigns/{id}/send` flips the campaign to `SENDING` and enqueues
  `grx.email_delivery.send_campaign`, never sending inline. New `campaigns.send`
  permission (Super Admin/Admin/Marketing Manager only, Content Creator excluded).
- The worker's job handler resolves recipients per targeting type (including live
  `DYNAMIC` segment rule evaluation), excludes suppressed or consent-withdrawn
  addresses (`DEC-GRX-008`), freezes one `campaign_versions` snapshot, sends via real
  `aiosmtplib`, and writes `message_deliveries`/`delivery_attempts`/`usage_records`.
  Idempotent via a `campaign_versions`-existence check rather than a separate key store.
- Also fixed a latent `apps/worker` test-config gap found while debugging the new
  tests: missing `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope
  = "session"` (present in `apps/api` since GRX-TEST-001, never added to the worker)
  was giving each test a fresh event loop, breaking the worker's cached DB engine
  across tests.
- `apps/api` `pytest`: 135 passed, 3 skipped (8 new). `apps/worker` `pytest`: 8 passed
  (new). `alembic check` clean on both.
- **Documented evidence gap (DEC-GRX-011 / SPRINT_03's pre-approved fallback)**: no
  live Postmark account is available in this environment. Live-verified everything up
  to the credential boundary — a real TCP/TLS + STARTTLS handshake against Postmark's
  actual relay, rejected with a genuine `535 5.7.8 authentication failed` — proving the
  SMTP path is real, not mocked. The worker correctly caught the failure, still wrote
  the `campaign_versions` snapshot and a `usage_records` row (`quantity=0`), and left
  the campaign `SENT` rather than crashing. Closes automatically once a real Postmark
  server token is configured. Commit `aa2bdb4`

## 2026-08-03 — GRX-EMAIL-003: campaigns CRUD + targeting

- New `growixa_api.campaigns` module. Migration `d7fa144e5c60` creates all three tables
  named in this task — `campaigns`, `campaign_versions`, `campaign_recipients` — since
  `DATABASE_SCHEMA.md` groups them in one migration step, but only `campaigns` gets
  CRUD here; the other two are schema-only until `GRX-EMAIL-004`'s send pipeline
  populates them (same schema-now/write-path-later split as `GRX-AUDIT-001`→`002`).
- Recipient targeting (`SEGMENT`/`LIST`/`ALL_CONTACTS`, exactly one of
  `recipient_segment_id`/`recipient_list_id` set per type) is validated at the service
  layer, calling directly into `integrations`/`templates`/`contacts`' own repository
  functions to check referenced IDs exist, per `MODULE_BOUNDARIES.md`'s cross-module
  call convention. No new permissions — reused `campaigns.manage`/`campaigns.view`.
- Draft editing uses `exclude_unset` so a `PATCH` can explicitly null a field (e.g.
  clearing `recipient_segment_id` when switching to `ALL_CONTACTS`) — the first module
  needing that over the simpler "`None` means don't touch" convention used elsewhere.
  Editing is blocked (409) once `status` leaves `DRAFT`.
- `pytest` 127 passed, 3 skipped (10 new integration tests); `alembic check` clean.
  Live-verified against Compose: created and edited a campaign via curl (targeting
  switched cleanly, old segment reference cleared), an invalid both-set payload got
  400, a throwaway Viewer got 403. Commit `52fa336`

## 2026-08-03 — GRX-EMAIL-002: email templates + versioning

- New `growixa_api.templates` module: `EmailTemplate`/`EmailTemplateVersion` models,
  gated on `campaigns.manage` (create/edit) and `campaigns.view` (read) per
  `RBAC.md`'s Slice 3 matrix. Migration `d36211c53aed` seeds both permission codes —
  neither existed yet, since Slice 3 planning deferred seeding them to whichever task
  first needed them; `campaigns.send` stays deferred to `GRX-EMAIL-004`.
- `POST /templates` creates a template and its first version (version 1) together, since
  a template can't exist without content. `POST /templates/{id}/versions` appends
  version `max+1`; the previous version's row is never mutated, matching
  `ConsentRecord`'s insert-only pattern — "current" is derived as the highest
  `version_number`, not a mutable pointer.
- `pytest` 117 passed, 3 skipped (6 new integration tests); `alembic check` clean.
  Live-verified against Compose: created and edited a template via curl (version
  1 → 2, both rows intact), a throwaway Viewer got 403 on read. Commit `1dac3ff`

## 2026-08-03 — GRX-EMAIL-001: email provider connection + sender identity

- First Sprint 3 task. New `growixa_api.integrations` module (named per
  `MODULE_BOUNDARIES.md` — the designated home for all future provider connections, not
  email-specific) with `EmailProviderConnection`/`SenderIdentity` models and CRUD routes
  gated on a new `integrations.manage` permission, granted to Super Admin only — the
  project's first Admin-excluded permission.
- Added Fernet symmetric encryption (`auth/encryption.py`, a new `encryption_key`
  setting) for SMTP credentials at rest per `DEC-GRX-009`; `EmailProviderConnectionOut`
  never returns the password or its encrypted form. Creating a new connection
  deactivates any existing active one instead of mutating it in place.
- Migration `393c4222c8af` adds `email_provider_connections`/`sender_identities` plus
  the partial `(is_active) WHERE is_active` index, and seeds `integrations.manage`.
- **Real bug found and fixed**: the sender-identity status-update route hit
  `MissingGreenlet` on `updated_at` after commit — `onupdate=func.now()` columns expire
  on UPDATE and need an explicit `session.refresh()` before serialization, the same
  issue and fix already documented in `contacts/services.py`.
- `pytest` 111 passed, 3 skipped (7 new integration tests); `alembic check` clean;
  rebuilt the `api` container for the new `cryptography` dependency. Live-verified
  against Compose: Super Admin created a connection + sender identity via curl with the
  password never appearing in any response, and a throwaway Admin-role user got 403 on
  the same routes. Commit `f545ad0`

## 2026-08-01 — Sprint 3 (Email Marketing) planning

- Slice 3 (First Email Campaign) needed one prerequisite Sprint 1/2 never did:
  [OQ-002](OPEN_QUESTIONS.md) (email provider) had to be resolved before planning could
  start at all. Logged as [DEC-GRX-015](DECISIONS.md): **Postmark, integrated via its
  SMTP relay endpoint** — the user initially picked Postmark from a shortlist, then
  asked about using their own SMTP server instead; resolved by using Postmark's own
  SMTP relay (API token as the password) rather than a generic personal-mailbox SMTP
  server, which keeps Postmark's bounce/open/click webhook tracking that a generic
  mailbox can't provide while still satisfying `MVP_SCOPE.md`'s "SMTP support" bullet.
- Data model: added Slice 3 entities in full field-level detail —
  `email_provider_connections`, `sender_identities`, `email_templates`/
  `email_template_versions`, `campaigns`/`campaign_versions`, `campaign_recipients`,
  `message_deliveries`/`delivery_attempts`, `email_events`, `unsubscribe_events` — to
  `DATA_MODEL.md`, `DATABASE_SCHEMA.md`, and `ERD.md`. `campaign_schedules` (Slice 4)
  and generic multi-provider `webhook_*`/`analytics_events` tables stay explicitly
  deferred, with reasons recorded rather than silently dropped.
- RBAC: added `integrations.manage`, `campaigns.manage`, `campaigns.send`,
  `campaigns.view`. Unlike Slice 2's single manage/view pair, Slice 3 splits drafting
  from sending and carves out provider credentials separately — both splits were
  already implied by RBAC.md's own Sprint-1-era Roles table (Content Creator's "no
  send/publish authority," Super Admin's "provider credentials" scope distinct from
  Admin's), not new invention. `integrations.manage` is the project's first
  Admin-excluded permission.
- Threat model: added a Slice 3 addendum (T13–T19) covering SMTP credential handling,
  forged webhook events, suppression-bypass, personalization-variable injection,
  recipient data exposure, bulk-send abuse, and SSRF via the provider host — the first
  threat-model update since Sprint 1's baseline.
- Wrote `SPRINT_03_EMAIL_CAMPAIGN.md` (included/excluded scope, acceptance criteria,
  definition of done) and added a Slice 3 readiness-gate table to
  `DEVELOPMENT_READINESS.md`, following the exact structure Slice 1/2 established.
- Added ten tasks to `MASTER_TASK_TRACKER.md` (`GRX-EMAIL-001`–`010`): provider
  connection + sender identity, templates, campaigns CRUD, the send pipeline (worker +
  `email_delivery`), the Postmark webhook receiver, a campaign report endpoint, and four
  matching frontend tasks. `GRX-EMAIL-001` is `READY`; the rest are `BACKLOG`, chained
  sequentially per this project's one-task-at-a-time practice.
- Documentation only — no code in this entry. Commit `b870849`.

## 2026-08-01 — GRX-FOUND-009: Collapsible/responsive sidebar navigation

- Ad hoc, user-requested — not part of any sprint plan. Two parts, both requested in
  the same conversation.
- **Whole-sidebar hamburger toggle.** New `DashboardShell` client component (split out
  of `layout.tsx`, which stays a server component for the auth check) owns one
  `sidebarOpen` boolean and renders a hamburger button. On desktop, closing it
  collapses the sidebar to zero width (content reflows — no per-item icons exist yet,
  so this is a full hide, not an icon rail). On mobile (new `768px` breakpoint, the
  first in this app), the sidebar is an off-canvas overlay: hidden by
  `translateX(-100%)` by default, slid into view with a dismissible backdrop when
  open. One boolean, driven entirely by CSS media queries — no JS viewport branching
  needed for the toggle itself. A `useEffect` on `usePathname()` auto-closes the
  drawer after navigating on mobile (checked via `window.matchMedia`), so it doesn't
  cover the new page; desktop navigation is unaffected.
- **Per-section accordion**, requested as an immediate follow-up referencing a
  third-party product's sidebar (expandable "Market"/"Automation" headings): each nav
  section (OVERVIEW/AUDIENCE/SETTINGS) is now its own independent collapse, defaulting
  to expanded. Complementary to the whole-sidebar toggle, not a replacement — collapsing
  one section doesn't touch the others or the sidebar's own open state.
- Added a `window.matchMedia` polyfill to `vitest.setup.ts` (jsdom has none) — exposed
  by this task, now available to any future responsive-behavior test.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 54 passed (4 new);
  `test:e2e` (Playwright, 4 tests) unaffected. Live-verified at both `desktop` and
  `mobile` (375×812) presets against the rebuilt `web` container: hamburger
  collapse/expand and mobile drawer/backdrop/auto-close-on-navigate all confirmed;
  collapsing "AUDIENCE" hid its 5 items while "OVERVIEW"/"SETTINGS" stayed unaffected.
  Commit `ef877c1`.

## 2026-07-31 — GRX-AUDIT-002: Audit log viewing (API + frontend)

- Added `GET /audit` (`apps/api/src/growixa_api/audit/api.py`, new), gated on `audit.view`,
  with optional `entity_type`/`actor_user_id` filters reusing `GRX-AUDIT-001`'s existing
  `list_events` service function — no new query logic needed on the backend.
- **Real bug found by the test suite, not manual testing**: `AuditLogOut.ip_address` was
  typed `str | None`, but Postgres `INET` comes back from asyncpg as an
  `ipaddress.IPv4Address` object. Every row with a real IP address 500'd on response
  serialization until a `field_validator` stringified it — caught immediately because the
  local dev database already had a row with a real IP from earlier session traffic.
- Built `AuditPage` (`/dashboard/audit`): read-only list (action, resolved actor email,
  timestamp, non-empty metadata inline, entity_type badge), with a client-side
  entity_type filter dropdown built from the already-loaded events (no re-fetch per
  filter change). Actor emails resolved via `GET /users`, gated `users.manage` rather
  than `audit.view` — safe today since both permissions have identical Super
  Admin/Admin-only grants, same reasoning as `roles/api.py`'s existing list endpoint.
- Added "Audit Log" to the sidebar's SETTINGS section (gated `audit.view`) and a
  page-title entry.
- `ruff`/`mypy` clean (the handful of pre-existing mypy errors elsewhere were confirmed
  unrelated via `git stash` diff); `pytest` 107 passed, 3 skipped (3 new: list, filter,
  403 for a non-`audit.view` role); `alembic check` → no drift (no schema changes —
  `GRX-AUDIT-001`'s table already fit). `eslint`/`tsc --noEmit`/`prettier --check` clean;
  `vitest` 54 passed (4 new).
- Live-verified against rebuilt Compose containers: real `user.login`/`user.login_failed`
  events rendered with resolved actor emails; created a contact and confirmed a new
  `contact.created` event appeared newest-first; filtered by entity_type to `contact` and
  confirmed only that row remained; confirmed a fresh Analyst (no `audit.view`) sees no
  "Audit Log" nav item and gets an access-denied message on direct navigation.
- Also recreated the `admin@growixa.local` smoke-test account, which running the full
  `pytest` suite wiped again via `test_migrations.py`'s known table-drop side effect
  (documented in this file's `GRX-CONTACT-001`/`002` entries) — not a regression from
  this task, just a recurring cost of running the full suite against the shared dev DB.
- This closes `GRX-AUDIT-002` and, with it, the last open gap from `GRX-DOC-003`'s
  feature audit — no `BACKLOG` or `READY` tasks remain in the tracker. Commit
  `347a801`.

## 2026-07-31 — GRX-DOC-003: Sprint 1 documentation + handoff update (closes Sprint 1)

- Created `FEATURE_STATUS_MATRIX.md` (new): per-feature implementation status, checked
  against actual code rather than trusted from tracker claims alone.
- Found a real gap while doing that check: `GRX-FEAT-027` (Audit Logs) only has the
  write path — `growixa_api/audit/` has no `api.py`, so there's no `GET` endpoint and no
  frontend page, meaning `audit.view` is a permission code nothing checks. Sprint 1's
  acceptance criterion that audit logs be "visible to users with `audit.view`" was never
  actually met. Filed as new task `GRX-AUDIT-002` (`BACKLOG`) rather than left silent.
- Also confirmed Notifications/Usage Metering/Integrations/Admin Portal — all tagged
  "Slice 1" in `FEATURE_CATALOG.md` — were never in Sprint 1's actual task list
  (`SPRINT_01_FOUNDATION.md`'s "Included" section) and remain `NOT_STARTED`; the
  catalog's slice tags reflect the target release, not delivery.
- Updated `PROJECT_STATUS.md` to reference the new matrix and record Sprint 1 as fully
  `DONE` with that one gap tracked, not hidden.
- This closes Sprint 1 for real (all `GRX-FOUND-*`/`GRX-AUTH-*`/`GRX-USER-*`/`GRX-RBAC-*`/
  `GRX-COMPANY-*`/`GRX-AUDIT-001`/`GRX-TEST-*`/`GRX-DEVOPS-001`/`GRX-DOC-003` are `DONE`).
  Commit `2cc3acc`.

## 2026-07-31 — GRX-DEVOPS-001 confirmed DONE

- The user pushed `main` to GitHub and confirmed the CI workflow (`.github/workflows/ci.yml`,
  built in this task's original commit `7ff54dc`) ran green. Moved `GRX-DEVOPS-001` from
  `IN_REVIEW` to `DONE` in the tracker; this unblocks `GRX-DOC-003` (Sprint 1 documentation
  + handoff update), now `READY`. No code changes in this entry — documentation only.

## 2026-07-31 — GRX-CONTACT-009: Consent/suppression frontend (closes Sprint 2)

- Extended `ContactsPage`'s detail panel with a lazy-loaded (on row expand) consent
  history list (`GET /contacts/{id}/consent`, newest-first) and, for managers, an
  inline record-consent form (channel/status selects + optional source input)
  posting to `POST /contacts/{id}/consent`.
- Built `SuppressionPage` (`/dashboard/contacts/suppression`): a list of all
  suppression entries (email, linked contact or "No matching contact", reason
  badge, timestamp) and, for managers, a "+ Suppress an email" form (email, reason
  select, optional contact picker sourced from `GET /contacts`) posting to `POST
  /contacts/suppression`. Since the backend has no unsuppress endpoint by design
  (`GRX-CONTACT-005`), the UI never offers a remove control.
- Re-suppressing an already-suppressed email is handled by matching the POST
  response's `id` against existing state and replacing in place rather than
  appending, mirroring the backend's upsert-on-email semantics — covered by a
  dedicated test and confirmed live.
- Added "Suppression" to the sidebar's AUDIENCE section and a page-title entry.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 46 passed (7 new: 2
  consent-history/record tests on `ContactsPage`, 5 on `SuppressionPage`).
- Live-verified against the rebuilt dev server: recorded GRANTED then WITHDRAWN
  consent for a contact and confirmed newest-first ordering; suppressed an email
  with a linked contact (its Contacts-page row correctly flipped to "Suppressed"),
  re-suppressed the same email with a different reason and confirmed the entry
  updated in place (still exactly one row); confirmed a fresh Analyst sees both the
  consent history and suppression list read-only with no record-consent form and no
  "+ Suppress an email" button.
- This closes GRX-CONTACT-009 — **all of Sprint 2 (GRX-CONTACT-001 through 009) is
  now DONE.** Commit `81332b5`.

## 2026-07-31 — GRX-CONTACT-008: CSV import frontend

- Built `ImportsPage` (`/dashboard/contacts/imports`): a file picker reads the CSV
  header row client-side, auto-guesses common column→field mappings
  (email/first_name/last_name/phone/source), and renders a target select per column
  (including `custom_field:<key>` options from `GET /contacts/custom-fields`).
  Submitting builds a `column_mapping` JSON string and multipart-POSTs to `POST
  /contacts/imports`.
- This was the frontend's first file upload, which surfaced that `apiFetch`
  unconditionally set `Content-Type: application/json` — fixed by skipping that
  header when the body is a `FormData` instance, letting the browser set its own
  multipart boundary. Added `api-client.test.ts` (new, 2 tests) for this
  previously-uncovered shared utility.
- Below the upload form, an import-history list shows filename/status/counts per
  past import, each expandable via "View rows" into per-row email/status/
  error_message detail. The upload card is omitted entirely (not shown disabled) for
  non-managers.
- Added "Imports" to the sidebar's AUDIENCE section and a page-title entry.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 39 passed (7 new).
- Live verification note: the browser-automation tool cannot drive a native file
  picker dialog, so the "select a file" step itself couldn't be exercised through
  the browser. Instead, uploaded a real 3-row CSV via `curl` multipart (identical
  wire format to `fetch`+`FormData`) and confirmed the resulting history entry,
  counts, and row-level detail all rendered correctly in the browser from real
  backend data; confirmed the imported contacts appeared correctly on the Contacts
  page; confirmed a fresh Analyst sees only the history card, no upload form.
- This closes GRX-CONTACT-008. `GRX-CONTACT-009` (consent/suppression frontend) is
  the last remaining Sprint 2 task. Commit `7796f93`.

## 2026-07-31 — GRX-CONTACT-007: Tags/lists/segments frontend

- Extended `ContactsPage`'s detail panel with tag management: removable chips (an
  `×` button calling `DELETE /contacts/{id}/tags/{tag_id}`, resolving the tag's id
  from a fetched `/contacts/tags` list since `ContactOut.tags` only carries names), a
  select to attach an existing tag, and an inline "+ New tag" form that creates a tag
  and attaches it to the contact in one step.
- Built `ListsPage` (`/dashboard/contacts/lists`): create a list, and per-list
  add/remove-by-contact-picker controls. There is deliberately no member-browsing UI
  — the backend only ever exposed `member_count` for `contact_lists`, not a
  members-list endpoint (unlike segments), and adding one was judged out of this
  task's frontend-only scope.
- Built `SegmentsPage` (`/dashboard/contacts/segments`): a rule builder (field,
  operator, value per row — operators filtered to match each field's allowed set,
  with a `custom_field:<key>` sub-input when "Custom field" is selected), a segment
  list with type/member-count badges and a rule-summary, and "View members" backed
  by the existing `GET /contacts/segments/{id}/members`.
- Refactored the per-page `contacts-page.module.css` into a shared
  `shared.module.css` so contacts/lists/segments reuse one set of card, form, row,
  and badge styles instead of duplicating them three times.
- Added "Lists" and "Segments" to the sidebar's AUDIENCE section (gated
  `contacts.view`) and their page-title entries.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 32 passed (13 new).
- Live-verified against the rebuilt dev server: created a tag inline and attached it
  to a contact, detached and reattached it via the dropdown; created a list and
  added a contact (member count 0→1); created a DYNAMIC segment on `tag equals VIP`
  and confirmed it matched the tagged contact, with "View members" showing the right
  email; confirmed an Analyst sees all three pages' data with no write controls.
- This closes GRX-CONTACT-007. `GRX-CONTACT-008` (CSV import frontend) and
  `GRX-CONTACT-009` (consent/suppression frontend) remain `READY`. Commit `262d28a`.

## 2026-07-31 — GRX-CONTACT-006: Contacts frontend

- Built `ContactsPage` (`apps/web/src/app/dashboard/contacts/`): a list of contacts
  with an inline "+ Add contact" create form and an expandable per-row detail/edit
  panel. Page visibility is gated on `contacts.view`; the create form, edit fields,
  and archive/activate button are gated on `contacts.manage` — a view-only user sees
  a "You have view-only access to contacts." note in place of the edit form.
- The detail panel shows created/updated timestamps and read-only tag chips/custom
  fields (assigning tags or editing custom-field values through the UI is
  `GRX-CONTACT-007`'s scope, not this task's) plus the contact's `is_suppressed` flag.
- Added a new "AUDIENCE" sidebar section with a "Contacts" nav link (gated on
  `contacts.view` alone — every role holding `contacts.manage` also holds
  `contacts.view` per RBAC.md's role matrix, so one permission check covers both) and
  a page-title entry.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 19 passed (6 new
  component tests: list rendering, access-denied, view-only hides write controls,
  create, edit, archive).
- Live-verified against the rebuilt dev server: created a contact as Super Admin,
  edited its name inline, archived then re-activated it (toast confirmation each
  time), then logged in as a fresh Analyst and confirmed the same contact was visible
  with no write controls.
- This is the first of Sprint 2's four remaining frontend tasks.
  `GRX-CONTACT-007`/`008`/`009` (tags/lists/segments, CSV import, and
  consent/suppression frontends) all had their only frontend dependency
  (`GRX-CONTACT-006`) satisfied and were flipped to `READY`. Commit `07550c0`.

## 2026-07-31 — GRX-CONTACT-005: Consent & suppression

- Added `consent_records` (insert-only) and `suppression_entries` (upsert-on-email)
  tables (migration `97642610fb46`), matching DATA_MODEL.md's field-level spec exactly.
- `POST`/`GET /contacts/{id}/consent` record and list a contact's consent history per
  channel (`EMAIL`/`SMS`), newest-first. Current status per channel is derived as "most
  recent row" — there is no separate mutable current-status column.
- `POST /contacts/suppression` upserts on the unique `email` index: suppressing an
  already-suppressed email updates `reason`/`suppressed_at` in place (same row, no
  duplicate) rather than creating a second entry. `contact_id` is optional — an
  address can be suppressed with no matching contact (e.g. a hard bounce) — but is
  validated to exist when provided.
- Per the sprint's explicit acceptance criterion ("visibly flagged as suppressed
  wherever contacts are shown"), `ContactOut` gained `is_suppressed: bool`. This
  widened the internal `ContactSnapshot` tuple across every contacts service function
  and API call site to carry the flag through.
- No new permissions — suppression and consent recording were already scoped under
  `contacts.manage` (and viewing under `contacts.view`) in RBAC.md from Slice 2
  planning.
- `ruff`/`mypy` clean; `pytest` 101 passed, 3 skipped (8 new tests); `alembic check` →
  no drift.
- Live-verified against rebuilt Compose containers: recorded GRANTED then WITHDRAWN
  consent for a contact and confirmed the history came back newest-first; suppressed a
  contact's email and confirmed `is_suppressed` flipped true; re-suppressed the same
  email with a different reason and confirmed it updated the existing row instead of
  duplicating; suppressed an email with no matching contact; confirmed an unknown
  `contact_id` 404s.
- This closes out Sprint 2's entire backend slice (contacts, tags, lists, segments,
  CSV import, consent/suppression). `GRX-CONTACT-006` (contacts frontend) is next
  `READY`. Commit `30b5fc2`.

## 2026-07-31 — GRX-CONTACT-004: CSV contact import

- Added `contact_imports`/`contact_import_rows` tables (migration `b11cffc2cbcf`).
  `POST /contacts/imports` takes a multipart upload (`file` + a `column_mapping` JSON
  string mapping CSV headers to `email`/`first_name`/`last_name`/`phone`/`source`/
  `custom_field:<key>`), processes it synchronously, and returns imported/updated/
  skipped/error counts plus per-row detail via `GET /contacts/imports/{id}/rows`.
- Row outcomes: a fully blank row is `SKIPPED`; a row with no email value is `ERROR`;
  an email that already exists reuses `create_or_update_contact`'s dedup logic and is
  marked `UPDATED`, a new email `IMPORTED`. A `column_mapping` missing an `email`
  target, or naming an unknown `custom_field:<key>`, returns 400 before any row runs.
- `GET /contacts/imports` and `GET /contacts/imports/{id}` expose import history. No
  new permissions — reuses `contacts.manage`/`contacts.view`.
- Added the `python-multipart` dependency (first use of FastAPI file/form uploads in
  this codebase) and extended ruff's `flake8-bugbear` immutable-calls allowlist with
  `fastapi.File`/`fastapi.Form`.
- `ruff`/`mypy` clean; `pytest` 93 passed, 3 skipped (8 new tests); `alembic check` →
  no drift.
- Live-verified against rebuilt Compose containers: a 3-row CSV (one new email, one
  pre-existing email, one blank email) mapped to `email`/`first_name`/
  `custom_field:plan` produced `imported_count=1`, `updated_count=1`, `error_count=1`;
  the new contact carried its custom field and the existing contact's first name and
  custom field were both updated; a mapping without an `email` target returned 400.
- This closes out Sprint 2's backend CSV import slice. `GRX-CONTACT-005` (consent &
  suppression) is next `READY`. Commit `52fb417`.

## 2026-07-31 — GRX-CONTACT-003: Segments

- Added `segments`/`segment_rules`/`segment_members` tables (migration `18cf808f2b87`)
  and a rule evaluator supporting `status`/`email`/`source` (equals; email also
  supports contains), `tag` (equals), `created_at` (before/after), and
  `custom_field:<key>` (equals/contains) — all AND-combined only, per the Slice 2
  scope decision (no OR/grouping).
- `consent_status` was named as an example field during earlier Slice 2 planning but
  isn't implemented yet, since `consent_records` doesn't exist until `GRX-CONTACT-005`
  — using it now correctly returns 400 as an unsupported field rather than silently
  matching nothing.
- `POST /contacts/segments` validates every rule up front (unknown field, unsupported
  operator for that field, unknown custom-field key, or an unparseable `created_at`
  date all return 400) before creating anything.
- `DYNAMIC` segments compute membership live on every read; `SAVED` segments evaluate
  once at creation and freeze into `segment_members`. Verified live: tagging a new
  contact after creating both segment types changed the `DYNAMIC` segment's count but
  left the `SAVED` one unchanged.
- `ruff`/`mypy` clean; `pytest` 85 passed, 3 skipped (93% coverage, 9 new tests);
  `alembic check` → no drift (needed `index=True` added to `SegmentRule.segment_id` in
  the ORM model to match the migration's explicit index — `alembic check` caught the
  mismatch itself).
- This closes out the backend half of Slice 2's core contact-organization features
  (contacts, tags, lists, segments). `GRX-CONTACT-004` (CSV import) is next `READY`.
  Commit `a725e0e`.

## 2026-07-30 — GRX-CONTACT-002: Tags & lists

- Added `tags`/`contact_tags` and `contact_lists`/`contact_list_members` tables (migration
  `788ff9dd33db`) and their API: `GET`/`POST /contacts/tags`, attach/detach via
  `POST`/`DELETE /contacts/{id}/tags[/{tag_id}]`, `GET`/`POST /contacts/lists`, `GET
  /contacts/lists/{id}`, and member add/remove via `POST`/`DELETE
  /contacts/lists/{id}/members[/{contact_id}]`.
- `ContactOut` now includes `tags: list[str]`; `ContactListOut` includes a live
  `member_count` computed on every read rather than stored and risking drift.
- Tag/list changes emit `contact.tagged`/`contact.list_added` audit events, continuing to
  reuse `audit_logs` rather than a new activity table.
- No RBAC changes needed — `contacts.manage`/`contacts.view` already covered tag/list
  management per this session's Slice 2 planning pass.
- `ruff`/`mypy` clean; `pytest` 76 passed, 3 skipped (94% coverage, 7 new tests); `alembic
  check` → no drift. Live-verified against rebuilt Compose containers: attached/detached a
  tag (tags array updated both times), added/removed a list member (`member_count` went
  0→1→0), and confirmed the same Analyst-view/Viewer-none permission split as
  `GRX-CONTACT-001`.
- Note for future sessions: the full `pytest` run's migration round-trip test drops and
  recreates all tables against the same database Compose uses, wiping any manually
  created accounts (like `admin@growixa.local`) — recreated it again after this run, same
  as after `GRX-CONTACT-001`.
- `GRX-CONTACT-003` (segments) is now the next `READY` task. Commit `1e69461`.

## 2026-07-30 — GRX-CONTACT-001: Contacts schema + CRUD

- First Slice 2 implementation task. Added `contacts`, `contact_custom_fields`,
  `contact_field_values` tables (migration `209d29349ccf`) and
  `contacts.manage`/`contacts.view` permission codes + role grants (Super
  Admin/Admin/Marketing Manager manage; those three plus Analyst view; Viewer gets
  neither, per RBAC.md's Slice 2 rationale).
- `POST /contacts` creates or updates by email (the sole dedup key — no fuzzy matching);
  `GET /contacts`, `GET /contacts/{id}`, `PATCH /contacts/{id}`, `PATCH
  /contacts/{id}/status` (archive/unarchive); `GET`/`POST /contacts/custom-fields`.
  Contact activity reuses the existing `audit_logs` table rather than a new one
  (`contact.created`/`updated`/`archived`).
- **Real bug found and fixed during live verification**: `Contact.updated_at`'s
  server-side `onupdate` expires that attribute after `session.commit()`; reading it
  synchronously afterward (as the API's response serialization does) raised
  `sqlalchemy.exc.MissingGreenlet`. Fixed with an explicit `await
  session.refresh(contact)` right after each mutating commit. Worth checking whether
  `company_profile`'s equivalent `onupdate` column has the same latent bug — its existing
  test suite only ever creates a profile once per test, never exercises a second `PUT`
  against an already-saved row.
- Extended `test_auth_schema_seed.py`'s exact-match permission-set assertion to include
  the two new codes — a legitimate extension of Sprint 1's test now that Slice 2 adds
  permissions, not a regression.
- `ruff`/`mypy` clean; `pytest` 69 passed, 3 skipped (94% coverage, 12 new tests);
  `alembic check` → no drift. Live-verified against rebuilt Compose containers: created a
  contact with a custom field value, re-created with the same email (dedup confirmed —
  same id, list count stayed at 1), archived then reactivated (audit event confirmed via
  DB query), and confirmed Analyst gets 200 on list/403 on create while Viewer gets 403
  on both.
- Also recreated the `admin@growixa.local` smoke-test account, which the full pytest run's
  migration round-trip test (`test_migrations.py`) wiped as a side effect of dropping and
  recreating all tables against the same database Compose uses — a pre-existing test
  characteristic, not something introduced by this task, but worth knowing before running
  the full suite against a Compose stack with data you want to keep.
- `GRX-CONTACT-002` (tags & lists) is now the next `READY` task. Commit `7ec6c93`.

## 2026-07-30 — Sprint 2 (Contacts) planning

- All tracked Sprint 1 tasks are `DONE` except `GRX-DEVOPS-001` (push confirmation) and
  `GRX-DOC-003` (blocked on it) — per the user's direction, moved on to planning Slice 2
  (Contacts) rather than waiting.
- Extended `DATA_MODEL.md`, `DATABASE_SCHEMA.md`, and `ERD.md` with full field-level detail
  for `contacts`, `contact_custom_fields`/`contact_field_values`, `tags`/`contact_tags`,
  `contact_lists`/`contact_list_members`, `segments`/`segment_rules`/`segment_members`,
  `contact_imports`/`contact_import_rows`, and `consent_records`/`suppression_entries`.
  Notable design calls: dedup is email-only; segment rules are AND-only in Slice 2 (no
  OR/grouping); "contact activity history" reuses the existing `audit_logs` table instead
  of a new one; `consent_records` is insert-only (compliance history) while
  `suppression_entries` is a fast current-state upsert-on-email table — deliberately
  different patterns for different jobs.
- Extended `RBAC.md` with `contacts.manage`/`contacts.view` and a Slice 2 role matrix —
  Marketing Manager gets full manage access (matches its stated scope), Analyst gets
  view-only, Content Creator and Viewer get neither yet (no stated Slice 2 need; Sprint 1
  set the precedent that view access is granted explicitly per module, not assumed).
- Wrote `SPRINT_02_CONTACTS.md` (scope, exclusions, acceptance criteria) and a Slice 2
  readiness gate in `DEVELOPMENT_READINESS.md`, mirroring Sprint 1's structure.
- Added nine tasks to `MASTER_TASK_TRACKER.md` (`GRX-CONTACT-001`–`009`): schema+CRUD,
  tags/lists, segments, CSV import, consent/suppression — each with a frontend
  counterpart. `GRX-CONTACT-001` is the first `READY` task.
- Planning only — no code written yet for Slice 2.

## 2026-07-30 — Toast notification system (UI polish, no tracker ID)

- Found while manually testing `GRX-USER-002`: form errors only showed as an inline red
  banner easy to miss, and successful role/status changes gave no feedback at all. Added a
  shared `ToastProvider`/`useToast()` (`apps/web/src/components/toast/`), wired into the
  root layout so it's available app-wide.
- Login, company settings, and the Team page now show errors and successes as an
  auto-dismissing (5s) popup in the top-right corner instead of (or in addition to) inline
  banners. The Team page's invite-token success banner stays inline since it holds an
  actionable value the admin needs to copy, not a transient message.
- Added a proper `--color-error` token to `globals.css` (previously every page hardcoded
  the same `rgba(244, 63, 94, ...)` value inline).
- `eslint`/`prettier`/`tsc` clean; Vitest 17 passed (4 new for the toast component, 3
  existing test files updated to wrap renders in `ToastProvider`); `next build` succeeds;
  Playwright 4 passed (unaffected). Live-verified in a real browser against rebuilt
  Compose containers: a failed login showed an error toast, a successful role change
  showed a success toast, both auto-dismissed after 5 seconds.
- Not filed as a tracked `GRX-*` task — a UI-quality fix found and resolved during manual
  testing, not a Sprint 1/2 backlog item. A related, not-yet-fixed gap: unlike self-disable
  (blocked), there's no guard against changing your own role and accidentally losing
  `users.manage` — flagged to the product owner, not yet actioned.

## 2026-07-29 — GRX-FOUND-007: RabbitMQ connectivity and worker skeleton

- Added the shared `JobEnvelope` schema and a `publish_job()` producer to
  `apps/api/src/growixa_api/jobs/`, plus an `admin.access`-gated `POST
  /system/jobs/healthcheck` so the pipeline can be triggered and tested — Sprint 1 has no
  real business job to trigger it otherwise.
- New standalone `apps/worker/` app (own `pyproject.toml`, `Dockerfile`, ruff/mypy config
  mirroring `apps/api`) connects to RabbitMQ, declares the `grx.system.healthcheck` queue,
  and logs each job it processes. Kept as its own deployable app rather than an entrypoint
  inside `apps/api`, per `SYSTEM_ARCHITECTURE.md`'s "independently scalable Python
  workers" — corrected a stale `LOCAL_DEVELOPMENT.md` line that had said otherwise.
- Wired into `compose.yaml` as a new `worker` service, into `ci.yml` as a new parallel job
  (no service containers needed — the worker's own tests are pure-unit against a fake AMQP
  message), and into `.pre-commit-config.yaml` (ruff/format/mypy hooks mirroring `apps/api`'s).
- `ruff`/`mypy` clean on both apps; `apps/api` `pytest` 58 passed, 3 skipped (95%
  coverage) — the new producer round-trip test skips locally for the same
  host-unreachable-broker reason as `GRX-FOUND-006`'s Redis test, but runs for real in CI;
  `apps/worker` `pytest` 2 passed. Live-verified against rebuilt Compose containers:
  triggered a real healthcheck job as a smoke Admin via curl, confirmed
  `docker compose logs worker` showed the exact same `job_id` being processed; confirmed a
  Viewer gets 403; `/health`'s `rabbitmq` check still reports `ok`.
- This was the last `BACKLOG` Sprint 1 task. Only `GRX-DEVOPS-001` (push confirmation) and
  `GRX-DOC-003` (blocked on that same push) remain open in Sprint 1. Commit `a0a1eea`.

## 2026-07-29 — GRX-USER-002: User management screens (list, invite, disable, role assignment)

- Backend: `GET /roles` (gated on `users.manage`, since it only backs the role-picker
  dropdown — not exposing the full permission matrix), `GET /users` (list with roles +
  status), `PATCH /users/{id}/status`, `PATCH /users/{id}/role`. Self-disable is blocked
  (no `seed_first_admin` CLI yet, so a self-lockout would be unrecoverable); disabling a
  user revokes all their active sessions; role changes emit a `role.changed` audit event
  with old/new roles.
- Frontend: `/dashboard/team` — lists members, invites new users (shows the raw invite
  token directly since there's no email delivery yet), changes roles, disables/enables.
  Sidebar's "Team" link only renders for users with `users.manage`.
- `ruff`/`mypy` clean, `pytest` 55 passed (95% coverage, 10 new); frontend
  lint/format/typecheck/build clean, Vitest 14 passed (5 new), Playwright 4 passed (1 new
  e2e: invite → accept → login). Live-verified in a real browser against rebuilt Compose
  containers: invited a user, changed their role, disabled them (session revoked, login
  now 401), confirmed self-disable is blocked in the UI.
- This was the last tracked Sprint 1 task; all Sprint 1 tasks are now `DONE` except
  `GRX-DEVOPS-001`'s pending push confirmation. Commit `22ba450`.

## 2026-07-27 — GRX-COMPANY-002: Company settings screen

- Built the company profile + brand voice form at `/dashboard/company-settings`. Extended
  `GET /auth/me` to also return the caller's permission codes (new `permissions/repositories.py`
  helper, new `MeOut` schema) so the UI can render editable vs. read-only correctly — only
  Admin/Super Admin hold `company.settings.edit` per RBAC.md, everyone else sees the same
  data with every field disabled and a view-only note, rather than a form that would only
  fail on submit.
- Saves company then brand profile in sequence on one "Save changes" click (brand requires
  company to exist first, per `GRX-COMPANY-001`'s existing 400 behavior).
- Sidebar gained a real `SETTINGS` section (`Company`); the topbar title is now
  route-driven instead of hardcoded to "Dashboard".
- Found and fixed a real Vitest/RTL bug while writing the component test: without
  `test.globals: true`, `@testing-library/react`'s automatic `afterEach(cleanup)` never
  registers, so DOM from one test leaks into the next in the same file. Fixed with an
  explicit `afterEach(cleanup)` in `vitest.setup.ts`.
- `ruff`/`mypy` clean, `pytest` 45 passed/2 skipped; frontend lint/format/typecheck/build
  clean, Vitest 5 passed (4 new, mocked `apiFetch`), Playwright 3 passed (unaffected).
  Live-verified against rebuilt Compose containers as both an Admin (edits, saves,
  survives reload) and a Viewer (same data, fully disabled, no Save button). Commit
  `9989373`.

## 2026-07-27 — GRX-DEVOPS-001: CI pipeline (IN_REVIEW)

- Picked immediately after `GRX-FOUND-008` — both dependencies (`GRX-TEST-001`,
  `GRX-TEST-002`) were already `DONE` (the tracker still marked it `BACKLOG`, corrected as
  part of this pick, same pattern as `GRX-FOUND-006` and `GRX-AUTH-004` earlier). This
  locks in every testing investment made across this session so future regressions get
  caught automatically instead of relying on an agent session remembering to re-verify.
- Added `.github/workflows/ci.yml` implementing all 8 stages from `TEST_STRATEGY.md`
  §CI test stages, split across 3 jobs rather than one linear pipeline — an explicit,
  flagged refinement that preserves the documented "fail fast, in order" intent while
  actually running faster: `backend` and `frontend` run in parallel (independent stacks,
  stages 1–3 shared plus each side's own tests/build), and `e2e` (`needs: [backend,
  frontend]`) only stands up the expensive full stack once the cheap checks already
  passed.
- `backend` job runs against real GitHub Actions service containers for Postgres, Redis,
  and RabbitMQ — meaning **Redis is host-reachable in CI**, unlike local dev
  (`GRX-FOUND-006`'s documented finding that Compose's `redis` has no host port mapping).
  The tests that skip locally for that exact reason (`test_redis.py`, the rate-limit
  integration test) will actually execute for real in CI — exactly the outcome flagged as
  intentional when those skips were written.
- Migration check step runs `alembic upgrade head && alembic check` — deliberately
  distinct from `test_migrations.py`'s upgrade/downgrade round-trip (already covered by
  the `Tests` step): `alembic check` catches a model changed without a matching
  migration, which the round-trip test doesn't verify on its own.
- `e2e` job runs the real Compose stack (`docker compose up postgres redis rabbitmq api`)
  — deliberately omitting the `web` container, since Playwright already brings its own
  Next.js instance (`playwright.config.ts`'s `webServer`); standing up both would just
  build the frontend twice for no benefit.
- Made `apps/web/tests/e2e/{global-setup,global-teardown}.ts` compose-binary-portable: a
  new `COMPOSE_BIN` env var (default `podman`, this project's local dev tool; CI sets
  `docker`, what GitHub's runners actually have) means the identical e2e suite runs
  unmodified in both environments — no CI-specific test duplication.
- Locally re-verified every command the workflow runs, since the workflow itself can't be
  executed without pushing: `ruff check`/`ruff format --check`/`mypy` clean;
  `alembic upgrade head && alembic check` → "No new upgrade operations detected";
  `pytest` → 45 passed, 2 skipped; frontend `eslint`/`prettier --check`/`tsc --noEmit`/
  `vitest run` all clean; `next build` → succeeds, correctly classifies `/`/`/login`
  static and `/dashboard` dynamic; `npm run test:e2e` → 3 passed with the new
  `COMPOSE_BIN` parameterization defaulting to `podman` (unchanged local behavior).
  Workflow YAML syntax-validated with `python3 -c "import yaml; yaml.safe_load(...)"`.
- **Left at `IN_REVIEW`, not `DONE`.** A real green run on GitHub Actions has not been
  observed — confirming one requires pushing to the remote, which this session will not
  do without the user's explicit go-ahead (pushing is a permission-gated action). Move to
  `DONE` once the user pushes and a run is confirmed green; if it fails, the failure will
  be in something this local re-verification couldn't reach (GHA-specific networking,
  action version pinning, etc.) rather than in the commands themselves. Commit `7ff54dc`.

## 2026-07-27 — GRX-FOUND-008: Dashboard shell

- Picked immediately after `GRX-TEST-002` gave the frontend a real test harness. The user
  directed this UI work explicitly, pointing to the previously captured design reference
  (`DESIGN_REFERENCES.md` + `mockups/growixa-login-and-dashboard-mockup.html`) and a fresh
  screenshot of the same dashboard mockup for visual grounding.
- **Two small, necessary backend additions**, discovered while scoping this frontend task
  (not originally listed in its Files/Modules column): CORS middleware
  (`cors_allowed_origins` setting, defaulting to `localhost:3000` and `localhost:3100`) so
  a browser can complete the cross-origin, credentialed fetches auth relies on; and
  `GET /auth/me` (identifies the session via the access-token cookie itself, the same
  shape as `/refresh`/`/logout-all` — no separate permission needed, added to the
  route-protection audit's allowlist alongside them). Without `/auth/me` there is no way
  for a Server Component to determine "is this user logged in," since the access token is
  HttpOnly and unreadable by client-side JS.
- Frontend: `globals.css` design tokens (colors, gradients, card/pill styles) taken
  directly from the design brief; a real email+password `/login` page (dark navy
  gradient, glass card) — not the mockup's demo "Sign in as Super Admin/Team Member"
  buttons, since the real backend needs actual credentials; an authenticated
  `/dashboard` route whose layout calls `getCurrentUser()` server-side and redirects to
  `/login` on failure, rendering a sidebar + top bar shell around an empty-state landing
  page. Root `/` now redirects to `/dashboard`, which is the actual auth gate.
- Per `DESIGN_REFERENCES.md`'s scope caveat, the sidebar wires up only the "Dashboard" nav
  item for real — Contacts/Campaigns/Team/Settings/etc. have no page behind them yet in
  Sprint 1, so they're not rendered at all (not even as inert placeholders), rather than
  shipping dead links.
- `ruff`/`mypy` clean; `pytest` 45 passed, 2 skipped (unchanged skip count/reason from
  `GRX-AUTH-004`). Frontend `eslint`/`prettier --check`/`tsc --noEmit`/Vitest all clean.
  Added a Playwright global setup/teardown that creates and deletes a fixed e2e test user
  directly via the ORM inside the `api` container (no public "create user" endpoint
  exists). 3 e2e tests passed against real Compose Postgres/Redis: an anonymous visit to
  `/dashboard` (and separately to `/`) redirects to `/login`; a full login shows the
  dashboard shell (sidebar, top bar, correct user name, empty-state card) and logging out
  clears the session for real, confirmed by re-visiting `/dashboard` afterward and landing
  back on `/login`.
- **A real bug found and fixed during Compose verification, not caught by the host-run
  Playwright suite**: server-side fetches issued from inside the `web` container used
  `NEXT_PUBLIC_API_URL=http://localhost:8000`, but `localhost` inside that container
  resolves to the container itself, not the `api` container — every dashboard visit 500'd
  in the real Dockerized stack even though it worked perfectly via `next build && next
  start` on the host (where both processes genuinely do share one `localhost`). Fixed by
  adding a server-only `API_INTERNAL_URL` (falls back to `NEXT_PUBLIC_API_URL` when unset,
  so running outside Docker needs no change) and setting it to `http://api:8000` — the
  Compose service DNS name — in `compose.yaml`. This is exactly the kind of gap Playwright
  running against a host-built app can't catch, which is why this task's verification
  included rebuilding both containers and driving the actual login → dashboard → logout
  flow in a real browser against them, not just trusting the e2e suite's green result.
- Cosmetic, non-blocking: the icon-mark PNG asset has an opaque light backdrop baked in,
  which shows as a small white square against the dark login card rather than blending in
  — a future visual-polish pass could swap in the monochrome/white logo variant instead;
  not worth blocking this task over. Commit `886329a`.

## 2026-07-27 — GRX-FEAT-SMS-001: SMS Marketing & Twilio Integration documentation

- Added feature specification `docs/02-features/FEATURE_SMS_MARKETING.md` detailing Admin Twilio provider credential setup, E.164 phone formatting, SMS consent management (`OPTED_IN`/`OPTED_OUT`), SMS campaign composer with 160-char / GSM-7 segment calculator, and Twilio DLR / `STOP` opt-out webhooks.
- Updated `MVP_SCOPE.md`, `ROADMAP.md` (Release 1.2), `FEATURE_CATALOG.md`, and `PROJECT_STATUS.md` to stage SMS Marketing in Release 1.2.

## 2026-07-27 — GRX-TEST-002: Frontend test foundation

- Picked ahead of `GRX-FOUND-008` (dashboard shell) — the user directed frontend/UI work
  next, pointing to the design reference already captured in `DESIGN_REFERENCES.md`, but
  `GRX-FOUND-008`'s own "Required Tests" (a frontend e2e smoke test) has nothing to run in:
  `apps/web` had zero test tooling. Same reasoning as why `GRX-TEST-001` (backend test
  foundation) was done before most backend feature work this session.
- Added Vitest + React Testing Library + jsdom for component tests
  (`vitest.config.ts`, `vitest.setup.ts`) and Playwright for e2e (`playwright.config.ts`,
  Chromium only for now). `npm run test` / `npm run test:e2e` scripts added.
- One trivial component test (`src/app/page.test.tsx`) renders the existing `HomePage` and
  asserts its heading — will be revisited once `GRX-FOUND-008` changes what the root route
  renders. One e2e smoke test (`tests/e2e/smoke.spec.ts`) drives a real
  `next build && next start` and confirms the root route returns 200 with the heading
  visible.
- Playwright's dev server runs on port 3100 (not 3000) specifically so the e2e suite never
  collides with the Compose `web` container, which developers may have running at the same
  time on the standard port.
- `npm run lint`/`format:check`/`typecheck` all pass; `npm run test` → 1 passed; `npm run
  test:e2e` → 1 passed. Rebuilt the `web` image with the new devDependencies and confirmed
  `/` still returns 200 and an unknown route still 404s in Compose — no regression from
  adding test tooling. No CI pipeline exists yet (`GRX-DEVOPS-001`, which depends on this
  task); a green local test suite is this task's actual deliverable, matching
  `GRX-TEST-001`'s equivalent backend evidence. Commit `a804186`.

## 2026-07-27 — GRX-AUTH-004: Login rate limiting

- Picked immediately after `GRX-FOUND-006` (Redis connectivity) unblocked it — the highest
  remaining P0 backend task, and it closes T1 (credential stuffing/brute force) and T12
  (unbounded login/reset flooding) from `THREAT_MODEL.md` on the exact `/auth/login` and
  `/auth/password-reset/request` endpoints built in the two sessions before this one.
- Added `rate_limit_max_attempts` (default 5) and `rate_limit_window_seconds` (default 60)
  settings, and `auth/rate_limit.py`'s `enforce_rate_limit()`: a Redis `INCR`+`EXPIRE`
  fixed-window counter keyed `grx:ratelimit:{bucket}:{identifier}` — the exact key format
  `LOCAL_DEVELOPMENT.md` already documented in its Redis-inspection section, ahead of this
  task even existing. Both `/auth/login` (bucket `login`) and
  `/auth/password-reset/request` (bucket `password_reset_request`) call it keyed by
  `email:ip`, so the two endpoints are limited independently and the same email can't
  exhaust the other endpoint's budget.
- **Explicit, flagged design call: the limiter fails open on `RedisError`.** If Redis is
  unreachable, `enforce_rate_limit()` swallows the error and allows the request through
  rather than raising — a Redis outage must degrade *security posture*, not *availability*
  of login/password-reset entirely (the same trade-off `/health` already makes by reporting
  "degraded" instead of crashing). This also has a load-bearing practical consequence:
  Compose's `redis` service has no host port mapping (`GRX-FOUND-006`'s finding), so every
  host-run `pytest` login/password-reset test in this whole session continues to pass
  unaffected — the limiter transparently no-ops under that specific, documented
  environment constraint instead of breaking 40+ pre-existing tests.
- `ruff`/`mypy` clean; `pytest` 43 passed, 2 skipped (95% coverage). Five pure unit tests
  against a fake in-memory Redis stand-in cover the limiter logic directly (allows up to
  max, raises past max, isolates by identifier, isolates by bucket, fails open on
  `RedisError`) with no real Redis needed. One integration test exercises the real
  `/auth/login` endpoint end-to-end and skips under host-run pytest for the same documented
  reason as `GRX-FOUND-006`'s `test_redis.py`.
- Rebuilt the `api` image and verified live against real Compose Redis: 6 wrong-password
  attempts against one email+IP returned `401×5` then `429`; a *correct* password against
  that same already-limited identifier also returned `429` (rate limiting is
  identity-keyed, not correctness-keyed — the intended defense, since checking the
  password before the limiter would let an attacker's eventual correct guess bypass
  protection entirely); a different email+IP logged in normally (`200`), proving
  unaffected traffic elsewhere; the same 5-then-429 pattern was confirmed independently on
  `/auth/password-reset/request`. Verified via `redis-cli KEYS "grx:ratelimit:*"` that the
  real keys match the documented naming exactly, then cleaned up. Commit `5c26200`.

## 2026-07-27 — GRX-FOUND-006: Redis connectivity

- Picked because its only listed dependency (`GRX-FOUND-003`, FastAPI application
  foundation) was already `DONE` — the tracker still marked it `BACKLOG`, a stale status
  corrected as part of this pick — and because it directly unblocks `GRX-AUTH-004` (login
  rate limiting), a P0 security task (T1/T12 in THREAT_MODEL.md) covering the exact
  login/password-reset-request endpoints built in the last two sessions.
- Added `growixa_api/redis.py`: a module-level pooled `redis.asyncio` client built from
  `settings.redis_url`, plus a `get_redis()` FastAPI dependency generator — the same shape
  as `db.py`'s `engine`/`get_session()`. This is the reusable client `GRX-AUTH-004`'s rate
  limiter (and later locks/idempotency keys) will import, rather than each future feature
  opening its own throwaway connection.
- `health.py`'s Redis check previously opened a new client, pinged it, and closed it on
  every single `/health` request; it now reuses the shared pooled client, matching the
  Postgres engine-reuse fix already landed alongside `GRX-AUTH-005`.
- **Environment-constraint finding**: Compose's `redis` service has no host port mapping
  by design (`compose.yaml`'s comment, confirmed in `LOCAL_DEVELOPMENT.md`'s Redis
  inspection section: "not required to be reachable from outside the compose network").
  Only Postgres/RabbitMQ are host-mapped, so a host-run pytest process cannot open a real
  TCP connection to Redis. The new connectivity smoke test (`tests/test_redis.py`) skips
  with an explicit reason under this documented constraint rather than being written to
  silently pass or made to fail the whole suite; real set/get/delete round-trip
  correctness was instead verified live via the shared client executed inside the running
  `api` container.
- `ruff`/`mypy` clean; `pytest` 38 passed, 1 skipped (95% coverage, unchanged from before —
  the skip contributes no missed lines). Rebuilt the `api` image; `GET /health` still
  returns `{"status":"ok",...}` using the new pooled client; a live
  set → get → delete → get(None) sequence run inside the `api` container via
  `growixa_api.redis.client` confirmed correct round-trip behavior against the real
  Compose Redis instance. Commit `32aacdf`.

## 2026-07-27 — GRX-AUTH-005: Password reset flow

- Picked as the last P0 backend auth task remaining (everything else `READY` at that point
  was frontend work) — closes the final account-recovery gap in the auth system.
- Added `password_reset_tokens` table (migration `bb25de08ba84`), matching
  `DATABASE_SCHEMA.md`'s spec exactly: `user_id` FK `ON DELETE CASCADE`, unique `token_hash`,
  `expires_at`, `used_at`. Reused the already-generalized `generate_token()`/`hash_token()`
  from `auth/tokens.py` (no new token machinery needed).
- `auth/services.py`: `request_password_reset()` always records a
  `user.password_reset_requested` audit event and always runs the same code shape regardless
  of whether the account exists — only the returned raw token differs (a string vs. `None`).
  `complete_password_reset()` validates the token (exists, unused, unexpired), sets the new
  password hash, marks the token used, calls the existing `revoke_all_active_sessions()`
  (built in `GRX-AUTH-003`) to kill every active session, and records
  `user.password_reset_completed`.
- **Enumeration-safety design (THREAT_MODEL.md T11)**: `POST /auth/password-reset/request`
  always returns the same generic message regardless of whether the email is registered.
  The raw token is additionally echoed back in the response, but **only** when
  `settings.environment == "local"` — mirroring the existing `Secure`-cookie
  environment-conditional pattern and GRX-USER-001's invitation-token interim behavior.
  Verified via a monkeypatched-`ENVIRONMENT=production` test that the token is `null` for
  both known and unknown emails outside local dev.
- Both new endpoints (`/auth/password-reset/request`, `/auth/password-reset/complete`) are
  public (no session yet) and added to the route-protection audit's allowlist.
- `ruff`/`mypy` clean; `pytest` 38 passed (95% coverage) incl. full request→complete
  round-trip (old password rejected, new password works, sessions revoked, all three audit
  events emitted), identical response for known/unknown email, and invalid/reused-token
  rejection. Rebuilt the `api` image, confirmed `alembic current` → head, and ran a live curl
  request→complete flow against Compose with direct `psql` verification of audit events,
  refresh-token revocation, and the reset token's `used_at`. Commit `730519b`.

## 2026-07-27 — GRX-USER-001: Internal user invitation + acceptance

- Picked next per explicit user direction as "most needed": the only way to add any user
  to the system besides the still-unbuilt `seed_first_admin` CLI (flagged since
  `GRX-AUTH-001`) or direct DB manipulation.
- **First cross-cutting refactor of already-`DONE` auth code this session**: generalized
  `auth/tokens.py`'s `generate_refresh_token`/`hash_refresh_token` to
  `generate_token`/`hash_token` — invitation tokens need the exact same "high-entropy
  opaque token, SHA-256 hash for lookup" treatment as refresh tokens
  (AUTHENTICATION.md's token model lists both under the same shape), and duplicating that
  logic under an invitation-specific name would just be the same code twice. Verified only
  `auth/services.py` called the old names before renaming, so this was a safe,
  contained rename — updated its 2 call sites, all 28 pre-existing tests still passed
  afterward.
- Added `user_invitations` table (migration `f356da0136c3`) — both indexes
  `DATABASE_SCHEMA.md` specifies: a plain one on `email`, and a partial one on
  `email WHERE accepted_at IS NULL` for "does this email already have an open invite"
  lookups.
- Added `roles/repositories.py` (`get_role_by_name`) — `roles`'s first repository file,
  needed to resolve an invitation's `role_name` (e.g. "Viewer") to the seeded role's UUID.
- `users/services.py`: `invite_user()` resolves the role, checks the email isn't already
  registered (fails fast for the admin rather than only failing at acceptance),
  generates+hashes a token, and returns `(invitation, raw_token)` — the raw token only
  ever exists in memory, never persisted. `accept_invitation()` re-validates
  not-yet-accepted/not-expired/email-still-free (closes a race between two acceptances or
  the person registering some other way in between), creates the `User`, assigns the
  `UserRole`, marks the invitation accepted, and records `invitation.accepted` (Sprint 1's
  audit event set) with `actor_user_id` set to the **new** user (they're the one taking
  the accepting action, even though an admin initiated the invite).
- **Explicit, flagged scope decision — not a silent shortcut**: `POST /users/invitations`
  returns the raw invitation token directly in its JSON response. Sprint 1 has no
  email-delivery channel at all (no task for it exists in the tracker), so there is
  currently no other way for the invitee to receive it. This is the correct interim
  behavior given the constraint, not the intended end state — revisit the moment a
  notifications/email-delivery task exists, at which point the token should be sent
  out-of-band and dropped from the API response entirely.
- Added `apps/api/tests/test_users_invitations.py`: full invite → accept round-trip (role
  assigned, audit event recorded with the right actor), non-admin invite attempt (403,
  via the real `users.manage` permission check — no test-only bypass), unknown role (400),
  inviting an already-registered email (409), accepting with an invalid token (400), and
  accepting an already-accepted token (400, replay protection).
- Verified beyond the automated suite: rebuilt the `api` image, then ran a real
  login → invite → accept flow via curl against the live Compose stack, confirming via
  direct `psql` queries that the new user got the correct role and the
  `invitation.accepted` audit row was recorded.
- Verified: `ruff`/`format --check`/`mypy` clean across 63 source files; `pytest` 34
  passed, 94% coverage.
- `GRX-USER-001` marked `DONE`. `GRX-USER-002` (user management screens, frontend) is
  newly `READY`, alongside the already-`READY` `GRX-AUTH-005`, `GRX-TEST-002`,
  `GRX-COMPANY-002`, `GRX-FOUND-008`. This completes the third step of the user-directed
  "most needed" sequence this session (`GRX-AUTH-002` → `GRX-AUTH-003` → `GRX-USER-001`).
- Commit: `87d2110`.

## 2026-07-27 — GRX-AUTH-003: Refresh-token rotation + session revocation

- Picked next per explicit user direction as "most needed first": closes a real security
  gap `GRX-AUTH-002` left open by design (refresh tokens issued, but no rotation, no reuse
  detection — a stolen refresh token could otherwise be replayed indefinitely).
- Added `POST /auth/refresh` and `POST /auth/logout-all` — both public routes (added to
  the route-protection audit's allowlist) that identify the acting user via the refresh
  token itself, consistent with the existing `/auth/logout`, rather than via
  `get_current_user_id`/`require_permission`.
- `auth/services.refresh()`: looks up the presented token; if already revoked by a
  *previous rotation* (not by logout), treats this as a reuse/compromise signal and calls
  the new `revoke_all_active_sessions()` to kill every session for that user — not just
  reject the one request — before raising. Otherwise rotates: issues a new access +
  refresh token, marks the presented one `revoked_at` + `replaced_by_token_id` pointing at
  the new one (the `refresh_tokens` column that existed since `GRX-AUTH-002`'s migration
  but stayed unused until now), and re-validates `user.status == "ACTIVE"` on every
  refresh (defense in depth beyond relying solely on disable always successfully revoking
  sessions elsewhere).
- Added `auth/services.revoke_all_active_sessions(session, user_id, *, reason)` —
  deliberately public (not `_`-prefixed) and does not commit itself, so a future
  disable-user action (no such endpoint exists yet; out of `apps/api/auth/`'s own scope)
  can call it as one step in a larger transaction. Records a `session.revoked` audit event
  (Sprint 1's audit event set) with the reason and count, only when it actually revoked
  something.
- `auth/services.logout_all()` reuses the same revoke function, keyed off the presented
  refresh token — logging out "everywhere" from any one of your own sessions.
- Added `apps/api/tests/test_auth_refresh.py`: rotation (new cookies issued, old token
  revoked with the correct `replaced_by_token_id`), reuse detection (replaying the
  pre-rotation token 401s *and* revokes the entire chain including the token it had
  already rotated to), `logout-all` across two simulated devices (two separate
  `AsyncClient`s, since one client's cookie jar would silently overwrite the first
  session's refresh cookie on a second login), disable-revokes-sessions (proves the
  `revoke_all_active_sessions()` building block works, since no disable-user endpoint
  exists to exercise end-to-end yet), and expired-token rejection.
- Verified beyond the automated suite: rebuilt the `api` image, then ran a real
  login → refresh → replay-old-token flow via curl against the live Compose stack,
  confirming via direct `psql` queries that *both* refresh tokens ended up revoked and the
  `session.revoked` audit row was recorded with `reason: "refresh_token_reuse_detected"`.
  Cleaned up the smoke-test user/rows afterward.
- Verified: `ruff`/`format --check`/`mypy` clean across 57 source files; `pytest` 28
  passed, 94% coverage.
- `GRX-AUTH-003` marked `DONE`. No task became newly `READY` from this alone — nothing
  else in the tracker lists it as a dependency yet.
- Commit: `27a22af`.

## 2026-07-27 — GRX-AUTH-002: Password hashing + login/logout

- Picked next per explicit user direction: P0, backend-only, continuing the session's
  backend momentum rather than branching into frontend work (`GRX-TEST-002`) or a P1 task
  (`GRX-COMPANY-002`).
- Added `apps/api/src/growixa_api/auth/security.py`: Argon2id `hash_password`/
  `verify_password`, cost parameters (`argon2_time_cost`/`memory_cost`/`parallelism`) added
  to `Settings` as configuration per
  [AUTHENTICATION.md](../08-security/AUTHENTICATION.md) ("tuned parameters set as
  configuration... so cost can be raised as hardware improves"), defaulting to
  argon2-cffi's own OWASP-baseline `PasswordHasher` defaults.
- Added `apps/api/src/growixa_api/auth/tokens.py`: `create_access_token` — the **issuing**
  half of the JWT that `permissions.dependencies.get_current_user_id` (`GRX-RBAC-001`) has
  been verifying since that task, same signing key/algorithm, closing the gap flagged at
  the time. Also refresh-token generation (`secrets.token_urlsafe`) and hashing
  (SHA-256 — fast/deterministic is correct here since, unlike a password, a refresh token
  is already high-entropy, not a low-entropy brute-forceable input).
- Added the `refresh_tokens` table (migration `ea25a5343142`) — deferred from
  `GRX-AUTH-001` since that task's own scope was schema for users/roles/permissions only;
  needed now because issuing a refresh token requires persisting its hash. Includes
  `replaced_by_token_id`, populated only once `GRX-AUTH-003` (rotation) lands, but present
  now as part of the fixed schema in DATABASE_SCHEMA.md.
- Added `apps/api/src/growixa_api/users/repositories.py` (`get_user_by_email`) — the
  `users` module's first repository file; `auth` depends on `users` for identity lookup per
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md), so this lookup belongs
  there, not duplicated inside `auth`.
- `auth/services.py`: `login()` raises a single `InvalidCredentialsError` for unknown
  email, wrong password, *and* disabled accounts alike — deliberately indistinguishable
  per [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T11, each still recording a
  `user.login_failed` audit event (with `entity_id` set only when a user was actually
  found, so the audit trail itself still distinguishes them for legitimate incident
  response — that distinction just never reaches the HTTP response). Successful login
  updates `last_login_at`, issues both tokens, and records `user.login`. `logout()`
  revokes the presented refresh token and records `user.logout`.
- `auth/api.py`: `POST /auth/login` and `POST /auth/logout`, added to the
  route-protection audit's public allowlist (they are the entry points before a session
  exists). Cookies are `HttpOnly` + `SameSite=Lax` unconditionally; `Secure` is
  conditional on `settings.environment != "local"` — local dev runs over plain HTTP, and a
  browser will not resend a `Secure` cookie without HTTPS.
- Added `apps/api/tests/test_auth_login.py`: valid login (cookies present, **no token
  values in the JSON body** — verified directly per T2, not assumed), identical generic
  error for wrong-password vs. unknown-email (compared byte-for-byte, not just both-401),
  disabled-account rejection, and logout (revokes the token row, clears both cookies,
  records the audit event). Extended the shared `user_factory` (`GRX-TEST-001`) to hash a
  real, known password (`DEFAULT_TEST_PASSWORD`) and accept an explicit `email` override,
  rather than duplicating user-creation logic for this task's tests.
- **Real bug found and fixed — this one affects every coverage number recorded so far this
  session.** `auth/services.py` showed 50% coverage despite all 4 new tests passing with
  assertions that only make sense if the "uncovered" lines ran (audit rows created,
  `last_login_at` set, tokens revoked). Root cause: SQLAlchemy's async engine bridges into
  the sync DBAPI driver via `greenlet_spawn`, and coverage.py's default tracer does not
  follow into that greenlet context, silently under-reporting any code that runs on the
  other side of an `await session.execute(...)`/`commit()` call. Fixed by adding
  `concurrency = ["greenlet"]` to `[tool.coverage.run]`. Total coverage jumped from 85% to
  **94%** on rerun — the true baseline was always higher; this was purely a measurement
  bug, not new code appearing. `GRX-TEST-001`'s previously-recorded 87% baseline is now
  known to have been an undercount for the same reason; not retroactively rewritten there
  (historical evidence is point-in-time), but flagged here since this is where it was found.
- Verified beyond the automated suite: rebuilt the `api` image, confirmed `alembic current`
  reports the new head inside the container, then ran a real login → wrong-password →
  logout flow via curl against the live Compose stack — inspected the actual `Set-Cookie`
  headers (`HttpOnly`, `SameSite=lax`, correct `Max-Age` matching config, no `Secure` in
  local) and confirmed logout's `Set-Cookie` headers clear both cookies (`Max-Age=0`).
  Cleaned up the smoke-test user/rows afterward.
- Verified: `ruff`/`format --check`/`mypy` clean across 56 source files; `pytest` 23 passed,
  94% coverage (corrected).
- `GRX-AUTH-002` marked `DONE`. `GRX-AUTH-003` (refresh-token rotation + session
  revocation), `GRX-AUTH-005` (password reset flow), and `GRX-FOUND-008` (dashboard shell,
  frontend) are newly `READY`, alongside the already-`READY` `GRX-TEST-002`,
  `GRX-USER-001`, `GRX-COMPANY-002`. `GRX-AUTH-004` (rate limiting) still needs
  `GRX-FOUND-006` (Redis connectivity), not yet started.
- Commit: `b7cf4d8`.

## 2026-07-25 — GRX-COMPANY-001: Company profile + brand settings

- First task this session to ship real, RBAC-gated HTTP endpoints (previous tasks were
  schema/dependency foundations with no routes of their own besides `/health`).
- Added `apps/api/src/growixa_api/company/{models,schemas,repositories,services,api}.py`
  and the equivalent `brand/` module, following the full layered structure from
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md) for the first time
  (`models` → `repositories` → `services` → `api`, plus `schemas` for the Pydantic
  request/response shapes) since this is the first task that actually needs every layer.
- `company_profile`/`brand_profiles` are true singletons per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) — "exactly one row, enforced in the
  service, not a DB constraint." Implemented as get-then-upsert in `company/services.py`
  and `brand/services.py`, explicitly documented as **not race-safe** against two
  concurrent first-time saves (acceptable for Sprint 1's single-admin-at-a-time usage; a
  unique constraint or advisory lock would close that gap if it ever matters).
- `brand` depends on `company` per module boundaries — `brand.services` calls
  `company.repositories.get_company_profile` directly (the documented same-request
  cross-module call pattern) and raises a small domain error
  (`CompanyProfileRequiredError`) if no company profile exists yet, translated to a 400 at
  the API layer. No new permission codes were invented for brand — RBAC.md's existing
  `company.settings.view`/`company.settings.edit` cover both, matching RBAC.md's own
  framing of brand as part of company settings.
- Added migration `1abf62872712` (clean autogenerate: `company_profile` then
  `brand_profiles`, correct FK order).
- Added `apps/api/tests/test_company_settings.py`: admin edit+view, viewer view-only (403
  on edit) for *both* company and brand, unauthenticated 401, and the
  brand-requires-company-first 400 case. Since both tables are true singletons shared
  across the whole test run, every test clears both tables before and after itself via an
  autouse fixture — order-independent by construction, not by accident.
- Verified beyond the automated suite: rebuilt the `api` image, confirmed
  `alembic current` reports the new head inside the container, and ran a live end-to-end
  curl flow against the running Compose stack (mint a real Admin JWT inside the container,
  `PUT`/`GET /company/profile`, `PUT /brand/profile`) — real HTTP round-trip, not just the
  test suite's ASGI transport.
- Verified: `ruff`/`format --check`/`mypy` clean across 45 source files; `pytest` 19 passed
  (14 pre-existing + 5 new), 86% coverage.
- `GRX-COMPANY-001` marked `DONE`. `GRX-COMPANY-002` (company settings screen, frontend) is
  newly `READY`, alongside the already-`READY` `GRX-TEST-002`, `GRX-AUTH-002`,
  `GRX-USER-001`. This completes the user-specified sequence
  (`GRX-AUDIT-001` → `GRX-TEST-001` → `GRX-COMPANY-001`).
- Commit: `e40f6f8`.

## 2026-07-25 — GRX-TEST-001: Backend test foundation

- Added `apps/api/tests/conftest.py`: a `user_factory` fixture (async, factory-function
  pattern) that creates a real user, optionally assigns it an existing seeded role, and
  deletes every user it created at teardown. Kept deliberately simple — commit-and-cleanup
  per creation, not a transactional-rollback session — see the module's own docstring and
  [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for why the heavier pattern wasn't adopted now.
- Refactored `test_require_permission.py` (`GRX-RBAC-001`) and `test_audit_log.py`
  (`GRX-AUDIT-001`) to use the shared `user_factory` instead of their own near-identical
  ad hoc fixtures — the direct point of this task, not incidental cleanup.
- Added `pytest-cov` and `[tool.coverage.run]` config (`source = ["growixa_api"]`,
  tests excluded). Current baseline: **87%** line coverage (`pytest` with default addopts).
  No enforced minimum threshold yet — establishing the baseline measurement is this task's
  job; a specific enforced number is better decided once `GRX-DEVOPS-001` wires up CI and
  there's more code to judge a rational threshold against.
- Registered a `pytest.mark.integration` marker (in `pyproject.toml`, avoiding
  "unknown marker" warnings) and applied it to every test that touches a real backing
  service: `test_audit_log.py`, `test_auth_schema_seed.py`, `test_migrations.py`, and two of
  `test_require_permission.py`'s four tests (the other two — missing/invalid token — never
  reach `get_session` because `get_current_user_id` raises first, per FastAPI's
  parameter-order dependency resolution, and were left unmarked *and separately verified* to
  need no DB — see below).
- **Verified the split is real, not just labeled**: ran
  `pytest -m "not integration"` with `DATABASE_URL`/`REDIS_URL`/`RABBITMQ_URL` all pointed
  at unreachable hosts — all 7 unit-tier tests still passed. This is the actual proof (not
  an assumption) that the unit/integration boundary holds.
- No CI pipeline exists yet (`GRX-DEVOPS-001`, which depends on this task and
  `GRX-TEST-002`, hasn't started) — this task's own acceptance criterion
  ("`pytest` runs green ... in CI") is satisfied by `pytest` running green locally with the
  new foundation in place, matching how earlier foundation tasks satisfied "smoke test"
  criteria before their own supporting infrastructure existed.
- Verified: `ruff`/`format --check`/`mypy` clean across 31 source files; `pytest` 14 passed
  (same 14 as before this task — this task changed test *infrastructure*, not test *count*).
- `GRX-TEST-001` marked `DONE`. No task became newly `READY` from this alone (only
  `GRX-DEVOPS-001` depends on it, and that also needs `GRX-TEST-002`, not done). Per
  explicit user direction, `GRX-COMPANY-001` is next.
- Commit: `de55382`.

## 2026-07-25 — GRX-AUDIT-001: Audit log module

- **Task-ordering note**: this was the deferred half of the `GRX-AUDIT-001`/`GRX-AUTH-001`
  ordering issue flagged during `GRX-AUTH-001` — `audit_logs.actor_user_id` FKs to
  `users.id`, so this task genuinely needed `GRX-AUTH-001` done first. It was, so this
  proceeded cleanly.
- Added `apps/api/src/growixa_api/audit/models.py`: `AuditLog` matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly — indexes on
  `(entity_type, entity_id)`, `actor_user_id`, and `created_at`; the DB column `metadata` is
  mapped to a Python attribute named `event_metadata` since SQLAlchemy's `DeclarativeBase`
  already reserves `.metadata` for the ORM's own `MetaData` object.
- Added migration `6575d09949f9` (clean autogenerate, no hand-editing needed beyond
  ruff-driven line wrapping) creating `audit_logs`.
- Added `apps/api/src/growixa_api/audit/repositories.py` (`create_audit_log`,
  `list_audit_logs` — raw persistence only) and `services.py` (`record_event`,
  `list_events`). `record_event` redacts known-sensitive metadata keys (`password`,
  `password_hash`, `token`, `token_hash`, `refresh_token`, `access_token`, `secret`) to
  `"[REDACTED]"` before the row is ever written — the "structured-log redaction" half of
  this task's description, and defense-in-depth for
  [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T7 (secret leakage in logs). No
  `update`/`delete` function exists anywhere in either module — the "insert-only" property
  is enforced by omission, not a runtime guard.
- Added `apps/api/tests/test_audit_log.py`: write→list round-trip (real Postgres), a
  system-actor event (`actor_user_id=None`, explicitly allowed per the schema doc), and a
  redaction test asserting sensitive keys are stripped while unrelated keys survive intact.
- Added `apps/api/tests/test_audit_insert_only.py`: introspects `audit.repositories` and
  `audit.services` via `inspect.getmembers` and asserts no public function name contains
  "update"/"delete"/"modify"/"edit" — the tracker's required "negative test for missing
  update/delete routes," adapted to code-path auditing since no HTTP API layer exists yet
  in this module (matches the broader wording in
  [TEST_STRATEGY.md §Audit-log tests](../10-testing/TEST_STRATEGY.md#audit-log-tests): "no
  application code path... updates or deletes").
- **Real bug found and fixed while validating this task**: the write/list test's fixture
  teardown (deleting its throwaway test user) initially failed with a Postgres FK violation
  — `actor_user_id` correctly has no `ON DELETE CASCADE` (an audit trail must survive the
  actor being removed), so the test's own audit row was still referencing that user. Fixed
  by having the fixture delete its audit rows before the user.
- **Second, more interesting bug found and fixed**: `test_require_permission.py` started
  intermittently failing with `asyncpg.exceptions.InternalServerError: cache lookup failed
  for type ...` when run in the same session as `test_migrations.py`. Root cause:
  `test_migrations.py`'s downgrade-then-upgrade round trip was dropping and recreating the
  `citext` Postgres extension (added in `GRX-AUTH-001`'s migration, downgrade path) — each
  `CREATE EXTENSION` assigns the type a new internal OID, which poisons asyncpg's
  per-connection type cache for any already-pooled connection (recall `growixa_api.db`'s
  engine/pool is a session-wide singleton) that later touches a `citext` column. Fixed by no
  longer dropping the `citext` extension in that migration's `downgrade()` — a common,
  low-risk exception to full reversibility (table-level state is still fully reversible;
  leaving an installed extension behind is standard practice) that eliminates the whole
  class of failure rather than papering over one symptom of it.
- Verified: `ruff`/`format --check`/`mypy` clean across 30 source files; `pytest` 14 passed
  (10 pre-existing + 4 new); rebuilt the `api` image, `podman compose exec api alembic
  current` → new head, `/health` unaffected.
- `GRX-AUDIT-001` marked `DONE`. `GRX-AUTH-002` and `GRX-USER-001` (both depended on this
  and `GRX-AUTH-001`, both now done) are newly `READY`, alongside the already-`READY`
  `GRX-TEST-001`, `GRX-TEST-002`, `GRX-COMPANY-001`. Per explicit user direction, the next
  two tasks to pick up are `GRX-TEST-001` then `GRX-COMPANY-001`.
- Commit: `2b1dd7e`.

## 2026-07-25 — Design reference intake (not a tracker task)

- Product owner supplied brand assets (`apps/web/src/assets/`: primary, stacked, icon,
  wordmark, monochrome logo variants) and a self-contained HTML mockup covering the login
  screen and a full dashboard concept, plus a written design brief.
- Saved as [`docs/03-ux-ui/DESIGN_REFERENCES.md`](../03-ux-ui/DESIGN_REFERENCES.md) +
  [`docs/03-ux-ui/mockups/growixa-login-and-dashboard-mockup.html`](../03-ux-ui/mockups/growixa-login-and-dashboard-mockup.html)
  so this context survives outside chat history for whichever future session builds
  `GRX-AUTH-002`'s login UI or `GRX-FOUND-008`'s dashboard shell.
- **Explicit scope caveat recorded in that doc**: the brief describes the full eventual
  product (Contacts, Campaigns, Social, AI Assistant, Billing, ...), almost all of which is
  out of Sprint 1 per [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md) — this
  is reference material, not an approved implementation spec for any current task. No UI was
  built from it in this session.
- Added a `check-added-large-files` exclusion in `.pre-commit-config.yaml` for
  `apps/web/src/assets/` and `docs/03-ux-ui/mockups/` (several logo PNGs and the mockup HTML
  legitimately exceed the repo's default 1MB cap).
- Three additional files the brief references (`Growixa Dashboard v2.dc.html`,
  `Growixa Onboarding.dc.html`, `Growixa Style Options.dc.html`) were not available locally —
  noted as missing in the reference doc in case they're added later.
- Not tied to a `GRX-*` tracker row — this is reference intake, not an implementation task.

## 2026-07-24 — GRX-RBAC-001: Centralized permission-check dependency

- **Scope decision, made explicit up front**: `require_permission()` cannot function
  without some way to resolve "who is making this request," but token issuance/validation
  is conceptually `auth`-module territory per
  [AUTHENTICATION.md §Centralized authorization](../08-security/AUTHENTICATION.md#centralized-authorization)
  and the `AuthProvider` adapter-boundary language — and `apps/api/auth/` doesn't exist yet
  (`GRX-AUTH-002`). Resolved by adding a narrowly-scoped `get_current_user_id()` to the
  `permissions` module: it only *verifies* an already-issued JWT cookie and extracts the
  user id — genuine, working code (hand-craft a validly-signed JWT with the same
  `jwt_signing_key` and it correctly authenticates), not a stub — but it issues nothing.
  `GRX-AUTH-002`'s login endpoint is what will actually mint that cookie. This mirrors how
  `GRX-FOUND-004`'s `apiFetch` was real code nothing called yet.
- Added `apps/api/src/growixa_api/permissions/repositories.py`:
  `user_has_permission(session, user_id, code) -> bool`, an ORM query joining
  `Permission`/`RolePermission`/`UserRole` — the only place in this module that talks to
  the database directly, per [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md).
  Note: `permissions`'s dependency table only lists `roles`, but this query necessarily also
  reads `users.models.UserRole` (owned by `users`) since a permission check inherently spans
  both — a read-only cross-module dependency, not a boundary violation (comparable to how
  `analytics` is documented to read across all modules).
- Added `apps/api/src/growixa_api/permissions/dependencies.py`:
  - `get_current_user_id(request) -> uuid.UUID` — decodes the `access_token` cookie via
    PyJWT (`HS256`, `Settings.jwt_signing_key`), 401s on missing/invalid/expired.
  - `RequirePermission` — a callable class (not a closure) so a route-protection audit can
    `isinstance()`-check a route's dependency tree; depends on `get_current_user_id` and
    `get_session`, 403s if `user_has_permission` is false, otherwise returns the user id.
  - `require_permission(code)` — the public factory matching the exact name used in
    [AUTHENTICATION.md](../08-security/AUTHENTICATION.md).
- Added `apps/api/tests/test_require_permission.py`: allowed / 403 / 401-missing-token /
  401-invalid-token cases, using the **real** Viewer role seeded by `GRX-AUTH-001`'s
  migration (Viewer has `company.settings.view`, not `users.manage`, per RBAC.md) — no
  fixture-only fake roles, the actual Sprint 1 seed data.
- Added `apps/api/tests/test_protected_routes_audit.py`, per
  [TEST_STRATEGY.md §RBAC authorization tests](../10-testing/TEST_STRATEGY.md#rbac-authorization-tests):
  walks every `APIRoute` in `create_app()` and asserts each one not explicitly allowlisted
  as public is guarded by a `RequirePermission` dependency somewhere in its dependency tree.
  Trivially true today (only `/health`, allowlisted) but becomes a real regression trap the
  moment the first protected route ships.
- **Bug found and fixed (test infra, not app code)**: `growixa_api.db`'s async engine/pool
  is a module-level singleton shared for the whole test process; pytest-asyncio's default
  function-scoped event loop meant a second async DB-touching test could be handed a pooled
  asyncpg connection opened under a *different* (already-closed) loop, raising
  `RuntimeError: ... attached to a different loop`. Fixed by setting
  `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope = "session"` in
  `pyproject.toml` so the whole test session shares one loop.
- **Bug found and fixed (test infra)**: the route-protection audit initially found zero
  `APIRoute`s at all — this FastAPI version (`0.139.2`) doesn't flatten
  `include_router()`'s routes directly into `app.routes` the way older versions did; it
  wraps them in an internal `_IncludedRouter` object exposing the real routes via
  `.original_router.routes`. Fixed by recursing through that wrapper (via `getattr`, not by
  importing the private class) rather than assuming a flat route list.
- Also added `extend-immutable-calls = ["fastapi.Depends", ...]` to ruff's `flake8-bugbear`
  config — B008 otherwise flags FastAPI's own required `Depends(...)`-in-defaults pattern as
  a mutable-default-argument bug, which it isn't.
- Verified: `ruff`/`format --check`/`mypy` clean across 23 source files; `pytest` 9 passed
  (4 pre-existing + 1 seed-data + 4 new); rebuilt the `api` image, `/health` unaffected.
- `GRX-RBAC-001` marked `DONE`. `GRX-COMPANY-001` (depended on this and `GRX-FOUND-005`,
  both now done) is newly `READY`, alongside the already-`READY` `GRX-AUDIT-001`,
  `GRX-TEST-001`, `GRX-TEST-002`.
- Commit: `7e77444`.

## 2026-07-24 — GRX-AUTH-001: Users, roles, permissions schema + seed

- **Task-ordering note**: picked this task ahead of the other three tasks that became
  `READY` alongside it after `GRX-FOUND-005` (`GRX-AUDIT-001`, `GRX-TEST-001`,
  `GRX-TEST-002`), even though the tracker doesn't encode the dependency: `audit_logs`
  (`GRX-AUDIT-001`) has `actor_user_id uuid FK → users.id` per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md), so the `users` table has to exist
  first. The tracker's `GRX-AUDIT-001` row only lists `GRX-FOUND-005` as a dependency — this
  is a real gap worth fixing in a future tracker-hygiene pass, not something to silently
  work around by reordering without a note.
- Added `apps/api/src/growixa_api/{roles,permissions,users}/models.py`: SQLAlchemy 2.0
  models (`Role`; `Permission`, `RolePermission`; `User`, `UserRole`) matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly — UUID PKs generated
  application-side (`default=uuid.uuid4`, no `pgcrypto` dependency), `CITEXT` email (case-
  insensitive per the schema doc), the `status IN ('ACTIVE','DISABLED')` check constraint.
  Split module-by-module per [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)
  (`permissions` owns `role_permissions`; `users` owns `user_roles`, since it references
  `assigned_by_user_id`). Only `models.py` was added per module — no `api/`, `services/`,
  `repositories/` yet, since this task's scope is schema + seed only (those layers have no
  real logic to hold yet; endpoints are `GRX-AUTH-002`/`GRX-RBAC-001`).
  `migrations/env.py` now imports all three model modules so `Base.metadata` is fully
  populated for `--autogenerate`.
- Added migration `d330e8b64b48` (autogenerated table DDL, hand-edited to add
  `CREATE EXTENSION IF NOT EXISTS citext` and seed data): creates all 5 tables in FK-safe
  order, then seeds the 6 Sprint 1 roles, 6 permission codes, and the full 16-row
  `role_permissions` matrix, exactly per [RBAC.md](../08-security/RBAC.md)'s role →
  permission table. Seed rows use fixed (not per-run-random) UUIDs hardcoded in the
  migration, generated once, so the migration is reproducible. Uses `sa.table()`/
  `op.bulk_insert()` proxies rather than importing the ORM models directly, per Alembic's
  own guidance (so a future model change can't silently rewrite this migration's meaning).
  Downgrade drops the 5 tables and the `citext` extension — full round-trip to empty.
- Added `apps/api/tests/test_auth_schema_seed.py`: an integration-tier test (real Postgres,
  same reasoning as `GRX-FOUND-005`'s migration test) asserting the *exact* set of 6 role
  names, *exact* set of 6 permission codes, and the *exact* role→permission matrix (not just
  row counts) match RBAC.md after `alembic upgrade head`.
- Verified: `ruff check`/`format --check`/`mypy` clean; `pytest` 4 passed (2 health + the
  generic migration round-trip from `GRX-FOUND-005`, now covering both migrations, + this
  task's seed-data test); spot-checked seed data directly via `psql` in the `postgres`
  container (6 roles, 6 permission codes, 16 `role_permissions` rows); rebuilt the `api`
  image and confirmed `podman compose exec api alembic current` reports the new head.
- **Known gap, explicitly not addressed in this task**: `LOCAL_DEVELOPMENT.md` documents a
  `python -m growixa_api.cli.seed_first_admin` command "finalized when `GRX-AUTH-001` ... is
  implemented," but no tracker task actually owns it, and it needs Argon2id password
  hashing, which is `GRX-AUTH-002`'s explicit scope (`apps/api/auth/`). Building it here
  would mean creating `apps/api/auth/` ahead of the task that owns that module. Left as a
  gap to resolve when `GRX-AUTH-002` is picked up (or as its own tracker line item) rather
  than silently expanding this task's scope into another module's territory.
- `GRX-AUTH-001` marked `DONE`. `GRX-RBAC-001` (its only dependency was this task) is newly
  `READY`, alongside the already-`READY` `GRX-AUDIT-001`, `GRX-TEST-001`, `GRX-TEST-002`.
- Commit: `daf9bc7`.

## 2026-07-24 — GRX-FOUND-004: Next.js application foundation

- Added `apps/web/src/lib/api-client.ts`: a small typed `fetch` wrapper (`apiFetch<T>`) that
  prepends `getApiUrl()`, sends `credentials: "include"` (auth is HttpOnly-cookie-based per
  [DEC-GRX-014](DECISIONS.md), not bearer tokens), and throws a typed `ApiError` on any
  non-2xx response instead of leaving every caller to check `response.ok`. Not yet consumed
  by any UI — nothing calls the API from the frontend until `GRX-AUTH-002`/`GRX-USER-002` —
  but this is genuine, working infrastructure (foundation work, explicitly allowed to stand
  alone per [DEFINITION_OF_DONE.md §No placeholder completion](DEFINITION_OF_DONE.md#no-placeholder-completion)),
  not a stub.
- Added `apps/web/src/app/not-found.tsx` as the routing-baseline piece: Next.js App Router's
  convention for a real custom 404, verified to actually return 404 (not just exist).
- Reworded `apps/web/src/app/page.tsx`'s placeholder copy — it referenced `GRX-FOUND-002`
  ("Placeholder page for local Docker Compose validation"), which was accurate when it was
  added as a stopgap for that task's stack validation, but this task is what actually
  establishes the app shell, so the copy no longer references a specific task.
- No changes to `.env.example`/env config — `NEXT_PUBLIC_API_URL` and `getApiUrl()` were
  already established in `GRX-FOUND-001`/`GRX-FOUND-002` and remain the single env surface.
- Verified: `npm run lint`, `format:check`, `typecheck`, and `build` all pass. Local smoke
  test (`next start`): `/` → 200 (renders "Growixa"), an unknown route → 404. Rebuilt the
  `web` Docker image and re-verified through the full Compose stack: all 5 services healthy,
  `GET /` → 200, unknown route → 404, `api`'s `/health` unaffected.
- No automated test harness was added — `GRX-TEST-002` (test runner config, component test
  harness, one e2e smoke test) is a separate, already-tracked task that owns building that
  infrastructure; this task's "smoke test loads root route" requirement was satisfied via
  the manual/scripted verification above, consistent with how `GRX-FOUND-002`'s smoke-test
  requirement was satisfied before any test runner existed.
- `GRX-FOUND-004` marked `DONE`. `GRX-AUDIT-001`, `GRX-AUTH-001`, `GRX-TEST-001` (already
  `READY` from `GRX-FOUND-005`), and `GRX-TEST-002` (newly `READY` — its only dependency was
  this task) are all now `READY`.
- Commit: `8269436`.

## 2026-07-24 — GRX-FOUND-005: PostgreSQL connectivity + Alembic foundation

- Added `apps/api/src/growixa_api/db.py`: SQLAlchemy 2.0 `DeclarativeBase` (`Base`), a
  module-level async engine (`pool_pre_ping=True`) built from `Settings.database_url`, an
  `async_sessionmaker`, and a `get_session()` FastAPI dependency (async generator) for
  future modules (`GRX-AUDIT-001`, `GRX-AUTH-001`, etc.) to depend-inject.
- Initialized Alembic with the async template (`alembic init -t async migrations`):
  `apps/api/alembic.ini` and `apps/api/migrations/{env.py,script.py.mako,versions/}`.
  `migrations/env.py` is wired to read `DATABASE_URL` from `growixa_api.config.get_settings()`
  (overriding `alembic.ini`'s placeholder URL at runtime, so there is one source of truth for
  the connection string) and sets `target_metadata = Base.metadata` for future autogeneration.
  Customized `script.py.mako` to match this project's ruff config (`collections.abc.Sequence`,
  `X | Y` union syntax) so every future generated migration passes lint without manual edits.
- Added the first migration (`migrations/versions/9ca09405a2b3_initial_empty_migration.py`):
  genuinely empty `upgrade`/`downgrade` (`pass`) — establishes the `alembic_version`
  tracking table baseline only; no application tables exist yet (those are `GRX-AUDIT-001`/
  `GRX-AUTH-001`/`GRX-COMPANY-001`, per [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md)).
- Added `apps/api/tests/test_migrations.py`: an integration-tier smoke test (real Postgres
  required, per [TEST_STRATEGY.md §Database migration tests](../10-testing/TEST_STRATEGY.md#database-migration-tests))
  that runs `alembic upgrade head` → asserts the head revision is recorded → `alembic
  downgrade base` → asserts no revision is recorded → `upgrade head` again, using Alembic's
  Python API directly (a plain sync test, since Alembic's async `env.py` calls
  `asyncio.run(...)` internally and cannot be nested inside pytest-asyncio's event loop).
- **Bug found and fixed**: `greenlet` — required by SQLAlchemy's async engine — was missing
  from `apps/api/pyproject.toml`. It happened to resolve as a transitive dependency inside
  the Docker image's `pip install`, masking the gap, but was absent from the local `uv`-
  managed dev venv, so any async engine use (including the `/health` checks added in
  `GRX-FOUND-002`) would have failed outside Docker. Added `greenlet>=3.1` as an explicit
  dependency.
- **Bug found and fixed**: `apps/api/Dockerfile` only ever `COPY`'d `pyproject.toml`,
  `README.md`, and `src/` — `alembic.ini` and `migrations/` were never in the image or the
  `compose.yaml` bind mounts, so `docker compose exec api alembic upgrade head` (this task's
  literal acceptance criterion, and the command documented in
  [LOCAL_DEVELOPMENT.md](../11-devops/LOCAL_DEVELOPMENT.md)) would have failed. Added them to
  the Dockerfile `COPY` steps and added matching bind mounts in `compose.yaml` (consistent
  with the existing `src` mount) so migrations stay live-editable like application code.
- Verified: `ruff check` 0 errors, `ruff format --check` pass, `mypy` 0 issues (11 source
  files), `pytest` 3 passed (2 health + 1 migration round-trip against real Compose
  Postgres). `alembic upgrade head` / `alembic current` succeed both from the host (via
  `localhost:5433`) and via `podman compose exec api alembic upgrade head` against the
  running Compose Postgres.
- `GRX-FOUND-005` marked `DONE`. `GRX-AUDIT-001`, `GRX-AUTH-001`, and `GRX-TEST-001` (all
  depend only on `GRX-FOUND-005`) are now `READY`, alongside the still-open `GRX-FOUND-004`.
- Commit: `0cff500`.

## 2026-07-23 — GRX-FOUND-003: FastAPI application foundation

- Refactored the ad hoc FastAPI app added during `GRX-FOUND-002` validation into a proper
  app-factory structure: `growixa_api/app.py` (`create_app()`, sets title/version, mounts
  the health router), `growixa_api/health.py` (`GET /health` route plus three isolated,
  independently-testable `_check_postgres`/`_check_redis`/`_check_rabbitmq` functions),
  `growixa_api/main.py` (thin `app = create_app()` uvicorn entrypoint — unchanged Docker
  CMD reference).
- OpenAPI docs (`/docs`, `/redoc`, `/openapi.json`) are enabled — this is FastAPI's default
  when nothing disables it; verified reachable (200) rather than left as an unverified
  assumption.
- Added `apps/api/tests/test_health.py`: two tests (all-dependencies-ok, one-dependency-
  degraded) that assert full response-body shape, not just status code, per
  [TEST_STRATEGY.md §Rules preventing shallow tests](../10-testing/TEST_STRATEGY.md#rules-preventing-tasks-from-being-marked-done-with-shallow-tests).
  Tests monkeypatch the three check functions directly (no real DB/Redis/MQ connection) and
  set required `Settings` env vars via `monkeypatch.setenv` + `get_settings.cache_clear()`,
  so the unit suite runs without any backing service, per
  [TEST_STRATEGY.md §Backend unit-test approach](../10-testing/TEST_STRATEGY.md#backend-unit-test-approach).
- Fixed a stale `pyproject.toml` mypy override (`growixa_api.tests.*`, a module path that
  never matched the actual `apps/api/tests/` layout) to `tests.*`, and added
  `apps/api/tests/__init__.py`.
- Verified: `ruff check` 0 errors, `ruff format --check` pass, `mypy` 0 issues (7 source
  files), `pytest` 2 passed. Rebuilt the `api` Docker image and re-validated the full
  Compose stack: all 5 services healthy, `GET /health` → 200
  `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`,
  `GET /docs` and `GET /openapi.json` → 200.
- `GRX-FOUND-003` marked `DONE`. `GRX-FOUND-004` (Next.js application foundation) and
  `GRX-FOUND-005` (PostgreSQL connectivity + Alembic foundation) are both now `READY`
  (only one to be worked at a time per [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md)).
- Commit: `c69eb10`.

## 2026-07-23 — GRX-FOUND-002: Docker Compose local environment

- Added `compose.yaml` defining `postgres` (16-alpine), `redis` (7-alpine), `rabbitmq`
  (3-management-alpine), `api`, and `web` services on a shared bridge network, with
  healthchecks and `depends_on: condition: service_healthy` gating startup order.
- Added `apps/api/Dockerfile` (python:3.13-slim, editable install, `uvicorn --reload`) and
  `apps/web/Dockerfile` (node:22-alpine, `npm run dev`) — local-development images, not
  production-optimized (no multi-stage/distroless build or non-root hardening yet).
- Added a minimal `growixa_api` app (`main.py`, `config.py`) with a real `GET /health`
  endpoint that checks Postgres/Redis/RabbitMQ connectivity, so the compose stack has
  something functional to validate against ahead of `GRX-FOUND-003`.
- Added a minimal Next.js `apps/web/src/app/` (App Router `layout.tsx`/`page.tsx`) and
  `next.config.mjs` so `apps/web` builds/serves, ahead of `GRX-FOUND-004`.
- Added root `.env.example` documenting all Compose-level variables (DB/MQ credentials,
  host port mappings, JWT signing settings per [DEC-GRX-014](DECISIONS.md)).
- Validated end-to-end: `podman compose up -d` brings up all 5 services `healthy`;
  `GET /health` returns `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`;
  the web root returns HTTP 200.
- Fixed a podman-compose bug encountered during validation: a multi-word `CMD`-array
  healthcheck test (`api` service's `python -c "..."` health check) was being incorrectly
  re-split into separate argv tokens by podman-compose, breaking the check even though the
  app itself was healthy. Switched to `CMD-SHELL` form in `compose.yaml`, which
  podman-compose preserves as a single string correctly.
- Local-environment note (not a repo change): the default `POSTGRES_PORT=5432` in
  `.env.example` can collide with a natively-running Postgres on the host; `.env` is
  gitignored so this is a per-machine `.env` adjustment, not a schema/compose change.
- `GRX-FOUND-002` marked `DONE`; `GRX-FOUND-003` (FastAPI application foundation) now `READY`.
- Commit: `76354d2`.

## 2026-07-23 — GRX-FOUND-001: repository and development tooling

- First Sprint 1 implementation task. Added `apps/api/` (FastAPI/Python tooling: `ruff`,
  `mypy`, `pytest`, `.venv`, `.env.example`) and `apps/web/` (Next.js/TypeScript tooling:
  ESLint 9 flat config, Prettier, `tsc`, `.env.example`) — tooling and config only, no
  application code yet.
- Added `.pre-commit-config.yaml` wiring lint/format/type-check for both apps plus standard
  hygiene hooks; installed the git hook.
- Fixed 3 `npm audit` findings (moderate `postcss` XSS, high `sharp`/`libvips` CVEs, both
  pinned internally by Next.js on every current release) via a `package.json` `overrides`
  block. Verified 0 vulnerabilities after.
- All required checks verified passing: `ruff check`, `ruff format --check`, `mypy`,
  `eslint`, `prettier --check`, `tsc --noEmit`, `pre-commit run --all-files`.
- `GRX-FOUND-001` marked `DONE`; `GRX-FOUND-002` (Docker Compose) now `READY`.
- Commit: `42f8b37`.

## 2026-07-22 — Documentation gate closed; Sprint 1 authorized

- Added standalone [`docs/10-testing/TEST_STRATEGY.md`](../10-testing/TEST_STRATEGY.md) and
  [`docs/11-devops/LOCAL_DEVELOPMENT.md`](../11-devops/LOCAL_DEVELOPMENT.md), closing the
  last two distributed-only gaps in the Development Readiness Gate.
- [`DEVELOPMENT_READINESS.md`](DEVELOPMENT_READINESS.md) now shows every mandatory Slice 1
  gate item as `PASS` with a standalone document as evidence.
- Sprint 1 implementation authorized to begin at `GRX-FOUND-001`.

## 2026-07-22 — Slice 1 readiness: architecture, data, security baseline

- Resolved [OQ-001](OPEN_QUESTIONS.md) via [DEC-GRX-014](DECISIONS.md): application-managed
  FastAPI authentication (Argon2id, rotating refresh tokens, HttpOnly/Secure/SameSite
  cookies, centralized RBAC, OIDC/SSO adapter boundary for later). No Keycloak/third-party
  provider in MVP.
- Added `docs/04-architecture/` (SYSTEM_ARCHITECTURE, MODULE_BOUNDARIES,
  BACKGROUND_JOB_ARCHITECTURE), `docs/05-data/` (DATA_MODEL, ERD, DATABASE_SCHEMA), and
  `docs/08-security/` (SECURITY_ARCHITECTURE, AUTHENTICATION, RBAC, THREAT_MODEL) for Slice
  1 scope.
- Added [`MASTER_TASK_TRACKER.md`](MASTER_TASK_TRACKER.md) seeded with Sprint 1 tasks and
  [`SPRINT_01_FOUNDATION.md`](../14-sprints/SPRINT_01_FOUNDATION.md).
- Development Readiness Gate for Slice 1 reached PASS (with two items still in distributed
  form, closed in the entry above).
- Commit: `cc46e6d`.

## 2026-07-22 — Scope correction: Growixa remains the broader growth platform

- Corrected an earlier documentation pass that had read as a full product pivot. Logged as
  [DEC-GRX-001](DECISIONS.md): Growixa's positioning stays "AI-powered growth and marketing
  automation platform"; only the **first release** scope narrowed to email/social/contacts/
  AI-assist/scheduling/analytics. SEO/AEO/GEO/website-intelligence work from the original
  discovery PRD is preserved and mapped to future releases V1.5–V3 in
  [`FUTURE_SCOPE_SEO_AEO_GEO.md`](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md), not dropped.
- Relabeled `docs/archive/source-prd-seo-aeo-geo-website-intelligence/` (previously named as
  if it were an unrelated/superseded product) to reflect it as valid future-release source
  material.
- Added `docs/01-product/` (PRODUCT_VISION, PRD, MVP_SCOPE, ROADMAP,
  FUTURE_SCOPE_SEO_AEO_GEO), `docs/02-features/FEATURE_CATALOG.md` (stub), and
  `docs/00-project-control/` core docs (PROJECT_STATUS, ASSUMPTIONS, OPEN_QUESTIONS,
  DECISIONS, DEFINITION_OF_DONE, DEVELOPMENT_READINESS) and
  `docs/12-development/AGENT_EXECUTION_RULES.md`.
- Commit: `50b93cf`.

## 2026-07-22 — Repository initialized

- `git init`, `.gitignore`, root `README.md`.
- Original SEO/AEO/GEO discovery PRD (from an uploaded `.docx`) converted to Markdown and
  placed under `docs/archive/` (naming corrected in the entry above).
- Commit: `92bbdad`.
