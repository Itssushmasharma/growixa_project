# Project Status

- Document ID: DOC-PROJECT-STATUS
- Status: ACTIVE
- Version: 1.41
- Last updated: 2026-08-03
- Owner: Coding agent (on behalf of product owner)
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [DECISIONS](DECISIONS.md), [DEVELOPMENT_READINESS](DEVELOPMENT_READINESS.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Product identity (confirmed)

- Product name: **Growixa**
- Product type: **AI-powered growth and marketing automation platform.** It begins with
  email and social media automation, then expands into SEO, AEO, GEO, website intelligence,
  content optimization, and integrated growth workflows.
- Tenancy model: MVP is **single-tenant**, one company installation, multiple internal users
- MVP focus (this release only): contact management, email marketing, one social platform,
  AI content assistant with mandatory human approval, campaign scheduling, basic analytics
- **Deferred to future releases (V1.5–V3), not cancelled:** SEO automation, AEO, GEO,
  website crawler, website audits, metadata recommendations, WordPress integration, GitHub
  integration, Search Console integration, content optimization agents, website improvement
  workflows, full multi-agent growth system. See
  [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md).
- **Deferred indefinitely** (not currently roadmapped at all): full multi-tenancy,
  customer-facing SaaS signup, tenant billing, white-label platform.

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

**Ad hoc UX addition (not tied to a sprint plan):** `GRX-FOUND-009` (collapsible/
responsive sidebar navigation — hamburger toggle for desktop collapse + mobile overlay
drawer, plus an independent per-section accordion for each nav heading), requested
directly by the user mid-session, is `DONE`.

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
| `docs/01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md` | DONE (idea capture only — self-service multi-tenant SaaS + IITDEVELOPER platform-admin control plane; requires revisiting DEC-GRX-002/013, not scheduled into any release) |
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
   `GRX-EMAIL-001` → `GRX-EMAIL-002` → `GRX-EMAIL-003`.
   **Sprint 1 and Sprint 2 (Contacts) are both fully `DONE`**, including `GRX-DEVOPS-001`
   (user pushed and confirmed a green CI run), `GRX-DOC-003` (Sprint 1 doc/handoff
   update, which filed `GRX-AUDIT-002` for the audit-viewing gap it found), and
   `GRX-AUDIT-002` itself (closed the same session it was filed). **Sprint 3 (Email
   Marketing) is under way**: `GRX-EMAIL-001` (provider connection + sender identity),
   `GRX-EMAIL-002` (email templates + versioning), and `GRX-EMAIL-003` (campaigns CRUD +
   targeting) are all `DONE`; next task is `GRX-EMAIL-004` (send pipeline).
2. `RISKS.md`/`BLOCKERS.md` remain not required by any task yet; create them if/when a
   task's scope actually calls for one.
3. Write full feature specs in `02-features/` for Slice 3 features (`EMAIL_PROVIDERS.md`,
   `EMAIL_TEMPLATES.md`, `EMAIL_CAMPAIGNS.md`) as each task is picked up, not all upfront
   — same practice as Sprints 1–2.
4. Do not begin any V1.5+/SEO-AEO-GEO work until Slices 1–6 (MVP) are stable in production.
5. Do not resolve OQ-003/004/006/007/009/012 early — they don't block Slice 3 (explicit
   instruction; OQ-002 is the one exception, resolved because Slice 3 genuinely needed it).
6. Do not start more than one Sprint 1 task concurrently (explicit instruction).

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the full reverse-chronological history.
