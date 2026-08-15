# Agent Execution Rules

- Document ID: DOC-AGENT-RULES
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [DEFINITION_OF_DONE](../00-project-control/DEFINITION_OF_DONE.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS](../00-project-control/DECISIONS.md)

Any coding agent (including a future session of this same assistant) working in this
repository must follow this workflow. It exists to keep work traceable across sessions and
to prevent silent scope drift — see [DEC-GRX-001](../00-project-control/DECISIONS.md) for
why that matters here specifically.

## Before starting any task

1. Read `docs/README.md`.
2. Read `docs/00-project-control/PROJECT_STATUS.md`.
3. Read `docs/00-project-control/MASTER_TASK_TRACKER.md` (once it exists).
4. Read the relevant feature specification in `docs/02-features/` for the task at hand —
   **not** the whole documentation tree. Use `docs/README.md`'s index to find the right file.
5. Read relevant architecture decisions in `docs/00-project-control/DECISIONS.md`.
6. Check dependencies and confirm the task is `READY` (not `BLOCKED` on an open question —
   see `docs/00-project-control/OPEN_QUESTIONS.md`).
7. **Git Branch Setup**: Pull the latest code from `main` (`git checkout main && git pull origin main`) and checkout a new feature branch following the naming convention: `feature/BACKEND/<task-id>` or `feature/FRONTEND/<task-id>`.
8. Set the task to `IN_PROGRESS`, record the start time.
9. State expected files, acceptance criteria, and required tests before writing code.

## Scope discipline (specific to this repository)

- MVP work is limited to [MVP_SCOPE.md](../01-product/MVP_SCOPE.md) — email, social,
  contacts, AI assistant, scheduling, basic analytics, single-tenant foundation.
- Anything from [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md)
  (SEO, AEO, GEO, crawler, WordPress, GitHub, Search Console, content-optimization agents)
  must **not** be implemented, scaffolded, or added to the task tracker until its target
  release (V1.5/V2/V3) is actually scheduled and the MVP is stable in production.
- If a task seems to require one of those capabilities, stop and flag it — do not build a
  smaller/simplified version of it "just in case."

## During development

- Work only on the selected task; modify only the files necessary to satisfy it. Do not
  perform opportunistic cleanup, rename or reformat unrelated code, reorganize folders,
  or rewrite working code merely because another style is preferred — record an unrelated
  problem you notice as a follow-up task instead of fixing it inline.
