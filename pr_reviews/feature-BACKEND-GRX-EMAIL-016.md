Task: GRX-EMAIL-016 — Platform-published default/public email templates
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session (re-review pass)
Branch: feature/BACKEND/GRX-EMAIL-016
Worktree: .worktrees/grx-email-016
Base Commit: d125b2e
Latest Commit: 10c74bc
Status: APPROVED

## Update — 4c6f147 (post-approval addition)

Per explicit user request after the prior APPROVED review, this branch now also adds a
**platform-admin frontend UI** for managing default templates (previously deliberately
out of scope, API-only). This changed code after the `Reviewed Code Commit: 47aa65e`
recorded below, so per AGENTS.md §4 rule 4 that approval is now stale — a fresh
independent review of the new diff (`47aa65e..4c6f147`) is required before merge.

**New in `4c6f147`** (`apps/web/src/app/(platform)/platform/(protected)/templates/`):
- `page.tsx`, `templates-page.tsx`, `templates-page.module.css`, `types.ts` — full CRUD
  UI: list existing platform default templates, publish a new one, edit-by-appending-a-
  new-version, retire (with a `window.confirm` explaining clone-independence).
- `templates-page.test.tsx` — 7 new vitest tests (403 access-denied, list, empty state,
  publish, edit-appends-version, retire-after-confirm, retire-declined).
- `sidebar.tsx` — new "Templates" nav entry gated on `platform.templates.manage`
  (permission already existed/granted from the original migration — no backend change
  needed for this to appear).
- `docs/02-features/EMAIL_TEMPLATES.md` — corrected the now-false "No platform-admin
  frontend UI ships in this pass" claim.

No backend/schema/migration changes in this update — same `platform.templates.manage`
permission and routes from `47aa65e`, just a UI on top of the already-approved API.

Verified locally before pushing: `eslint`, `prettier --check`, `tsc --noEmit` all clean
on the new/changed files; full frontend suite `npm run test -- --run` — **311 passed**
(53 files); `npm run build` succeeds and lists `/platform/templates` as a generated
route. No browser tool available this session either — same known gap as before, now
applying to this new UI too.

---

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
- ~~No platform-admin frontend UI for creating/editing/retiring platform templates —
  deliberately out of scope~~ **Superseded in `4c6f147`** — see "Update" section above;
  a platform-admin UI was added per explicit user request.

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
Granted — 2026-08-30, product owner (Ravi Kant Yadav) gave explicit approval to merge in
chat ("ok then merge"), after both the original review (`47aa65e`, APPROVED) and the
re-review of the platform-admin UI addition (`4c6f147`, APPROVED) were reported back.
Note: no live browser visual check was performed by the product owner before this
approval — recorded here plainly since it was called out as recommended in prior review
passes, though not a hard blocker for this sign-off.

---

## Re-Review — 2026-08-30 (post-approval platform-admin UI addition, `4c6f147`)

Reviewer: Claude Code growixa-reviewer subagent — fresh independent context, no memory of
either the original developer's session or the prior reviewer's session (fallback case per
`growixa-reviewer` SKILL.md §1 — no other tool available this session; recorded plainly per
that rule).

Scope: **only** the diff introduced by `4c6f147` (`git show 4c6f147`, 7 files, 780
insertions / 2 deletions) — a platform-admin frontend UI for managing default email
templates, added after the prior `APPROVED` verdict at `47aa65e` per explicit user request.
The prior review's scope (`d125b2e..47aa65e`, backend + customer-facing "Default Templates"
UI) was not re-verified; it stays covered by the original review section above. Confirmed
via `git log --oneline 47aa65e..4c6f147` that the range also contains `2f31fcd` and
`7f2db93`, which are the pre-existing handoff/tracker commits that recorded the *original*
approval (docs-only, already covered) — not new scope; the only code/tests/docs change in
this pass is `4c6f147` itself, confirmed via `git show --stat 4c6f147` matching `git diff
47aa65e..4c6f147 --stat` minus the tracker/pr_reviews files.

**RBAC correctness in the UI** — confirmed:
- `templates-page.tsx`'s `load()` effect calls `GET /platform/templates` and, on
  `ApiError` with `status === 403`, renders `"You don't have access to manage platform
  default templates."` instead of assuming access or silently showing an empty list.
  Verified this branch is real (not vacuous) via
  `templates-page.test.tsx::"shows an access-denied message on a 403"`, which mocks
  `apiFetch` to reject with `new ApiError(403, "Forbidden")` and asserts the message
  renders.
