Task: GRX-BUG-010 — E2E team spec's invite-confirmation text matches two elements (toast + inline panel), causing a strict-mode violation
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: feature/FRONTEND/GRX-BUG-010
Worktree: .worktrees/grx-bug-010
Base Commit: 2d3215e
Latest Commit: ae98e7a
Status: APPROVED

## What Changed

Three compounding issues in the same `team.spec.ts` invite/accept/login flow, found and
fixed together:

1. `apps/web/src/app/(dashboard)/dashboard/team/team-page.tsx` — added
   `data-testid="invite-success-panel"` to the persistent invite-confirmation `<div>`.
2. `apps/web/tests/e2e/team.spec.ts` — scoped the confirmation-text assertion and the
   `<code>` token lookup to `page.getByTestId("invite-success-panel")` instead of a bare
   page-wide `getByText`, and now extracts just the `token` query param from the
   displayed accept-invitation URL via `new URL(...)` instead of passing the whole URL
   string as the token.
3. `apps/web/tests/e2e/global-setup.ts` — the manually-created e2e `Account` now also gets
   an `AccountSubscription` row (on the `starter` plan, 3 seats), matching what real
   registration creates automatically.

## Why

- **The original bug (task scope)**: `page.getByText(/Invitation sent to .../)` strict-mode
  matched both the transient toast (`showToast(...)`) and the persistent inline panel
  (`team-page.tsx:257`). Scoped the locator to the panel — it's the stable, non-
  auto-dismissing element, and it's also where the test already reads the invite token
  from, so scoping both to the same container is the natural fix.
