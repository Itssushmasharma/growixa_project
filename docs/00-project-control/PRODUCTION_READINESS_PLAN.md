# Production readiness implementation

Authorized by the product owner on 2026-09-20 following the repository audit.
This expands the earlier MVP-only roadmap; it does not authorize production deployment.
Branch: feature/BACKEND/GRX-PRODUCTION-FOUNDATION.

## Acceptance criteria
Preserve working code; use official providers only; never invent production data or
successful delivery. Enforce tenant isolation and human approval, migrate every new table,
and verify UI states, accessibility, responsiveness, performance and discoverability.
Each major module requires lint, typecheck, tests, build, fixes and independent review.
No module is complete merely because its unsafe implementation is disabled.

## Sequential checkpoints
1. IN_PROGRESS — Foundation: startup, CORS/CSRF, identity and tenant isolation,
   truthful availability, migration registration and schema repair.
2. PENDING — Contacts/CRM, consent, suppression, company/team, billing and audit.
3. PENDING — Content/templates/media, email campaigns, approval and reliable dispatch.
4. PENDING — Official social adapters, composer, scheduling and calendar.
5. PENDING — WhatsApp/SMS provider verification, consent, delivery and signed webhooks.
6. PENDING — Unified inbox, authenticated subscriptions and durable message delivery.
7. PENDING — Automation triggers, conditions, actions, retries and execution history.
8. PENDING — Provenance-backed analytics, AI insights and real report generation.
9. PENDING — Agency onboarding, client authorization and verified white-label domains.
10. PENDING — Every public/dashboard/platform/portal page: coherent UI, all states,
    responsive and keyboard flows; truthful marketing, metadata and documentation.
11. PENDING — Full regression, migration/restore checks, accessibility/performance,
    independent review, deployment readiness report and production approval.

## Validation constraints
The audit baseline had failing frontend tests and API/worker lint/type checks.
Local Docker/PostgreSQL availability must be restored before DB-backed validation.
Provider credentials, approvals, verified domains and test accounts remain external
requirements; no claim of live integration can be made without observed evidence.

## Foundation evidence
- Seven startup/CORS/availability/health regression tests passed on 2026-09-20.
- Public chat and SEO crawling are explicitly pending; tenant AI workspace is retained.
- Full checkpoint and release validation remain outstanding.
