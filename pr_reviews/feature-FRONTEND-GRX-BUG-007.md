Task: GRX-BUG-007 — Login page `getByLabel("Password")` strict-mode collision breaks Playwright e2e login flow
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: feature/FRONTEND/GRX-BUG-007
Worktree: .worktrees/grx-e2e-password-label
Base Commit: 9792da6
Latest Commit: 3e0a26d
Status: APPROVED

## What Changed

`apps/web/src/components/auth/password-field.tsx` — renamed the password-visibility
toggle button's `aria-label` from `"Show password"`/`"Hide password"` to
`"Show characters"`/`"Hide characters"`. One-line change, shared component used by both
`login-form.tsx` and `register-form.tsx`.

## Why

Playwright's `getByLabel("Password")` does substring, case-insensitive matching, so the
toggle's old `aria-label` (containing "password") collided with the field's own label,
producing a strict-mode violation ("resolved to 2 elements") whenever a spec called
`getByLabel("Password").fill(...)`.

## Important Files

- `apps/web/src/components/auth/password-field.tsx` (the only code change)

## Tests

Ran locally against the real Compose stack (`podman compose up postgres redis rabbitmq
api`, `COMPOSE_BIN=podman npm run test:e2e` in `apps/web`):

- Confirmed the fix: `getByLabel("Password")` no longer strict-mode-violates. A Playwright
  page snapshot after the fix shows `textbox "Password"` and `button "Show characters"` as
  distinct, non-colliding accessible names.
- `dashboard.spec.ts` (login flow) and `team.spec.ts` (invite/accept/login) still fail
  end-to-end, but on a **different, unrelated** failure now: both time out waiting for
  `getByRole("button", { name: "Sign in" })` — the real submit button says `"Login to
  Growixa"` (`login-form.tsx:131`), not `"Sign in"`. This is a separate, pre-existing
  copy/spec mismatch, filed as `GRX-BUG-008`. Not fixed here — out of scope for this
  aria-label fix, and deciding which side (UI copy vs. spec) is "correct" is a product
  call, not a one-line test fix.
- `npx eslint`, `npx prettier --check`, `npx tsc --noEmit` on the changed file: all clean.

## Known Issues / Evidence Gaps

- `GRX-BUG-008` (new, filed in the tracker) blocks `dashboard.spec.ts`/`team.spec.ts` from
  fully passing end-to-end even after this fix. The specific defect this task targets
  (the `getByLabel("Password")` collision) is fixed and independently verified via the
  page snapshot; the remaining spec failures are unrelated.

## Review Findings

Verified independently against the real worktree (not the handoff's own account):

- `git show 3e0a26d`: confirms the diff is exactly one line in
  `apps/web/src/components/auth/password-field.tsx` — `aria-label` changed from
  `"Hide password"/"Show password"` to `"Hide characters"/"Show characters"`. Matches
  the handoff's description exactly.
- `git diff main...HEAD --name-only`: only 4 files touched —
  `password-field.tsx`, `MASTER_TASK_TRACKER.csv`, `MASTER_TASK_TRACKER.md`, and this
  `pr_reviews/...md` handoff. Confirmed the doc-only commit `84e461e` (after the code
  commit `3e0a26d`) touches only tracker + handoff files, no code/tests/config — matches
  the claim that nothing besides docs changed after the code fix.
- `grep -rn "Show password|Hide password"` across `apps/web` (excluding `.next`/
  `node_modules`) — zero remaining references to the old aria-label strings in tracked
  source or tests. Confirmed via `grep` that no e2e spec (`dashboard.spec.ts`,
  `team.spec.ts`, `smoke.spec.ts`) asserts on the toggle button's accessible name at all
  — they only use `getByLabel("Email")`/`getByLabel("Password")` against the field
  labels, which is exactly the collision this fix resolves. Read the current
  `password-field.tsx` directly: the field's own `<label>` renders `"Password"`
  (line 14/24-26) and the toggle button now renders `"Hide/Show characters"` (line 43) —
  no substring overlap with `getByLabel("Password", { exact: false })`'s default
  case-insensitive substring match, so the strict-mode collision described in the task is
  correctly eliminated.
- Scope check: diff touches only `password-field.tsx` — no drive-by changes to
  `login-form.tsx`, `register-form.tsx`, or any other file that consumes this shared
  component, consistent with an aria-label-only rename that doesn't change the component's
  props or visible behavior.
- Secrets scan: `git diff main...HEAD -- apps/web/src/components/auth/password-field.tsx`
  grepped for credential/token/key patterns — nothing found. No secrets anywhere in the
  branch's diff.
- Ran real toolchain in the worktree (not trusting the handoff's claimed results):
  `npx tsc --noEmit` — clean, no errors. `npx eslint
  src/components/auth/password-field.tsx` — clean. `npx prettier --check
  src/components/auth/password-field.tsx` — "All matched files use Prettier code style!".
- Did not re-run the full Playwright e2e suite against a live Compose stack — the change
  is a single-line, non-collision-inducing aria-label rename with no logic/behavior
  change, the developer's own page-snapshot evidence (documented above) is directly
  verifiable reasoning (accessible names no longer share the "password" substring), and
  this is explicitly a LOW-risk change per the task description; re-running the full stack
  was judged unnecessary to reach a confident verdict.
- GRX-BUG-008 (the pre-existing "Sign in" vs "Login to Growixa" button-text mismatch) is
  correctly out of scope for this diff — confirmed it is not touched anywhere in
  `git diff main...HEAD`.

## Review Decision

APPROVED

## Reviewed Code Commit

3e0a26d3d5209f46df4fbcd9fc26c98cffbd4208

## Review Record Commit

(recorded in the commit that adds this verdict to the handoff file)

## Human Approval
Not Required — internal aria-label rename, same visible icon/behavior, no copy change to
sighted users (screen-reader-only label wording change). Confirmed by reviewer: no
customer-facing visible copy changed, LOW risk, no auth/RBAC/billing/migration surface
touched.

Status: APPROVED
