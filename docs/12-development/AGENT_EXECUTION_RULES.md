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
7. Set the task to `IN_PROGRESS`, record the start time.
8. State expected files, acceptance criteria, and required tests before writing code.

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

- Work only on the selected task; avoid unrelated refactoring.
- Follow the module boundaries in `docs/04-architecture/MODULE_BOUNDARIES.md` (once created).
- Use database migrations for every schema change.
- Add tests alongside the implementation, not as a follow-up task.
- Protect secrets — never log provider credentials or insert them into AI prompts (GRX-AI-005).
- Add structured logs and audit events per the feature spec.
- Add usage-metering checks for any cost-generating operation (§33 of the PRD).
- Handle retry and failure paths, not just the happy path.
- Keep commits small and scoped to one logical change.
- Avoid broad, unfinished scaffolding — see [DEFINITION_OF_DONE.md §No placeholder completion](../00-project-control/DEFINITION_OF_DONE.md#no-placeholder-completion).

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

## End of work session

Update `docs/00-project-control/AGENT_HANDOFF.md` (once created) with: task worked on, work
completed, files changed, commands run, test results, migrations, decisions made, blockers,
known issues, current state, the exact next task, resume commands, and the latest commit
hash.

## Git and repository discipline

- Commit format: `<type>(<scope>): <summary>` — e.g. `feat(auth): add secure login flow`,
  `test(email): add duplicate-send prevention tests`.
- Do not combine unrelated work in one commit.
- Do not force-push, skip hooks, or rewrite published history without explicit user approval.
- Do not silently guess on the decision-gate items listed in `DECISIONS.md` — log a
  `PROPOSED` decision and get it confirmed, or mark the dependent task `BLOCKED`.

## Diagrams

Mermaid diagrams live in `docs/diagrams/`. Every diagram must use valid Mermaid syntax,
match the written architecture it accompanies, and use meaningful names — do not let a
diagram and its prose description drift apart.
