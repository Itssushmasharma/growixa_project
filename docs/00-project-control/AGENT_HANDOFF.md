# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-29
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-FOUND-007` — RabbitMQ connectivity and health check (producer/consumer + worker
skeleton). Picked after `GRX-USER-002` per the user's "go next thst needed"; it was the
last remaining `BACKLOG` Sprint 1 task with satisfied dependencies (`GRX-FOUND-003` DONE).

## Work completed

- `apps/api/src/growixa_api/jobs/schemas.py`: `JobEnvelope` (job_id, idempotency_key,
  job_type, payload, created_at, attempt_count, created_by_user_id) per
  `BACKGROUND_JOB_ARCHITECTURE.md`'s shared envelope spec.
- `apps/api/src/growixa_api/jobs/producer.py`: `publish_job(queue_name, envelope)` —
  connects via `aio_pika.connect_robust`, declares the queue durable, publishes a
  persistent message.
- `apps/api/src/growixa_api/jobs/api.py`: `POST /system/jobs/healthcheck`, gated on
  `admin.access` (Sprint 1 has no dedicated jobs permission and no real business job to
  trigger the pipeline otherwise — this exists purely so the connectivity claim is
  testable, not as a permanent ops surface).
- New `apps/worker/` app — a separate deployable, not an entrypoint bolted onto
  `apps/api`, per `SYSTEM_ARCHITECTURE.md`'s "independently scalable Python workers":
  `pyproject.toml`/`Dockerfile` mirroring `apps/api`'s tooling, `config.py` (Settings:
  `rabbitmq_url`), `consumer.py` (`consume_forever`, declares `grx.system.healthcheck`,
  logs each processed job's `job_id`), `main.py` (entrypoint).
- `compose.yaml`: new `worker` service, depends on `rabbitmq` health.
- `.github/workflows/ci.yml`: new parallel `worker` job (lint/format/mypy/pytest — no
  service containers needed, its tests are pure-unit against a fake AMQP message).
- Corrected a stale line in `LOCAL_DEVELOPMENT.md` that said the worker would build from
  `apps/api/` — that was a placeholder from before this task was implemented.

## Files changed

- `apps/api/src/growixa_api/jobs/{__init__,schemas,producer,api}.py` (new)
- `apps/api/src/growixa_api/app.py` (wired `jobs_router`)
- `apps/api/tests/test_jobs.py` (new, 4 tests: envelope defaults, admin trigger,
  non-admin 403, real producer→queue round trip)
- `apps/api/.env` (new, git-ignored — needed for host-run pytest against Compose Postgres
  at `localhost:5433`; wasn't present at the start of this session)
- `apps/worker/` (new app): `pyproject.toml`, `README.md`, `Dockerfile`,
  `src/growixa_worker/{__init__,config,consumer,main}.py`, `tests/test_consumer.py`
- `compose.yaml` (new `worker` service)
- `.github/workflows/ci.yml` (new `worker` job)
- `docs/11-devops/LOCAL_DEVELOPMENT.md` (corrected worker build source + health-check
  verification steps)
- `docs/00-project-control/MASTER_TASK_TRACKER.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`
  (this update)

## Commands executed

```bash
cd apps/worker
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .
.venv/bin/pytest -q   # 2 passed

cd ../api
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .
.venv/bin/pytest -q   # 58 passed, 3 skipped (95% coverage)

cd ../..
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
podman compose up -d --build worker api
# docker compose logs worker -> "growixa-worker listening on grx.system.healthcheck"
# created a smoke Admin, logged in, POST /system/jobs/healthcheck -> 202 {job_id: X}
# docker compose logs worker -> "Processed healthcheck job X" (same job_id)
# created a smoke Viewer, same POST -> 403
# curl /health -> rabbitmq: ok (unaffected)
# cleaned up both smoke users via psql DELETE
```

## Test results

`apps/worker`: `ruff`/`mypy` clean, `pytest` 2 passed. `apps/api`: `ruff`/`mypy` clean,
`pytest` 58 passed, 3 skipped (95% coverage) — the new RabbitMQ producer round-trip test
skips locally (broker not host-reachable, same as `GRX-FOUND-006`'s Redis test) but will
run for real in CI. Live-verified end-to-end against rebuilt Compose containers: a
triggered job's ID appeared in the worker's log, proving the full publish→consume path
works, not just that a connection opens.

## Migrations

None — no schema changes.

## Decisions

Built the worker as a genuinely separate app (`apps/worker/`) rather than an entrypoint
inside `apps/api`, even though an early draft of `LOCAL_DEVELOPMENT.md` had assumed the
latter — `SYSTEM_ARCHITECTURE.md`'s "independently scalable Python workers" and the
`MASTER_TASK_TRACKER.md` Files/Modules column (`apps/api/`, `apps/worker/`) both point to
a separate app, and that stale doc line has been corrected.

## Blockers

None.

## Known issues

- `GRX-DEVOPS-001` still `IN_REVIEW` — needs a push to confirm a green Actions run.
- `GRX-DOC-003` (Sprint 1 documentation wrap-up) is blocked on `GRX-DEVOPS-001` moving to
  `DONE`, since its dependency is "all Sprint 1 tasks above."
- No dead-letter queue, retry/backoff, or job-state visibility yet — explicitly out of
  Sprint 1 scope per `BACKGROUND_JOB_ARCHITECTURE.md`; will land with the first real
  business job type in Slice 3+.
- Same pre-existing gaps as before: `seed_first_admin` CLI, no
  "list/revoke invitation" endpoints, raw password-reset token exposed in local dev only.

## Current state

`GRX-FOUND-007` was the last `BACKLOG` Sprint 1 task. Every tracked Sprint 1 task is now
`DONE` except `GRX-DEVOPS-001` (built and locally verified, waiting on a push) and
`GRX-DOC-003` (blocked on that same push). No code has been pushed to remote this session.

## Exact next task

No explicit user direction beyond closing out `GRX-FOUND-007`. Nothing is `READY` and
unblocked in the tracker anymore except via pushing to confirm `GRX-DEVOPS-001`. Await
user direction on whether to: (a) push and confirm CI (unblocks `GRX-DOC-003` too), (b)
start Sprint 2 planning, or (c) something else.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
podman compose up -d
```

## Latest commit

`a0a1eea` — feat(worker): RabbitMQ connectivity and worker skeleton (GRX-FOUND-007)
