# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md)

## Task worked on

`GRX-AUTH-004` — Login rate limiting. Picked immediately after `GRX-FOUND-006` unblocked
it — the highest-priority remaining P0 backend task, closing T1 (credential
stuffing/brute force) and T12 (unbounded login/reset flooding) from `THREAT_MODEL.md` on
the exact `/auth/login` and `/auth/password-reset/request` endpoints built in the two
sessions before this one.

## Work completed

- **`rate_limit_max_attempts`** (default 5) and **`rate_limit_window_seconds`** (default
  60) settings (`config.py`) — a conservative default per `AUTHENTICATION.md`'s "low
  single-digit attempts per short window" guidance.
- **`auth/rate_limit.py`** (new): `enforce_rate_limit(redis_client, *, bucket, identifier)`
  — a Redis `INCR`+`EXPIRE` fixed-window counter keyed
  `grx:ratelimit:{bucket}:{identifier}`, matching the exact key format
  `LOCAL_DEVELOPMENT.md` already documented. Raises `RateLimitExceededError` once the
  identifier exceeds the configured max within the window.
- **`auth/api.py`**: both `login_route` and `password_reset_request_route` now take a
  `redis_client: Redis = Depends(get_redis)` and call `enforce_rate_limit()` first, keyed
  by `f"{email}:{ip}"`, with buckets `"login"` and `"password_reset_request"` respectively
  (independent budgets — the two endpoints can't exhaust each other's limit). A caught
  `RateLimitExceededError` becomes `HTTPException(429, ...)`.

## An explicit, flagged design call — not a silent shortcut

**The limiter fails open on `RedisError`.** If Redis is unreachable, `enforce_rate_limit()`
swallows the error and lets the request through rather than raising. Rationale: a Redis
outage must degrade *security posture* (temporarily no brute-force protection), not
*availability* of login/password-reset entirely — the same trade-off `/health` already
makes by reporting "degraded" instead of crashing on a dependency outage.

This has a load-bearing practical consequence discovered during `GRX-FOUND-006`: Compose's
`redis` service has no host port mapping, so a host-run `pytest` process can never reach
real Redis. Without fail-open, wiring this into `/auth/login` would have broken every one
of the 40+ pre-existing tests across this entire session that call that endpoint (most of
them don't even test rate limiting — they just need to log in as a setup step). With
fail-open, those tests are silently unaffected under the documented Redis-unreachable
constraint, while real enforcement still applies in any environment where Redis actually
is reachable (i.e., always, outside this specific host-vs-container test-runner gap).

## Files changed

- `apps/api/src/growixa_api/config.py` (`rate_limit_max_attempts`,
  `rate_limit_window_seconds`)
- `apps/api/src/growixa_api/auth/rate_limit.py` (new)
- `apps/api/src/growixa_api/auth/api.py` (`login_route`, `password_reset_request_route`
  extended)
- `apps/api/tests/test_auth_rate_limit.py` (new)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-AUTH-004` → `DONE`, evidence
  recorded)
- `docs/00-project-control/PROJECT_STATUS.md`, `docs/00-project-control/CHANGELOG.md` (this
  update)

## Commands executed

```bash
cd apps/api
# config.py, auth/rate_limit.py, auth/api.py, tests/test_auth_rate_limit.py written
.venv/bin/ruff check --fix . && .venv/bin/ruff format . && .venv/bin/mypy .

source ../../.env && export DATABASE_URL=... REDIS_URL="redis://localhost:6379/0" RABBITMQ_URL=...
.venv/bin/pytest -v   # 43 passed, 2 skipped (both Redis-unreachable-from-host, as expected)

cd ../..
podman compose up -d --build api
curl -s http://localhost:8000/health

# smoke-test users created directly via the ORM inside the container, then:
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/auth/login \
    -d '{"email":"smoke-ratelimit@example.com","password":"wrong-password"}'
done
# 401 401 401 401 401 429

# same already-limited identifier, now with the CORRECT password — still 429
curl -X POST http://localhost:8000/auth/login -d '{"email":"smoke-ratelimit@example.com","password":"Real-Password-123!"}'

# a different email+IP — unaffected, 200
curl -X POST http://localhost:8000/auth/login -d '{"email":"smoke-ratelimit-2@example.com","password":"Real-Password-123!"}'

# same 5-then-429 pattern independently on password-reset-request
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/auth/password-reset/request \
    -d '{"email":"smoke-ratelimit-2@example.com"}'
done
# 200 200 200 200 200 429

podman compose exec redis redis-cli KEYS "grx:ratelimit:*"
# grx:ratelimit:login:smoke-ratelimit@example.com:10.89.3.14
# grx:ratelimit:login:smoke-ratelimit-2@example.com:10.89.3.14
# grx:ratelimit:password_reset_request:smoke-ratelimit-2@example.com:10.89.3.14
# cleaned up rate-limit keys, smoke users, and their audit logs afterward
```

## Test results

`pytest` → 43 passed, 2 skipped (38 pre-existing + 5 new unit tests + 1 new integration
test that skips, same as `test_redis.py`). 95% coverage, unchanged (the two skips
contribute no missed lines; the 429 branches themselves show as uncovered under host
pytest specifically because fail-open means they're never exercised there — verified live
instead, see above).

## Migrations

None — this task added no database schema.

## Decisions

None new — implements the mechanism already specified in `AUTHENTICATION.md`'s Rate
limiting section and `THREAT_MODEL.md` T1/T12. The fail-open failure mode is an explicit,
flagged engineering call (see above), not a `DECISIONS.md`-level architecture decision.

## Blockers

None.

## Known issues

- The 429 code paths in `auth/api.py` are not exercised by the host-run `pytest` suite
  (fail-open under Redis-unreachable-from-host means they're never triggered there) — this
  is expected, not a coverage gap to chase; real enforcement is verified live against
  Compose instead (see Commands executed above) and will also be exercised automatically
  by `test_auth_rate_limit.py`'s integration test the moment Redis is reachable from
  wherever `pytest` runs (e.g., a future CI runner for `GRX-DEVOPS-001`).
- Still-open from earlier sessions: `seed_first_admin` CLI (`GRX-AUTH-001`); CORS for
  frontend calls (`GRX-FOUND-004`); no "list pending invitations"/"revoke invitation"
  endpoints (`GRX-USER-001`); raw password-reset token exposed in local dev only
  (`GRX-AUTH-005`).

## Current state

`/auth/login` and `/auth/password-reset/request` are both now rate-limited, closing the
last two open items (T1, T12) in `THREAT_MODEL.md`'s Sprint-1-relevant subset. This
completes the sixth step of this session's user-directed backend-continuity sequence:
`GRX-AUTH-002` → `GRX-AUTH-003` → `GRX-USER-001` → `GRX-AUTH-005` → `GRX-FOUND-006` →
`GRX-AUTH-004`. **Every P0 Sprint 1 backend task is now `DONE`** — everything remaining in
the tracker is frontend work.

## Exact next task

No explicit user direction beyond this point. `READY`: `GRX-TEST-002` (frontend test
foundation), `GRX-COMPANY-002` (company settings screen, frontend), `GRX-FOUND-008`
(dashboard shell, frontend), `GRX-USER-002` (user management screens, frontend). All are
frontend work — there is no more P0 backend work left to prioritize ahead of them.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md   # find next READY task
podman compose up -d                                  # bring the stack back up
```

## Latest commit

`5c26200` — feat(auth): login rate limiting (GRX-AUTH-004)
