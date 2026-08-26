Task: File GRX-BUG-006 in the master tracker for the e2e seed NOT NULL failure
Developer: Claude Code
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: docs/BACKEND/tracker-file-e2e-seed-bug
Worktree: /Users/ravi/Projects/growixa
Status: APPROVED

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

## Review Findings

Independently re-verified every claim, not just the handoff's account of it:

1. **Scope is genuinely docs-only.** `git diff origin/main..origin/docs/BACKEND/tracker-file-e2e-seed-bug --stat`
   touches exactly `MASTER_TASK_TRACKER.md` (+1 row), `MASTER_TASK_TRACKER.csv`
   (+1 generated row), and the handoff file itself. No source/test/config file changed.
2. **CSV regeneration verified, not hand-edited.** Ran `python3 scripts/tracker_to_csv.py --check`
   myself in the branch worktree → `up to date (135 tasks)`, exit 0. Confirms the
   committed CSV is exactly what the generator produces from the `.md`, not a divergent
   hand-edit.
3. **Underlying claim independently confirmed, end to end** — did not trust the row's
   prose:
   - `gh run list --branch main --limit 15` shows all 15 most recent `main` CI runs
     (back to 2026-08-23) as `failure`/`startup_failure`.
   - Job-level breakdown on two sampled runs (`32982810819`, `32665187976`) shows
     `backend`, `worker`, `frontend` all `success` while `e2e` is `failure` in both —
     confirms this is isolated to the `e2e` job, not a broader regression across all
     checks.
   - Pulled the actual `e2e` job log (`gh run view 32982810819 --log`) and found the
     literal error: `asyncpg.exceptions.NotNullViolationError: null value in column
     "account_id" of relation "user_roles" violates not-null constraint`, from
     `INSERT INTO user_roles (account_id, user_id, role_id, assigned_by_user_id) ...`.
   - Read `apps/web/tests/e2e/global-setup.ts` on current `main` directly: line 58 is
     `session.add(UserRole(user_id=user.id, role_id=admin_role.id))` — `account_id` is
     indeed omitted. Matches the row's description exactly.
4. **No Task ID collision, no other row modified.** Checked all existing `GRX-BUG-00N`
   rows (001–005) in `MASTER_TASK_TRACKER.md`; `GRX-BUG-006` is new and unused. The diff
   contains exactly one added line in the `.md` (and its CSV counterpart) — no existing
   row's text changed.
5. **Secrets scan clean**, as expected for a docs-only change (`git diff` grepped for
   secret/token/password/credential/api-key patterns — only doc prose matched, no real
   values).

No issues found. The row's severity (P1), status (`READY`, correctly left unfixed per
the user's explicit instruction to file rather than fix), and evidence are all accurate
and independently reproducible.

## Review Decision
APPROVED

## Reviewed Code Commit
57aaf9ba1b962e3a538a72f023acee0b12efed18

## Human Approval
Not Required (docs-only, internal task-tracking row; no customer-facing or product-judgment change)

Status: APPROVED
