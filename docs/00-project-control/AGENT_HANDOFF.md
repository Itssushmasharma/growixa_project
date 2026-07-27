# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-COMPANY-002` — Company settings screen. Picked next after `GRX-DEVOPS-001`; the user
confirmed no need to push/verify CI right now and to continue.

## Work completed

- `/dashboard/company-settings`: a form for company profile + brand voice, built as a
  Client Component (`company-settings-form.tsx`) that fetches `/auth/me`,
  `/company/profile`, `/brand/profile` on mount via `apiFetch` (matches
  `TEST_STRATEGY.md`'s "mocked API client, not real network calls" testability
  requirement).
- **Backend extension**: `GET /auth/me` now returns `permissions: string[]` (new
  `list_permission_codes_for_user()` in `permissions/repositories.py`, new `MeOut` schema)
  — needed because the frontend has no other way to know if the caller can edit
  (`company.settings.edit`, Admin/Super Admin only per RBAC.md) versus view-only. Viewers
  see the identical data, every field disabled, with a "view-only access" note and no
  Save button — not a form that would only fail after clicking Save.
- Save submits company then brand profile in sequence (brand requires company to exist
  first, an existing `GRX-COMPANY-001` behavior).
- Sidebar (`sidebar.tsx`) is now a real client-side nav with a `SETTINGS` section; topbar
  title (`page-title.tsx`) is route-driven instead of hardcoded.

## A real testing-infra bug found while writing the component test

Vitest doesn't auto-wire `@testing-library/react`'s cleanup unless `test.globals: true`
is set (which this project doesn't use — tests import `describe`/`it`/`expect` explicitly).
Without it, DOM from one `it()` block was leaking into the next within the same file,
causing false "multiple elements found" failures. Fixed with an explicit
`afterEach(cleanup)` in `vitest.setup.ts` — this was a latent bug in `GRX-TEST-002`'s
setup that only surfaced once a test file had more than one `it()` block rendering
overlapping content.

## Files changed

- `apps/api/src/growixa_api/permissions/repositories.py` (`list_permission_codes_for_user`)
- `apps/api/src/growixa_api/auth/schemas.py` (`MeOut`)
- `apps/api/src/growixa_api/auth/api.py` (`/auth/me` returns permissions)
- `apps/api/tests/test_auth_login.py` (updated `/auth/me` test to assert permissions)
- `apps/web/vitest.config.ts` (added `@/*` alias — Vite doesn't read `tsconfig.json`'s
  path mapping on its own)
- `apps/web/vitest.setup.ts` (`afterEach(cleanup)`)
- `apps/web/src/lib/auth.ts` (`CurrentUser.permissions`)
- `apps/web/src/app/dashboard/sidebar.tsx` (real nav, client component)
- `apps/web/src/app/dashboard/sidebar.module.css` (`.navItem` for inactive state)
- `apps/web/src/app/dashboard/page-title.tsx` (new)
- `apps/web/src/app/dashboard/layout.tsx` (uses `PageTitle`)
- `apps/web/src/app/dashboard/company-settings/{page.tsx,company-settings-form.tsx,
  company-settings-form.module.css,company-settings-form.test.tsx,types.ts}` (new)
- `apps/web/package.json` (added `@testing-library/user-event`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`
  (this update — trimmed `PROJECT_STATUS.md`'s "Immediate next steps" narrative down
  significantly per explicit user feedback that doc updates had grown too verbose)

## Commands executed

```bash
cd apps/api
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .
.venv/bin/pytest -q   # 45 passed, 2 skipped

cd ../web
npm install --save-dev @testing-library/user-event
npm run lint && npm run format:check && npm run typecheck && npm run test   # 5 passed
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
npm run test:e2e   # 3 passed, unaffected

cd ../..
podman compose up -d --build api web
# created a smoke Admin and a smoke Viewer directly via the ORM, both roles verified in a
# real browser: Admin edits + saves + reload shows persisted values; Viewer sees the same
# data fully disabled with no Save button. Cleaned up smoke users + company/brand rows.
```

## Test results

Backend: `pytest` → 45 passed, 2 skipped (unchanged). Frontend: `eslint`/
`prettier --check`/`tsc --noEmit` clean; Vitest → 5 passed (4 new); Playwright → 3 passed
(unaffected); `next build` succeeds. Manually verified both permission levels in a real
browser against rebuilt Compose containers.

## Migrations

None — no schema changes.

## Decisions

None new. `contact_details` (a free-form JSON dict) is intentionally not exposed in this
form — building a generic key-value editor is disproportionate to Sprint 1 scope; revisit
if a real need for it shows up.

## Blockers

None.

## Known issues

- `GRX-DEVOPS-001` still `IN_REVIEW`, unchanged from before this task — still needs a push
  to confirm a green Actions run.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); no "list
  pending invitations"/"revoke invitation" endpoints (`GRX-USER-001`); raw password-reset
  token exposed in local dev only (`GRX-AUTH-005`); icon-mark logo asset has an opaque
  light backdrop on the dark login card (`GRX-FOUND-008`, cosmetic).

## Current state

Company settings is live end-to-end: real backend permission data drives a real
editable/read-only UI split, verified both by an automated component test and by hand in
a browser as both roles. `GRX-USER-002` (user management screens) is the only Sprint 1
task left in the tracker.

## Exact next task

No explicit user direction beyond this point. `GRX-USER-002` (user management screens:
list, invite, disable, role assignment) is the last `READY` Sprint 1 task.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
podman compose up -d
```

## Latest commit

`9989373` — feat(web): company settings screen (GRX-COMPANY-002)
