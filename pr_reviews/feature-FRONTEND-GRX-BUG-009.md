Task: GRX-BUG-009 — E2E dashboard spec asserts "Welcome to Growixa" text that no longer exists on the dashboard
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: feature/FRONTEND/GRX-BUG-009
Worktree: .worktrees/grx-bug-009
Base Commit: 6dcce1d
Latest Commit: e796a09
Status: READY_FOR_REVIEW

## What Changed

`apps/web/tests/e2e/dashboard.spec.ts` — replaced
`expect(page.getByText("Welcome to Growixa")).toBeVisible()` with an assertion on the
dashboard's real `PageHeader` description text ("Welcome back! Track your multi-channel
marketing performance and audience growth."). One-line assertion change (reformatted by
Prettier across a few lines).

## Why

`git log -p` on `dashboard-page.tsx`/`page.tsx` shows "Welcome to Growixa" was the heading
of a pre-`GRX-SAAS-014` empty-state placeholder ("There's nothing here yet. Once you add
contacts and campaigns...") — deliberately removed on 2026-08-14 (commit `79c8825`) when
the real `DashboardPage`/Overview UI (KPI grid, trend chart, live activity, quota gauges)
shipped. The e2e spec was never updated to match, so once `GRX-BUG-008` fixed the login
button-name mismatch and login could actually complete, this assertion started timing out
since no "Welcome to Growixa" text exists anywhere on the current dashboard. Chose to
update the assertion (test-only) rather than restore the removed placeholder, since the
placeholder was intentionally replaced by real content, not accidentally dropped.

## Important Files

- `apps/web/tests/e2e/dashboard.spec.ts` (the only change)

## Tests

Ran locally against the real Compose stack (`docker compose up postgres redis rabbitmq
api`, `npx playwright test tests/e2e/dashboard.spec.ts` in `apps/web`):

- `dashboard.spec.ts` now passes fully end-to-end (both specs): logged-out redirect, and
  the login → dashboard → logout → session-actually-gone flow, including the new welcome
  assertion.
- Sanity-checked `team.spec.ts`/`smoke.spec.ts` still behave as expected: `smoke.spec.ts`
  passes; `team.spec.ts` still fails, but on the separately-filed, unrelated `GRX-BUG-010`
  (invite-confirmation text strict-mode collision) — not touched here.
- `npx eslint`, `npx prettier --check`, `npx tsc --noEmit` on the changed file: all clean.

## Known Issues / Evidence Gaps

- `GRX-BUG-010` (already tracked separately) still blocks `team.spec.ts` from passing
  end-to-end. Unrelated to this fix, not touched.

## Review Findings

Verified independently against the real branch (not the handoff's account):

1. **Diff scope confirmed clean.** `git diff 6dcce1d..HEAD --stat -- . ':(exclude)pr_reviews/**'`
   shows exactly 3 files: `apps/web/tests/e2e/dashboard.spec.ts` (the actual fix, 6 lines),
   and `MASTER_TASK_TRACKER.csv`/`.md` (status field `READY` → `IN_REVIEW` for the
   GRX-BUG-009 row only, diffed line-by-line to confirm no other row content changed).
   No production/app code touched.
2. **Replacement text is byte-exact.** `grep -n "description=" apps/web/src/app/(dashboard)/dashboard/dashboard-page.tsx`
   line 77 reads `description="Welcome back! Track your multi-channel marketing
   performance and audience growth."` — matches the new `page.getByText(...)` assertion
   in the spec verbatim.
3. **Historical claim verified, not trusted.** `git show 79c8825656c2a3be55c202d2a990413340c8965c -- 'apps/web/src/app/(dashboard)/dashboard/page.tsx'`
   confirms "Welcome to Growixa" was the `<h2>` heading of the old empty-state placeholder
   ("There's nothing here yet...") and was deliberately removed and replaced by the real
   `DashboardPage` component in that commit (2026-08-14, GRX-SAAS-014). `grep -rn "Welcome
   to Growixa" apps/web/src apps/web/tests` today shows the string exists only in unrelated
   template/campaign preset fixtures (sample email subject text), never as real dashboard
   copy — the developer's "not accidentally dropped" premise holds under current `main`.
4. **No secrets.** Full diff scanned for credential/token/password/private-key patterns —
   only hits are the pre-existing word "token" in unrelated personalization-feature tracker
   prose, not a real leak.
5. **Quality gates re-run myself** in the worktree (not just cited from the handoff):
   `npx eslint tests/e2e/dashboard.spec.ts` — clean; `npx prettier --check
   tests/e2e/dashboard.spec.ts` — "All matched files use Prettier code style!"; `npx tsc
   --noEmit -p .` — clean. Did not re-run the live Playwright e2e suite against Compose
   (not necessary at this risk level given the diff is a single self-contained assertion
   change verified byte-exact against real rendered copy); the developer's own
   Compose-backed run is consistent with what the diff shows and is corroborating, not
   load-bearing, evidence.

No findings. Test-only, single-file production-code-adjacent change, correctly scoped,
correctly reasoned, no drive-by changes, no secrets.

## Review Decision
APPROVED

## Reviewed Code Commit
e796a09 (last commit touching code/tests; `0838a5b` after it is doc-only — tracker status
update + this handoff file, confirmed via `git diff e796a09..0838a5b --stat`)

## Review Record Commit
5ba8e1009322c620ea0bd8a99ce98b868943c9c9

## Human Approval
Not Required — test-only fix (spec assertion), no production/customer-facing code
changed.

Status: APPROVED
