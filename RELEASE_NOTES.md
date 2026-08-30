# 🚀 Growixa Release Notes

---

## 🟡 [v0.5.8-rc1] (Upcoming Release) — 2026-08-30

> **Release Tag**: `v0.5.8-rc1`
> **Platform Status**: 🟡 Staging / Preview
> **Target Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added & Enhanced
- **Tabbed Email Template Library Redesign (`GRX-EMAIL-016`)**:
  - **Top-Level Tabs**: 📁 **"My Templates"** (account custom library) vs 🌟 **"Default Templates"** (Growixa starter library) with dynamic count badges.
  - **Unified Filtering**: Shared search input, sort selector (*Last updated*, *Name*), category filter pills (*All*, *Marketing*, *Onboarding*, *Announcement*, *Newsletter*, *Transactional*), and Grid/List switcher across both tabs.
  - **Interactive KPI Stat Cards**: Clickable overview cards for quick tab switching.
  - **Smart Empty State**: 1-click CTA button to explore default templates when an account has 0 custom designs.
- **Side-by-Side Live Preview Editor Modal for Platform Admin**:
  - Spacious 2-column modal for creating (`+ New default template`) and editing platform templates with real-time live preview iframe and Desktop 🖥️ / Mobile 📱 device toggles.
  - Full toolbar (Search + Category Pills + Grid/List Views) added to `/platform/templates`.
- **Reusable Template Preview Modal**:
  - Extracted shared presentational component into `apps/web/src/components/template-preview/`.

---

## 🟡 [v0.5.7-rc1] (Upcoming Release) — 2026-08-28

> **Release Tag**: `v0.5.7-rc1` (points at `ba576e6`)
> **Platform Status**: 🟡 Staging / Preview — tag pushed, but every `deploy-uat` run failed
> immediately (~6s) due to this GitHub account's Actions minutes being exhausted for the
> billing cycle; nothing has actually deployed yet. Re-push the tag (or re-run the workflow)
> once minutes reset.
> **Target Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🐛 Fixed
- **E2E CI seed script `NOT NULL` failure (`GRX-BUG-006`)**: the e2e seed script created `UserRole` rows without `account_id`, failing every `e2e` CI run on `main` since 2026-08-23 before any test executed.
- **Password-toggle `aria-label` collision (`GRX-BUG-007`)**: the "Show/Hide password" toggle button's `aria-label` collided with the password field's own label, breaking Playwright's `getByLabel("Password")`.
- **Stale login button assertion (`GRX-BUG-008`)**: e2e specs expected a "Sign in" button that doesn't exist — updated to match the real "Login to Growixa" copy.
- **Stale dashboard welcome assertion (`GRX-BUG-009`)**: e2e spec asserted pre-redesign empty-state copy ("Welcome to Growixa") that no longer renders — updated to match the real `PageHeader` welcome text.
- **Team invite e2e flow (`GRX-BUG-010`)**: fixed a Playwright strict-mode collision (toast vs. persistent confirmation panel), a broken invite-token extraction (was sending the full URL instead of the token), and gave the e2e seed account a proper subscription so quota checks pass. Closes out the entire `GRX-BUG-006`→`010` chain — the full e2e suite is green for the first time.

### ⚙️ Infrastructure
- **Reduced GitHub Actions minutes usage**: docs-only changes skip the full CI suite, superseded runs get cancelled automatically, and pip/npm/Docker/Playwright caching cuts job time. Dependency vulnerability scans moved to a weekly schedule.
- **Production deploys now promote the tested UAT image** instead of re-testing and rebuilding from source when a matching release-candidate image already exists — falls back to the original full build automatically otherwise.
- **Added `scripts/deploy_manual.sh`**: an interactive manual VPS deployment script for UAT/Production with pre-flight tests and Telegram notifications, plus Claude skill adapter pointers for all 5 canonical Growixa skills.
- **Deep Docker cleanup on every deploy**: `deploy_manual.sh` now auto-prunes buildx cache, dangling images, and stray build artifacts to keep server/local disk usage minimal.
- **CI notification dependency migration**: moved from `iitdeveloper-git-shared-workflows` to the stable `shared-workflows@v1` release, then to `deploykit/actions/notify@v1` — maintained-dependency swap, no behavior change.

### 📋 Product
- **Lead Intelligence brainstorm** (Find → Understand → Act framing) with competitive-positioning research — idea capture and a `DEC-GRX-033` traceability addendum only; nothing scheduled or ticketed yet.

