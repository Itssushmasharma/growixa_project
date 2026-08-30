Task: GRX-EMAIL-016 — Platform-published default/public email templates
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: feature/BACKEND/GRX-EMAIL-016
Worktree: .worktrees/grx-email-016
Base Commit: d125b2e
Latest Commit: 47aa65e
Status: APPROVED

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

Reviewed at HIGH depth (RBAC + isolation-model + customer-facing UI), per AGENTS.md §4.5.
All claims in the handoff were independently re-verified against the real diff, a fresh
Postgres instance, and the actual test suites — not accepted on the developer's account.

**Design decisions (pre-specified in tracker, not re-litigated):** reserved
`accounts.is_platform_system` singleton, clone-not-edit, `platform.templates.manage`
following the exact `platform.ai.manage`/`platform.email.manage`/`platform.validation.manage`
shape — all confirmed correctly implemented, not redesigned.

**Migration (`b8704f3eeada`)**: applied cleanly on a fresh Postgres 16 container starting
from `72e376f46c26`; `alembic check` clean; `alembic downgrade -1` then `upgrade head`
round-trips correctly (FK-safe order: role_permissions → permissions → email_templates →
account_subscriptions → accounts → drop indexes/columns). `PLAN_FREE` UUID confirmed to
exist by that point in migration history (`e926f73f7ece` is a genuine ancestor of
`72e376f46c26`). `Account.__table_args__`'s `Index("ux_accounts_platform_system_singleton",
"is_platform_system", unique=True, postgresql_where=text("is_platform_system"))` matches
the migration's `op.create_index(...)` exactly (name, column, `postgresql_where`) —
confirmed the singleton-via-partial-unique-index pattern is sound (a second `is_platform_system
= true` row would collide on the filtered index).

**Account isolation**: `templates/repositories.py::get_template` filters by the caller's
own `account_id` (never the platform account's), so `GET/DELETE /templates/{id}` and
`POST /templates/{id}/versions(/versions)` all correctly 404 on a platform template id —
verified in code and in `test_account_cannot_read_or_mutate_a_platform_template_via_
account_scoped_routes` (real integration test against Postgres, all 4 routes assert 404).

**Clone gating**: `clone_template_for_account` sources exclusively via
`get_platform_default_template` (`WHERE is_platform_default = true`), so a customer
cannot clone another account's private template or their own — confirmed by
`test_clone_of_a_regular_account_owned_template_returns_404` and
`test_clone_of_nonexistent_template_returns_404`. Clone-not-edit genuinely creates
independent `EmailTemplate`/`EmailTemplateVersion` rows with no FK back to the source;
`test_clone_creates_independent_copy_unaffected_by_later_platform_edits` proves a clone
survives retirement of its platform source.

**RBAC route audit**: every new customer route uses `require_permission("campaigns.view"/
"campaigns.manage")` (existing dependency, matching the rest of `templates/api.py`);
every new platform route uses `require_platform_permission("platform.templates.manage")`,
never `require_permission`. `tests/permissions/test_protected_routes_audit.py` (a real
structural audit walking every registered `APIRoute`'s dependants, not a stub) passes
against the actual `create_app()` including the two new routers. RBAC.md's new section
matches the migration's seed grants exactly (`platform.owner`/`platform.admin` only).

**`created_by_user_id` nullable**: pre-existing nullability (not weakened by this branch),
consistent with `DEC-GRX-018`; grepped `apps/worker` and found no code assuming non-null.

**Frontend**: `templates-page.tsx`'s new "Default Templates" section is browse/preview-only
(no Edit/Duplicate/Delete), `canManage`-gated "Use this template" clone-and-navigate
action, structurally separate from "My Templates" — matches the tracker's spec. iframe
preview uses `sandbox=""` (no scripts), same pattern already used for the account's own
templates — no new XSS surface introduced. Scope-cutting the platform-admin frontend UI is
reasonable: the tracker's frontend file list only named the customer-facing `templates/`
directory, and platform-admin routes remain fully usable via API/curl in the interim
(matches the existing pattern where several other `platform_admin/api.py` routes also have
no dedicated admin UI yet).

**Independently executed verification (not just re-reading the handoff's claims):**
- `ruff check` / `ruff format --check` / `mypy src` — all clean.
- Backend `pytest -q` against a disposable fresh Postgres 16 container (own instance, not
  reused from the developer's session): **462 passed, 8 skipped**, matches handoff.
- `alembic upgrade head` from `72e376f46c26`, `alembic check`, `alembic downgrade -1` +
  re-upgrade — all clean, confirmed myself.
- `tests/permissions/test_protected_routes_audit.py` run directly: 3 passed.
- Frontend `npm run test -- --run`: **304 passed**, matches handoff. `npm run lint` clean
  (2 pre-existing warnings in an unrelated file, `social/post-form-page.tsx`, not touched
  by this branch). `npm run typecheck` clean.
- Secret scan of the full `d125b2e..47aa65e` diff for hardcoded credentials/tokens/keys:
  none found.

**Gaps / not independently re-verified:**
- No browser tool was available in this review session either — I could not do a live
  visual check of the "Default Templates" section, same limitation the developer already
  flagged. This is stated explicitly, not implied. Vitest coverage of the section's
  visibility/permission-gating/clone-navigation was reviewed and is genuine (not vacuous),
  but a real rendered-page check is still outstanding before merge, per the handoff's own
  "Known Issues" note.
- Did not re-run the developer's live curl flow against the shared Compose `api` container
  (pre-existing, already running, not necessarily built from this exact commit) to avoid
  disturbing shared state; substituted with my own disposable Postgres + the real
  integration pytest suite covering the identical scenarios (isolation, clone gating,
  RBAC denial), which I consider equivalent evidence for this review.

No scope creep found — diff is limited to what the task describes. No secrets found.

## Review Decision

APPROVED

## Reviewed Code Commit

47aa65e (last commit touching code/tests/docs; 2f31fcd is tracker+handoff-only, confirmed
via `git diff 47aa65e..2f31fcd --stat`)

## Review Record Commit


## Human Approval
Required — customer-facing UI change (new "Default Templates" section) and a new
higher-trust platform permission, per AGENTS.md §4.5. Independent code review above is
APPROVED, but this is a separate gate: the product owner still needs to give explicit
sign-off before merge, including ideally a real visual check of `/dashboard/templates`
(neither the developer nor this reviewer had working browser tooling to do that check).

Status: APPROVED
