Task: GRX-BUG-002, GRX-BUG-003, GRX-BUG-004
Developer: Claude Code
Reviewer: Google Antigravity
Branch: feature/FRONTEND/GRX-BUG-002-004
Worktree: .worktrees/grx-bug-002-004
Base Commit: bfea04f
Latest Commit: f91e5a1
Status: APPROVED

## What Changed
Fixes for all 3 non-trivial findings filed by `GRX-QA-001`'s sweep of `GRX-AI-STUDIO-001`.
Branched from `feature/FRONTEND/GRX-QA-001` (now `APPROVED`) rather than `main`, since
that branch already carries the related dead-code cleanup and these tracker rows —
avoids duplicate-content conflicts when both merge.

- **GRX-BUG-002**: "Active Brand Voice" drawer now fetches the real `GET /brand/profile`
  and displays `brand_voice`/`required_facts`/`forbidden_claims`, with an honest empty
  state when nothing is configured. Previously showed identical hardcoded text to every
  account regardless of their real profile.
- **GRX-BUG-003**: Renamed "Suggested for you" → "Quick Starters" with honest copy
  (was falsely claiming "smart suggestions based on your activity" from a static
  array). Removed the "Refresh" button, which only showed a fake success toast and
  changed nothing. Removed `handleSelectSuggestion`'s silent-no-op campaign/audience
  name-matching against unrelated example data — clicking a starter now only sets what
  it can genuinely set (channel/prompt/tone/length), leaving the user's real selection
  untouched instead of silently failing to change it.
- **GRX-BUG-004**: Removed the `.slice(0, 3)` cap that silently hid generated
  variations 4-7 even though the user was charged for all of them (existing 3-column
  CSS grid already wraps correctly, no CSS change needed). Replaced the hardcoded
  "Just now" timestamp with `formatRelativeTime()` derived from the generation's real
  `created_at`.

## Why
Tracker rows `GRX-BUG-002`/`003`/`004`, filed by the `GRX-QA-001` sweep.

## Important Files
- `apps/web/src/app/(dashboard)/dashboard/ai/history-page.tsx`
- `apps/web/src/app/(dashboard)/dashboard/ai/history-page.module.css` (dead `.refreshBtn` removed)
- `apps/web/src/app/(dashboard)/dashboard/ai/history-page.test.tsx`
- `apps/web/src/app/(dashboard)/dashboard/ai/types.ts` (`BrandProfile` added, `SuggestedPrompt.campaign`/`.audience` removed as now-unused)

## Tests
- Command: `eslint`, `tsc --noEmit`, `prettier --check` on touched files — clean.
- Command: `vitest run history-page.test.tsx` — 9/9 passing (6 existing, 2 updated for
  the new copy/behavior, 3 new: brand-profile empty state, starter-click leaves
  campaign/audience untouched, all 7 variations render).
- Command: `vitest run` (full suite) — 274/274, no regressions.
- Command: `next build` — compiles clean.

## Known Issues / Evidence Gaps
None. All 9 component tests pass and cover real brand profile display, empty state, starter parameter mapping, full variation rendering, and timestamps.

## Review Findings
- Verified `GET /brand/profile` integration in Brand Voice drawer: displays real account brand voice, required facts, and guardrails; cleanly renders empty state if not configured.
- Verified Quick Starters UI: cleanly maps channel, prompt, tone, and length without silently dropping or clobbering selected campaign/audience context.
- Verified all generated variations (1 to 7) render completely without arbitrary slice caps.
- Verified timestamps format relative time from real `created_at`.
- Zero secrets inspection: clean, no credentials or keys added.
- All 274 web vitest tests passing with 0 type errors.

## Review Decision
APPROVED

## Reviewed Code Commit
f91e5a1

## Review Record Commit
This commit (review-record metadata only).

## Human Approval
Not Required — bug fix and quality hardening.

Status: APPROVED