### 🧹 Housekeeping
- Cleaned up 28 stale `pr_reviews/` bookkeeping/small-fix handoffs and ~115 already-merged Git branches.

---

## 🟢 [v0.5.6] — 2026-08-25

> **Release Tag**: `v0.5.6`
> **Release Date**: August 25, 2026
> **Platform Status**: 🟢 Promoted to Production
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added & Enhanced
- **Executive Analytics Overview (`GRX-DASHBOARD-004`)**:
  - **6th KPI Stat Card — Click-to-Open Rate (`🎯 CTOR`)**: Added global CTOR card on `/dashboard` evaluating content quality (`Unique Clicks ÷ Unique Opens × 100`).
  - **Live Recipient Activity Stream**: Added real-time recipient activity feed component (`LiveActivityStream.tsx`) with pulse badge, contact email badges, campaign links, and human-readable time-ago timestamps (`just now`, `2m ago`, `15m ago`).
  - **Recent Activity API Endpoint**: Backend database queries returning recipient open and click events across campaigns.
- **Strict Production Deployment Gate Policy**: Added strict release tag rule in `AGENTS.md` requiring explicit user approval before deploying production release tags (`vX.Y.Z`).

---

## 🟢 [v0.5.4] — 2026-08-25

> **Release Tag**: `v0.5.4`
> **Release Date**: August 25, 2026
> **Platform Status**: 🟢 Promoted to Production

### 🚀 Added & Enhanced
- **Total vs Unique Email Engagement Metrics (`GRX-CAMP-010`)**:
  - Enhanced **Delivery report** card in campaign view with **Unique Opens** (`17 (22%) ↳ 22 total views`) and **Unique Clicks** (`17 (22%) ↳ 70 total clicks · 100% CTOR`).
  - Extended API endpoints and schemas with `total_opened`, `total_clicked`, and golden CTOR calculations.

---

## 🟢 [v0.5.2] — 2026-08-24

> **Release Tag**: `v0.5.2`
> **Release Date**: August 24, 2026
> **Platform Status**: 🟢 Promoted to Production

### 🚀 Added & Enhanced
- **Campaign List Inline Performance Metrics (`GRX-CAMP-009`)**:
  - Added **Performance** column on `/dashboard/campaigns` list view with open rate & click rate pills and exact delivery counts.
  - Zero N+1 batch query aggregation (`get_campaigns_metrics_batch`).
- **Postal Reverse DNS & SSL Alignment**:
  - Configured OVH VPS PTR record (`postal.iitdeveloper.com`) and verifiedNetlify CNAME + SSL for tracking domain `track.iitdeveloper.com`.

---

## 🟢 [v0.5.1] — 2026-08-24


> **Release Tag**: `v0.5.1`
> **Release Date**: August 24, 2026
> **Platform Status**: 🟢 Promoted to Production
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added & Enhanced
- **Dynamic Email Personalization Engine & Merge Tags (`GRX-CONTENT-001` / `DEC-GRX-036`)**:
  - Full support for recipient-scope merge tokens (`{{first_name}}`, `{{last_name}}`, `{{email}}`, `{{phone}}`, and account-authorized custom fields like `{{school_name}}`).
  - Full support for account-scope merge tokens (`{{company_name}}`, `{{website_url}}`, `{{sender_name}}`).
  - Fallback default filter syntax: `{{ first_name | default:"there" }}` preventing missing-token errors.
  - Strict security guardrails: regex-bounded parsing (no SSTI vulnerability), prohibited internal columns (`source`, `status`, `id`), and automatic HTML escaping for untrusted recipient values.
  - Real-time personalization rendering across both API test-send and worker bulk dispatch.
- **In-Flight Live Campaign Emergency Stop (`GRX-CAMP-008`)**:
  - Immediate campaign cancellation for actively sending campaigns (`SENDING` / `DISPATCHING`) via `POST /campaigns/{id}/cancel`.
  - Redis broadcast interruption flag and real-time database status sync halting remaining queued dispatch batches mid-flight.
  - Automatic quota and credit usage reconciliation returning unsent messages back to account balances.
- **Postal & Self-Hosted SMTP Live Webhooks (`GRX-EMAIL-012`)**:
  - Live webhook receiver (`POST /webhooks/postal`) for delivery receipts, open tracking, click tracking, and bounce telemetry.
  - Automatic suppression entry creation on hard bounces to safeguard sender reputation.
