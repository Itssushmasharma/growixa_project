# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-FOUND-008` — Dashboard shell. Picked immediately after `GRX-TEST-002` gave the
frontend a real test harness. The user directed this UI work explicitly, pointing to the
previously captured design reference (`DESIGN_REFERENCES.md` +
`mockups/growixa-login-and-dashboard-mockup.html`) and a fresh screenshot of the same
dashboard mockup for visual grounding.

## Work completed

- **Backend — two small, necessary additions** (discovered while scoping this frontend
  task, not in its original Files/Modules column):
  - CORS middleware (`app.py`), driven by a new `cors_allowed_origins` setting
    (`config.py`, default `["http://localhost:3000", "http://localhost:3100"]` — the
    Compose `web` container and Playwright's e2e webServer respectively). Without this, a
    browser can't complete the cross-origin, credentialed (cookie) requests auth needs.
  - `GET /auth/me` (`auth/api.py`): identifies the session via the access-token cookie
    itself, the same shape as `/refresh`/`/logout-all` — no `require_permission()`, added
    to the route-protection audit's allowlist alongside them, since any authenticated user
    may know who they are. Without this, there is no way for a Server Component to
    determine "is this user logged in" — the access token is HttpOnly, unreadable by
    client-side JS.
- **Frontend**:
  - `globals.css`: design tokens (colors, gradients, card/pill radii/shadows) taken
    directly from the design brief already captured in `DESIGN_REFERENCES.md`.
  - `/login` (`src/app/login/`): a real email+password form, dark navy gradient
    background, glass card — not the mockup's demo "Sign in as Super Admin/Team Member"
    buttons, since the real backend needs actual credentials, not a role toggle.
  - `/dashboard` (`src/app/dashboard/`): `layout.tsx` calls `getCurrentUser()`
    server-side and `redirect("/login")` on failure; renders a sidebar + top bar shell
    around `page.tsx`'s empty-state landing content.
  - `src/lib/auth.ts`: `getCurrentUser()` forwards the incoming request's cookies (via
    `next/headers`'s `cookies()`) to `GET /auth/me` — this is the only way a Server
    Component can check auth state, since the cookie is HttpOnly.
  - Root `/` (`src/app/page.tsx`) now `redirect("/dashboard")`, making the dashboard's own
    auth check the real entry-point gate.
  - Per `DESIGN_REFERENCES.md`'s scope caveat, the sidebar renders only the "Dashboard" nav
    item — Contacts/Campaigns/Team/Settings/etc. have no page behind them yet in Sprint 1,
    so they're omitted entirely rather than shipped as dead links.

## A real bug found and fixed during Compose verification — not caught by the e2e suite

Server-side fetches issued from inside the `web` container (i.e. `getCurrentUser()`
running in Next's Node process) used `NEXT_PUBLIC_API_URL=http://localhost:8000` — but
`localhost` inside that container resolves to the container itself, not the `api`
container. Every dashboard visit 500'd in the real Dockerized stack, even though the
identical code worked perfectly via `next build && next start` on the host (where both
processes genuinely share one `localhost`, since Playwright's e2e webServer isn't
containerized at all).

Fixed with a server-only `API_INTERNAL_URL` (`src/lib/env.ts`'s new `getServerApiUrl()`,
falling back to `NEXT_PUBLIC_API_URL` when unset — so running outside Docker needs no
change), set to `http://api:8000` (the Compose service DNS name) in `compose.yaml`. This
is exactly the class of bug a host-run e2e suite structurally cannot catch — it's why this
task's verification included rebuilding both containers and driving the actual
login → dashboard → logout flow in a real browser against them (see Commands executed),
not stopping at a green Playwright result.

## Files changed

- `apps/api/src/growixa_api/config.py` (`cors_allowed_origins`)
- `apps/api/src/growixa_api/app.py` (CORS middleware)
- `apps/api/src/growixa_api/auth/api.py` (`GET /auth/me`)
- `apps/api/tests/test_protected_routes_audit.py` (`/auth/me` added to the public
  allowlist)
- `apps/api/tests/test_auth_login.py` (two new tests: `/auth/me` returns the session,
  `/auth/me` without a session is 401)
- `apps/web/src/app/globals.css` (new — design tokens)
- `apps/web/src/app/layout.tsx` (imports `globals.css`)
- `apps/web/src/app/page.tsx` (now redirects to `/dashboard`)
- `apps/web/src/app/page.test.tsx` (updated for the redirect, mocks `next/navigation`)
- `apps/web/src/app/login/{page.tsx,login.module.css}` (new)
- `apps/web/src/app/dashboard/{layout.tsx,page.tsx,sidebar.tsx,logout-button.tsx,
  layout.module.css,sidebar.module.css,topbar.module.css,page.module.css}` (new)
- `apps/web/src/lib/auth.ts` (new — `getCurrentUser()`)
- `apps/web/src/lib/env.ts` (new `getServerApiUrl()`)
- `apps/web/tests/e2e/{fixtures.ts,global-setup.ts,global-teardown.ts,dashboard.spec.ts}`
  (new)
- `apps/web/tests/e2e/smoke.spec.ts` (updated: root now redirects to `/login`, not a
  static heading)
- `apps/web/playwright.config.ts` (added `globalSetup`/`globalTeardown`)
- `compose.yaml` (`web` service: added `API_INTERNAL_URL=http://api:8000`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-FOUND-008` → `DONE`, evidence
  recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this
  update)

## An observation, not part of this task

Another session/process is concurrently editing `docs/01-product/MVP_SCOPE.md`,
`docs/01-product/ROADMAP.md`, `docs/02-features/FEATURE_CATALOG.md`, and a new
`docs/02-features/FEATURE_SMS_MARKETING.md` (`GRX-FEAT-SMS-001`, SMS Marketing/Twilio).
Left entirely untouched throughout this task — noted here only so it isn't mistaken for
something this session did, and so a future reader isn't confused about why those files
show unrelated uncommitted changes.

## Commands executed

```bash
cd apps/api
# config.py, app.py, auth/api.py, test_protected_routes_audit.py, test_auth_login.py updated
.venv/bin/ruff check --fix . && .venv/bin/ruff format . && .venv/bin/mypy .
source ../../.env && export DATABASE_URL=... REDIS_URL="redis://localhost:6379/0" RABBITMQ_URL=...
.venv/bin/pytest -v   # 45 passed, 2 skipped

cd ../web
# globals.css, login/, dashboard/, lib/auth.ts, lib/env.ts, e2e fixtures/setup/teardown written
npm run lint && npm run format:check && npm run typecheck && npm run test

cd ../..
podman compose up -d --build api    # pick up CORS + /auth/me
curl -i -X OPTIONS http://localhost:8000/auth/login -H "Origin: http://localhost:3000" ...  # CORS headers present
curl http://localhost:8000/auth/me  # 401 without a cookie
# created a smoke user, confirmed login -> /auth/me round trip via curl, cleaned up

cd apps/web && npm run test:e2e     # 3 passed against real Compose Postgres/Redis

cd ../..
podman compose up -d --build web    # FIRST attempt: curl -L http://localhost:3000/ -> 500
# root-caused: NEXT_PUBLIC_API_URL=localhost:8000 unreachable from inside the web container
# added API_INTERNAL_URL to compose.yaml + getServerApiUrl() in env.ts
podman compose up -d --build api web
curl -s -o /dev/null -w "%{http_code} -> %{url_effective}\n" -L http://localhost:3000/
# 200 -> http://localhost:3000/login

# opened a real browser against localhost:3000: verified login screen renders correctly,
# logged in as a smoke-test user, confirmed the dashboard shell (sidebar, top bar, user
# name, empty state), clicked Log out, confirmed redirect to /login, then re-visited
# /dashboard directly and confirmed it redirected to /login again (session really cleared)
# cleaned up the smoke user afterward
```

## Test results

Backend: `pytest` → 45 passed, 2 skipped (documented Redis-unreachable-from-host skips,
unchanged from `GRX-AUTH-004`). `ruff`/`mypy` clean across 69 source files.

Frontend: `eslint`/`prettier --check`/`tsc --noEmit` clean. Vitest → 1 passed. Playwright
→ 3 passed (logged-out `/dashboard` redirect, logged-out `/` redirect, full
login→shell→logout→re-verify-logged-out flow) against real Compose Postgres/Redis.

Manually verified in a real browser against the rebuilt `api`+`web` Compose containers
(see Commands executed) — this is what caught the `API_INTERNAL_URL` bug that neither
`pytest` nor the host-run Playwright suite could have found.

## Migrations

None — no schema changes.

## Decisions

None new. The CORS/`/auth/me` additions and the `API_INTERNAL_URL` split are
implementation necessities for the already-specified auth model (`AUTHENTICATION.md`),
not new architecture calls.

## Blockers

None.

## Known issues

- Cosmetic, non-blocking: the icon-mark PNG has an opaque light backdrop baked in, showing
  as a small white square against the dark login card. A future visual-polish pass could
  swap in the monochrome/white logo variant. Not worth blocking this task over.
- Per `DESIGN_REFERENCES.md`, no nav item besides Dashboard is wired up yet — expected,
  not a gap, until `GRX-COMPANY-002`/`GRX-USER-002` (and further future tasks) land pages
  for them.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); no "list
  pending invitations"/"revoke invitation" endpoints (`GRX-USER-001`); raw password-reset
  token exposed in local dev only (`GRX-AUTH-005`).

## Current state

The frontend has a real, working, end-to-end authenticated shell for the first time:
login → dashboard → logout, verified both by an automated e2e suite and by hand in a real
browser against the actual Dockerized stack. This completes the eighth step of this
session's continuous "most needed" sequence: `GRX-AUTH-002` → `GRX-AUTH-003` →
`GRX-USER-001` → `GRX-AUTH-005` → `GRX-FOUND-006` → `GRX-AUTH-004` → `GRX-TEST-002` →
`GRX-FOUND-008`.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-COMPANY-002` (company
settings screen, frontend — can now nest into the dashboard shell) and `GRX-USER-002`
(user management screens, frontend, same). Both are the only Sprint 1 tasks left.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`886329a` — feat(web): dashboard shell (GRX-FOUND-008)
