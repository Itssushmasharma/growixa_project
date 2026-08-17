# Agent Workspace Rules & Execution Guidelines

This is the canonical, tool-neutral entry point for every AI coding agent working in this
repository — Claude Code, OpenAI Codex, Google Antigravity, GitHub Copilot, and any future
tool. It is read automatically by Codex, Antigravity, and GitHub Copilot's coding agent
(all three natively discover a root-level `AGENTS.md`). Claude Code reads it via the
`@AGENTS.md` import in root [`CLAUDE.md`](CLAUDE.md). Tool-specific adapter files
(`CLAUDE.md`, `.agents/rules/growixa-governance.md`, `.github/copilot-instructions.md`)
are thin pointers back to this file — they do not duplicate these rules.

## 1. Git Branch Workflow

Before starting development on any new feature or task:

1. **Pull Latest Main**: Switch to `main` and pull latest changes:
   ```bash
   git checkout main && git pull origin main
   ```
2. **Checkout Feature Branch**: Create a dedicated branch adhering strictly to the naming
   convention:
   - Backend features: `feature/BACKEND/<task-id-or-feature-name>` (e.g.
     `feature/BACKEND/GRX-AUTH-005`)
   - Frontend features: `feature/FRONTEND/<task-id-or-feature-name>` (e.g.
     `feature/FRONTEND/GRX-COMPANY-002`)
3. Every parallel feature is built inside its own `.worktrees/<feature-name>` (see
   `docs/00-project-control/WORKTREE_TRACKER.md`). GitHub Copilot's coding agent is the
   one exception — it runs in a GitHub-hosted cloud sandbox on a real branch/PR instead;
   see `.github/copilot-instructions.md`.

## 2. Commit Message & Co-Author Attribution

1. **Format**: Follow Conventional Commits: `<type>(<scope>): <summary>`.
2. **Co-Author Trailer**: Dynamically query `git config user.name` and
   `git config user.email` (or terminal user info) and append a `Co-Authored-By:` trailer
   to every commit message body:
   ```text
   Co-Authored-By: <User Name> <<User Email>>
   ```

## 2.1. Zero Secrets & Credentials Leakage (Strict Hard Rule)

**Non-negotiable security requirement for ALL developers and reviewers:**

1. **NEVER Hardcode or Commit Secrets**: Never commit real credentials, API tokens,
   private keys, database passwords, SMTP credentials, webhook secrets, live auth tokens,
   or customer secrets into source code, migrations, tests, configs, scripts, or docs.
2. **Environment & Mock Values Only**: All secrets must be loaded via environment variables
   (`os.environ`, `process.env`) or secret stores. Test fixtures and examples must exclusively
   use obvious fake placeholders (e.g. `mock_token_123`, `demo-key`, `http://localhost`).
3. **Reviewer Blocking Gate**: Reviewers MUST inspect all diffs for credential leaks.
   **NEVER APPROVE, MERGE, OR PUSH CODE TO GITHUB IF ANY CREDENTIAL OR SECRET IS LEAKED.**
   Any detected credential leak is an immediate `CRITICAL BLOCKER` (`CHANGES_REQUESTED`).

## 3. Project Documentation Reference

- Follow all standards in
  [`docs/12-development/AGENT_EXECUTION_RULES.md`](docs/12-development/AGENT_EXECUTION_RULES.md).
- Infrastructure & DevOps Playbook:
  [`.agents/skills/growixa-infra/SKILL.md`](.agents/skills/growixa-infra/SKILL.md) and
  [`docs/11-devops/OVH_VPS_DEPLOYMENT.md`](docs/11-devops/OVH_VPS_DEPLOYMENT.md).
- Feature-development Playbook (any agent/tool — the pick-up-to-merge sequence, the
  repo-specific traps, the exact commands CI runs, and when to stop):
  [`.agents/skills/growixa-developer/SKILL.md`](.agents/skills/growixa-developer/SKILL.md).
- Code-review Playbook (any agent/tool — who may review, how to read a branch, the
  Growixa-specific checks, recording a verdict, and the merge gate):
  [`.agents/skills/growixa-reviewer/SKILL.md`](.agents/skills/growixa-reviewer/SKILL.md).

  Both link these rules rather than restating them — this file stays authoritative.
- Keep `docs/00-project-control/PROJECT_STATUS.md` and
  `docs/00-project-control/MASTER_TASK_TRACKER.md` updated as tasks progress.
- Definition of Done:
  [`docs/00-project-control/DEFINITION_OF_DONE.md`](docs/00-project-control/DEFINITION_OF_DONE.md).

