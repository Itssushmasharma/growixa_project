# Feature Status Matrix

- Document ID: DOC-FEATURE-STATUS-MATRIX
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-31
- Owner: Coding agent
- Related documents: [FEATURE_CATALOG](../02-features/FEATURE_CATALOG.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md)

Tracks what has actually been *built and verified* per MVP feature, distinct from
[FEATURE_CATALOG.md](../02-features/FEATURE_CATALOG.md) (the planned feature list, which
doesn't track implementation progress). Statuses: `NOT_STARTED`, `PARTIAL` (some acceptance
criteria met, gaps noted), `DONE` (fully built and verified per its owning `GRX-*` task(s)).

## Slice 1 (Sprint 1: Foundation)

| Feature ID | Feature | Status | Evidence | Notes |
|---|---|---|---|---|
| GRX-FEAT-001 | Authentication | DONE | `GRX-AUTH-001..005` | Login/logout, refresh rotation + reuse detection, password reset, login rate limiting all built and tested. |
| GRX-FEAT-002 | User Management | DONE | `GRX-USER-001`, `GRX-USER-002` | Invite/accept, list/disable/role-change, self-disable guard, frontend screens. |
| GRX-FEAT-003 | RBAC | DONE | `GRX-RBAC-001` | Centralized `require_permission` dependency; enforced route-by-route (audited by `test_protected_routes_audit.py`). |
| GRX-FEAT-004 | Company Settings | DONE | `GRX-COMPANY-001`, `GRX-COMPANY-002` | Company profile CRUD, edit/view permission split, frontend form. |
| GRX-FEAT-005 | Brand Profile | DONE | `GRX-COMPANY-001`, `GRX-COMPANY-002` | Built as part of the company settings module/screen, not a separate page. |
| GRX-FEAT-024 | Notifications | NOT_STARTED | — | A shared toast component exists (`apps/web/src/components/toast/`, built 2026-07-30, no tracker ID — UI polish only) for transient in-page feedback. It is not a notification *feature* (no persistence, no delivery outside the active page) and doesn't satisfy this catalog entry. |
| GRX-FEAT-025 | Usage Metering | NOT_STARTED | — | No task has touched this. |
| GRX-FEAT-026 | Integrations (management) | NOT_STARTED | — | No task has touched this. |
| GRX-FEAT-027 | Audit Logs | PARTIAL | `GRX-AUDIT-001` | Insert-only recording is DONE and tested (`test_audit_log.py`, `test_audit_insert_only.py`) and audit events are written for the Sprint 1 event set. **Gap: no way to actually view them** — the `audit` module has no `api.py` (no `GET` endpoint) and no frontend page, so Sprint 1's acceptance criterion "audit logs... are visible to users with `audit.view`" is not literally met; `audit.view` exists as a permission code but nothing checks it yet. Flagged as `GRX-AUDIT-002` (new, `BACKLOG`) in the tracker. |
| GRX-FEAT-028 | Admin Portal | NOT_STARTED | — | The dashboard shell (`GRX-FOUND-008`) provides authenticated layout/navigation but "Admin Portal" as its own feature (distinct admin-only management surface) was never separately scoped or built. |

## Slice 2 (Sprint 2: Contacts)

| Feature ID | Feature | Status | Evidence | Notes |
|---|---|---|---|---|
| GRX-FEAT-006 | Contact Management | DONE | `GRX-CONTACT-001`, `GRX-CONTACT-006` | CRUD + frontend, `contacts.manage`/`contacts.view` split. |
| GRX-FEAT-007 | Contact Import | DONE | `GRX-CONTACT-004`, `GRX-CONTACT-008` | CSV upload, column mapping, per-row status, import history. |
| GRX-FEAT-008 | Contact Tags | DONE | `GRX-CONTACT-002`, `GRX-CONTACT-007` | Tag CRUD + assignment UI. |
| GRX-FEAT-009 | Segmentation | DONE | `GRX-CONTACT-003`, `GRX-CONTACT-007` | Rule-based dynamic segments + builder UI. |
| GRX-FEAT-010 | Suppression and Consent | DONE | `GRX-CONTACT-005`, `GRX-CONTACT-009` | Insert-only consent history, upsert-on-email suppression, both with frontend. |

## Slices 3–6

Not started — no tasks exist yet for email (Slice 3), campaign scheduling (Slice 4), social
(Slice 5), or AI content assistant (Slice 6). See [ROADMAP.md](../01-product/ROADMAP.md) and
[MVP_SCOPE.md](../01-product/MVP_SCOPE.md).

## Summary

- **Slice 1: 7 of 10 features DONE, 1 PARTIAL (Audit Logs — recording works, viewing
  doesn't), 2 NOT_STARTED** (Usage Metering, Integrations — both explicitly out of Sprint
  1's minimal scope per [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md),
  which never included them as deliverables despite the catalog tagging them "Slice 1").
  Notifications and Admin Portal are likewise catalog-tagged Slice 1 but were never in
  Sprint 1's actual task breakdown.
- **Slice 2: 5 of 5 features DONE.**
