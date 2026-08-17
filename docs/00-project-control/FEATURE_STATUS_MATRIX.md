# Feature Status Matrix

- Document ID: DOC-FEATURE-STATUS-MATRIX
- Status: ACTIVE
- Version: 1.2
- Last updated: 2026-08-18
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
| GRX-FEAT-027 | Audit Logs | DONE | `GRX-AUDIT-001`, `GRX-AUDIT-002` | Insert-only recording (`GRX-AUDIT-001`) plus `GET /audit` (entity_type/actor_user_id filters, gated `audit.view`) and a frontend page (`GRX-AUDIT-002`) — closes the gap this matrix's first pass found. |
| GRX-FEAT-028 | Admin Portal | NOT_STARTED | — | The dashboard shell (`GRX-FOUND-008`) provides authenticated layout/navigation but "Admin Portal" as its own feature (distinct admin-only management surface) was never separately scoped or built. |

## Slice 2 (Sprint 2: Contacts)

| Feature ID | Feature | Status | Evidence | Notes |
|---|---|---|---|---|
| GRX-FEAT-006 | Contact Management | DONE | `GRX-CONTACT-001`, `GRX-CONTACT-006`, `GRX-CONTACT-010`, `GRX-CONTACT-011`, `GRX-CONTACT-015`, `GRX-CONTACT-016` | CRUD + frontend, `contacts.manage`/`contacts.view` split. Extended with soft deletion per `DEC-GRX-034` (`deleted_at`, orthogonal to `status`, partial unique index on live rows), multi-select with a bulk toolbar, bulk delete/suppress, and a Deleted view with single and bulk restore. Hard erasure is deliberately NOT built — see `GRX-CONTACT-013` (`BACKLOG`, design-first). |
| GRX-FEAT-007 | Contact Import | DONE | `GRX-CONTACT-004`, `GRX-CONTACT-008` | CSV upload, column mapping, per-row status, import history. |
| GRX-FEAT-008 | Contact Tags | DONE | `GRX-CONTACT-002`, `GRX-CONTACT-007` | Tag CRUD + assignment UI. |
| GRX-FEAT-009 | Segmentation | DONE | `GRX-CONTACT-003`, `GRX-CONTACT-007` | Rule-based dynamic segments + builder UI. |
| GRX-FEAT-010 | Suppression and Consent | DONE | `GRX-CONTACT-005`, `GRX-CONTACT-009` | Insert-only consent history, upsert-on-email suppression, both with frontend. |

## Slices 3–6

> ⚠️ **This section is stale as of 2026-08-15.** It was last assessed 2026-07-31, when
> Slices 3–6 genuinely had no tasks. Since then `GRX-EMAIL-001..012`, `GRX-SCHED-*`,
> `GRX-SOCIAL-001..011`, and `GRX-AI-001..011` have all reached `DONE` in
> [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md), as has the entire Sprint 5 /
> billing track. A full re-audit of `GRX-FEAT-011`–`028` against the shipped code is
> needed — the same kind of pass `GRX-DOC-003` did for Slices 1–2. That re-audit is out
> of scope for the product-intake triage that added this note; only the two rows below,
> which the triage actually verified, are recorded.

Original (2026-07-31) assessment, retained for history: not started — no tasks exist yet
for email (Slice 3), campaign scheduling (Slice 4), social (Slice 5), or AI content
assistant (Slice 6). See [ROADMAP.md](../01-product/ROADMAP.md) and
[MVP_SCOPE.md](../01-product/MVP_SCOPE.md).

## Post-MVP / ad hoc features (verified 2026-08-15)

Verified during the `need_review_docs/` product intake triage. These features came from
ad hoc `GRX-SAAS-*` tasks rather than a Slice 1–6 sprint, so they had no row on this
matrix.

| Feature ID | Feature | Status | Evidence | Notes |
|---|---|---|---|---|
| GRX-FEAT-030 | Email Validation | DONE | `GRX-SAAS-016`, `GRX-SAAS-017` | Free in-house checks (syntax, MX/A with RFC 5321 implicit-MX fallback, disposable list, role list) for all plans; platform-admin-configurable multi-vendor real-time verification (Clearout first) for paid plans, with a per-check opt-out. No SMTP mailbox probe or catch-all detection — deliberately excluded, see the task note. |
| GRX-FEAT-010 | Suppression and Consent (post-MVP extension) | DONE | `GRX-CONTACT-005/009`, `GRX-SAAS-015` | Extends the Slice 2 entry above: whole-domain blocking, CSV import/export, working remove, and RFC 8058 `List-Unsubscribe`/`List-Unsubscribe-Post` headers on outbound campaign mail. Hashed storage and a global cross-account list are **not** built and **not** scheduled — see `OQ-017`. |
| GRX-FEAT-023 / GRX-FEAT-028 | Analytics dashboard + platform admin overview | PARTIAL | `GRX-SAAS-014` | Customer overview (`GET /dashboard/overview`) and platform admin overview (`GET /platform/dashboard/summary`) shipped, replacing empty placeholders. Scoped to the source plan's own MVP tier: one unified view per surface. The 4 role-adaptive lenses and the "AI Next Best Actions" card are **not** built and **not** scheduled — see `GRX-FEAT-036` and `OQ-016`. No `account_daily_metrics` rollup table or Redis cache layer (accepted risk, direct SQL aggregation). |
| GRX-FEAT-037 | Customer Help Centre & in-app contextual help | DONE | `GRX-DOCS-001` | Public help centre at `/docs` — 20 markdown articles compiled to a JSON manifest by `scripts/compile-docs.js` at `predev`/`prebuild`/`pretest`, plus contextual help entry points in the dashboard. The generated manifest is Prettier-ignored deliberately (the compiler emits its own layout, so style-checking it fails on every rebuild). Content is static and reviewed for claim accuracy: it makes no security or pricing assertion the product does not implement. |

## Summary

- **Slice 1: 8 of 10 features DONE, 2 NOT_STARTED** (Usage Metering, Integrations — both
  explicitly out of Sprint 1's minimal scope per
  [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md), which never included
  them as deliverables despite the catalog tagging them "Slice 1"). Notifications and
  Admin Portal are likewise catalog-tagged Slice 1 but were never in Sprint 1's actual
  task breakdown. Audit Logs (`GRX-FEAT-027`) was `PARTIAL` on this matrix's first pass
  (2026-07-31) — `GRX-AUDIT-002` closed it to `DONE` the same day.
- **Slice 2: 5 of 5 features DONE.**
