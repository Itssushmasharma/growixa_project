Task: File GRX-BUG-006 in the master tracker for the e2e seed NOT NULL failure
Developer: Claude Code
Reviewer: (pending — independent review required before merge)
Branch: docs/BACKEND/tracker-file-e2e-seed-bug
Worktree: /Users/ravi/Projects/growixa
Status: READY_FOR_REVIEW

## What Changed

- `MASTER_TASK_TRACKER.md`: added row `GRX-BUG-006` (P1, `READY`) documenting the e2e CI
  seed failure.
- `MASTER_TASK_TRACKER.csv`: regenerated via `python3 scripts/tracker_to_csv.py` (the
  canonical generator — do not hand-edit the CSV) so it stays derived from the `.md`.

## Why

While independently re-reviewing PR #22 (`pr_reviews/docs-BACKEND-tracker-GRX-BUG-001-done.md`),
the `e2e` CI job was found failing with `NotNullViolationError` on `user_roles.account_id`
inside `apps/web/tests/e2e/global-setup.ts`'s seed script. Checked the last 15 `CI` runs on
`main` (`gh run list --branch main --limit 15`, back to 2026-08-23) — every single one has
`e2e` failing with the identical error, while `backend`/`worker`/`frontend` pass
independently. This is filing that finding as its own tracked task per the reviewer
skill's guidance (findings that aren't trivial to fix inline get filed, not fixed
in-branch) — the user asked for it to be filed in the tracker, not fixed here.

## Important Files

- `docs/00-project-control/MASTER_TASK_TRACKER.md`
- `docs/00-project-control/MASTER_TASK_TRACKER.csv` (generated)

## Tests

- `python3 scripts/tracker_to_csv.py --check` — "up to date (135 tasks)", confirming the
  CSV matches the `.md` exactly.
- No source/test/config files touched — docs-only, nothing else to run.

## Known Issues / Evidence Gaps

- This filing does not fix the underlying bug — `GRX-BUG-006` is left `READY` for
  whoever picks it up next.

Status: READY_FOR_REVIEW