- Sidebar nav entry: `sidebar.tsx`'s new `{ label: "Templates", href: "/platform/templates",
  requiresPermission: "platform.templates.manage" }` entry is filtered dynamically —
  `Sidebar({ permissions })` does `NAV_ITEMS.filter((item) =>
  permissions.includes(item.requiresPermission))`, and `permissions` is threaded from
  `layout.tsx`'s `apiFetch<PlatformAdmin>("/platform/auth/me")` →
  `admin.permissions` → `<PlatformShell permissions={admin.permissions}>` →
  `<Sidebar permissions={permissions} />`. Not hardcoded, not client-side-only guessed —
  reflects the real session's permission grants from the backend on every load.
- Backend route confirmed to match: `platform_admin/api.py` defines
  `_require_templates_manage = require_platform_permission("platform.templates.manage")`
  applied to all four routes (`GET/POST /templates`, `POST /templates/{id}/versions`,
  `DELETE /templates/{id}`) — the same permission the UI's sidebar and 403 handling assume,
  no drift between the gate and the check.

**Clone-independence messaging** — confirmed correct, not misleading:
- Retire confirmation (`window.confirm` in `handleRetire`): *"Retire "{name}"? Accounts
  that already cloned it keep their own independent copy — this only removes it from the
  Default Templates section for everyone else."* — accurately describes the backend's
  actual behavior (clone creates an independent row with no FK back to the source, per the
  original review's verification of `clone_template_for_account`).
- Edit form heading reinforces the same point: *"Edit "{name}" — saves as a new version,
  existing clones are unaffected."*
- Page-level hint text also states retiring/updating "never affects a copy an account
  already cloned." No copy anywhere overstates or contradicts the actual clone-not-edit
  guarantee.

**Edit = new version, not mutation** — confirmed: `handleEditSubmit` calls `POST
/platform/templates/${editingId}/versions` (append-only version endpoint, matching the
already-reviewed `add_platform_template_version` service function and its route at
`platform_admin/api.py:990`). No call to any endpoint that would mutate a version or the
template row in place. `templates-page.test.tsx::"edits a template by appending a new
version"` asserts the mock only resolves for that exact path + `POST`, not a hypothetical
`PUT`/`PATCH` on the template itself, and asserts the resulting toast reflects the new
version number (`v2`) returned by the (mocked) backend.

**Standard frontend hygiene** — all run directly in the worktree, not taken from the
handoff's claims:
- `npm run lint` (`eslint .`): 0 errors, 2 pre-existing warnings in
  `social/post-form-page.tsx` (unrelated file, not touched by `4c6f147`) — matches prior
  baseline.
- `npm run format:check` (`prettier --check .`): clean, "All matched files use Prettier
  code style!"
- `npm run typecheck` (`tsc --noEmit`): clean, no output/errors.
- `npm run test -- --run` (full suite): **53 files / 311 tests passed** — matches the
  handoff's claimed count exactly (their 311 already includes the 7 new tests in
  `templates-page.test.tsx`, confirmed by file count).
- `templates-page.test.tsx` reviewed line-by-line: 7 tests (403 access-denied, list
  render, empty state, publish, edit-appends-version, retire-after-confirm,
  retire-declined) — all assert real behavior via mocked `apiFetch` call
  paths/methods/payloads and resulting DOM/toast state, not implementation details that
  would pass regardless (e.g. the edit test would fail if the code called `PUT
  /platform/templates/{id}` instead of `POST .../versions`). Not vacuous.
- `npm run build` (`next build`): succeeds; route table lists `/platform/templates` (3.6
  kB, 106 kB First Load JS) alongside the rest of the platform-admin routes.

**Secrets scan** on `git show 4c6f147` (the actual scoped diff, not the wider 3-commit
range): grepped for `api[_-]?key|secret|password|token|BEGIN (RSA|PRIVATE)|AKIA|smtp|Bearer`
— only benign matches are UI copy ("Only standard recipient/account tokens are allowed")
and a doc section header ("## 6. Personalization tokens"), both referring to email
merge-field tokens, not credentials. No real secret, key, or credential found.

**Scope** — `4c6f147` alone touches exactly: `sidebar.tsx` (+6, one nav entry),
`templates/page.tsx` (new, 5 lines, thin wrapper), `templates/templates-page.tsx` (new),
`templates/templates-page.module.css` (new), `templates/templates-page.test.tsx` (new),
`templates/types.ts` (new), and `docs/02-features/EMAIL_TEMPLATES.md` (+8/-4, corrects the
now-false "no platform-admin UI" claim to describe what was actually added). No
backend/schema/migration/worker changes in this commit. No unrelated files touched. Matches
exactly what the task description says was added.

No CHANGES_REQUESTED-triggering findings. No secrets. No scope creep. No RBAC gap. No
misleading clone-independence copy. No mutation-in-place editing path.

### Re-Review Decision

APPROVED

### Re-Reviewed Code Commit

4c6f147 (the platform-admin UI addition; `10c74bc` on top is docs-only — tracker + this
handoff file — confirmed via `git show --stat 10c74bc`, no code/tests/config/docs-under-review
touched).

### Re-Review Human Approval

Still Required, unchanged from the original review's note above — this UI addition is
itself customer-facing (platform-admin-facing) and touches the same higher-trust
`platform.templates.manage` permission surface. Product owner sign-off (ideally including a
real visual check of `/platform/templates`, since neither this reviewer nor the prior one
had working browser tooling) is still outstanding and is a separate gate from this
independent code-review approval.

Status: APPROVED
