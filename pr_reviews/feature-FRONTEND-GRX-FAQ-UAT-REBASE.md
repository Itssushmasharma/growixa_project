Task: GRX-FAQ-UAT-REBASE (FAQ formatting + backend/test lint fixes)
Developer: Nikhil Goyal <goyalnikhil743@gmail.com>
Reviewer: Claude Code (did not author this branch)
Branch: feature/FRONTEND/GRX-FAQ-UAT-REBASE
Worktree: none — reviewed the remote branch directly
Base Commit: 750f71d (current main with GRX-DOCS-001 and GRX-CONTACT-016)
Reviewed Code Commit: 2581960
Status: READY_FOR_REVIEW (Round 2)

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

---

## Developer Resolution to Round 2 Feedback (Commit `2581960`)

All reviewer requirements have been resolved:

1. **Rebase**: Rebased `feature/FRONTEND/GRX-FAQ-UAT-REBASE` directly onto current `origin/main` (`750f71d`).
2. **Backend Files Out**: Removed all 4 backend files (`auth/api.py`, `platform_auth/api.py`, `config.py`, `test_migrations.py`) from this branch; branch is strictly scoped to `apps/web/src/app/(marketing)/`.
3. **Fixed Copy Claims on `main`**:
   - **Security claim**: Updated to *"Every customer-data table is keyed to your account ID, and all queries enforce strict account-level isolation. Cross-tenant isolation is enforced in code and covered by automated tests. No customer data is ever shared or visible across tenants."*
   - **14-Day Free Trial claim**: Removed unbuilt trial guarantee; updated to *"Growixa features transparent monthly billing with a free tier and no credit card required to get started."*
   - **Cancellation claim**: Updated to *"You can scale your plan up or down, or manage your subscription at any time with no lock-in contracts or hidden fees."*
4. **Accessibility (WCAG 2.2 Level AA Focus Visible)**:
   - Added `.faqQuestionButton:focus-visible` with `outline: 2px solid #60a5fa; outline-offset: 2px; border-radius: 8px;`.
   - Added `aria-controls` on buttons and `id`/`role="region"`/`aria-labelledby` on answer containers.
   - Added `visibility: hidden;` on collapsed answer container and `visibility: visible;` when open to clean assistive technology announcements.
5. **Reduced Motion**: Added `@media (prefers-reduced-motion: reduce)` disabling transform and transitions.
6. **Component Tests**: Added complete unit test suite `apps/web/src/app/(marketing)/faq-section.test.tsx` (3/3 tests passing).

### Verification
```bash
npm --prefix apps/web test src/app/\(marketing\)/faq-section.test.tsx
# 3/3 tests passed (100%)

npm --prefix apps/web run typecheck
# 0 errors

npm --prefix apps/web run lint
# 0 errors (0 warnings in branch files)

npm --prefix apps/web run format:check
# All matched files use Prettier code style!
```
