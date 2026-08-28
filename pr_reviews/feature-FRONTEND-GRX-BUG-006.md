Task: GRX-BUG-006 — E2E CI seed script violates `user_roles.account_id` NOT NULL, failing every run on `main`
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: feature/FRONTEND/GRX-BUG-006
Worktree: .worktrees/grx-e2e-seed-accountid
Base Commit: 49f94f7
Latest Commit: aa5cc03
Status: APPROVED

## What Changed

`apps/web/tests/e2e/global-setup.ts` now passes `account_id=account.id` when constructing
the seeded `UserRole` row. One-line fix.

## Why

`user_roles.account_id` is `NOT NULL` (`apps/api/src/growixa_api/users/models.py:53-58`),
but the seed script's inline Python omitted it, so every `e2e` CI run on `main` since
2026-08-23 failed at setup (`NotNullViolationError`) before any Playwright spec executed.

## Important Files

- `apps/web/tests/e2e/global-setup.ts` (the only change)

## Tests

Ran locally against the real Compose stack (`podman compose up postgres redis rabbitmq api`,
`COMPOSE_BIN=podman npm run test:e2e` in `apps/web`):

- Reproduced the original bug directly: re-running the old (unpatched) `UserRole(user_id=...,
  role_id=...)` call against the running API container raises exactly
  `NotNullViolationError: null value in column "account_id" of relation "user_roles"`.
- Confirmed the fix: the same call with `account_id=account.id` succeeds.
- Full `npm run test:e2e`: global-setup no longer fails. 2/4 specs now pass
  (`smoke.spec.ts`, `dashboard.spec.ts` logged-out redirect). 2 specs
  (`dashboard.spec.ts` login flow, `team.spec.ts` invite flow) fail on an **unrelated,
  pre-existing** issue — `getByLabel("Password")` strict-mode-matches both the password
  input and a "Show password" toggle button on the login page. Not touched here; filed as
  a follow-up (see below).

## Known Issues / Evidence Gaps

- New follow-up needed: login page's password field/toggle accessible-name collision
  breaks `getByLabel("Password")` in Playwright, failing `dashboard.spec.ts` (login) and
  `team.spec.ts`. Out of scope for this NOT-NULL fix. Not yet added to the tracker —
  reviewer or developer should file it.
- Local verification incidentally ran `podman compose down -v` against the shared
  `growixa` Compose stack (project name is fixed in `compose.yaml`), removing named
  volumes. Confirmed with the repo owner that no real local dev data was lost.

## Review Findings

Verified independently against the branch, not the handoff's account:

- **Diff scope**: `git diff main...HEAD --stat` shows exactly 4 files: the code fix
  (`apps/web/tests/e2e/global-setup.ts`, 1 line), two tracker files, and the handoff file
  itself. `da39148` (the only code-touching commit) changes exactly one line:
  `UserRole(user_id=..., role_id=...)` → `UserRole(account_id=account.id, user_id=...,
  role_id=...)`. No other files, no unrelated drive-by changes.
- **Constraint match confirmed**: `apps/api/src/growixa_api/users/models.py:47-58`,
  `UserRole.account_id` is `Mapped[uuid.UUID]` with `nullable=False` — the fix supplies
  exactly the field the NOT NULL constraint requires, sourced from the `account` object
  already flushed earlier in the same script (line 46-48, `account = Account(...);
  session.add(account); await session.flush()`), so `account.id` is populated before use.
  Correct and minimal.
- **Consistency check**: grepped every other `UserRole(...)` construction site in
  `apps/api/` (`auth/services.py`, `accounts/services.py`, `users/repositories.py`,
  `users/services.py`, `cli/onboard_iitdeveloper.py`) — all already pass `account_id`.
  The e2e seed script was the sole outlier, matching the bug report's premise.
- **Scope of doc changes**: `MASTER_TASK_TRACKER.md`/`.csv` diff moves GRX-BUG-006 to
  `IN_REVIEW` with accurate evidence, and adds a new GRX-BUG-007 row for the unrelated
  pre-existing `getByLabel("Password")` Playwright strict-mode collision found while
  verifying this fix (not fixed inline — correctly deferred as a follow-up, not scope
  creep). Cross-checked the GRX-BUG-007 claim directly: `password-field.tsx:43` has
  `aria-label={showPassword ? "Hide password" : "Show password"}` on the reveal toggle,
  which does collide with Playwright's `getByLabel("Password")` used in
  `dashboard.spec.ts`/`team.spec.ts` — the claim holds up.
- **Secrets check**: `git diff main...HEAD` grepped for password/secret/api-key/token/
  private-key patterns — only doc prose and test fixture identifiers matched.
  `apps/web/tests/e2e/fixtures.ts` (unchanged by this branch) uses
  `E2E_USER_PASSWORD = "E2E-Test-Password-123!"`, an obvious placeholder per AGENTS.md
  §2.1, not a real credential. No secret leakage.
- **Local checks run in the worktree** (`.worktrees/grx-e2e-seed-accountid/apps/web`):
  `npx tsc --noEmit` — clean; `npx eslint tests/e2e/global-setup.ts` — clean; `npx
  prettier --check tests/e2e/global-setup.ts` — "All matched files use Prettier code
  style!". Did not re-run the full Playwright e2e suite against live Compose (not
  available in this reviewer session); the developer's stated local verification
  (reproduced the original `NotNullViolationError` on unpatched code, confirmed the
  patched seed succeeds, ran `npm run test:e2e` with global-setup no longer failing and
  2/4 specs passing, the other 2 failing on the separately-filed GRX-BUG-007) is
  plausible and consistent with the code change and with the GRX-BUG-007 markup
  cross-check above — accepted for this LOW-risk, one-line test-infra fix per the task's
  stated review depth.
- **Commit hygiene**: `da39148` is the only commit touching code/tests; `eebd041` and
  `aa5cc03` are docs-only (tracker + handoff), confirmed via `git show --stat` on both.
  No secrets, no scope creep, no unrelated changes after the code commit.

## Review Decision
APPROVED

## Reviewed Code Commit
da39148740a27b48dc1460cc724cd389070f48a5

## Review Record Commit


## Human Approval
Not Required — internal test-infra fix, no customer-facing behavior, no auth/RBAC/billing/migration surface.

Status: APPROVED
