# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-23
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-FOUND-002` — Docker Compose local environment (Postgres, Redis, RabbitMQ, backend, frontend).

## Work completed

Built and validated the full local Docker Compose stack end-to-end.

**`compose.yaml`:** `postgres` (16-alpine), `redis` (7-alpine), `rabbitmq`
(3-management-alpine), `api`, `web` on a shared bridge network. Postgres/RabbitMQ mgmt UI
published on loopback only for local tooling; Redis and RabbitMQ AMQP not published at all
(reached over the compose network by service name). Healthchecks on every service; `api`
and `web` gate startup on `depends_on: condition: service_healthy`.

**`apps/api/Dockerfile`:** `python:3.13-slim`, editable install (`pip install -e ".[dev]"`),
`uvicorn --reload`. **`apps/web/Dockerfile`:** `node:22-alpine`, `npm install`, `npm run dev`.
Both are explicitly local-development images (no multi-stage/distroless build, no non-root
user hardening) — noted in-file as a future deployment-task concern, not deferred silently.

**Minimal application code** (enough to give the stack something real to validate, not the
full app foundation — that's `GRX-FOUND-003`/`GRX-FOUND-004`):
- `apps/api/src/growixa_api/{main.py,config.py}` — a `GET /health` endpoint that opens a
  real connection to Postgres, Redis, and RabbitMQ and reports per-dependency status.
- `apps/web/src/app/{layout.tsx,page.tsx}` and `apps/web/next.config.mjs` — minimal Next.js
  App Router shell so the image builds and serves.
- `apps/web/package.json` gained `next`/`react`/`react-dom` moved to `dependencies` (they
  were `devDependencies` in `GRX-FOUND-001`, which is wrong once the app actually runs) and
  `dev`/`build`/`start` scripts. `tsconfig.json`/`eslint.config.mjs`/`next-env.d.ts` were
  regenerated/adjusted by the Next.js toolchain itself when the app directory was added.

**Root `.env.example`:** documents every Compose-level variable — DB/MQ credentials, host
port mappings (`POSTGRES_PORT`, `RABBITMQ_MGMT_PORT`, `API_PORT`, `WEB_PORT`), and the JWT
signing settings from [DEC-GRX-014](DECISIONS.md).

**Validation (`podman compose up -d`):** all 5 containers reached `healthy`.
`GET http://localhost:8000/health` → `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`.
`GET http://localhost:3000/` → HTTP 200.

## Issues hit and fixed during validation

1. **Podman VM went unresponsive mid-build** after an earlier hard stop, then its overlay
   storage was genuinely corrupted (`podman images` itself failed with
   `readlink .../overlay: invalid argument`). Diagnosed with `podman system check` (16
   damaged layers, 5 damaged images — none belonging to unrelated running containers from
   other local projects) and repaired with `podman system check -r`. This was a host-machine
   podman issue, not a repository/compose defect, and required rebuilding the `api`/`web`
   images afterward.
2. **Host disk hit `ENOSPC`** (0 bytes free) partway through this session — even `echo`
   failed. Resolved outside the repo (user freed space); confirmed recovered via
   `df -h /` before resuming. Worth keeping an eye on: host disk was still at 96%/910Mi free
   afterward.
3. **Port conflict on 5432:** a native Postgres process already listens on the host's
   `127.0.0.1:5432` outside of any container. `POSTGRES_PORT` is already parameterized in
   `compose.yaml`, so this is a per-machine `.env` value (set to `5433` locally), not a
   compose/schema change. `.env.example` correctly keeps the plain default of `5432`.
4. **podman-compose healthcheck bug:** a `CMD`-array healthcheck test whose last element was
   a multi-word string (the `api` service's `python -c "import ...; urlopen(...)"` health
   check) was being re-split into separate argv tokens by podman-compose's docker-compose →
   podman translation, breaking the check even though `curl`-ing `/health` directly worked
   fine. Confirmed by inspecting `podman inspect <container> --format '{{json .Config.Healthcheck}}'`
   and comparing against the postgres service's `CMD-SHELL` healthcheck, which stayed intact.
   Fixed by switching the api healthcheck to `CMD-SHELL` form in `compose.yaml`, which
   podman-compose preserves as a single string.

## Files changed

- `compose.yaml` (new)
- `apps/api/Dockerfile`, `apps/api/.dockerignore` (new)
- `apps/api/src/growixa_api/main.py`, `apps/api/src/growixa_api/config.py` (new)
- `apps/web/Dockerfile`, `apps/web/.dockerignore` (new)
- `apps/web/next.config.mjs`, `apps/web/next-env.d.ts` (new)
- `apps/web/src/app/layout.tsx`, `apps/web/src/app/page.tsx` (new)
- `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/tsconfig.json`,
  `apps/web/eslint.config.mjs` (updated for the Next.js app directory)
- `.env.example` (new, root)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-FOUND-002 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
podman compose build api                    # succeeded first try
podman compose build web                    # hit corrupted overlay storage, see Issues above
podman system check                         # diagnosed 16 damaged layers / 5 damaged images
podman system check -r                      # repaired storage
podman compose build web                    # succeeded after repair
podman compose up -d                        # postgres/redis/rabbitmq up; port 5432 conflict
# set POSTGRES_PORT=5433 in local .env
podman compose up -d                        # all healthy except api (healthcheck bug)
podman inspect growixa-api-1 --format '{{json .Config.Healthcheck}}'   # confirmed mangled test
# switched api healthcheck to CMD-SHELL in compose.yaml
podman compose up -d --force-recreate api   # api healthy
podman compose up -d web                    # web healthy
curl http://localhost:8000/health           # {"status":"ok",...}
curl -o /dev/null -w "%{http_code}" http://localhost:3000   # 200
```

## Test results

Manual + smoke test only, per this task's acceptance criteria (no automated test suite
exists yet — that's `GRX-TEST-001`/`GRX-TEST-002`). All 5 containers healthy; both HTTP
smoke checks passed.

## Migrations

None — no database module exists yet (`GRX-FOUND-005`/`GRX-AUTH-001`).

## Decisions

None new. `POSTGRES_PORT`/`RABBITMQ_MGMT_PORT`/`API_PORT`/`WEB_PORT` in `.env.example` are
implementation of the port-mapping approach already implied by [DEC-GRX-004](DECISIONS.md),
not a new decision.

## Blockers

None. Host disk space (96% used, ~910Mi free as of this session) is worth monitoring — not
a blocker for this task, but future large builds/pulls could hit `ENOSPC` again.

## Known issues

- `apps/api/Dockerfile` and `apps/web/Dockerfile` are local-dev-only images (no multi-stage
  slim build, no non-root user) — flagged in-file, to be revisited under a dedicated
  deployment/production-hardening task, not Sprint 1.
- The podman-compose `CMD`-array healthcheck-splitting bug (see Issues above) applies to
  any future multi-word healthcheck test string added to `compose.yaml` — use `CMD-SHELL`
  form for any healthcheck whose command has more than one space-separated argument.

## Current state

Local Docker Compose environment is fully working and validated (`postgres`, `redis`,
`rabbitmq`, `api`, `web` all healthy; API and web both respond correctly). No FastAPI app
foundation, no Next.js app foundation, no database connectivity beyond the health-check
probe exist yet — those are the next tasks.

## Exact next task

`GRX-FOUND-003` — FastAPI application foundation (app factory, config loading, health
endpoint, OpenAPI docs enabled). Status: `READY`. Dependency (`GRX-FOUND-002`) is `DONE`.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

Recorded below after this handoff is committed alongside the `GRX-FOUND-002` change set.
