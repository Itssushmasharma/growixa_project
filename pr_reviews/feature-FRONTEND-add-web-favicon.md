Task: Add site favicon
Developer: Claude Code
Reviewer: Google Antigravity
Branch: feature/FRONTEND/add-web-favicon
Worktree: .worktrees/grx-web-favicon
Base Commit: a7bdeb8
Latest Commit: 9c13001
Status: APPROVED

## What Changed
Added `apps/web/src/app/icon.png` and `apps/web/src/app/apple-icon.png` (512x512,
resized via `sips` from the existing `public/assets/logo-icon.png` brand mark — the
same image already used as the sidebar logo). Next.js App Router auto-detects these
file names and injects `<link rel="icon">`/`<link rel="apple-touch-icon">` on every
page site-wide — no `metadata.icons` changes needed in `layout.tsx`.

## Why
Ad-hoc UI polish request — the site had no favicon at all.

## Important Files
- `apps/web/src/app/icon.png` (new)
- `apps/web/src/app/apple-icon.png` (new)

## Tests
- Command: `next build` — confirms `/icon.png` and `/apple-icon.png` are generated as
  real routes, no route conflicts.
- Command: `eslint`, `tsc --noEmit`, `prettier --check` — all clean.
- Manual: started a real dev server, confirmed via the live DOM that both `<link>` tags
  render with the correct `href`/`type`/`sizes` (512x512, image/png), and confirmed
  `fetch('/icon.png')` returns `200 image/png`.

## Known Issues / Evidence Gaps
None.

## Review Findings

No blocking findings.

- Verified that `apps/web/src/app/icon.png` and `apps/web/src/app/apple-icon.png` follow standard Next.js App Router convention for automatic favicon & Apple touch icon discovery.
- Binary asset inspection: Valid 512x512 PNG images derived cleanly from existing brand logo assets.
- Automated validation:
  - `npm run test` passed (50 test files, 270 passed).
  - `npm run typecheck` passed with 0 errors.
  - `npm run lint` passed with 0 errors.
- Zero Secret Leaks: Binary image additions only, no secrets or credentials.

## Review Decision
APPROVED

## Reviewed Code Commit
9c13001476db17fdb57d76cb5e23da671a539eb8

## Review Record Commit
This commit (review handoff update)

## Human Approval
Status: APPROVED (Product Owner sign-off confirmed in chat)