- **Self-Hosted SMTP Relay TLS Support (`GRX-SMTP-002`)**:
  - Configurable TLS certificate verification and STARTTLS negotiation for custom self-hosted Postal, Stalwart, and internal SMTP gateways.
- **Sender Identity Deletion Guard & Auto-Reassignment (`GRX-EMAIL-016`, `GRX-EMAIL-017`)**:
  - Guarded deletion preventing removal of sender identities mapped to active campaigns.
  - Auto-reassignment of orphaned identities when provider connections are updated.

---

## 🟢 [v0.4.4] — 2026-08-23

> **Release Tag**: `v0.4.4`
> **Release Date**: August 23, 2026
> **Platform Status**: 🟢 Promoted to Production
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added & Redesigned
- **Luminous Split-Screen & Unified Canvas Auth Redesign (`GRX-AUTH-007`)**: Complete visual and architectural overhaul of customer authentication pages (`/login` and `/register`).
  - **Unified Canvas & Edge-to-Edge Waves**: Smooth continuous background canvas with animated glowing cyan-to-purple wave ribbons.
  - **Floating 3D Metric Cards**: Interactive, responsive metric cards featuring campaign performance (`4.82x Growth`), deliverability gauge (`99.4% Delivered`), AI Audience Score (`High Intent`), and customer social proof testimonials.
  - **Zero Layout Shift Tab Switching**: Shared `<AuthSplitLayout>` shell preserving canvas geometry while toggling between Login and Sign up modes.
  - **Brand & Visual Polish**: Official Growixa brand horizontal asset in showcase header, scaled typography hierarchy, 56px high-contrast CTA button, and accessible form inputs.
  - **Redirect Security Hardening**: Sanitized relative-only path redirection preventing open redirect vulnerabilities across email/password and Google SSO flows.
  - **Full Test Suite Validation**: 287 passing unit tests across 51 test suites.

- **Google OAuth 2.0 & SSO Authentication (`GRX-AUTH-006`)**: Added 1-click Google Sign-In and Registration on `/login` and `/register` with Redis-backed CSRF state protection, OpenID Connect profile exchange, `oauth_identities` linking table, and seamless HttpOnly JWT session issuance.
- **Contact List Members API (`GET /contacts/lists/{list_id}/members`)**: Added dedicated backend endpoint returning active members of a contact list with strict multi-tenant account scoping.
- **Live Search in Segments & Lists Modals**: Added instant 0ms client-side search filtering across `first_name`, `last_name`, `email`, and `phone` in both the "View Segment Members" modal and "Manage List" modal, with dynamic counter feedback (`Matching Contacts (X of Y)`) and 1-click search clear.
- **Guarded Segment Deletion & Lifecycle Protection**: Automatically prevents deletion of segments targeted by active campaigns (`DRAFT`, `SCHEDULED`, `DISPATCHING`, `SENDING`) with a helpful `409 Conflict` naming the blocking campaigns; cleanly unlinks completed campaigns (`SENT`, `CANCELLED`, `FAILED`).
- **Dynamic Segment Editing & Rule Re-evaluation**: Edit segment name, description, and rules with real-time membership recalculation across standard and custom fields.
- **API & Worker Recipient Resolution Parity**: Added full support for `first_name`, `last_name`, `phone`, and tag `contains` operator across both API segment evaluator and worker recipient loader, guaranteeing preview and send agreement.
- **Architecture Decision DEC-GRX-036**: Defined channel-agnostic personalization tokens architecture covering recipient and account token scopes without template injection risks.

---

## 🟢 [v0.4.0] — 2026-08-20

> **Release Tag**: `v0.4.0`
> **Release Date**: August 20, 2026
> **Platform Status**: 🟢 Promoted to Production
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added
- **CSV Import Smart Auto-Matching & 1-Click Custom Fields Creation**: Auto-maps common B2B headers (`company`, `city`, `address`, `website`, `category`, `linkedin`, `phone_primary`, etc.) against existing schema; provides a 1-click button to automatically create and map missing custom fields.
- **Custom Fields in Contact Detail Modal & Segment Builder**: View, edit, and filter custom fields in a 2-column grid inside the contact detail modal and segment rule builder with automatic HTML entity decoding.
- **Bulk Move to Tag & Bulk Add to List**: Added **`🏷️ Move to Tag`** and **`📋 Add to List`** buttons to the contacts floating bulk action toolbar for 1-click batch categorization into existing or newly created tags and lists.
- **Filter Contacts by Tag**: Added quick tag filter dropdown in the contacts table toolbar.

