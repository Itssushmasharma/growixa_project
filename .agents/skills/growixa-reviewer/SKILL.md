---
name: growixa-reviewer
description: >-
  Independent code-review playbook for any coding agent reviewing a Growixa branch
  (Claude Code, OpenAI Codex, Google Antigravity, GitHub Copilot, VS Code). Covers who may
  review, how to read a branch, the Growixa-specific checks that matter, how to set review
  depth by risk, how to record a verdict and the Reviewed Code Commit, and the merge gate
  that decides whether an approval is still valid.
---

# Growixa Reviewer Skill

Operational playbook for the mandatory independent review before any branch merges to
`main`.

**This file does not replace the canonical rules.** The handoff template, the review
lifecycle, and the merge gate are defined in
[`AGENT_EXECUTION_RULES.md` §Independent review](../../../docs/12-development/AGENT_EXECUTION_RULES.md#independent-review-mandatory-before-merge)
and summarised in [`AGENTS.md` §4](../../../AGENTS.md) — those are authoritative wherever
this file appears to disagree. See also [`pr_reviews/README.md`](../../../pr_reviews/README.md).

Companion skills: [`growixa-developer`](../growixa-developer/SKILL.md),
[`growixa-infra`](../growixa-infra/SKILL.md).

---

## 1. Before you start: are you allowed to review this?

- **You may not review your own work.** If you wrote any part of the branch, stop.
- **A different agent/tool than the developer is strongly preferred** — cross-tool review
  catches what a same-model reviewer misses.
- A **fresh session of the same tool, with no memory of the developer's session**, is the
  explicitly documented *weaker* fallback, allowed only when no other tool is available.
  If that is your situation, record it plainly in the `Reviewer` field — e.g.
  `Codex (fresh session — same tool as developer, no other tool available)`. The weaker case
  must always be visible, never silent.
- **You review, you do not fix.** Findings go back to the developer, who fixes in the same
  branch. Do not push code changes into a branch you are reviewing.

---

## 2. How to read the branch

**The handoff file orients you. It is never evidence.** Its claims are the developer's
account of their own work — verify each one against the real diff. A handoff asserting
"tests pass" or "no behaviour change" proves nothing on its own.

Read in this order, expanding only as needed (`AGENTS.md` §5 — do not scan the whole repo):

1. `pr_reviews/<branch-with-dashes>.md` — what this branch claims to be.
2. `git log --oneline <base>..HEAD` and the full `git diff` — what it actually is.
3. The changed files.
4. Their dependencies, only where a real question requires it.
5. The owning `DEC-GRX-*` in
   [`DECISIONS.md`](../../../docs/00-project-control/DECISIONS.md) — did the branch
   implement the approved design, or quietly deviate from it?

Match depth to risk, not to diff size:

| Risk | Examples | Depth |
|---|---|---|
| LOW | docs, copy, styling | focused |
| MEDIUM | ordinary feature work | normal |
| HIGH | data model, worker/send paths, contact data | deep |
| CRITICAL | auth, RBAC, billing, migrations, suppression, anything customer-facing | maximum |

---

## 3. What to check against

Use the project's existing standards, not a checklist you invent:
[`DEFINITION_OF_DONE.md`](../../../docs/00-project-control/DEFINITION_OF_DONE.md),
[`RBAC.md`](../../../docs/08-security/RBAC.md),
[`THREAT_MODEL.md`](../../../docs/08-security/THREAT_MODEL.md).

Then the Growixa-specific checks that repeatedly matter:

**Account isolation.** Data is scoped by `account_id`. Is there a test proving account A
cannot read or mutate account B's rows? Absence of such a test on a new endpoint is a
finding, not a nitpick.

**RBAC.** Every new route gated through `require_permission()`
(`apps/api/src/growixa_api/permissions/dependencies.py`) — never a hand-rolled check. Does
`apps/api/tests/permissions/test_protected_routes_audit.py` still pass? Was a new permission
code added where an existing one would have done?

**API and worker both updated.** `apps/worker/src/growixa_worker/` has its own `models.py`
and queries; `recipients.py` resolves recipients without touching the API's repositories. If
the branch changes which contacts are eligible, visible, or mailable and only touches one
side, that is a real defect — the send path will disagree with the UI.

**Suppression is never undone.** Any change to contacts, deletion, restore, or import must
leave suppression entries intact and enforced (`DEC-GRX-008`). If a previously-unsubscribed
address could become mailable again, reject it.

**Human approval gate intact.** AI-generated content still cannot send or publish directly
(`GRX-AI-002`/`GRX-AI-003`, `DEC-GRX-006`). No exceptions, including "just for this flow."

**Migrations.** Is the module's `models.py` imported in `apps/api/migrations/env.py` (or
`alembic check` cannot see the table)? Is the migration reversible? Does it match the model
definitions? Are `CHECK` constraints and partial indexes declared on the model too, not only
in the migration?

