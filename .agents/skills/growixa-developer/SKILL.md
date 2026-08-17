---
name: growixa-developer
description: >-
  Feature-development playbook for any coding agent working in Growixa (Claude Code,
  OpenAI Codex, Google Antigravity, GitHub Copilot, VS Code). Covers the pick-up-to-merge
  sequence for a tracked task, the repo-specific traps that catch new agents, the exact
  test and lint commands CI runs, and the conditions that require stopping instead of
  proceeding.
---

# Growixa Developer Skill

Operational playbook for implementing a tracked Growixa feature, tool-neutral by design.

**This file deliberately does not restate the project's rules.** Branch naming, commit
format, co-author attribution, context efficiency, and the independent-review workflow all
live in [`AGENTS.md`](../../../AGENTS.md) and
[`AGENT_EXECUTION_RULES.md`](../../../docs/12-development/AGENT_EXECUTION_RULES.md) — read
those, and treat them as authoritative wherever this file appears to disagree. What follows
is only the part that is not written down elsewhere: the sequence, the traps, and the stop
conditions.

Companion skill: [`growixa-infra`](../growixa-infra/SKILL.md) for deployment, environments,
and CI/CD.

---

## 1. The sequence

1. **Take a task that is `READY`.** Read your row in
   [`MASTER_TASK_TRACKER.md`](../../../docs/00-project-control/MASTER_TASK_TRACKER.md).
   `BACKLOG`, `BLOCKED`, and design-only rows are not startable — see §4.
2. **Confirm the readiness gate passed** for that slice/phase in
   [`DEVELOPMENT_READINESS.md`](../../../docs/00-project-control/DEVELOPMENT_READINESS.md).
3. **Read the owning decision.** Most tasks reference a `DEC-GRX-*` in
   [`DECISIONS.md`](../../../docs/00-project-control/DECISIONS.md). An `APPROVED` decision
   is the design of record: **implement it, do not redesign it.** If you believe part of it
   is wrong, stop and say so — do not deviate silently.
4. **Branch and worktree** per `AGENTS.md` §1. Set the task `IN_PROGRESS`.
5. **State before coding**: expected files, acceptance criteria, and the tests you will
   write. If you cannot name the acceptance criteria, you do not yet understand the task.
6. **Implement**, following §2's traps and §3's layered testing.
7. **Definition of Done** —
   [`DEFINITION_OF_DONE.md`](../../../docs/00-project-control/DEFINITION_OF_DONE.md) in
   full, including doc and tracker updates.
8. **Handoff** — create `pr_reviews/<branch-with-dashes>.md`, set
   `Status: READY_FOR_REVIEW`. **Never merge your own work.**

Read progressively (`AGENTS.md` §5): the task, its acceptance criteria, the directly
relevant files, the owning decision. Not the whole documentation tree.

---

## 2. Repo-specific traps

These are the ones that have actually bitten, repeatedly. They are cheap to avoid and
expensive to discover in review.

**The worker resolves data independently of the API.**
`apps/worker/src/growixa_worker/` has its own `models.py` and its own queries —
`recipients.py` resolves campaign recipients without touching
`apps/api/src/growixa_api/*/repositories.py`. **A filter added on the API side does not
reach sending.** If you change which contacts are eligible, visible, or mailable, change it
in both places and test both.

**`migrations/env.py` must import every module's `models.py`.**
A new table is invisible to `alembic check` until its module is imported there. Every
existing module does this; a new one must too.

**RBAC lives in exactly one place.** Use the centralized `require_permission()` dependency
from `apps/api/src/growixa_api/permissions/dependencies.py`. Do not hand-roll a check in a
route. `apps/api/tests/permissions/test_protected_routes_audit.py` audits every route and
will fail on a new unprotected one — that test is a feature, not an obstacle.

**Prefer an existing permission code.** Several recent features shipped with no new
permission at all by reusing `contacts.manage` / `contacts.view` and friends. Add a new code
only when no existing one genuinely fits.

**Account isolation is a test, not an assumption.** Data is scoped by `account_id`.
Every new endpoint needs a test proving account A cannot read or mutate account B's rows.

**Suppression is never undone.** Deleting, archiving, restoring, or re-importing a contact
must leave a suppression entry intact and still enforced (`DEC-GRX-008`). If a change could
make a previously-unsubscribed address mailable again, it is wrong.

**Human approval before anything goes out.** AI-generated content cannot send or publish
directly; a human approves first (`GRX-AI-002`/`GRX-AI-003`, `DEC-GRX-006`). This has no
exceptions, and a task that appears to need one needs a decision, not a workaround.

**Credentials use the existing Fernet helper.** `auth/encryption.py`, encrypted at rest,
never logged, and omitted from read schemas. Do not introduce a second secret-handling path.

**Partial unique indexes are an established pattern here**, e.g. unique `(account_id,
domain) WHERE domain IS NOT NULL`. Reach for one before inventing a new uniqueness scheme.

**Don't build UI for capabilities that don't exist.** Established practice (`DEC-GRX-016`):
no provider cards, tabs, or buttons for backends that aren't implemented.

---

## 3. Tests and checks

Run the smallest relevant test while iterating; run the full set at the completion gate
(`AGENTS.md` §5). These are exactly what CI runs, per `.github/workflows/ci.yml`:

```bash
# apps/api and apps/worker
pytest
ruff check .
ruff format --check .
mypy .

# apps/web
npm run test          # vitest
npm run lint
npm run typecheck
npm run format:check
npm run build
npm run test:e2e      # playwright
```

Test layout, as reorganised by `GRX-TEST-ORG-001` — check it before adding a file:

- `apps/api/tests/<module>/` — one directory per API module (`contacts/`, `billing/`,
  `permissions/`, `platform_admin/`, …). Not flat.
- `apps/worker/tests/`
- `apps/web/src/**/*.test.tsx` — component tests co-located beside the component.
- `apps/web/tests/e2e/` — Playwright specs only.

Put new tests in the existing file for that area rather than creating a near-duplicate.

One strong behavioural test beats several overlapping ones — but required security, edge,
and regression cases are not optional.

---

## 4. Stop instead of proceeding

Stop, record what you found, and hand the question back when:

- The task is not `READY` — `BACKLOG`, `BLOCKED`, or a design-only row.
- It depends on an unresolved entry in
  [`OPEN_QUESTIONS.md`](../../../docs/00-project-control/OPEN_QUESTIONS.md). Mark the task
  `BLOCKED`; do not guess (`AGENT_EXECUTION_RULES.md` §When blocked).
- The work needs a decision that does not exist, or contradicts an `APPROVED` one — core
  architecture, replacing a library, a major dependency, database strategy, auth/RBAC
  shape, a public API contract, or a large refactor. Log a `PROPOSED` decision and get it
  confirmed.
- It touches anything in a `FUTURE_SCOPE_*.md` whose release is not confirmed as next.
- A referenced decision's factual claims about the code turn out to be wrong. That means
  the task is mis-specified — say so rather than working around it.
- Two or three evidence-based attempts have failed. Follow the `BLOCKED` procedure instead
  of continuing to experiment.

Anything unrelated you notice becomes a follow-up task, not an inline fix.
