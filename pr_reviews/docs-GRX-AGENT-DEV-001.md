Task: GRX-AGENT-DEV-001 (tool-neutral developer & reviewer playbooks)
Developer: Ravi Kant Yadav
Reviewer: Claude Code (different agent than the author; did not write this branch)
Branch: docs/GRX-AGENT-DEV-001
Worktree: none — branched from main in the root workspace
Base Commit: origin/main
Latest Commit: 080d34a
Status: APPROVED

## What Changed

Documentation only, +346 lines across 3 files:

- `.agents/skills/growixa-developer/SKILL.md` (+155) — pick-up-to-merge sequence,
  repo-specific traps, the exact commands CI runs, and when to stop.
- `.agents/skills/growixa-reviewer/SKILL.md` (+183) — who may review, how to read a
  branch, Growixa-specific checks, recording a verdict, and the merge gate.
- `AGENTS.md` (+8) — two pointer links to the playbooks.

## Why

Reviewer's note: no handoff existed — created here so the branch could be reviewed at
all, per AGENTS.md §4.1. Intent inferred from the diff and commit messages.

## Review Findings

Risk treated as **MEDIUM-HIGH** — not for technical blast radius (it is docs only, no
code, config, dependency or migration change) but because `AGENTS.md` is the file every
agent on this project reads. A governance file that contradicts itself is worse than no
guidance at all.

**1. The `AGENTS.md` change is purely additive and correctly scoped.** Eight added lines,
zero deletions — two links plus one sentence: *"Both link these rules rather than
restating them — this file stays authoritative."* That is the right architecture. The
failure mode for split guidance is duplicated rules drifting apart; this explicitly
forbids duplication and names the source of truth.

**2. The developer playbook's CI claims are exact.** It lists ten commands (lines
108–119). I compared them against `.github/workflows/ci.yml`:

| Playbook | In `ci.yml` |
|---|---|
| `pytest`, `ruff check .`, `ruff format --check .`, `mypy .` | ✅ all four |
| `npm run test / lint / typecheck / format:check / build / test:e2e` | ✅ all six |

All ten match, none invented. Worth singling out: **`npm run format:check` is included.**
Four separate handoffs this session claimed "lint clean" while skipping exactly that
command, and it was the sole blocker on two branches. Encoding it here is the single
highest-value line in the file.

**3. The reviewer playbook states the rules correctly.** Spot-checked the three most
error-prone:

- *Precedence* — defers to `AGENTS.md`, and says so explicitly where the two might
  appear to disagree. Correct, and consistent with finding 1.
- *Who may review* — a different tool strongly preferred, a fresh same-tool session as
  the documented weaker fallback, recorded rather than left silent, with the exact
  `Reviewer:` phrasing. Matches AGENTS.md §4.2.
- *`Reviewed Code Commit`* — branch HEAD **before** the reviewer edits the handoff, with
  the reason ("what makes the merge gate satisfiable"). This is the rule that broke twice
  today when rebases orphaned the recorded SHA; capturing the *why* is what stops it
  recurring.
- *The merge gate* — nothing outside `pr_reviews/**` may change between
  `Reviewed Code Commit` and HEAD. Correct.

**4. Traps captured are real ones.** Account isolation framed as "a test, not an
assumption", and partial unique indexes named as an established pattern — both are
lessons from `GRX-CONTACT-010`/`DEC-GRX-034`, not generic advice.

**No secrets.** The only matches for credential keywords are guidance *about* secret
handling (Fernet helper, redaction, omission from read schemas), not values.

### One note, not blocking

These playbooks encode process lessons the project learned expensively today — a
`CHANGES_REQUESTED` branch merged via PR #7, review records erased by a force-push, and
handoffs asserting fixes that were never made. Two of those (the PR path not consulting
the handoff verdict, and force-pushing shared branches) are **not** addressed here,
because they are enforcement gaps rather than knowledge gaps. Worth a follow-up: no
amount of playbook prevents a GitHub merge button from ignoring a verdict file.

## Review Decision
APPROVED

## Reviewed Code Commit
080d34a

## Review Record Commit
(this commit)

## Human Approval
Not Required — internal agent documentation. No customer-facing behaviour, no API
surface, no migration, no RBAC or account-isolation change.

Status: APPROVED
