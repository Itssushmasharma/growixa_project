# 🚀 Growixa Release Notes

---

## 🚧 [v0.2.0] — Unreleased (In Active Development)

> **Target Release Tag**: `v0.2.0`  
> **Status**: 🟡 In Progress (Preview on UAT via `v0.2.0-rc1`)  
> **Target Release Date**: August 2026  

### 🚀 Added
- **Customer Help Center (`/docs`)**: Full documentation and in-app assistance system at `/docs` with instant search, 6 categorized guide suites, rich markdown viewer with step badges, callout alerts, code copy, and Table of Contents ([`GRX-DOCS-001`](docs/00-project-control/MASTER_TASK_TRACKER.md)).
- **In-App Contextual Help Drawer**: Slide-over `<HelpDrawer />` accessible across dashboard navigation for inline guide reading without losing context.
- **Inline `<HelpTooltip />`**: Contextual helper tooltips across campaign and contact forms.
- **Deleted Contacts View & Recovery**: Dedicated "Deleted" tab in the Contacts CRM with individual and bulk restoration actions ([`GRX-CONTACT-016`](docs/00-project-control/MASTER_TASK_TRACKER.md)).

### 🛠️ Fixed
- **Contact Quota Overflow**: Added plan quota check safeguard when restoring bulk soft-deleted contacts to prevent exceeding tier limits.

### 🔒 Security & Compliance
- **Restoration Un-Suppress Safeguard**: Restoring a soft-deleted contact strictly verifies that previously suppressed email addresses remain suppressed.

### 📚 Reference Documentation
- **Active Branches**: `feature/FRONTEND/GRX-DOCS-001`, `feature/BACKEND/GRX-CONTACT-016`
- **Worktrees**: `.worktrees/grx-docs-help-center`, `.worktrees/grx-contact-016-restore`
- **Review Handoff**: `pr_reviews/feature-FRONTEND-GRX-DOCS-001.md`

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
