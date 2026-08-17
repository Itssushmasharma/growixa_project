Task: GRX-TEST-ORG-001
Developer: Codex
Reviewer: Claude Code (different tool than developer — Codex)
Branch: feature/BACKEND/test-folder-organization
Worktree: .worktrees/test-folder-organization
Base Commit: 8d751290b2844c2452dbdcf0a7b6fc5d5430de7e
Latest Commit: 3e94c20
Status: APPROVED

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

Reviewer: Claude Code (different tool than developer — Codex).

**The change is provably safe, and I can put a stronger number on that than the handoff
does.** `git diff main...HEAD --numstat` shows **62 files with `0` insertions and `0`
deletions** — every single moved test is a pure rename. Not one line of test logic
changed. The only files with real content are the two new READMEs, two tracker-doc lines,
and this handoff. For a reorganization, that is the strongest safety evidence available,
and it bounds the risk precisely: nothing can break except through pytest's own
discovery/import semantics.

Those semantics I checked directly:

- **Fixtures still resolve.** There is a single `conftest.py` at `apps/api/tests/`, which
  applies to every subdirectory beneath it, so no fixture went out of scope.
- **No basename collisions.** Duplicate `test_*.py` basenames across sibling folders are
  the classic way this refactor breaks pytest (`import file mismatch`); there are none.
- **Collection matches the claim** — 396 API tests, identical to `main`'s 396, so nothing
  was silently dropped or double-counted.

**I closed the handoff's stated evidence gap and ran the suites.** That is worth reporting
carefully, because the result is not a clean number:

- Branch, full API suite, run 1: **16 failed / 380 passed**.
- Branch, full API suite, run 2, identical command: **0 failed / 396 passed**.
- `main` control, same environment: **9 failed / 387 passed**, and the failing set was a
  different set again.

So the suite is **nondeterministic in this environment**, swinging by 16 tests between
two identical invocations of the same commit. That is the shared, non-isolated dev
Postgres — the same pollution already documented on `GRX-SAAS-009` and re-confirmed on
`GRX-CONTACT-010` (fixtures colliding with leftover fixed-UUID rows). It is **not caused by
this branch**, and I found no failure attributable to the reorganization. But it does mean
neither the developer nor I can currently demonstrate "the suite passes" for any branch,
and no reviewer should read "396 collected" as "396 healthy".

1. **LOW — packaging is now inconsistent.** `apps/api/tests/__init__.py` exists, making
   `tests` a package, but none of the nine new subdirectories have one. It works today
   (collection and execution both succeed), but a half-package tree is exactly the kind of
   thing that breaks later under a different `importmode` or when two subfolders eventually
   do share a basename. Adding `__init__.py` to each new subdirectory would make the tree
   internally consistent and close that off cheaply.

2. **OBSERVATION, not a defect — this fixes navigability, not the real pain.** The stated
   motivation is that 56 flat files made the suite hard to navigate, which is fair and this
   solves it. But the suite's actual problem is the nondeterminism above: tests that pass
   or fail depending on leftover database state and execution order. Reorganizing into
   folders *changes* collection order, so it perturbs precisely the weakness it does not
   fix. Worth filing the real one — per-test transaction rollback or a disposable database
   per run — as its own task while this area has someone's attention.

Nothing else: no source, config, dependency or migration changes; no security or
isolation surface touched. `Human Approval: Not Required` is the correct call — this is
internal test layout with no customer-facing or product-behaviour effect.

## Review Decision

APPROVED

## Reviewed Code Commit

3e94c20 (branch HEAD at review time; `015c9df` is the reorganization, `3e94c20` adds only
this handoff file)

## Review Record Commit


## Human Approval

Not Required

Status: APPROVED
