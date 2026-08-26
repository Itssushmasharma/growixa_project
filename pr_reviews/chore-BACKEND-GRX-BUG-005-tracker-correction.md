Task: Correct MASTER_TASK_TRACKER.md's GRX-BUG-005 entry — cancel a task superseded by GRX-CONTENT-001
Developer: Claude Code
Reviewer: Claude Code (fresh same-tool session, no memory of developer's work — documented fallback per AGENT_EXECUTION_RULES.md; no other tool available)
Branch: chore/BACKEND/GRX-BUG-005-tracker-correction
Worktree: .worktrees/grx-bug-005-tracker-fix
Base Commit: 7fea4f8
Latest Commit: 3eae3b7
Status: APPROVED

## What Changed

Docs-only. `docs/00-project-control/MASTER_TASK_TRACKER.md`:
- `GRX-BUG-005` row: status `READY` → `CANCELLED`, description and evidence columns
  rewritten to record that the bug it described (no email personalization substitution)
  no longer exists — `GRX-CONTENT-001` already shipped a working renderer.
- `GRX-CONTENT-002` row: removed a stale reference to "replaces GRX-BUG-005's removed
  control" (nothing was removed; the branch that would have removed it was discarded).

## Why

`GRX-BUG-005` (filed 2026-08-17) reported that the template editor's "Insert
Personalization Token" toolbar inserted `{{first_name}}`/`{{last_name}}`/
`{{company_name}}` as literal text with no substitution anywhere in the send path,
citing a `send_campaign.py` comment that has since been removed. `GRX-CONTENT-001`
(merged to `main` as `d987545`/`6b4d920` on 2026-08-23 — before `GRX-BUG-005`'s
description was ever re-verified) added `apps/worker/src/growixa_worker/
personalization.py`'s `render_personalization`, which `send_campaign.py` now calls for
every send; its `RECIPIENT_STANDARD_TOKENS`/`ACCOUNT_TOKENS` cover exactly the three
tokens the toolbar offers.

A fix branch (`feature/FRONTEND/GRX-BUG-005`) was built removing the toolbar, passed
lint/typecheck/tests, and got a human visual "looks good, merge" — but was caught by
independent review (`pr_reviews/feature-FRONTEND-GRX-BUG-005.md`, on the now-discarded
branch, so it no longer exists on `main`) before merge: removing the toolbar would have
regressed real, working customer-facing personalization, not removed dead UI. The
branch and worktree were discarded — nothing from it merged. This commit only corrects
the tracker to reflect that finding.

## Important Files

- `docs/00-project-control/MASTER_TASK_TRACKER.md`

## Tests

N/A — documentation only. No code changed.

Verification of the underlying claim (independently re-checked in this session before
writing this correction):
- `git log --oneline main` shows `d987545`/`6b4d920` (`GRX-CONTENT-001`) as ancestors.
- `grep -n "render_personalization\|RECIPIENT_STANDARD_TOKENS\|ACCOUNT_TOKENS"
  apps/worker/src/growixa_worker/personalization.py` confirms `first_name`, `last_name`
  in `RECIPIENT_STANDARD_TOKENS` and `company_name` in `ACCOUNT_TOKENS`.
- `grep -rn "render_personalization" apps/worker/src apps/api/src` confirms
  `send_campaign.py` calls it for `subject`/`body_html`/`body_text`.
- `publish_social_post.py` still has zero matches for merge-tag handling — the social
  half of the original report is still accurate and is tracked separately under
  `GRX-CONTENT-003`; not touched by this correction.

## Known Issues / Evidence Gaps

None — this is a factual correction to a tracker row based on evidence already gathered
and independently re-verified in this session.

## Review Findings

Independently re-verified every factual claim rather than trusting the handoff:

1. **Diff scope**: `git diff main..HEAD --stat` (base `7fea4f8`) touches only
   `docs/00-project-control/MASTER_TASK_TRACKER.md` and this handoff file. No code,
   tests, config, or migrations changed — matches the "documentation only" claim.
2. **GRX-CONTENT-001 provenance**: `git log --oneline main` shows both `d987545` and
   `6b4d920` (GRX-CONTENT-001 commits); `git merge-base --is-ancestor` confirms both are
   ancestors of `main`.
3. **Token coverage**: `apps/worker/src/growixa_worker/personalization.py` line 22
   defines `RECIPIENT_STANDARD_TOKENS = {"first_name", "last_name", "email", "phone",
   "unsubscribe_url"}` and line 26 defines `ACCOUNT_TOKENS = {"company_name",
   "website_url", "sender_name"}` — confirms `first_name`/`last_name` are recipient
   tokens and `company_name` is an account token, exactly the three the editor toolbar
   offers.
4. **Actually wired, not dead code**: `send_campaign.py` imports `render_personalization`
   and calls it three times (lines 298, 306, 315) for `subject`, `body_html`, `body_text`
   — confirms it is live in the real send path, not merely imported.
5. **Social gap still real**: `grep -n "merge_tag\|render_personalization\|{{"
   apps/worker/src/growixa_worker/publish_social_post.py` returns zero matches —
   confirms the tracker's claim that social substitution is still missing and correctly
   attributed to `GRX-CONTENT-003` rather than closed by this commit.
6. **Secrets scan**: `git diff main..HEAD | grep -iE` for API keys/secrets/passwords/
   private-key markers returned only an unrelated pre-existing tracker row (GRX-AUTH-007)
   whose prose happens to contain the word "token" — no actual credential leak.
7. **Prose accuracy**: text correctly avoids claiming GRX-CONTENT-002 is now unnecessary
   — it reframes it as an upgrade from a static 3-token toolbar to a dynamic,
   account/channel-aware picker with preview, not as replacing removed UI. This matches
   reality: nothing was removed, so the old "replaces GRX-BUG-005's removed control"
   phrasing was itself the stale bit being fixed.

No discrepancies found between the tracker text and the underlying evidence.

## Review Decision

APPROVED

## Reviewed Code Commit

68e81d52b9d4708ee7e98bda546229d02a9ab070

## Review Record Commit


## Human Approval
Not Required (internal documentation/tracker correction, no code/UI/customer-facing
change)

Status: APPROVED
