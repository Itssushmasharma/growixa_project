# Project Status

- Document ID: DOC-PROJECT-STATUS
- Status: ACTIVE
- Version: 1.25
- Last updated: 2026-07-29
- Owner: Coding agent (on behalf of product owner)
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [DECISIONS](DECISIONS.md), [DEVELOPMENT_READINESS](DEVELOPMENT_READINESS.md)

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
shell), `GRX-COMPANY-002` (company settings screen), and `GRX-USER-002` (user management
screens) are `DONE`. `GRX-DEVOPS-001` (CI pipeline) is `IN_REVIEW` — fully built and
locally verified, but not moved to `DONE` because a real green run on GitHub Actions
hasn't been observed; that requires pushing, a permission-gated action awaiting the
user's go-ahead.
**All other tracked Sprint 1 tasks are now `DONE`.** Per
[AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md), only one is worked
on at a time. See [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for session-by-session
detail.

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
| `docs/05-data/DATA_MODEL.md`, `ERD.md`, `DATABASE_SCHEMA.md` | DONE (Sprint 1 entities in full detail) |
| `docs/08-security/SECURITY_ARCHITECTURE.md`, `AUTHENTICATION.md`, `RBAC.md`, `THREAT_MODEL.md` | DONE |
| `docs/12-development/AGENT_EXECUTION_RULES.md` | DONE |
| `docs/14-sprints/SPRINT_01_FOUNDATION.md` | DONE |
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
| `docs/00-project-control/FEATURE_STATUS_MATRIX.md`, `RISKS.md`, `BLOCKERS.md` | NOT_STARTED (created as Sprint 1 tasks land) |
| `docs/03-ux-ui/DESIGN_REFERENCES.md` | DONE (reference material only — see its own scope caveat; not a Sprint 1 spec) |
| `docs/01-product/FUTURE_SCOPE_MULTI_BRAND.md` | DONE (idea capture only — multi-brand profiles + subscription tiers; contradicts DEC-GRX-002/013 as proposed, not scheduled into any release) |
| `docs/01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md` | DONE (idea capture only — self-service multi-tenant SaaS + IITDEVELOPER platform-admin control plane; requires revisiting DEC-GRX-002/013, not scheduled into any release) |
| Full per-feature specs under `02-features/`, all of `06-api/`, `07-ai/`, `09-integrations/`, `13-business/` | NOT_STARTED |

## Immediate next steps

1. Session sequence so far, each picked as "most needed" given dependencies/priority (full
   rationale per task in [CHANGELOG.md](CHANGELOG.md)): `GRX-AUTH-002` → `GRX-AUTH-003` →
   `GRX-USER-001` → `GRX-AUTH-005` → `GRX-FOUND-006` → `GRX-AUTH-004` → `GRX-TEST-002` →
   `GRX-FOUND-008` → `GRX-DEVOPS-001` (`IN_REVIEW`, needs a push to confirm green — see
   AGENT_HANDOFF.md) → `GRX-COMPANY-002` → `GRX-USER-002`. All tracked Sprint 1 tasks are
   now `DONE` except `GRX-DEVOPS-001`'s pending push confirmation; awaiting user direction
   on what to pick up next (Sprint 2, or push/confirm CI).
2. Create `FEATURE_STATUS_MATRIX.md`, `RISKS.md`, `BLOCKERS.md` alongside Sprint 1 tasks as they land, not all upfront.
3. Write full feature specs in `02-features/` for Slice 1 features as each task is picked up, not all upfront.
4. Do not begin any V1.5+/SEO-AEO-GEO work until Slices 1–6 (MVP) are stable in production.
5. Do not resolve OQ-002/003/004/006/007/012 early — they don't block Slice 1 (explicit instruction).
6. Do not start more than one Sprint 1 task concurrently (explicit instruction).

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for the full reverse-chronological history.
