Task: Bake list-endpoint pagination requirement into growixa-developer/growixa-reviewer skills
Developer: Claude (Sonnet 5), interactive session
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: docs/CORE/skill-list-endpoint-scale-standard
Worktree: /Users/ravi/Projects/growixa (main working directory, not a dedicated worktree)
Base Commit: main @ time of branch creation (rebased onto latest main before this handoff)
Latest Commit: 8cf1663f3df56f90979a95fa2462ad767ec4fdf6
Status: APPROVED

## What Changed

Docs-only, two files:
- `.agents/skills/growixa-developer/SKILL.md` — new entry in §2 "Repo-specific traps":
  every new list endpoint must paginate (server-enforced max page size, SQL-level
  LIMIT/OFFSET not in-memory slicing, batch-loaded related data not per-row lazy load),
  citing `contacts`/`campaigns` as the correct reference pattern already in the codebase
  and `templates`' N+1 as the mistake not to repeat.
- `.agents/skills/growixa-reviewer/SKILL.md` — matching entry in §3 "What to check
  against": reviewer should flag a new list endpoint with no server-enforced page-size
  cap, an in-memory-sliced query, or a per-row lazy load as a finding.

## Why

A 2026-08-30 backend audit found every existing `GET` list endpoint in the API (contacts,
campaigns, templates, audit, AI generations, and more) fully unbounded — no `limit`/
`offset`/cursor param anywhere in any route — captured as `GRX-PERF-001`/`002` in
`MASTER_TASK_TRACKER.md`. This branch is the prevention half: baking the lesson into both
skills so a newly-added endpoint doesn't repeat the same gap, and so the review gate
would actually catch it if it did.

## Important Files

- `.agents/skills/growixa-developer/SKILL.md` — the new trap entry (inserted before the
  existing "Centralize constants and enums" entry, same §2 list)
- `.agents/skills/growixa-reviewer/SKILL.md` — the new check entry (inserted before the
  existing "No fabricated or placeholder completion" entry, same §3 list)

## Tests

N/A — documentation/skill-instruction only, no code/config/schema changed.

## Known Issues / Evidence Gaps

- The `GRX-PERF-001`/`002` task IDs referenced here exist in `MASTER_TASK_TRACKER.md` on
  a separate, still-unreviewed branch (`docs/CORE/grx-perf-001-006-api-scale-tasks`), not
  yet merged to `main`. This branch's content doesn't depend on that one merging first —
  it references the task IDs for traceability, not as a hard dependency — but reviewer
  should confirm the reference doesn't read as though those tasks are already `DONE` or
  as though this branch requires them merged first.
- The `contacts/services.py::list_contacts_with_fields` and `campaigns` batch-metrics
  reference-pattern claim, and the `templates` N+1 claim, both come from the same
  2026-08-30 audit — reviewer should spot-check at least one against the real code
  rather than trusting the audit's account of itself, consistent with this session's
  general standard of not trusting doc/summary claims without verification.

## Review Findings

Verified `git diff main...origin/docs/CORE/skill-list-endpoint-scale-standard` directly
(not the handoff's account of it). Confirmed the diff touches only the two claimed files,
one new entry each, both docs-only (no code/config/migration changed).

1. **Code claims verified against real source, not trusted from the handoff:**
   - `contacts/services.py::list_contacts_with_fields` (lines 361-386): confirmed. It
     calls `get_all_field_values_for_account`, `get_all_tag_names_for_account`, and
     `get_all_suppressed_emails_for_account` once each, then maps results by
     `contact.id` in a Python comprehension — genuine batch-load, not per-row lazy load.
     Matches the entry's claim exactly.
   - `templates/services.py::list_templates_with_current_version` (line 118): confirmed
     N+1 — `[(template, await get_current_version(session, template.id)) for template in
     templates]` issues one `get_current_version` query per template inside the loop.
     Matches the entry's claim exactly.
   - `campaigns/services.py` (lines 157-176): confirmed batched-metrics pattern —
     `get_campaigns_metrics_batch(session, account_id, campaign_ids)` called once with
     the full ID list, then results mapped per campaign. Matches the entry's "campaigns'
     batched metrics are the reference pattern" claim.

2. **No contradiction/duplication with existing SKILL.md content.** Grepped both files
   for prior mentions of pagination/LIMIT/OFFSET/N+1/GRX-PERF before this diff — none
   existed. The new entries are inserted cleanly before pre-existing, unrelated entries
   ("Centralize constants and enums" in developer SKILL.md; "No fabricated or placeholder
   completion" in reviewer SKILL.md) without altering surrounding text.

3. **GRX-PERF-001/002 reference reads correctly.** Both entries say the audit finding is
   "tracked as `GRX-PERF-001`/`002`" — purely for traceability, never phrased as "fixed
   by" or "resolved in" those tasks, and nothing states or implies this branch depends on
   that other branch (`docs/CORE/grx-perf-001-006-api-scale-tasks`) merging first. Agree
   this avoids the trap the handoff flagged as a risk to check.

4. **Secrets scan (AGENTS.md §2.1):** clean. Diff is two markdown skill files with no
   credentials, tokens, keys, or connection strings; grepped for common secret patterns
   (api key/secret/password/token/private key headers) — only pre-existing, unrelated
   context lines about the Fernet encryption helper matched, not new secret material.

5. **Clarity:** the three numbered requirements (server-enforced page-size cap, SQL-level
   LIMIT/OFFSET or cursor not in-memory slicing, batch-loaded related data keyed on page
   IDs) are concrete and actionable, each with a real repo file/line reference a fresh
   agent can go inspect. The reviewer-side entry mirrors the same three checks as
   explicit review gates ("Absence of a page-size cap, or an in-memory slice of a
   full-table query, is a finding"). No ambiguity found.

6. **Scope:** diff is limited to exactly the two files and one entry each, as described.
   No unrelated changes.

7. **Human approval assessment:** agree with the handoff — docs/skill-instruction only,
   no UI/UX, customer-facing, or auth/RBAC/billing/migration surface touched. Human
   approval not required.

## Review Decision
APPROVED

## Reviewed Code Commit
8cf1663f3df56f90979a95fa2462ad767ec4fdf6

## Review Record Commit
a1d8ca3 (this verdict's initial commit; SHA recorded in a follow-up commit per repo convention)

## Human Approval
Not Required — documentation/skill-instruction change only, no UI/UX, customer-facing,
or high-risk (auth/RBAC/billing/migrations) surface touched. Reviewer confirms agreement
with this assessment (see Review Findings §7).

Status: APPROVED
