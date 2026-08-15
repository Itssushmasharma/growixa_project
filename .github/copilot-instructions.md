# Growixa — GitHub Copilot Instructions

Follow the canonical, tool-neutral rules in [`AGENTS.md`](../AGENTS.md) at the repository
root, and the full execution rules in
[`AGENT_EXECUTION_RULES.md`](../docs/12-development/AGENT_EXECUTION_RULES.md). This file
covers only what's different for Copilot's coding agent — it does not duplicate the
shared rules.

## What's different

Copilot's coding agent runs in a GitHub-hosted cloud sandbox and works on a real GitHub
branch/pull request directly — it does not use this repo's local `.worktrees/` model.
Treat the PR itself as the worktree-equivalent workspace.

## What's the same as every other agent

- [`DEFINITION_OF_DONE.md`](../docs/00-project-control/DEFINITION_OF_DONE.md) applies
  before considering any task complete.
- Still create/update a `pr_reviews/<branch-name>.md` handoff file for the branch — the
  GitHub PR is not a substitute for it.
- Independent review from a different agent/tool is mandatory before merge.
- Never self-approve or self-merge your own PR, regardless of any repository auto-merge
  setting.
- Nothing outside `pr_reviews/**` may change between the reviewed code commit and the
  branch's/PR's current HEAD before merge, or the approval is stale and a re-review is
  required.
- UI/UX, customer-facing, or high-risk (auth/RBAC/billing/migrations) changes need the
  product owner's explicit approval before merge, in addition to independent review.