- **Bug #2 (found while verifying #1)**: once the strict-mode violation was gone, the test
  progressed further and failed on the accept-invitation API call — the panel's `<code>`
  element shows the full shareable URL (`.../accept-invitation?token=XXX`), but the test
  was sending that whole string as `token`, which the backend correctly rejects (hashes
  don't match). Not a regression — this was always broken, just unreachable before #1 was
  fixed.
- **Bug #3 (found while verifying #2)**: with the token fixed, the accept call started
  500ing. Root cause: `billing/services.py:check_plan_limit` asserts every account has an
  `AccountSubscription` row (`BILLING_SYSTEM_ARCHITECTURE.md` §3.4) — real registration
  creates one automatically, but this e2e seed script's manually-constructed `Account`
  never did (the same gap class as `GRX-BUG-006`'s missing `account_id`). Seeded on
  `starter` rather than `free`: the free plan's 1-seat quota is already used by the
  seeded admin user itself, so inviting a second team member would otherwise be correctly
  rejected with 402 regardless of the first two fixes — this is real, working quota
  enforcement, not a bug, but it means the free plan can never be right for an e2e account
  a team-management test needs to add a second user to.

## Important Files

- `apps/web/tests/e2e/team.spec.ts`
- `apps/web/tests/e2e/global-setup.ts`
- `apps/web/src/app/(dashboard)/dashboard/team/team-page.tsx` (one `data-testid` attribute
  added, no behavior change)

## Tests

Ran locally against the real Compose stack (`docker compose up postgres redis rabbitmq
api`, full local run of each fix as it was found, then a clean end-to-end pass with all
three fixes applied together):

- `npm run test:e2e` (all 4 specs: `smoke`, `dashboard` ×2, `team`): **all pass**, for the
  first time since `GRX-BUG-006` first broke the e2e job's setup.
- `npm run lint`, `npm run format:check`, `npm run typecheck`: clean (2 pre-existing,
  unrelated `<img>` warnings in `post-form-page.tsx`, not touched by this branch).
- `npm run test -- team-page` (vitest, the existing unit suite for this page): 5/5 pass —
  the `data-testid` addition didn't affect existing component tests.

## Known Issues / Evidence Gaps

None outstanding — this was the last open e2e bug from the `GRX-BUG-006` → `010` chain;
the full suite is green.

## Review Findings

Independently re-verified against the actual branch (not the handoff's account of it),
MEDIUM depth given the bundled 3-part fix touching a billing-model-shaped seed script.

- **Diff matches description exactly.** `git diff 2d3215e..ae98e7a` shows only the three
  files claimed: `team-page.tsx` (+1 line, `data-testid="invite-success-panel"`, purely
  additive), `team.spec.ts` (locator scoping to the testid + `new URL(...).searchParams.get
  ("token")` extraction), `global-setup.ts` (seeded `AccountSubscription` row). No drive-by
  changes.
- **Original bug premise confirmed.** `team-page.tsx:69` (`showToast("success",
  \`Invitation sent to ${result.email}\`)`) and `team-page.tsx:257` (the persistent panel,
  same text) both match the old unscoped `page.getByText(/Invitation sent to .../)` regex —
  a real Playwright strict-mode collision, not an invented one.
- **Bug #2 (token extraction) verified.** `team-page.tsx:262-263` renders
  `${window.location.origin}/accept-invitation?token=${inviteResult.token}` — an absolute
  URL in the browser context Playwright always runs in (the relative fallback branch is
  SSR-only, unreachable in an e2e test), so `new URL(inviteLink).searchParams.get("token")`
  is correct and robust for this test, not just "happens to work."
- **Bug #3 (billing seed fix) verified against real model/migration code, not just the
  developer's account:**
  - `billing/models.py:97-147`'s `AccountSubscription` has exactly six NOT NULL columns
    with no default: `account_id`, `plan_id`, `status`, `currency`,
    `current_period_start`, `current_period_end` — all six are set by the new seed code;
    every other column is nullable or has a server default.
  - `CheckConstraint`s confirmed: `status IN ('PENDING','ACTIVE','PAST_DUE','CANCELED',
    'HALTED')` and `currency IN ('USD','INR')` — the seed's `"ACTIVE"`/`"USD"` satisfy both.
  - `billing/services.py:269` (`check_plan_limit`) does assert
    `subscription is not None, "every account has exactly one row (GRX-BILL-002)"` exactly
    as claimed, and a second identical assert exists at line 631.
  - `subscription_plans` seed migration (`e926f73f7ece_billing_schema_rbac_seed.py`)
    confirms a real `starter` plan row with `max_user_seats=3` and a `free` plan row with
    `max_user_seats=1` — the developer's stated reasoning (free's single seat is already
    consumed by the seeded admin, so `starter` is required for this test to ever reach the
    second-invite path) holds up against the actual seed data.
  - `FREE_PLAN_PERIOD_DAYS`/`get_plan_by_slug` imports match real exports in
    `billing/repositories.py`.
- **Scope/bundling judgment: reasonable, not scope creep.** All three fixes are in the same
  test function (`team.spec.ts`'s single invite/accept/login test), each was only reachable
  once the prior one was fixed, and all three block the same acceptance criterion
  ("`team.spec.ts` passes end-to-end") — consistent with the GRX-BUG-006→009 precedent of
  filing separately only when a compounding bug is in an unrelated file/page. Bug #3 does
  touch a billing-shaped model (`AccountSubscription`), which nominally reads as
  higher-risk, but the change is confined to a disposable e2e seed script (never imported
  by application code) and constructs the row using only real model columns/constraints —
  no production billing logic, migration, or schema changed.
- **Repeated seed-script touch (GRX-BUG-006, now this) noted, not a blocker.** Both changes
  are additive (missing `account_id`, then missing `AccountSubscription`) rather than
  contradictory rewrites of the same code — no thrash pattern, just the seed script
  catching up to what real registration has always done.
- **No secrets/credentials.** Full diff reviewed line by line; no tokens, keys, passwords,
  or credentials introduced. Only literal string is the local test password already present
  unchanged in the file (`E2E_USER_PASSWORD`, not part of this diff).
- **Nothing changed after the reviewed commit besides docs.** `git diff ae98e7a..a8fcb14`
  touches only `MASTER_TASK_TRACKER.md`, `MASTER_TASK_TRACKER.csv`, and the handoff file
  itself — no code/tests/config changed post-review.
- **Lint/typecheck re-run independently** (not trusting the handoff's numbers): `npm run
  lint` → 0 errors, 2 pre-existing `<img>` warnings in `post-form-page.tsx` (untouched by
  this branch, matches handoff claim exactly); `npm run typecheck` → clean.
- **Live e2e run not completed**: attempted to bring up the Compose stack
  (`docker compose up -d --build postgres redis rabbitmq api`) to directly confirm the
  4/4-spec pass claim, but port 5432 was already bound by other unrelated local Postgres
  containers on this machine (`docker-postgres-1`, `iam-postgres-1`, etc.) — did not
  proceed further to avoid disrupting those. Compensated with the deep static
  verification above (every one of the three fixes checked against the real model,
  constraint, service-layer, and rendered-markup code, not just re-reading the diff).
  Recommend a live e2e run before merge if that direct confirmation is wanted, on a
  machine/port range without a conflict.

## Review Decision

APPROVED

## Reviewed Code Commit

ae98e7a (last commit touching code/tests; a8fcb14 is docs-only — tracker + this handoff)

## Review Record Commit


## Human Approval
Not Required — test-only + one additive `data-testid` attribute (no visual/behavioral
change to the team page); the `AccountSubscription` seed addition is confined to a
disposable e2e test-setup script, not production billing code.

Status: APPROVED
