Task: Bugfix - return to all campaigns after scheduling
Developer: Codex
Reviewer: Codex
Branch: feature/FRONTEND/campaign-schedule-redirect
Worktree: /Users/ravi/Projects/growixa/.worktrees/campaign-schedule-redirect
Base Commit: ba7290cf9518e0f374c27f998741dbc894226e3f
Latest Commit: beb7b17f254e229c385ce024a51262ce84c62df0
Status: APPROVED

## What Changed

- Redirects to `/dashboard/campaigns` after `POST /campaigns/:id/schedule` succeeds.
- Extends the existing schedule regression test to assert navigation back to the all-campaigns page.

## Why

After confirming a schedule, the UI stayed on the campaign edit/detail page. The expected workflow is to return to the campaign list so the newly scheduled campaign is visible in the all-campaigns view.

## Important Files

- `apps/web/src/app/(dashboard)/dashboard/campaigns/campaign-form-page.tsx`
- `apps/web/src/app/(dashboard)/dashboard/campaigns/campaign-form-page.test.tsx`

## Tests

- `cd apps/web && npm run test -- campaign-form-page.test.tsx` - passed, 18 tests
- `cd apps/web && npm run lint` - passed with 0 errors; existing warnings remain in unrelated contacts/social files
- `cd apps/web && npm run typecheck` - passed
- `cd apps/web && npm run format:check` - passed

## Known Issues / Evidence Gaps

- Full web build/e2e suite was not run for this two-line frontend navigation fix.
- `npm install` in this worktree emitted a non-blocking jsdom engine warning because local Node is `v22.20.0`; tests still passed.
- Existing lint warnings outside this change remain in `contacts-page.tsx` and `social/post-form-page.tsx`.

## Review Findings

No blocking findings.

Review notes:
- Verified the reviewed-code diff is limited to adding the success redirect in `CampaignFormPage` and extending the existing schedule regression test.
- Confirmed the redirect runs only after `POST /campaigns/:id/schedule` succeeds; the error path remains on-page and surfaces the existing toast.
- Confirmed scheduling controls remain behind the existing `campaigns.send` and `campaigns.manage` UI checks.
- Confirmed no secret-shaped material was introduced in the reviewed diff.

Reviewer validation on 2026-08-18:
- `cd apps/web && npm run test -- campaign-form-page.test.tsx` - passed, 18 tests.
- `cd apps/web && npm run lint` - passed with 0 errors and 4 existing unrelated warnings in contacts/social files.
- `cd apps/web && npm run typecheck` - passed.
- `cd apps/web && npm run format:check` - passed.


## Review Decision
APPROVED

## Reviewed Code Commit
beb7b17f254e229c385ce024a51262ce84c62df0

## Review Record Commit
This commit (review-record metadata only).

## Human Approval
Approved by Ravi Kant Yadav via Codex chat on 2026-08-18; scheduling workflow is customer-facing.

Status: APPROVED
