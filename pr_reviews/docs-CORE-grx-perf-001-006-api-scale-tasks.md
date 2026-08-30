Task: Add GRX-PERF-001..005 (API pagination/scale) tasks from 2026-08-30 audit
Developer: Claude (Sonnet 5), background fork of an interactive session
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: docs/CORE/grx-perf-001-006-api-scale-tasks
Worktree: /Users/ravi/Projects/growixa (main working directory, not a dedicated worktree)
Base Commit: main @ time of branch creation (rebased onto latest main before this handoff)
Latest Commit: 5c7b444b5b5eb086c093b949e1db526d123d3f62
Status: READY_FOR_REVIEW

## What Changed

Docs-only. Adds five rows to `docs/00-project-control/MASTER_TASK_TRACKER.md`:
`GRX-PERF-001` (P1 — paginate contacts/audit/ai-generations), `GRX-PERF-002` (P2 —
paginate remaining list endpoints + fix templates N+1), `GRX-PERF-003` (P2 — DB
connection pool sizing for both API and worker engines), `GRX-PERF-004` (P3 — composite
indexes, sequenced after pagination), `GRX-PERF-005` (P3 — Redis caching, sequenced
last).

## Why

A 2026-08-30 audit of the backend API found every existing `GET` list endpoint fully
unbounded (no `limit`/`offset`/cursor param anywhere), plus a real N+1 in
`templates/services.py::list_templates_with_current_version`. These tasks capture that
finding as pickable, sequenced work rather than losing it back into conversation
history.

## Important Files

- `docs/00-project-control/MASTER_TASK_TRACKER.md` — the five new rows

## Tests

N/A — documentation only, no code/config/schema changed.

## Known Issues / Evidence Gaps

- Every claim in these five rows (unbounded queries, the templates N+1, missing pool
  sizing, missing composite indexes, absent caching) traces to the same 2026-08-30 audit.
  Reviewer should independently spot-check at least the two most load-bearing claims —
  that `contacts`/`audit`/`ai/generations` list endpoints genuinely have no
  `limit`/`offset` anywhere in their route/repository code, and that the `templates` N+1
  is real — against the actual source, not the audit's or this handoff's account of it.
  This is the same standard already applied and confirmed on the sibling
  `docs/CORE/skill-list-endpoint-scale-standard` branch's review.
- `GRX-PERF-001` through `005` are sequenced (pagination → indexes → caching) with the
  reasoning inline in each row and in the PR description — worth confirming that
  sequencing logic is actually sound, not just present.
- A parallel implementation of `GRX-PERF-001` may be starting around the same time as
  this review — if so, this branch (the task definition) and that one (the
  implementation) are independent; this branch doesn't require the implementation to
  exist, and the implementation branch will need its own separate review.

## Review Findings