### 🛠️ Fixed & Improved
- **Telegram Release & Deployment Notifications (`GRX-TELEGRAM-NOTIFY`)**: Integrated automated Telegram group notifications into `deploy-production.yml` and `deploy-uat.yml` using the central DeployKit (`iitdeveloper-git/deploykit/actions/notify@v1`) action.
- **Email Template Personalization Token Insertion**: Fixed content synchronization in visual editor so clicking token buttons (`+ First Name`, `+ Email`, `+ Company Name`) immediately reflects in both the visual editor and live HTML preview.
- **AI Assistant Real Brand Voice Integration (`GRX-BUG-002`)**: Brand Voice slide-over drawer now fetches live profile data from `GET /brand/profile` to display real brand voice, core tone, required facts, and guardrails.
- **AI Assistant Quick Starters (`GRX-BUG-003`)**: Updated starter cards with clean parameter loading (channel, prompt, tone, length) without clobbering selected campaign or audience context.
- **AI Assistant Multi-Variation Rendering (`GRX-BUG-004`)**: Removed the 3-item display limit so all generated variations (1 to 7) are rendered; replaced static timestamps with real relative time.
- **Quality & Dead Code Cleanup (`GRX-QA-001`)**: Removed dead `.notificationButton`/`.notificationBadge` styles from `history-page.module.css` and removed obsolete `QualityMetrics` types.

---

## ✅ [v0.3.0] — 2026-08-20

> **Release Tag**: `v0.3.0`
> **Release Date**: August 20, 2026
> **Platform Status**: 🟢 Production release promoted from UAT `v0.3.0-rc2`
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added
- **Site Favicon & Apple Touch Icon**: High-resolution 512×512 PNG brand favicon and Apple Touch Icon (`/icon.png`, `/apple-icon.png`) automatically linked across the application.

### 🛠️ Fixed & Hardened (Infrastructure & CI/CD)
- **Production & UAT Deploy Workflows**: Added automated permission pre-checks, directory synchronization, and project isolation in `.github/workflows/deploy-production.yml` and `deploy-uat.yml`.
- **Pre-commit Branch Protection Hook**: Enforced branch naming conventions and main commit prevention (`scripts/check_branch_name.sh`, `make init-hooks`).
- **Database Backup & Retention**: Standardized backup scripts to use the stable `growixa-prod` project name.
- **Postgres Port Conflict Elimination (`GRX-INFRA-005`)**: Production PostgreSQL is Docker-network internal, eliminating host port 5432 collisions during rollout migrations.

---

## ✅ [v0.2.0] — 2026-08-18

> **Release Tag**: `v0.2.0`
> **Release Date**: August 18, 2026
> **Platform Status**: 🟢 Production release promoted from UAT `v0.2.0-rc4`
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)

### 🚀 Added
- **Customer Forgot-Password & Reset Flow**: Full transactional reset email pipeline, generic security responses, and dedicated `/forgot-password` and `/reset-password?token=...` pages with single-use 30-minute token expiration.
- **Customer Help Center (`/docs`)**: Documentation and in-app assistance at `/docs` — instant client-side search, 6 categorised guide suites, markdown viewer with step badges, callout alerts, code copy and a table of contents (`GRX-DOCS-001`).
- **Git-backed docs architecture**: Articles are authored as markdown under `apps/web/src/content/docs/` and compiled to a manifest by `scripts/compile-docs.js` on `predev`/`prebuild`/`pretest`, so documentation is reviewed as source rather than embedded in TypeScript.
- **In-App Contextual Help Drawer**: Slide-over `<HelpDrawer />` across dashboard navigation for reading guides without losing context.
- **Inline `<HelpTooltip />`**: Contextual helpers on campaign and contact forms.
- **Deleted Contacts View & Recovery**: A "Deleted" tab in the Contacts CRM with individual and bulk restoration (`GRX-CONTACT-016`).
- **Agent playbooks**: Tool-neutral `growixa-developer` and `growixa-reviewer` skills under `.agents/skills/`, linked from `AGENTS.md`, covering the pick-up-to-merge sequence, repo-specific traps, the exact commands CI runs, reviewer eligibility and the merge gate (`GRX-AGENT-DEV-001`).

