Task: GRX-EMAIL-016 — Platform-published default/public email templates
Developer: Claude Code
Reviewer:
Branch: feature/BACKEND/GRX-EMAIL-016
Worktree: .worktrees/grx-email-016
Base Commit: d125b2e
Latest Commit: 47aa65e
Status: READY_FOR_REVIEW

## What Changed

Adds a platform-scoped email template concept: every account can browse and clone a
platform-published default template, published only by Growixa's own platform team.

- **Schema**: `accounts.is_platform_system` (singleton, enforced by a partial unique
  index `ux_accounts_platform_system_singleton`) + `email_templates.is_platform_default`.
  Migration `b8704f3eeada` seeds the reserved "Growixa Platform" account, its
  `AccountSubscription` (satisfies the "every account has exactly one" invariant), the
  new `platform.templates.manage` permission, and its role grants
  (`platform.owner`/`platform.admin`).
- **Backend**: `templates/services.py` gains `create_platform_template`,
  `add_platform_template_version`, `retire_platform_template`,
  `list_platform_default_templates_with_current_version`, `clone_template_for_account`.
  New routes: `GET /templates/platform-defaults` + `POST /templates/{id}/clone`
  (customer-facing, `templates/api.py`); `GET/POST /platform/templates` +
  `POST/DELETE /platform/templates/{id}(/versions)` (platform-admin,
  `platform_admin/api.py`, gated by `platform.templates.manage`).
- **Frontend**: `templates-page.tsx` gains a "Default Templates" section (browse/preview
  + "Use this template", `campaigns.manage`-gated), separate from "My Templates". Cloning
  navigates straight to the new copy's edit page.
- **Docs**: `docs/08-security/RBAC.md` (new permission section, same shape as
  `platform.ai.manage`/`platform.email.manage`/`platform.validation.manage`);
  `docs/02-features/EMAIL_TEMPLATES.md` (new, `GRX-FEAT-012` was previously unwritten).

## Why

The tracker row (filed after a 2026-08-30 product-owner-approved brainstorm) laid out the
design already-settled: reserved system account over nullable `account_id` (chosen, since
it's schema-consistent with every other table's isolation model and needs no
nullable-FK special-casing elsewhere); clone-not-edit as a hard requirement (implemented —
a clone is a fully independent row, so a later platform edit/retirement can never alter,
break, or silently mutate a campaign already built from a previously-cloned copy);
`platform.templates.manage` following the exact existing `platform.*.manage` shape.

## Important Files

- `apps/api/migrations/versions/b8704f3eeada_platform_default_email_templates.py`
- `apps/api/src/growixa_api/accounts/models.py`, `accounts/repositories.py`
- `apps/api/src/growixa_api/templates/{models,schemas,repositories,services,api}.py`
- `apps/api/src/growixa_api/platform_admin/api.py`, `app.py`
- `apps/web/src/app/(dashboard)/dashboard/templates/{templates-page.tsx,types.ts,templates-page.module.css}`
- `docs/08-security/RBAC.md`, `docs/02-features/EMAIL_TEMPLATES.md` (new)

## Tests

Ran against a live Compose stack (`docker compose up postgres redis rabbitmq api`, then
`api web`) and both automated suites:

- **Migration**: applied cleanly on top of `72e376f46c26`; `alembic check` clean (had to
  add the partial unique index to `Account.__table_args__` explicitly — autogenerate
  otherwise saw it as a pending diff). Downgrade path reverses all seed data and columns.
- **Manual curl flow**: platform owner creates a default template (201) → customer
  browses `/templates/platform-defaults` (sees it) and `/templates` (doesn't) → customer
  clones it (201, `is_platform_default: false`, independent id) → clone appears in
  `/templates` → customer's `DELETE`/`GET` on the platform template's id via
  account-scoped routes both 404 (isolation) → `platform.support` role gets 403 on
  `POST /platform/templates` (RBAC).
- **Backend**: `pytest` — 462 passed (15 new: 7 in `test_templates.py` covering clone
  independence from later platform edits/retirement, account isolation on all 4
  account-scoped mutation routes, RBAC (`campaigns.manage` required to clone), 404 on a
  nonexistent/non-platform clone target; 5 in new `test_platform_templates.py` covering
  platform-admin create/edit/retire, `platform.support` denial, insert-only version
  history, 404s). `ruff check`/`ruff format --check`/`mypy` all clean.
- **Frontend**: `npm run test` — 304 passed (4 new: Default Templates section
  hidden/shown correctly, "Use this template" hidden for view-only users, clone-then-
  navigate flow). `eslint`/`prettier --check`/`tsc --noEmit`/`npm run build` all clean.
- **`test_protected_routes_audit.py`**: passed — every new route is recognized as
  correctly gated (`require_permission` vs `require_platform_permission`, never both,
  never neither).

## Known Issues / Evidence Gaps

- **No live browser verification.** The Claude-in-Chrome extension wasn't connected this
  session, so I could not visually confirm the "Default Templates" section renders as
  intended in a real browser. Compensated with explicit vitest coverage of the new UI's
  behavior (section visibility, button permission-gating, clone navigation), plus a full
  manual API-level verification of the underlying flow — but a human visual check of the
  actual rendered page is still recommended before merge, given this is customer-facing UI.
- **No platform-admin frontend UI** for creating/editing/retiring platform templates —
  deliberately out of scope (not listed in the tracker's frontend file scope,
  `apps/web/.../templates/` only). Platform template management is API-only for now; a
  UI can be added later with zero backend changes.

## Review Findings


## Review Decision


## Reviewed Code Commit


## Review Record Commit


## Human Approval
Required — customer-facing UI change (new "Default Templates" section) and a new
higher-trust platform permission, per AGENTS.md §4.5. Also recommend the reviewer or
product owner do a live visual check of the frontend section, since the developer could
not (browser extension unavailable this session).

Status:
