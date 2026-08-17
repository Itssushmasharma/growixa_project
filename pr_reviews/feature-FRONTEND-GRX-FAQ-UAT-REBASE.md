Task: GRX-FAQ-UAT-REBASE (FAQ formatting + backend/test lint fixes)
Developer: Nikhil Goyal <goyalnikhil743@gmail.com>
Reviewer: Claude Code (did not author this branch)
Branch: feature/FRONTEND/GRX-FAQ-UAT-REBASE
Worktree: none — reviewed the remote branch directly
Base Commit: eff1628 (merge of PR #7, GRX-FAQ-ANIMATION)
Latest Commit: f07bf5c
Status: CHANGES_REQUESTED

## What Changed

One commit, five files (+19/−15):

- `apps/web/src/app/(marketing)/faq-section.tsx` — Prettier formatting only
- `apps/api/src/growixa_api/auth/api.py` — E501 line-wrap
- `apps/api/src/growixa_api/platform_auth/api.py` — E501 line-wrap
- `apps/api/src/growixa_api/config.py` — one blank line
- `apps/api/tests/infrastructure/test_migrations.py` — unused `Base` import removed (F401)

## Review Findings

### First, two things that are NOT problems — stated so they are not chased

**1. The branch is stale, not destructive.** `git diff origin/main..HEAD` shows **64 files
and −5,135 lines**, appearing to delete the entire help centre, contact restoration, and
the contacts UI. It does not. The merge-base is `eff1628`, and the `GRX-DOCS-001`
(`89624bd`) and `GRX-CONTACT-016` (`95189af`) merges are **not ancestors** of this branch —
so a two-dot diff renders everything the branch *lacks* as deletions. The three-dot diff
(what a merge would actually apply) is the five files above. **Merging would delete
nothing.** Rebase onto current `main` to make the diff readable.

**2. The auth changes are behaviourally inert.** I parsed both files before and after and
compared the **Python AST**: identical. `_set_auth_cookies` and `_set_platform_auth_cookie`
are unchanged — same `secure`, `samesite`, and `x-forwarded-proto` handling. The edit only
wraps a 108-character line to satisfy ruff's 100-char limit.

### Required change 1 — remove the backend files; this branch is marketing-only

Per the product owner's direction, this branch must touch **only the marketing website**.
Four files must come out:

- `apps/api/src/growixa_api/auth/api.py`
- `apps/api/src/growixa_api/platform_auth/api.py`
- `apps/api/src/growixa_api/config.py`
- `apps/api/tests/infrastructure/test_migrations.py`

They are safe in isolation, but a `feature/FRONTEND/` branch editing authentication files is
the wrong shape under AGENTS.md §5 ("stay in scope"). Auth is where an unexpected diff costs
the most reviewer attention, and bundling it here means it inherits this branch's blockers
instead of merging on its own. Move them to a dedicated lint branch — that fix is genuinely
useful and can merge quickly on its own merits.

### Required change 2 — the round-1 blockers are still unfixed, and are now live on `main`

`GRX-FAQ-ANIMATION` was merged as **PR #7 (`eff1628`) while carrying a
`CHANGES_REQUESTED` verdict**. Every finding from that review is therefore in production on
the marketing site, and none is addressed by this branch. Verified against `origin/main`:

| Finding | On `main` now |
|---|---|
| "Every single database table is keyed with a tenant account ID" | **present** — false; 11 tables have no `account_id` |
| "14-day free trial (no credit card required)" | **present** — no trial implementation exists in the backend |
| "cancel at any time directly from your billing panel" | **present** — no cancel endpoint in `billing/api.py` |
| `outline: none` with no focus ring | **present** — `grep -c focus-visible` on `marketing.module.css` → **0** |

The focus-indicator failure is the one to fix first: it is **WCAG 2.2 Level AA, SC 2.4.7**,
which `GRX-NFR-003` commits the product to, and it needs no product decision — just:

```css
.faqQuestionButton:focus-visible {
  outline: 2px solid #60a5fa;
  outline-offset: 2px;
}
```

The three copy claims need a product decision first (build the trial and in-panel
cancellation, or withdraw the claims), then a copy edit. Suggested replacement for the
security sentence, true and no weaker: *"Every customer-data table is keyed to your account
ID and every query is account-scoped, enforced in code and covered by automated
cross-tenant isolation tests."*

### Still open from round 1, unchanged

- Collapsed answers stay in the accessibility tree — `overflow: hidden` clips visually but
  screen readers still announce all five answers.
- No `prefers-reduced-motion` handling on a feature whose purpose is animation.
- No tests for a stateful accordion; one assertion that opening item 2 closes item 1 would
  lock in the contract.

### Process note

A branch carrying `CHANGES_REQUESTED` reached `main` through PR #7. That is the one outcome
the review workflow exists to prevent, and it is worth deciding how the GitHub PR path and
the `pr_reviews/` handoff path stay in agreement — right now a GitHub merge does not consult
the handoff verdict.

## Review Decision
CHANGES_REQUESTED

## Reviewed Code Commit
f07bf5c

## Review Record Commit
(this commit)

## Human Approval
**Required** — customer-facing marketing page. Two of the required changes are product
decisions rather than code fixes: whether the 14-day trial and in-panel cancellation are
things Growixa will build, or claims to withdraw.

Status: CHANGES_REQUESTED