### 🛠️ Fixed
- **Deployment reported success on a broken deploy**: `scripts/deploy_vps.sh` printed a warning on a failed health check and then "Deployment Successfully Completed!" with exit code 0, so cron, CI and operators saw success while the API was down. It now exits non-zero (`GRX-INFRA-003`).
- **Production migrations ran without a restore point**: the deploy script now takes a fresh backup immediately before `alembic upgrade head`, instead of relying on the 02:00 cron backup which could be up to 24 hours stale (`GRX-INFRA-003`).
- **Contact Quota Overflow**: plan quota check when restoring bulk soft-deleted contacts, preventing tier limits being exceeded.
- **Backend CI was red**: ruff import ordering broke across 16 test files when the suites were reorganised into domain folders; resolved and the ordering restored.
- **Frontend CI was red**: `generated-docs.json` formatting discrepancies resolved by appending standard trailing newline to `compile-docs.js`.
- **Backend Linting & Formatting**: resolved E501 line-length violations in `auth/api.py` and `platform_auth/api.py`, removed unused imports in migration tests, and formatted `config.py`.
- **Campaign scheduling redirect**: after a campaign is scheduled successfully, the dashboard now returns to `/dashboard/campaigns` so the scheduled campaign is visible in the all-campaigns workflow.
- **Marketing FAQ removed**: the FAQ section was reverted and the marketing site restored to its `v0.1.0-rc2` state.

### 🔒 Security & Compliance
- **Dependabot 7 CVE Remediation & Triage (`GRX-SEC-002`)**:
  - Triaged all 7 Dependabot alerts (6 high, 1 moderate) in [`docs/08-security/DEPENDABOT_TRIAGE.md`](docs/08-security/DEPENDABOT_TRIAGE.md), confirming all CVEs were isolated to dev/build tooling.
  - Applied package overrides for `postcss@^8.5.26`, `nanoid@^3.3.18`, `js-yaml@^4.3.1`, and version-selector overrides for `brace-expansion@^1.1.0: ^1.1.18` + `brace-expansion@^5.0.0: ^5.0.9`.
  - **`npm audit` reports 0 vulnerabilities** across all dependencies.
  - Next.js preserved at stable `15.5.21` without requiring breaking major upgrades.
  - Automated CI dependency security gates added to `.github/workflows/ci.yml` (`pip-audit` for backend & worker, `npm audit --audit-level=high` for frontend).
- **Strict Zero-Secrets Hard Rule**: Enforced non-negotiable reviewer blocking gate across `AGENTS.md`, `AGENT_EXECUTION_RULES.md`, and `DEFINITION_OF_DONE.md` preventing any code approval, merge, or push with leaked credentials.
- **Tested database restore procedure** (`docs/11-devops/OVH_VPS_DEPLOYMENT.md` §8a): `GRX-NFR-008` requires a restore procedure that is *tested*, not merely defined. The documented procedure was rehearsed against a real dump — restored into a scratch database and compared with the source (60 tables, `accounts` 75, `users` 79, `subscription_plans` 4, matching `alembic_version`). It restores to a scratch database first and promotes by rename, so a damaged database stays recoverable.
- **Restoration Un-Suppress Safeguard**: restoring a soft-deleted contact verifies that previously suppressed addresses remain suppressed (`DEC-GRX-008`).
- **Marketing claim accuracy**: unsupported public claims were removed from the site — a "14-day free trial" with no trial implementation, in-panel cancellation with no cancel endpoint, and an overstated tenant-isolation claim.
- **WCAG 2.2 AA focus indicator**: an `outline: none` with no replacement left keyboard users with no visible focus indicator (SC 2.4.7), against the `GRX-NFR-003` target. Corrected before removal of the affected section.

### ⚡ Infrastructure & DevOps
- Backend and worker test suites reorganised into domain/job folders (`GRX-TEST-ORG-001`) — 62 files moved, rename-only.
- CI: Node runner upgraded to v22; explicit `working-directory` on pytest and npm steps; test environment variables passed to all backend and worker jobs; GHCR authentication during SSH deployment.
- Hardened VPS Deployment (`GRX-INFRA-004`): `docker image prune -f` in `scripts/deploy_vps.sh` moved to run only after the post-deploy health check passes, preserving previous Docker images for immediate rollback on failure.
- `.claude-flow/` and `data/` added to `.gitignore` (`GRX-CHORE-001`).

### 📌 Known Issues
- None.

---

## ✅ [v0.1.0] — 2026-08-17 (Initial Public Release)

