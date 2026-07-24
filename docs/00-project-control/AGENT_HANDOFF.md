# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-24
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-FOUND-004` — Next.js application foundation (app shell, routing baseline, API client
setup, env config).

## Work completed

- **`apps/web/src/lib/api-client.ts`** (new): `apiFetch<T>(path, init)` — a small typed
  `fetch` wrapper. Prepends `getApiUrl()` (already established in `GRX-FOUND-001`/
  `GRX-FOUND-002`), sends `credentials: "include"` since auth is HttpOnly-cookie-based per
  [DEC-GRX-014](DECISIONS.md) (not bearer tokens, so cross-origin cookies matter even in
  local dev where the frontend is `:3000` and the API is `:8000`), and throws a typed
  `ApiError` (carries `status`) on any non-2xx response. Nothing calls it yet — no UI needs
  the API until `GRX-AUTH-002`/`GRX-USER-002` — but it's real, working code, not a stub;
  foundation tasks are explicitly allowed to stand alone per
  [DEFINITION_OF_DONE.md §No placeholder completion](DEFINITION_OF_DONE.md#no-placeholder-completion).
- **`apps/web/src/app/not-found.tsx`** (new): Next.js App Router's custom-404 convention —
  the "routing baseline" piece, verified to actually return a 404 status, not just render.
- **`apps/web/src/app/page.tsx`**: reworded away from "Placeholder page for local Docker
  Compose validation (GRX-FOUND-002)" (accurate when it was a `GRX-FOUND-002` stopgap, but
  this task is what actually establishes the app shell) to plain product copy.
- No env-config changes needed — `NEXT_PUBLIC_API_URL` / `getApiUrl()` were already
  established and remain the only env surface.

## Files changed

- `apps/web/src/lib/api-client.ts` (new)
- `apps/web/src/app/not-found.tsx` (new)
- `apps/web/src/app/page.tsx` (reworded)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-FOUND-004 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/web
npm run lint            # pass
npm run format:check    # pass
npm run typecheck       # pass
NEXT_PUBLIC_API_URL="http://localhost:8000" npm run build   # pass — routes: /, /_not-found

NEXT_PUBLIC_API_URL="http://localhost:8000" PORT=3001 npm run start &
curl -o /dev/null -w "%{http_code}" http://localhost:3001/                 # 200
curl http://localhost:3001/ | grep -o "Growixa"                           # matched
curl -o /dev/null -w "%{http_code}" http://localhost:3001/no-such-route   # 404

cd ../..
podman compose up -d --build web   # rebuilds web image; all 5 services healthy
curl -o /dev/null -w "%{http_code}" http://localhost:3000/                # 200
curl -o /dev/null -w "%{http_code}" http://localhost:3000/no-such-route   # 404
curl http://localhost:8000/health                                         # unaffected, still ok
```

## Test results

No automated test harness exists yet for the frontend — that is `GRX-TEST-002`'s explicit
scope (test runner config, component test harness, one e2e smoke test), a separate already-
tracked task, not something to build ad hoc inside this one. This task's required test
("Build passes; smoke test loads root route") was satisfied via the manual/scripted
verification above — `npm run build` passing, plus curl-based checks of `/` (200, expected
content) and an unknown route (404), both locally and through the full Docker Compose
stack. This mirrors how `GRX-FOUND-002` satisfied its own smoke-test requirement before any
test runner existed.

## Migrations

None — frontend-only task.

## Decisions

None new.

## Blockers

None.

## Known issues

- `apiFetch`/`ApiError` are unconsumed foundation code until the first real API call is
  wired up (`GRX-AUTH-002` login, most likely). Nothing to fix now — noted so a future
  session doesn't mistake it for dead code.
- CORS is not yet configured on the FastAPI side to accept credentialed cross-origin
  requests from `localhost:3000`. Not a blocker for this task (nothing calls the API from
  the browser yet), but whichever task first wires up a real `apiFetch` call (likely
  `GRX-AUTH-002`) will need to add FastAPI's `CORSMiddleware` with
  `allow_credentials=True` and the frontend origin allow-listed.

## Current state

Next.js app shell, routing baseline, and API client foundation are done and validated:
build passes, lint/format/typecheck clean, and the root route (and a 404 case) work both
locally and through the full Docker Compose stack. No authenticated dashboard shell exists
yet (`GRX-FOUND-008`, blocked on `GRX-AUTH-002`). No frontend test harness exists yet
(`GRX-TEST-002`, now unblocked).

## Exact next task

Four tasks are now `READY`:

- `GRX-AUDIT-001` — Audit log module (`audit_logs` table/migration, insert-only
  repository/service, structured-log redaction).
- `GRX-AUTH-001` — Users, roles, permissions schema + seed.
- `GRX-TEST-001` — Backend test foundation (test runner config, DB test fixtures/factories,
  coverage baseline).
- `GRX-TEST-002` — Frontend test foundation (test runner config, component test harness, one
  e2e smoke test) — newly unblocked by this task.

Per [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md), only one Sprint
1 task is worked on at a time.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`8269436` — feat(found): Next.js application foundation (GRX-FOUND-004)