## 4. Independent Code Review (mandatory before merge)

No agent may merge its own work into `main`. Every branch needs one independent review
before it can merge:

1. When implementation is complete, tested, and committed, create ONE handoff file at
   `pr_reviews/<branch-name-with-slashes-as-dashes>.md` (never a second file for the same
   branch — update the existing one across fix/re-review cycles).
2. Prefer a **different agent/tool** as reviewer; a fresh same-tool session with no
   memory of the developer's work is an explicitly documented fallback when no other tool
   is available. The reviewer inspects the actual branch (diff, commits, tests, **secrets
   inspection**) — not just the handoff file — and records `APPROVED` or `CHANGES_REQUESTED`
   plus the `Reviewed Code Commit` SHA (the commit whose code was reviewed — not the commit
   that records the verdict itself, since writing the verdict into the file is a later commit)
   in the same file.
3. **Hard Blocker — Secret Leakage**: If any real secret, private key, API token, live
   password, or credential leak is found in the diff, the reviewer MUST reject the PR
   with `CHANGES_REQUESTED` and MUST NOT approve or push the branch to GitHub under any
   circumstances.
4. Before merge, no code/tests/config/migrations/docs/dependencies may have changed
   between `Reviewed Code Commit` and the branch's current HEAD, other than edits to the
   handoff file itself. If anything else changed, the approval is stale — re-review is
   required.
5. UI/UX, customer-facing, or high-risk (auth/RBAC/billing/migrations) changes also need
   the product owner's explicit approval before merge, recorded in the same file.

Full template and rules: [`AGENT_EXECUTION_RULES.md` — Independent
review](docs/12-development/AGENT_EXECUTION_RULES.md#independent-review-mandatory-before-merge).
See also [`pr_reviews/README.md`](pr_reviews/README.md).

## 5. Token & Context Efficiency

Applies to every agent — Claude, Codex, Antigravity, Copilot, and future tools. This is
a context-efficiency policy, not permission to skip required engineering validation:
correctness, security, tests, account isolation, and required review are never traded
for lower token usage.

- **Load context progressively, not exhaustively.** Do not read the whole repository or
  documentation tree by default. Start with: the assigned Task ID, its acceptance
  criteria, the directly relevant files, and only the architecture/decision/security docs
  the task actually touches. Expand only when a concrete dependency or uncertainty
  requires it.
- **Stay in scope.** Anything unrelated you notice becomes a follow-up task, not an
  inline change.
- **Don't rediscover known context.** Reuse existing summaries, handoffs, and
  project-control artifacts instead of rereading unchanged large documents.
- **Reviewing:** read the handoff → `git diff` → changed files → dependencies, only as
  needed. Don't scan the whole repo automatically. Match review depth to risk — LOW
  (focused), MEDIUM (normal), HIGH (deep), CRITICAL (maximum).
- **Keep handoffs concise:** summary ≤10 lines, only the files/decisions that matter,
  exact test commands and results, 3–5 primary review-focus points — not more.
- **Test in layers.** Run targeted tests/checks while developing; run the full required
  CI/validation suite at the completion/merge gate, not on every iteration.
- **Don't flood context with command output.** Summarize successful output; preserve
  exact relevant error output.
- **Don't duplicate work.** Unless explicitly requested, avoid two agents implementing
  the same task — prefer different agents for independent tasks and for cross-agent
  review (see §4).
- **If blocked, stop rediscovering.** Don't retry the same failing approach repeatedly —
  record evidence and follow the `BLOCKED` procedure in `AGENT_EXECUTION_RULES.md`.

## 6. Controlled Execution & Bounded Exploration

Solve tasks deliberately, not by uncontrolled trial-and-error:

- Understand the task and prefer existing architecture/patterns before writing code.
- One primary approach — don't cycle A → B → C on preference; justify before switching.
- Touch only the files the task requires; leave no temp/dead/duplicate files behind.
- Test progressively (targeted → module → full CI at the merge gate); one strong
  behavioral test beats several overlapping ones.
- Debug from evidence, not guesswork; after 2–3 failed attempts, stop and follow
  `BLOCKED` instead of continuing to experiment.
- These are efficiency rules, not license to skip correctness, security, tests, account
  isolation, or independent review.

Full rules: [`AGENT_EXECUTION_RULES.md` — Controlled execution &
bounded exploration](docs/12-development/AGENT_EXECUTION_RULES.md#controlled-execution--bounded-exploration).
