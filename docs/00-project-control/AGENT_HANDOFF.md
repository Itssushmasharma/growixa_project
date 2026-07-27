# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-DEVOPS-001` — CI pipeline. Picked immediately after `GRX-FOUND-008` — both
dependencies (`GRX-TEST-001`, `GRX-TEST-002`) were already `DONE` (the tracker still had
it `BACKLOG`, corrected as part of this pick, the same stale-status pattern already
caught for `GRX-FOUND-006` and `GRX-AUTH-004`). This is the highest-value remaining P0:
it locks in every testing investment made this whole session (backend pytest suite,
frontend Vitest/Playwright suite) so future regressions are caught automatically instead
of depending on an agent session remembering to re-run everything by hand.

## Work completed

- **`.github/workflows/ci.yml`** (new): implements all 8 stages from
  `TEST_STRATEGY.md` §CI test stages, across 3 jobs:
  - `backend`: lint (`ruff check`), format check (`ruff format --check`), type check
    (`mypy`), migration check (`alembic upgrade head && alembic check`), tests
    (`pytest`) — against real GitHub Actions service containers for Postgres, Redis, and
    RabbitMQ.
  - `frontend`: lint, format check, type check, unit/component tests (`vitest run`),
    build (`next build`) — independent of `backend`, so it runs in parallel.
  - `e2e`: `needs: [backend, frontend]` — only stands up the real Compose stack
    (`docker compose up postgres redis rabbitmq api`) once the cheaper checks already
    passed, then runs Playwright (which brings its own Next.js instance via
    `playwright.config.ts`'s `webServer` — the `web` container isn't needed here).
- **`apps/web/tests/e2e/{global-setup,global-teardown}.ts`**: made compose-binary-portable
  via a new `COMPOSE_BIN` env var (default `podman`, this project's local dev tool; the
  workflow sets `COMPOSE_BIN=docker`, what GitHub's runners actually have). The identical
  e2e suite now runs unmodified in both environments — no CI-specific test duplication.

## Two deliberate refinements over the literal spec — flagged, not silent

1. **Three jobs instead of one linear pipeline.** `TEST_STRATEGY.md` describes 8 stages
   "executed in this order," which read literally suggests one sequential job. Splitting
   backend/frontend into parallel jobs (both independent stacks) and gating `e2e` on both
   preserves the intent — fail fast, don't waste time on expensive stages after a cheap
   one already failed — while running measurably faster than true linear execution.
2. **Migration check is `alembic check`, not a second upgrade/downgrade round-trip.**
   `TEST_STRATEGY.md`'s required-commands table literally says
   `alembic upgrade head && alembic downgrade base`, but `test_migrations.py` (part of the
   `Tests` step) already does exactly that round-trip. Repeating it as a separate step
   would be pure duplication. `alembic check` instead catches a *different* failure mode
   the round-trip doesn't: a model changed without a matching migration ever being
   generated.

## A real, load-bearing consequence of `GRX-FOUND-006`'s Redis finding

GitHub Actions' `services:` containers are always host-reachable to the job (that's how
GHA services work), unlike this project's local Compose setup where Redis deliberately
has no host port mapping. That means **`tests/test_redis.py` and the rate-limit
integration test, which both skip under local `pytest`, will actually execute for real in
CI** — exactly the outcome anticipated and explicitly written into those tests' skip
messages when they were built. Nothing needed to change in the tests themselves for this
to work.

## Why this is `IN_REVIEW`, not `DONE`

Everything the workflow runs was re-verified locally, command by command (see below), and
the YAML was syntax-checked. But the workflow itself has never actually executed on
GitHub Actions — doing that requires pushing this branch to the remote, and **pushing is
a permission-gated action** this session will not take without the user's explicit
go-ahead. `MASTER_TASK_TRACKER.md`'s own status vocabulary has `IN_REVIEW` for exactly
this situation: work complete and locally verified, final confirmation pending something
outside this session's authority to do unprompted. Move this row to `DONE` once the user
pushes and a run is confirmed green.

## Files changed

- `.github/workflows/ci.yml` (new)
- `apps/web/tests/e2e/global-setup.ts` (`COMPOSE_BIN` parameterization)
- `apps/web/tests/e2e/global-teardown.ts` (`COMPOSE_BIN` parameterization)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-DEVOPS-001` → `IN_REVIEW`,
  evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this
  update)

## Commands executed

```bash
# workflow YAML syntax check
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

cd apps/api
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .
source ../../.env && export DATABASE_URL=... REDIS_URL="redis://localhost:6379/0" RABBITMQ_URL=...
.venv/bin/alembic upgrade head && .venv/bin/alembic check
# -> "No new upgrade operations detected."
.venv/bin/pytest -q   # 45 passed, 2 skipped

cd ../web
npm run lint && npm run format:check && npm run typecheck && npm run test
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build
# -> succeeds; / and /login static, /dashboard dynamic (as expected — it reads cookies)
npm run test:e2e   # 3 passed, with the new COMPOSE_BIN parameterization (default podman)
```

## Test results

Backend: `ruff`/`mypy` clean; `alembic check` clean; `pytest` → 45 passed, 2 skipped
(unchanged documented Redis-unreachable-from-host skips — will not skip in actual CI).
Frontend: `eslint`/`prettier --check`/`tsc --noEmit` clean; Vitest → 1 passed; `next
build` succeeds; Playwright → 3 passed. Workflow YAML is syntactically valid. **Not yet
verified**: an actual GitHub Actions run (see above).

## Migrations

None — no schema changes.

## Decisions

None new. The job-splitting and migration-check refinements above are implementation
judgment calls within `TEST_STRATEGY.md`'s existing, already-agreed spec, not new
architecture decisions.

## Blockers

**Soft blocker on reaching `DONE`**: needs the user to push and confirm a green Actions
run. Not a blocker on any other work — `GRX-COMPANY-002`/`GRX-USER-002` can proceed
independently regardless of when this gets pushed.

## Known issues

- CI workflow is unverified against real GitHub Actions (see above) — the most likely
  failure class if something does go wrong is GHA-specific (action version pinning,
  runner image differences, `docker compose` version quirks) rather than the commands
  themselves, all of which were independently re-verified locally.
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); no "list
  pending invitations"/"revoke invitation" endpoints (`GRX-USER-001`); raw password-reset
  token exposed in local dev only (`GRX-AUTH-005`); icon-mark logo asset has an opaque
  light backdrop that shows against the dark login card (`GRX-FOUND-008`, cosmetic).

## Current state

A complete CI pipeline exists, is committed, and every command it runs has been
independently re-verified locally — it is waiting only on the user's decision to push and
a live Actions run. This completes the ninth step of this session's continuous "most
needed" sequence: `GRX-AUTH-002` → `GRX-AUTH-003` → `GRX-USER-001` → `GRX-AUTH-005` →
`GRX-FOUND-006` → `GRX-AUTH-004` → `GRX-TEST-002` → `GRX-FOUND-008` → `GRX-DEVOPS-001`.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-COMPANY-002` (company
settings screen, frontend) and `GRX-USER-002` (user management screens, frontend) — the
only two Sprint 1 tasks left. Ask the user whether to push and verify CI, or continue
straight into one of these.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`7ff54dc` — ci: GitHub Actions pipeline (GRX-DEVOPS-001)