> **Release Tag**: `v0.1.0`
> **Release Date**: August 17, 2026
> **Platform Status**: 🟢 **Production & UAT Staging Live**
> **Production URL**: [https://growixa.iitdeveloper.com](https://growixa.iitdeveloper.com)
> **UAT Staging URL**: [https://uat.growixa.iitdeveloper.com](https://uat.growixa.iitdeveloper.com)
> **Platform Admin Portal**: [https://growixa.iitdeveloper.com/platform/login](https://growixa.iitdeveloper.com/platform/login)

### 🚀 Added (New Features & Capabilities)
- **Self-Service Multi-Tenant SaaS**: Customer registration, email token verification, session management (`/register`, `/verify-email`).
- **Platform Super Admin Hub**: Centralized `/platform` dashboard, account list, usage tracking, and unified provider settings (`/platform/providers`).
- **Audience CRM**: Full contact management, custom fields, tags, static lists, and dynamic segments.
- **CSV Bulk Importer**: Asynchronous CSV contact ingestion with real-time progress streaming and error handling.
- **Email Marketing Suite**: Template designer with versioning and merge tags; multi-provider delivery (Postmark, Resend, SendGrid, Custom SMTP).
- **Social Media Studio**: Multi-account OAuth connectivity (Instagram, Facebook, LinkedIn, Twitter/X) and interactive scheduling calendar.
- **AI Growth Studio**: Multi-model copy generation powered by OpenAI GPT-4o, Anthropic Claude 3.5, and Google Gemini.
- **Billing & Subscriptions**: Plan quotas (Free, Starter, Pro, Enterprise), credit pack top-ups, and coupon discount code redemption.

### 🛠️ Fixed (Bug Fixes & Hardening)
- **Same-Origin API Proxying**: Fixed Next.js client-side Mixed Content blocking by routing browser requests through same-origin `/api` path.
- **Email Verification Base URL**: Corrected verification email links to point to `https://growixa.iitdeveloper.com/verify-email` instead of local IP.
- **CORS Configuration**: Updated Pydantic settings parser in `config.py` to seamlessly accept comma-delimited strings and JSON lists.
- **Suppression Removal Endpoint**: Added missing `DELETE /contacts/suppression/{id}` backend route and repository layer (`GRX-SAAS-015`).
- **Pydantic Validation in CI**: Resolved test runner path resolution for `ALEMBIC_INI` and isolated Redis rate-limit keys between test cases.

### 🔒 Security & Compliance
- **Zero-Secret Architecture**: Strictly enforced that zero production secrets are baked into container images or committed to Git.
- **AES-Fernet Credential Encryption**: All third-party SMTP passwords, OAuth tokens, and API keys encrypted at rest.
- **Append-Only Audit Logs**: Immutable recording of authentication events, user role changes, and support impersonation sessions.
- **Sliding-Window Rate Limiting**: Redis-backed brute-force protection on `/auth/login` and `/accounts/register`.
- **RFC 8058 Compliance**: Added `List-Unsubscribe` headers and one-click unsubscribe endpoint (`POST /unsubscribe/{id}`).
- **Audience Protection**: Domain-level suppression blocks and un-suppress prevention during contact restore.

### ⚡ Infrastructure & DevOps
- **Dedicated OVHcloud VPS (`149.56.101.2`)**: Self-contained Docker Compose architecture without external cloud vendor dependencies.
- **Dual-Domain Auto-SSL**: Caddy reverse proxy with automated Let's Encrypt TLS for Production and UAT Staging.
- **Automated GitHub Actions CI/CD**:
  - `v*-rc*` tags $\rightarrow$ Deploys to UAT (`/opt/growixa-uat`)
  - `v*.*.*` tags $\rightarrow$ Deploys to Production (`/opt/growixa`)
- **Automated Database Backups**: Daily dual-database backup cron with gzip compression and 14-day retention pruning.
- **Universal Coding Agent Skill**: Created [`.agents/skills/growixa-infra/SKILL.md`](.agents/skills/growixa-infra/SKILL.md).

### 📚 Reference Documentation
- **Architecture & Deployment Runbook**: [`docs/11-devops/OVH_VPS_DEPLOYMENT.md`](docs/11-devops/OVH_VPS_DEPLOYMENT.md)
- **Review Handoffs**: [`pr_reviews/feature-BACKEND-GRX-INFRA-002.md`](pr_reviews/feature-BACKEND-GRX-INFRA-002.md), [`pr_reviews/feature-BACKEND-GRX-SAAS-007.md`](pr_reviews/feature-BACKEND-GRX-SAAS-007.md)
- **Key Decision Records**: `DEC-GRX-017` (Self-Service Multi-Tenancy), `DEC-GRX-034` (Soft Delete Safeguards)
