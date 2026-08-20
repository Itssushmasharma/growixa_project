Task: Add site favicon
Developer: Claude Code
Reviewer:
Branch: feature/FRONTEND/add-web-favicon
Worktree: .worktrees/grx-web-favicon
Base Commit: a7bdeb8
Latest Commit: 9c13001
Status: READY_FOR_REVIEW

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


## Review Decision


## Reviewed Code Commit


## Review Record Commit


## Human Approval
Required (visual/UI change) — please confirm the icon looks right in an actual browser
tab, not just the automated checks above.

Status:
