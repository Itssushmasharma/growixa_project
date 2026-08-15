# PR Reviews

One markdown file per branch, tracking that branch's independent code review from
handoff through decision. This is the lightweight Phase 1 of Growixa's multi-agent
review workflow — one file per branch, no folder-state machine yet.

- File name: branch name with `/` replaced by `-`
  (e.g. `feature/FRONTEND/GRX-AI-STUDIO-001` → `feature-FRONTEND-GRX-AI-STUDIO-001.md`).
- Exactly one active file per branch. Fix/re-review cycles update the same file — never
  create a second one for the same branch.
- The file is context for the reviewer, not evidence. The reviewer must inspect the real
  branch (diff, commits, tests), not just trust what the file says.

Full template, review process, and merge rules:
[`AGENT_EXECUTION_RULES.md` — Independent review](../docs/12-development/AGENT_EXECUTION_RULES.md#independent-review-mandatory-before-merge).

This applies to every agent/tool working in this repository (Claude, Codex, Antigravity,
GitHub Copilot, others) — see [`AGENTS.md`](../AGENTS.md) at the repository root.
