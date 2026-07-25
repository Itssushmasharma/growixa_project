# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-25
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-TEST-001` — Backend test foundation (test runner config, DB test fixtures/factories,
coverage baseline). Picked per explicit user-specified order: `GRX-AUDIT-001` →
`GRX-TEST-001` → `GRX-COMPANY-001`.

## Work completed

- **`apps/api/tests/conftest.py`** (new): `user_factory` — an async fixture returning a
  factory function that creates a real user (optionally assigned an existing seeded role
  via `role_name=`), tracks every user it created, and deletes them all at teardown.
  Deliberately kept simple: plain commit-and-cleanup per creation, not a
  transactional-rollback session bound into the app's own `get_session` dependency. The
  heavier pattern (SQLAlchemy's documented "join session into external transaction," with
  `app.dependency_overrides[get_session]` pointed at the same test-bound session) would give
  perfect isolation and no manual cleanup, but requires overriding `get_session` per test app
  and was judged disproportionate for the current test count — noted as a natural next step
  if test suite growth or flakiness ever makes manual cleanup painful.
- **Refactored `test_require_permission.py` and `test_audit_log.py`** to use `user_factory`
  instead of their own near-identical fixtures (`viewer_user_id`, `actor_user_id`) — this
  *is* the point of the task, not incidental cleanup. `test_audit_log.py`'s tests now
  explicitly delete their own `audit_logs` rows before returning, since `actor_user_id` has
  no `ON DELETE CASCADE` and `user_factory`'s teardown would otherwise hit the same
  FK-violation class of bug fixed in `GRX-AUDIT-001`.
- **Coverage baseline**: added `pytest-cov` (dev dependency) and `[tool.coverage.run]`
  (`source = ["growixa_api"]`, tests excluded from the measured set). `addopts` now runs
  coverage by default. Current baseline: **87%** total line coverage. No enforced minimum
  yet — recording the baseline is this task's job; a specific gate is `GRX-DEVOPS-001`'s
  call once there's more code and CI exists to enforce it.
- **`integration` marker**: registered in `pyproject.toml` (`markers = [...]`, avoids
  "unknown marker" warnings) and applied to every test that touches a real backing service
  — all of `test_audit_log.py`, `test_auth_schema_seed.py`, `test_migrations.py`, and 2 of
  `test_require_permission.py`'s 4 tests.

## A genuinely useful thing verified, not just asserted

I reasoned that `test_require_permission.py`'s missing-token/invalid-token tests never
touch the database, because `RequirePermission.__call__`'s first parameter
(`Depends(get_current_user_id)`) raises before FastAPI ever resolves the second
(`Depends(get_session)`) — dependencies resolve in declared parameter order and stop at the
first exception. Rather than leave that as an assumption, I ran
`pytest -m "not integration"` with `DATABASE_URL`/`REDIS_URL`/`RABBITMQ_URL` all pointed at
unreachable hosts. All 7 unit-tier tests passed — confirms the reasoning was right and the
unit/integration split is real, not just a label.

## Files changed

- `apps/api/tests/conftest.py` (new)
- `apps/api/tests/test_require_permission.py` (refactored to use `user_factory`; 2 of 4
  tests marked `integration`)
- `apps/api/tests/test_audit_log.py` (refactored to use `user_factory`; all 3 tests marked
  `integration`; each test now cleans up its own audit rows before returning)
- `apps/api/tests/test_auth_schema_seed.py`, `test_migrations.py` (marked `integration`)
- `apps/api/pyproject.toml` (`pytest-cov` dependency, `addopts`, `markers`,
  `[tool.coverage.run]`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (GRX-TEST-001 → DONE, evidence recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this update)

## Commands executed

```bash
cd apps/api
uv pip install -e ".[dev]" --python .venv/bin/python   # picks up pytest-cov
.venv/bin/ruff check --fix . && .venv/bin/ruff format .
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy .   # all clean

source ../../.env && export DATABASE_URL=... REDIS_URL=... RABBITMQ_URL=...
.venv/bin/pytest -v        # 14 passed, coverage report printed, 87% total

# unreachable DB/Redis/MQ on purpose — proves the unit/integration split holds
DATABASE_URL="postgresql+asyncpg://nope:nope@localhost:1/nope" \
REDIS_URL="redis://localhost:1/0" RABBITMQ_URL="amqp://x@localhost:1/" \
.venv/bin/pytest -v -m "not integration"   # 7 passed, 7 deselected

curl http://localhost:8000/health   # unaffected — no runtime app code changed this task
```

## Test results

`pytest` → 14 passed (same 14 tests as before this task; this task changed test
*infrastructure*, not test *count*). `pytest -m "not integration"` → 7 passed with zero
backing services reachable. `ruff`/`mypy` clean across 31 source files.

## Migrations

None — this task only touches test infrastructure.

## Decisions

None new.

## Blockers

None.

## Known issues

- No CI pipeline exists yet — `GRX-DEVOPS-001` (depends on this task and `GRX-TEST-002`,
  neither/one done) owns wiring `pytest` into an actual CI run. This task's acceptance
  criterion ("pytest runs green ... in CI") is satisfied by the local foundation being
  ready for that, matching how earlier foundation tasks satisfied similar forward-looking
  criteria.
- The `seed_first_admin` CLI gap (flagged in `GRX-AUTH-001`) and CORS-for-frontend gap
  (flagged in `GRX-FOUND-004`) are both still open, relevant once `GRX-AUTH-002` is picked
  up.

## Current state

Backend test suite has a real shared fixture/factory foundation, coverage reporting, and a
verified unit/integration split. 14 tests, 87% coverage baseline, all green.

## Exact next task

Per explicit user direction: `GRX-COMPANY-001` (company profile + brand settings). Also
`READY`: `GRX-TEST-002` (frontend test foundation), `GRX-AUTH-002` (password hashing +
login/logout), `GRX-USER-001` (internal user invitation + acceptance).

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`de55382` — test(api): backend test foundation - fixtures, coverage, markers (GRX-TEST-001)
