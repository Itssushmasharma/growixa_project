# Changelog

- Document ID: DOC-CHANGELOG
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [PROJECT_STATUS](PROJECT_STATUS.md), [DECISIONS](DECISIONS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md)

Reverse-chronological log of material changes to the Growixa repository (documentation and,
from Sprint 1 onward, code). Each entry names what changed and the commit(s) it landed in.

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
- Commit: see [`AGENT_HANDOFF.md`](AGENT_HANDOFF.md) / `git log`.

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
