# Sprint 01 — Foundation

- Document ID: DOC-SPRINT-01
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-010](../00-project-control/DECISIONS.md)

Sprint 1 is Slice 1 (Foundation) from [DEC-GRX-010](../00-project-control/DECISIONS.md).
Its job is to prove the platform boots, an admin can log in and manage users, permissions
restrict actions, company settings persist, audit events are visible, and CI/tests pass —
nothing more.

## Included

1. Repository and development tooling (lint, format, type-check, pre-commit, `.env.example`)
2. Docker Compose (Postgres, Redis, RabbitMQ, backend, frontend)
3. FastAPI foundation (app factory, config, health endpoint, OpenAPI)
4. Next.js foundation (app shell, routing, API client)
5. PostgreSQL (connectivity, session management)
6. Redis (connectivity, used for rate limiting)
7. RabbitMQ connectivity and health checks (no business jobs — see [BACKGROUND_JOB_ARCHITECTURE.md](../04-architecture/BACKGROUND_JOB_ARCHITECTURE.md))
8. Alembic migrations foundation
9. Authentication (login, logout, refresh rotation, password reset, rate limiting — full detail in [AUTHENTICATION.md](../08-security/AUTHENTICATION.md))
10. Internal user management (invite, accept, disable, role assignment)
11. RBAC (centralized permission enforcement — [RBAC.md](../08-security/RBAC.md))
12. Company settings (company profile + brand basics)
13. Audit logging (insert-only log, Sprint 1 event set)
14. Dashboard shell (authenticated layout, navigation, empty landing page)
15. Backend and frontend test foundations
16. CI validation (lint, format, type-check, tests, migration check)
17. Documentation and handoff updates

Full task breakdown with dependencies: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-FOUND-*`, `GRX-AUTH-*`, `GRX-USER-*`, `GRX-RBAC-*`, `GRX-COMPANY-*`, `GRX-AUDIT-*`,
`GRX-TEST-*`, `GRX-DEVOPS-*`).

## Explicitly excluded from Sprint 1

- Email campaigns and any email-provider integration
- Social integrations
- AI generation / AI content assistant
- SEO, AEO, GEO, website crawler
- WordPress integration
- GitHub integration
- Billing / payment provider
- Advanced automation workflows

If implementing a Sprint 1 task seems to require touching any of the above, stop and flag it
— it means the task is scoped wrong, not that a shortcut through excluded territory is
warranted.

## Sprint 1 acceptance criteria

- Application starts locally via `docker compose up`.
- Backend health check passes.
- Frontend loads.
- Database migrations run cleanly from empty.
- An admin can log in.
- An admin can invite, view, and disable internal users, and assign roles.
- Roles restrict protected actions (verified by a negative test: a Viewer cannot perform an
  Admin-only action).
- Company settings can be saved and reloaded.
- Audit logs capture the Sprint 1 event set (see [AUTHENTICATION.md §Audit events](../08-security/AUTHENTICATION.md#audit-events-minimum-set-sprint-1))
  and are visible to users with `audit.view`.
- Automated backend and frontend tests pass.
- CI passes on a clean baseline.
- Documentation (`PROJECT_STATUS.md`, `FEATURE_STATUS_MATRIX.md`, `CHANGELOG.md`) matches
  what was actually implemented.

## Definition of done for this sprint

[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) applies to every task
in this sprint individually — the sprint itself is done only when every task in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) tagged for Sprint 1
is `DONE`, not merely attempted.
