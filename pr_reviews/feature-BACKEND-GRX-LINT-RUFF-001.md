Task: GRX-LINT-RUFF-001 (restore backend ruff import ordering after the test reorganisation)
Developer: Claude Code
Reviewer: UNASSIGNED — must be a different agent/tool. The author is disqualified, and is
also the reviewer who missed this in GRX-TEST-ORG-001, so a same-tool fresh session is a
weaker fallback than usual here. Prefer Codex or Antigravity.
Branch: feature/BACKEND/GRX-LINT-RUFF-001
Worktree: none (branched directly from main in the root workspace)
Base Commit: 69dcd2d
Latest Commit: 9df2ce3
Status: READY_FOR_REVIEW

## What Changed

One commit. `ruff check --fix .` in `apps/api`, resolving 16 `I001` unsorted-imports
findings across 16 test files. Import lines only — no source, config, migration or
dependency changes.

## Why

`ruff check .` has been failing on `main` since the `GRX-TEST-ORG-001` merge (`f4d2b13`).
Relocating tests into domain subfolders changed how isort classifies
`from tests.conftest import ...` relative to each file's new position, leaving 16 files
with unsorted import blocks. `ci.yml:78` runs `ruff check .` in the backend job, so
**main's backend CI job has been red since that merge** — bisected:

| Commit | `ruff check .` |
|---|---|
| `8d75129` — main before the test-org merge | 17 errors |
| after `f4d2b13` (test-org merge) | 33 errors |
| `69dcd2d` — main today | 16 errors |
| this branch | **0 errors** |

(The 17 pre-existing errors were separately resolved by the `GRX-CONTACT-010`/`015`
merges, which is why today's baseline is 16 rather than 33.)

## Important Files

- `apps/api/tests/auth/` (3 files), `billing/` (1), `email_validation/` (1),
  `permissions/` (1), `platform_admin/` (9), `users/` (1) — 16 test files total.

## Tests

Run against the real Postgres/Redis/RabbitMQ stack on the compose network
(`growixa_growixa-net`), not mocked:

- `ruff check .` → **All checks passed** (was 16 errors).
- `ruff format --check .` → 290 files already formatted.
- `mypy .` → no issues in 288 source files.
- `pytest --collect-only` → **404 tests collected**, unchanged from `main`.
- `pytest` over the six affected packages → 8 failed / 189 passed. **`main` run
  identically in the same environment → 14 failed.** The branch's failing set is a strict
  subset of `main`'s; `comm -13` of the two sorted failure lists is empty, so this change
  introduces **no new failure**.

## Known Issues / Evidence Gaps

1. **I cannot demonstrate a green backend suite, and neither can anyone else right now.**
   The shared dev Postgres makes the suite nondeterministic — documented on
   `GRX-SAAS-009`, re-confirmed on `GRX-CONTACT-010`, and measured on `GRX-TEST-ORG-001`
   where the same commit produced 16 failures then 0 on identical runs. My evidence above
   is therefore comparative (branch vs `main`, same session, same database state), not
   absolute. A reviewer should reproduce the comparison rather than expect a clean run.
2. **This is a lint fix, not a fix for the underlying fragility.** Import ordering broke
   because file moves changed isort's first-party resolution; nothing prevents the next
   reorganisation from doing the same. A durable fix would pin `known-first-party` in
   ruff's isort config. Deliberately not done here — it changes shared tooling config and
   belongs in its own reviewed change, not bundled into a formatting cleanup.
3. No behavioural test was added, because no behaviour changed.

## Review Focus

1. **Confirm the diff is import-ordering only.** `git diff -U0 9df2ce3^..9df2ce3 | grep
   -vE '^[+-](import |from |$)'` should return nothing outside diff headers.
2. **Re-run the comparison, don't trust my numbers** — the six affected packages on this
   branch versus on `main`, in the same session, and check the branch's failure set is a
   subset.
3. **Confirm `ruff check .` passes and `pytest --collect-only` is still 404** — the
   collection count is the cheapest proof nothing was lost.
4. **Judge whether finding 2 should block.** I argue the isort config change belongs in a
   separate task; disagree if you think shipping the cleanup without the guard just
   defers the same breakage.

## Review Findings


## Review Decision


## Reviewed Code Commit


## Review Record Commit


## Human Approval

Not Required — internal lint hygiene in test files only. No customer-facing behaviour, no
API surface, no migration, no RBAC or account-isolation surface touched.

Status: READY_FOR_REVIEW
