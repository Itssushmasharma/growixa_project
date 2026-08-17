Task: GRX-TEST-ORG-001
Developer: Codex
Reviewer:
Branch: feature/BACKEND/test-folder-organization
Worktree: .worktrees/test-folder-organization
Base Commit: 8d751290b2844c2452dbdcf0a7b6fc5d5430de7e
Latest Commit: 015c9df
Status: READY_FOR_REVIEW

## What Changed

Reorganized the flat API pytest suite into domain folders and the worker pytest suite into
job/runtime folders. Added short README files documenting where future tests should live.

## Why

The API test folder had grown to 56 top-level test files, making navigation and ownership
harder. The new layout keeps pytest discovery unchanged while making the suite manageable.

## Important Files

- `apps/api/tests/README.md`
- `apps/api/tests/*/test_*.py`
- `apps/worker/tests/README.md`
- `apps/worker/tests/*/test_*.py`
- `docs/00-project-control/MASTER_TASK_TRACKER.md`
- `docs/00-project-control/WORKTREE_TRACKER.md`

## Tests

- `cd apps/api && DATABASE_URL=postgresql+asyncpg://growixa:growixa@localhost:5433/growixa_test REDIS_URL=redis://localhost:6379/0 RABBITMQ_URL=amqp://guest:guest@localhost:5672/ uv run --extra dev pytest --collect-only -q` -> 396 tests collected
- `cd apps/worker && uv run --extra dev pytest --collect-only -q` -> 28 tests collected

## Known Issues / Evidence Gaps

Full test execution was not run because this is a path-only reorganization; collection
verifies importability and discovery from the new structure.

## Review Findings


## Review Decision

CHANGES_REQUESTED / APPROVED

## Reviewed Code Commit

015c9df

## Review Record Commit


## Human Approval

Not Required

Status: READY_FOR_REVIEW