- Follow the module boundaries in `docs/04-architecture/MODULE_BOUNDARIES.md` (once created).
- Use database migrations for every schema change.
- Add tests alongside the implementation, not as a follow-up task.
- Protect secrets — never log provider credentials or insert them into AI prompts (GRX-AI-005).
- Add structured logs and audit events per the feature spec.
- Add usage-metering checks for any cost-generating operation (§33 of the PRD).
- Handle retry and failure paths, not just the happy path.
- Keep commits small and scoped to one logical change.
- Avoid broad, unfinished scaffolding — see [DEFINITION_OF_DONE.md §No placeholder completion](../00-project-control/DEFINITION_OF_DONE.md#no-placeholder-completion).

## Controlled execution & bounded exploration

Solve tasks deliberately, not by uncontrolled trial-and-error — evidence from this repo
(a branch that cycled through several full rewrites of the same feature, and a shipped
fabricated-data shortcut) shows what happens without this discipline.

- **Understand before editing.** Read the task and acceptance criteria, inspect the
  directly relevant existing implementation, identify the expected files/modules and
  tests, and form one primary approach before changing anything.
- **Prefer existing architecture.** Reach for existing patterns, utilities, components,
  services, and test structure before introducing a new abstraction, package, or
  directory. Don't create a second way of doing something the repository already
  supports.
- **One primary approach.** Don't cycle Approach A → B → C on preference alone. Switch
  only when the current approach demonstrably fails, hits a real architectural
  constraint, or evidence shows it's wrong — and record briefly: current approach, why
  it failed, evidence, new approach, why it's better.
- **No temporary file pollution.** Don't leave behind `*_new`/`*_final`/`*_v2` files,
  backups, scratch/debug scripts, duplicate components, abandoned test files, or
  commented-out code. Delete investigation files before handoff unless they're
  intentionally part of the deliverable.
- **Controlled testing.** Run the smallest relevant test, fix the concrete failure,
  re-run it, then expand to the module/suite as the implementation stabilizes; run full
  required CI at the completion/merge gate. Don't rerun the entire suite after every
  small edit, and don't create multiple test files that are just variations of the same
  test.
- **Test quality over quantity.** Every new test verifies a meaningful behavior or
  regression — one strong behavioral test beats several overlapping tests of the same
  implementation detail. Required edge/security/regression cases still must be covered.
- **Debug from evidence.** Read the actual error, identify the likely root cause, inspect
  the relevant code, make the smallest justified correction, rerun. Don't modify several
  files hoping one change fixes it, and don't retry the same command unchanged.
- **Retry limit.** If a problem is still unresolved after 2–3 evidence-based attempts,
  stop broad experimentation and follow the "When blocked" procedure below instead of
  continuing to burn context.
- **Dependency control.** Before adding a new dependency, check whether the standard
  library, an existing project dependency, or an existing internal utility already
  solves the problem. Significant new dependencies need justification.
- **Preserve working behavior.** Don't rewrite working code outside task scope. Preserve
  backward compatibility unless the task explicitly changes the contract; for bug fixes,
  prefer the smallest safe fix plus a regression test.
- **Final cleanup before review.** Before creating the handoff file: inspect the full
  `git diff`, remove experiments/dead code/unused imports/temporary files/debug logging,
  confirm no accidental unrelated modifications and no duplicate implementation remains,
  confirm tests live in the correct existing locations, and verify acceptance criteria.
  The branch should represent the chosen solution, not the history of experiments.
- **Quality overrides efficiency.** These controls exist to reduce wasted work — they
  never justify skipping necessary investigation, correctness, security checks, account
  isolation, required tests, Definition of Done, or independent review. If more
  investigation is genuinely required for correctness, do it.

## When blocked

1. Mark the task `BLOCKED` in the task tracker.
2. Record the exact blocker (usually an unresolved item in `OPEN_QUESTIONS.md`).
3. Record what was attempted.
4. Explain the impact.
5. Propose options rather than silently picking one for a high-impact/hard-to-reverse choice.
6. Continue an independent, unblocked task where possible rather than stalling.

## Before marking a task done

Follow [DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) in full:
run tests, linting, type checking; verify acceptance criteria; record evidence; update
documentation, feature status, project status, and changelog; reference the commit.

## Independent review (mandatory before merge)

No agent — Claude, Codex, Antigravity, or any other tool — may merge its own work into
`main`. Every branch needs one independent review before it can merge. This applies
uniformly regardless of which tool wrote the code, and is entirely separate from
`MASTER_TASK_TRACKER.md`: the task stays `IN_REVIEW` for the whole review/fix/re-review
cycle — reviewing never introduces a new task status, only file-level states inside the
handoff file below.

### Who reviews

Prefer a **different agent/tool** than the one that wrote the code — cross-agent review
catches blind spots a same-model reviewer tends to miss. When no other tool is available,
a **fresh session of the same tool with no memory of the developer's session** is an
acceptable, explicitly documented fallback: what matters most is that the reviewer has no
prior investment in the code and must verify the real diff rather than recall writing it.
Record which case applies in the `Reviewer` field (e.g. `Codex (fresh session — same tool
as developer, no other tool available)`), so the weaker case is always visible, never
silent.

### Handoff file

One file per branch at `pr_reviews/<branch-name-with-slashes-as-dashes>.md` (e.g. branch
`feature/FRONTEND/GRX-AI-STUDIO-001` → `pr_reviews/feature-FRONTEND-GRX-AI-STUDIO-001.md`).
Never create a second file for the same branch — update the existing one across
fix/re-review cycles. Keep it short and structured, not a long essay:

```text
Task:
Developer:
Reviewer:
Branch:
Worktree:
Base Commit:
Latest Commit:
Status: READY_FOR_REVIEW

## What Changed


## Why


## Important Files


## Tests


## Known Issues / Evidence Gaps


## Review Findings


## Review Decision
CHANGES_REQUESTED / APPROVED

## Reviewed Code Commit
<sha>

## Review Record Commit
<sha>

## Human Approval
Required / Not Required

Status:
```

### Review process

1. Developer implements, tests, commits, then creates the handoff file with
   `Status: READY_FOR_REVIEW`.
2. A different agent/tool reviews the **actual branch** — `git diff`, commits, tests,
   code — not just the handoff file. The handoff exists to orient the reviewer faster
   (what this branch is, what files matter, what was already run); it is never evidence
   on its own. The reviewer verifies claims against the real diff.
3. Reviewer records findings and exactly one decision — `APPROVED` or
   `CHANGES_REQUESTED` — plus `Reviewed Code Commit: <sha>`, the exact commit whose code
   was reviewed (this is the branch's HEAD *before* the reviewer edits the handoff file
   — writing the review verdict into the file is itself a commit, so it necessarily
   happens after the commit being reviewed; recording it separately, rather than
   claiming the review-verdict commit is "the reviewed commit," avoids a rule that could
   never actually be satisfied). Optionally record `Review Record Commit: <sha>` — the
   commit that added this verdict — for traceability; it is not what gets checked at
   merge time.
4. `CHANGES_REQUESTED`: the original developer fixes in the same branch/worktree, adds
   regression tests where relevant, updates `Latest Commit`, and sets
   `Status: READY_FOR_REVIEW` again in the same file. Do not open a new file.
5. Before merge, there must be **no changes outside `pr_reviews/**`** between
   `Reviewed Code Commit` and the branch's current HEAD — conceptually:
   ```bash
   git diff <reviewed-code-sha>..HEAD -- . ':(exclude)pr_reviews/**'
   ```
   must be empty. Only edits to the handoff file itself (recording the verdict, claiming
   a re-review, etc.) may happen after `Reviewed Code Commit` without invalidating the
   approval. Any change to source code, tests, configuration, migrations, product
   documentation, or dependencies after that commit — including a merge-conflict
   resolution that touches real logic — invalidates the approval: re-review is required
   before merging.
6. Reviewers check against
   [DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md),
   [RBAC.md](../08-security/RBAC.md), and [THREAT_MODEL.md](../08-security/THREAT_MODEL.md)
   rather than inventing a separate checklist.

### Human approval

Independent-agent `APPROVED` is required for every merge. In addition, the product
owner's explicit approval is required before merge for UI/UX changes, customer-facing
behavior changes, and high-risk changes (auth, RBAC, billing, migrations) — record this
as `Human Approval: Required` in the handoff file. Backend-only/internal changes with
nothing to visually or product-judge may merge on independent-agent approval alone
(`Human Approval: Not Required`).

### When to upgrade beyond one file per branch

This lightweight, single-file-per-branch system is deliberately not a full
`pending/in_review/changes_requested/approved/archived` state machine. Move to that
heavier system only when the workflow becomes genuinely concurrent and unsupervised —
for example: 3–5+ worktrees regularly active at once; agents picking up tasks without
being individually assigned; more than one reviewer operating at the same time;
duplicate task ownership becomes a real risk; branches waiting for review can no longer
be tracked from memory; reviews start happening asynchronously across sessions; or
merges are increasingly delegated rather than done by the product owner directly. Until
then, the folder-state machine is overhead without a matching problem.

## End of work session

Update `docs/00-project-control/AGENT_HANDOFF.md` (once created) with: task worked on, work
completed, files changed, commands run, test results, migrations, decisions made, blockers,
known issues, current state, the exact next task, resume commands, and the latest commit
hash.

## Git and repository discipline

- **Branch Naming**: Always pull from `main` before starting a task and create a dedicated branch following the format:
  - Backend features: `feature/BACKEND/<task-id-or-feature-name>` (e.g., `feature/BACKEND/GRX-AUTH-005`)
  - Frontend features: `feature/FRONTEND/<task-id-or-feature-name>` (e.g., `feature/FRONTEND/GRX-COMPANY-002`)
- **Commit Format**: `<type>(<scope>): <summary>` — e.g. `feat(auth): add secure login flow`, `test(email): add duplicate-send prevention tests`.
- **Co-Author Attribution**: Query terminal/git config (`git config user.name`, `git config user.email`) and include a `Co-Authored-By:` trailer in every commit message body:
  ```text
  Co-Authored-By: <User Name> <<User Email>>
  ```
- Do not combine unrelated work in one commit.
- Do not force-push, skip hooks, or rewrite published history without explicit user approval.
- Do not silently guess on the decision-gate items listed in `DECISIONS.md` — log a `PROPOSED` decision and get it confirmed, or mark the dependent task `BLOCKED`. This
  always applies when a task appears to require changing core architecture, replacing an
  existing library, introducing a major dependency, changing database strategy, changing
  auth/RBAC architecture, changing a public API contract, touching multiple unrelated
  modules, or a large refactor — stop and get it confirmed rather than making the change
  automatically, unless an existing approved decision already authorizes it.

## Diagrams

Mermaid diagrams live in `docs/diagrams/`. Every diagram must use valid Mermaid syntax,
match the written architecture it accompanies, and use meaningful names — do not let a
diagram and its prose description drift apart.