**Secrets.** Credentials encrypted via the existing Fernet helper (`auth/encryption.py`),
redacted from logs, and omitted from read schemas. No second secret-handling path.

**No fabricated or placeholder completion.**
[`DEFINITION_OF_DONE.md §No placeholder completion`](../../../docs/00-project-control/DEFINITION_OF_DONE.md#no-placeholder-completion).
Check specifically for hardcoded or invented data standing in for a real query, endpoints
returning fixtures, and "TODO" paths presented as working. This has shipped here before —
look for it.

**Tests assert behaviour.** Do the tests fail if the feature breaks, or do they assert
implementation details that pass regardless? Are the required edge, security, and regression
cases covered? Were tests placed in the existing per-module directory
(`apps/api/tests/<module>/`) rather than a near-duplicate new file?

**Cleanliness.** No `*_new`/`*_v2` files, backups, scratch scripts, debug logging,
commented-out code, or unrelated drive-by changes. The diff should be the chosen solution,
not the history of experiments.

---

## 4. Recording the verdict

In the **same** handoff file — never create a second file for a branch:

1. `## Review Findings` — specific and actionable. Name the file and line, state the
   concrete failure (inputs → wrong result), and rank by severity. "Consider refactoring"
   is not a finding.
2. `## Review Decision` — exactly one of `APPROVED` or `CHANGES_REQUESTED`. Not both, not
   "approved with comments."
3. `## Reviewed Code Commit` — the branch HEAD **before** you edit the handoff file.
   Writing the verdict is itself a commit, so it necessarily comes after the code you
   reviewed. Recording this separately is what makes the merge gate satisfiable.
4. `## Review Record Commit` — optional, the commit that added your verdict.
5. `## Human Approval` — `Required` for UI/UX, customer-facing behaviour, or high-risk
   changes (auth, RBAC, billing, migrations). `Not Required` only for backend/internal
   changes with nothing to product-judge.
6. Set `Status:` at the end of the file to match your decision.

On `CHANGES_REQUESTED`: the original developer fixes in the same branch, adds regression
tests, updates `Latest Commit`, and sets `Status: READY_FOR_REVIEW` again in that same file.
The task stays `IN_REVIEW` in the tracker throughout — review states live only in the
handoff file, never as task statuses.

---

## 5. The merge gate

An approval goes stale. Before merge, nothing outside `pr_reviews/**` may have changed
between `Reviewed Code Commit` and the branch's current HEAD:

```bash
git diff <reviewed-code-sha>..HEAD -- . ':(exclude)pr_reviews/**'
```

That must be empty. Any change to source, tests, config, migrations, product documentation,
or dependencies after the reviewed commit — **including a merge-conflict resolution that
touches real logic** — invalidates the approval and requires re-review.

Practical consequence worth telling the developer: merge `main` into the branch *before*
review, not after. Doing it afterwards throws the approval away.

Independent `APPROVED` is necessary but not always sufficient — where `Human Approval:
Required`, the product owner's explicit sign-off must also be recorded in the file before
merge. And no agent merges its own work, approved or not.

---

## 6. Reviewer failure modes

- **Trusting the handoff.** The most common failure. Verify every claim against the diff.
- **Reviewing the diff only.** A diff can be individually correct and still wrong in
  context — check the callers, the worker side, and the decision it claims to implement.
- **Approving because tests pass.** Passing tests that assert nothing meaningful are worse
  than no tests, because they buy false confidence.
- **Rubber-stamping a large diff.** If it is too large to review honestly, say so and ask
  for it to be split — that is a legitimate finding.
- **Silent scope creep.** Changes unrelated to the task belong in a follow-up, even good
  ones.
- **Inventing standards.** If the project's docs do not require it, it is a suggestion, not
  a blocker — label it as such.
