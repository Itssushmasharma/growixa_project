---
name: growixa-reviewer
description: >-
  Growixa independent-review playbook — who may review, how to read a branch, the
  Growixa-specific checks that matter, review depth by risk, recording a verdict and the
  Reviewed Code Commit, and the merge gate. Use before approving/merging any Growixa
  branch, or when asked to review a branch/PR in this repo.
---

# Growixa Reviewer

This is a thin pointer, not the playbook itself. The canonical, tool-neutral playbook
(also read by OpenAI Codex, Google Antigravity, and GitHub Copilot) lives at
[`.agents/skills/growixa-reviewer/SKILL.md`](../../../.agents/skills/growixa-reviewer/SKILL.md)
in the repository root.

Read that file now with the Read tool and follow it exactly. Do not duplicate or
paraphrase its content here — it stays the single source of truth.

**Before starting: you may not review your own work.** If this session (or an earlier
turn of it) wrote any part of the branch under review, stop and say so instead of
proceeding — use the `growixa-reviewer` subagent (fresh, isolated context) instead, or
hand off to a different tool.

It in turn defers to
[`AGENT_EXECUTION_RULES.md` §Independent review](../../../docs/12-development/AGENT_EXECUTION_RULES.md#independent-review-mandatory-before-merge)
and [`AGENTS.md` §4](../../../AGENTS.md) for the handoff template, review lifecycle, and
merge gate — those are always authoritative.
