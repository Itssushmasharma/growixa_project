# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-FOUND-006` — Redis connectivity. Picked because its only dependency
(`GRX-FOUND-003`) was already `DONE` — the tracker still had it marked `BACKLOG`, a stale
status corrected as part of picking this up — and because it directly unblocks
`GRX-AUTH-004` (login rate limiting), a P0 security task covering the exact
login/password-reset-request endpoints built in the two sessions before this one.

## Work completed

- **`growixa_api/redis.py`** (new): a module-level pooled `redis.asyncio` client built
  from `settings.redis_url`, plus a `get_redis()` FastAPI dependency generator — the same
  shape as `db.py`'s `engine`/`get_session()`. This is the reusable client `GRX-AUTH-004`'s
  rate limiter (and later locks/idempotency keys, per `SYSTEM_ARCHITECTURE.md`) will
  import.
- **`health.py`**: the Redis check previously opened a brand-new client, pinged it, and
  closed it on every single `/health` request; now reuses the shared pooled client
  (matching the Postgres engine-reuse fix already landed alongside `GRX-AUTH-005`).
- **`tests/test_redis.py`** (new): a real set/get/delete round-trip against the shared
  client.

## An explicit, flagged environment finding — not a silent workaround

Compose's `redis` service has **no host port mapping**, by design (see the comment in
`compose.yaml` and `LOCAL_DEVELOPMENT.md`'s Redis inspection section: "not required to be
reachable from outside the compose network"). Postgres and RabbitMQ both are host-mapped
(the whole reason every earlier task's `pytest` run could hit real Postgres from the host
venv), but Redis deliberately is not. A host-run pytest process therefore cannot open a
real TCP connection to it.

`tests/test_redis.py` accounts for this: it attempts a real `SET`, and if that raises a
`redis.exceptions.RedisError` (connection refused, as it will under host-run pytest against
this Compose setup), it calls `pytest.skip()` with the reason, rather than silently
"passing" against nothing or failing the whole suite for an environment fact that isn't a
code defect. The actual set/get/delete round-trip was verified for real by executing it
live inside the running `api` container (see Commands executed below), where
`REDIS_URL=redis://redis:6379/0` resolves over the compose network. **If a CI runner is
ever added** (`GRX-DEVOPS-001`) with a reachable Redis service, this same test will start
actually exercising the connection instead of skipping — no test rewrite needed.

## Files changed

- `apps/api/src/growixa_api/redis.py` (new)
- `apps/api/src/growixa_api/health.py` (Redis check reuses the pooled client)
- `apps/api/tests/test_redis.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-FOUND-006` → `DONE`, evidence
  recorded; `GRX-AUTH-004` flipped `BACKLOG` → `READY` now that both its dependencies are
  `DONE`)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this
  update)

## Commands executed

```bash
cd apps/api
# growixa_api/redis.py written; health.py updated to reuse it; tests/test_redis.py written
.venv/bin/ruff check --fix . && .venv/bin/ruff format . && .venv/bin/mypy .

source ../../.env && export DATABASE_URL=... REDIS_URL="redis://localhost:6379/0" RABBITMQ_URL=...
.venv/bin/pytest -v   # 38 passed, 1 skipped (test_redis.py skips: Redis unreachable from host)

cd ../..
podman compose up -d --build api
curl -s http://localhost:8000/health   # {"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}

# live verification of the actual pooled client, executed inside the container where
# REDIS_URL correctly resolves over the compose network:
podman compose exec api python3 -c "
import asyncio
from growixa_api.redis import client
async def main():
    await client.set('grx:smoke:test', 'hello-redis', ex=10)
    print('GET ->', await client.get('grx:smoke:test'))
    await client.delete('grx:smoke:test')
    print('after delete ->', await client.get('grx:smoke:test'))
asyncio.run(main())
"
# GET -> hello-redis
# after delete -> None
```

## Test results

`pytest` → 38 passed, 1 skipped (34 pre-existing from before `GRX-AUTH-005` + 4 from
`GRX-AUTH-005` + 1 new skip). 95% coverage, unchanged (a skip contributes no missed lines).
`ruff`/`mypy` clean across 67 source files.

## Migrations

None — this task added no database schema.

## Decisions

None new. The host/container Redis-reachability split is an existing, already-documented
architecture choice (`compose.yaml`, `LOCAL_DEVELOPMENT.md`), not a new decision — this
task's contribution was noticing the tracker's dependency/status was stale and building the
reusable client, not changing how Redis is exposed.

## Blockers

None.

## Known issues

- `tests/test_redis.py` skips under the standard host-run `pytest` workflow used by every
  task in this session, because Redis has no host port mapping. This is expected and
  documented, not a gap to "fix" by adding a host mapping (that would contradict the
  existing, deliberate compose.yaml decision) — revisit only if `GRX-DEVOPS-001` (CI
  pipeline) needs it addressed for a hosted runner.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); CORS for
  frontend calls (`GRX-FOUND-004`); no "list pending invitations"/"revoke invitation"
  endpoints (`GRX-USER-001`); raw password-reset token exposed in local dev only
  (`GRX-AUTH-005`).

## Current state

A reusable, pooled Redis client now exists for the rest of the backend to build on.
`GRX-AUTH-004` (login rate limiting) is now fully unblocked — both of its dependencies
(`GRX-AUTH-002`, `GRX-FOUND-006`) are `DONE`. This completes the fifth step of this
session's user-directed backend-continuity sequence: `GRX-AUTH-002` → `GRX-AUTH-003` →
`GRX-USER-001` → `GRX-AUTH-005` → `GRX-FOUND-006`.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-AUTH-004` (login rate
limiting, P0, backend — the highest-priority pick given this session's established
backend-continuity preference), `GRX-TEST-002` (frontend test foundation), `GRX-COMPANY-002`
(company settings screen, frontend), `GRX-FOUND-008` (dashboard shell, frontend),
`GRX-USER-002` (user management screens, frontend).

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`32aacdf` — feat(api): Redis connectivity (GRX-FOUND-006)
