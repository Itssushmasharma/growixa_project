Task: GRX-LINT-RUFF-001 (restore backend ruff import ordering after the test reorganisation)
Developer: Claude Code
Reviewer: Claude Code (fresh session — same tool as developer, no other tool available in
session; documented fallback per AGENT_EXECUTION_RULES.md. Did not author this branch and
has no memory of the developer's session or of the GRX-TEST-ORG-001 review.)
Branch: feature/BACKEND/GRX-LINT-RUFF-001
Worktree: none (branched directly from main in the root workspace)
Base Commit: 69dcd2d
Latest Commit: 9df2ce3
Status: APPROVED

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

Reviewer: **Claude Code — a fresh session, same tool as the developer.** The handoff asked
for Codex or Antigravity and flagged this fallback as weaker than usual; neither is
available in this session, so the documented fallback applies and is recorded here rather
than left silent. I did not author this branch and have no memory of the developer's
session or of the `GRX-TEST-ORG-001` review. Risk treated as **LOW** — import lines in
test files only.

### Everything below I ran myself; none of it is copied from the handoff

**1. The diff is import-ordering only — confirmed mechanically.**
`git diff -U0 69dcd2d..9df2ce3` filtered to drop diff headers and `^[+-](import |from |$)`
returns **nothing**. 16 files, `+16/−16`, exactly one moved line each, all under
`apps/api/tests/`. No source, config, migration, or dependency file is touched. This bounds
the risk completely: the only way this change can affect behaviour is through import
resolution, and collection (below) proves imports resolve.

**2. `main` really is red, and this branch really fixes it.**
I checked out `69dcd2d` into a throwaway worktree and ran ruff there rather than trusting
the handoff's bisect table:

| Tree | `ruff check .` |
|---|---|
| `69dcd2d` (main baseline) | **16 errors**, all `I001` |
| this branch (`9df2ce3`) | **All checks passed** |

`ci.yml:78` runs `ruff check .` in the backend job, so the red-CI claim holds.

**3. The other claimed commands, re-run on the branch:**
- `uv run ruff format --check .` → 290 files already formatted.
- `uv run mypy .` → Success, no issues in 288 source files.
- `pytest --collect-only -q` → **404 tests collected**.

**4. Collection is unchanged from `main` — verified as a controlled comparison, not an
assertion.** Same command in the `69dcd2d` worktree → **404 collected**. Identical. Nothing
was dropped or duplicated.

**5. On Review Focus item 2, I deliberately did not reproduce the failure-set comparison,
and I think that is the right call rather than a gap.** `pytest --collect-only` imports
every test module, so it already proves the only failure mode an import-only diff can have.
Re-running a suite the project has three times documented as nondeterministic — including
the `GRX-TEST-ORG-001` measurement of 16 failures then 0 on identical runs — would produce
a number that cannot distinguish this change from the noise. Spending that time would buy
confidence the diff-shape proof already gives for free. The developer's comparative
evidence is sound; it is just not the load-bearing evidence here.

### On Review Focus item 4 — I agree with deferring the isort config fix, with one condition

Not bundling a shared-tooling config change into a formatting cleanup is correct under
`AGENTS.md` §5/§6, and I would have pushed back had it been included.

But the deferral is worth stating precisely, because the committed fix is the *lesser* of
the two available ones. `ruff check --fix` resolved `I001` by reclassifying
`from tests.conftest import …` as **third-party**, so it now sits in the same block as
`httpx`, `pytest` and `sqlalchemy`. That grouping is semantically wrong — `tests` is
first-party — and `pyproject.toml:51` already declares `src = ["src", "tests"]`, which
shows the config's intent was for it to be first-party. So the repo's config and its
committed import blocks now disagree with each other. When the durable fix lands
(`known-first-party = ["tests"]`, or adding `"."` to `src`), it will re-churn these same 16
files back.

That is a small, acceptable cost — churn in test import blocks, nothing else — so it does
not block. The condition is that the follow-up must **exist**: I searched `docs/` and found
no task, decision, or open-question entry for it anywhere. A deferral with no task is a
drop.

### Findings that do not block the code, but must be closed before this task is `DONE`

**F1 — `GRX-LINT-RUFF-001` has no row in `MASTER_TASK_TRACKER.md`.** There is no task
entry, so `DEFINITION_OF_DONE.md` item 19 (test evidence recorded in the task entry) has
nowhere to land, and items 16–18 (`FEATURE_STATUS_MATRIX`, `PROJECT_STATUS`, `CHANGELOG`)
are unaddressed.

**F2 — `GRX-TEST-ORG-001` is still `IN_REVIEW` in the tracker** (line 26) despite having
been merged to `main` as `f4d2b13`. `AGENTS.md` §3 requires the tracker track task
progress; a merged task sitting in `IN_REVIEW` is how the next agent picks up work that is
already done.

**F3 — the `known-first-party` follow-up from Known Issue 2 needs a real tracker row**, as
argued above.

**F4 — process observation, offered so the gap does not recur.** I read the
`GRX-TEST-ORG-001` review record (`dee3e17`) directly: it verified pytest collection and
full-suite runs, and never ran `ruff check`, `ruff format --check`, or `mypy` — the words
do not appear in it. That is precisely how a lint-only regression reached `main` behind an
`APPROVED` verdict. The lesson is not about that reviewer; it is that a *file-move* change
needs the lint/format/type gate re-run specifically, because moves are the one refactor
that changes tooling classification without changing a line of code.

### Checked and clean

Account isolation, RBAC, permission gating, secrets, fabricated data: **not applicable and
not touched** — I confirmed the diff reaches no source file, no route, no query, and no
config. `THREAT_MODEL.md` and `RBAC.md` have no surface here.

### Merge safety

`git diff 9df2ce3..21b8470 -- . ':(exclude)pr_reviews/**'` is **empty** — the only commit
after the reviewed code is the handoff file itself. The gate is open at the time of this
verdict.

**Important, please read before acting on F1–F3:** fixing those means editing
`MASTER_TASK_TRACKER.md`, which is product documentation. Per
`AGENT_EXECUTION_RULES.md` § Independent review item 5, doing that **on this branch** would
put a non-`pr_reviews` change after `Reviewed Code Commit` and **invalidate this
approval**, forcing a re-review of a 16-line lint fix. The clean route is to merge this
branch first and make the tracker updates as a separate commit on `main` afterwards — that
leaves the reviewed commit untouched. If you would rather have them on the branch, that is
fine too, but flag it and I will do a confirm-only re-review.

## Review Decision

**APPROVED**

The code is correct, minimal, provably scoped to import lines, and independently verified
to take backend CI from 16 errors to 0 with test collection unchanged at 404. The findings
above are tracker and follow-up hygiene, not defects in the change.

## Reviewed Code Commit

`9df2ce3`

## Review Record Commit


## Human Approval

Not Required — internal lint hygiene in test files only. No customer-facing behaviour, no
API surface, no migration, no RBAC or account-isolation surface touched.

Status: APPROVED