**Scope.** `git diff 3f2c3ad..docs/CORE/grx-perf-001-006-api-scale-tasks` (this branch's
merge-base with `main`) touches exactly two files: `MASTER_TASK_TRACKER.md` (+5 rows,
`GRX-PERF-001`..`005`) and this handoff file. No other tracker row, source file, test,
migration, or config is touched. All five new rows have `Status = BACKLOG` and
`Assigned Agent = unassigned` — nothing is prematurely marked `DONE`/`IN_REVIEW`. (Note:
a naive `git diff main..HEAD` looked much larger because `main`'s history includes an
unrelated already-merged PR (#49, GRX-EMAIL-016); diffing against the true merge-base
`3f2c3ad` gives the correct, small diff above. The shared working directory also got
switched to `main` by a concurrent process mid-review — confirmed the branch ref
`docs/CORE/grx-perf-001-006-api-scale-tasks` itself was unaffected and re-verified by
diffing against explicit refs rather than trusting checked-out `HEAD`.)

**Load-bearing claim 1 — unbounded list endpoints (verified true).**
- `apps/api/src/growixa_api/contacts/repositories.py::list_contacts` — plain
  `select(Contact).where(...)`, ordered, no `.limit()`/`.offset()` anywhere in the
  function. Confirmed.
- `apps/api/src/growixa_api/audit/api.py::list_audit_logs_route` — `Query` params are
  only `entity_type`/`actor_user_id`, no `limit`/`offset`; calls `list_events(...)`
  which is unbounded. Confirmed.
- `apps/api/src/growixa_api/ai/api.py::list_ai_generations_route` — same pattern, filter
  params only (`capability`, `linked_entity_type`, `linked_entity_id`), no pagination.
  Confirmed.
- Broader grep of `limit`/`offset` across every `*/api.py` in `growixa_api` turned up
  zero pagination params anywhere (only unrelated hits: plan/seat "limit" messages,
  rate-limit prose). The row's "confirmed by grep across every `*/api.py`" claim holds.

**Load-bearing claim 2 — templates N+1 (verified true).**
`apps/api/src/growixa_api/templates/services.py::list_templates_with_current_version`
(lines 114-118):
```python
templates = await list_templates(session, account_id)
return [(template, await get_current_version(session, template.id)) for template in templates]
```
This is exactly the claimed N+1 — one `get_current_version` query per template inside
the list comprehension, not a batch/window-function fetch. Confirmed.

**Sequencing logic — mostly sound, one loose justification (non-blocking).**
`GRX-PERF-004` (composite indexes) depending on `GRX-PERF-001`/`002` (pagination) is
reasonable planning guidance, though technically a composite index on
`(account_id, deleted_at, created_at DESC)` would help an unbounded `ORDER BY` query
just as much as a `LIMIT`-bounded one — Postgres can early-terminate an index scan under
either. The dependency isn't wrong, just not as load-bearing as the row's prose implies.
More notably, `GRX-PERF-005` (caching) lists dependencies on `GRX-PERF-001`, `002`, AND
`004`, with the stated reason "caching without fixing [the unbounded query] first just
caches an expensive unbounded result" — but the caching candidates named in that same row
(`dashboard/overview`, `billing/plans`, `billing/credit-packs`, `contacts/segments`
metadata) are **not** among the endpoints `GRX-PERF-001`/`002` actually paginate
(contacts/audit/ai/campaigns/templates/social/users/roles/billing-catalog/integrations).
So the row's own justification for the dependency doesn't quite match its own candidate
list — the dashboard/billing endpoints it names for caching aren't fixed by the
pagination tasks at all. This is a documentation-quality nit for whoever picks up
`GRX-PERF-005` to resolve (e.g., caching could plausibly ship independently of
001/002/004 for the dashboard/billing candidates specifically), not a reason to block
this tracker addition — sequencing dependencies in this tracker are advisory planning
notes, not enforced gates, and the general principle (fix the underlying scale problem
before layering a cache on top) is sound even if the specific dependency list is looser
than stated.

**DB pool sizing claim (GRX-PERF-003) spot-checked — true.** Both
`apps/api/src/growixa_api/db.py` and `apps/worker/src/growixa_worker/db.py` call
`create_async_engine(..., pool_pre_ping=True, connect_args={...})` with no `pool_size`/
`max_overflow`/`pool_timeout` set.

**Caching claim (GRX-PERF-005) spot-checked — true.** `redis` usage in `*/services.py`
is confined to `auth/services.py` and `social/services.py`; no read-caching layer exists.

**Table formatting.** `python3 scripts/tracker_to_csv.py --check` reports the CSV is
stale (expected — this is a docs-only branch that doesn't regenerate it; CSV
regeneration happens after merge per the reviewer skill). All five new rows parse to 17
pipe-delimited columns, matching the header row exactly, with `Status` landing in the
`Status` column (`BACKLOG` for all five) — no stray `|` inside a cell shifted any column.

**Secrets scan.** `git diff 3f2c3ad..docs/CORE/grx-perf-001-006-api-scale-tasks | grep -iE
"password=|secret=|api[_-]?key=|BEGIN (RSA|PRIVATE)|AKIA..."` — no matches. Diff is
markdown prose referencing file paths/line numbers only; no credentials.

**Handoff's own self-assessment.** Agreed — the handoff correctly identified the two
claims most worth independently verifying (pagination absence, templates N+1) and both
checked out. Its note about a possible parallel `feature/BACKEND/GRX-PERF-001`
implementation branch starting concurrently is also accurate (that branch ref exists
locally); this tracker-only branch does not depend on it existing.

## Review Decision
APPROVED

## Reviewed Code Commit
3e35879436cc5e7fc92268699cb17088a80c6898

## Review Record Commit
Branch HEAD after this file's final commit (self-referential field, omitted — see
`git log` on this branch for the commit(s) adding this verdict).

## Human Approval
Not Required — agreed with the handoff's own assessment. This is a documentation/
task-tracker-only change (five new `BACKLOG` rows), no UI/UX, customer-facing behavior,
or high-risk (auth/RBAC/billing/migrations) surface touched, and no task is marked
`DONE`.

Status: APPROVED
