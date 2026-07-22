# Test Strategy

- Document ID: DOC-TEST-STRATEGY
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [DEFINITION_OF_DONE](../00-project-control/DEFINITION_OF_DONE.md), [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [AUTHENTICATION](../08-security/AUTHENTICATION.md), [RBAC](../08-security/RBAC.md), [THREAT_MODEL](../08-security/THREAT_MODEL.md), [BACKGROUND_JOB_ARCHITECTURE](../04-architecture/BACKGROUND_JOB_ARCHITECTURE.md)

This document previously existed only in distributed form (per-task rows in
`MASTER_TASK_TRACKER.md` and the criteria in `DEFINITION_OF_DONE.md`). This is now the
single standalone reference; the distributed detail still applies but must not contradict
this document — if it ever does, this document wins and the other is corrected.

## Test pyramid

```text
        /\
       /  \    E2E smoke tests (few) — real browser against the full Docker Compose stack
      /----\
     /      \  API integration tests (moderate) — real Postgres/Redis/RabbitMQ, real HTTP
    /--------\
   /          \ Unit tests (many) — services/domain logic, no network, no real DB
  /------------\
```

Most coverage lives at the unit level. Integration tests exist for anything that crosses a
real boundary (DB, Redis, RabbitMQ, HTTP). E2E tests exist only for the handful of flows
that must be proven to work end-to-end through the real UI (login, a protected action, a
permission-denied case) — not for every screen.

## Backend unit-test approach

- Framework: `pytest`.
- Scope: `services/` and `domain/` logic in isolation. Repositories are exercised through
  integration tests, not mocked-and-unit-tested, since their entire job is talking to
  Postgres — a mocked repository test proves nothing about the SQL being correct.
- External calls (future email/social/AI providers) are mocked at the adapter boundary
  only, never by mocking internal application code.
- Fast: the full unit suite must run without a database, Redis, or RabbitMQ connection.

## API integration-test approach

- Framework: `pytest` + `httpx`'s async test client against the real FastAPI app.
- Backing services: a real (test) PostgreSQL database, migrated fresh per test run or per
  test class via transactional rollback; real Redis for rate-limit tests where relevant.
- Scope: request → router → service → repository → DB → response, including status codes,
  response schema, and actual persisted state — not just the status code (see
  [§Rules preventing shallow tests](#rules-preventing-tasks-from-being-marked-done-with-shallow-tests) below).
- Each protected endpoint has at minimum: one authorized-success case, one
  wrong-permission-403 case, and one unauthenticated-401 case.

## Database migration tests

- Every Alembic migration must be exercised by: `alembic upgrade head` from empty, and
  `alembic downgrade base` back to empty, both against a disposable test database, as part
  of CI (see [§CI test stages](#ci-test-stages)).
- A migration that cannot downgrade cleanly is not acceptable unless explicitly justified
  and logged (e.g. an irreversible data migration) — the default is reversible.
- Seed-data migrations (roles/permissions) are verified by a test that asserts the expected
  seed rows exist after `upgrade head`.

## Authentication and refresh-token tests

Required cases (backing [AUTHENTICATION.md](../08-security/AUTHENTICATION.md)):

- Successful login issues valid access + refresh cookies and records `last_login_at`.
- Failed login (wrong password, unknown email) returns the same generic error in both
  cases and does not leak which one occurred (T11 in [THREAT_MODEL.md](../08-security/THREAT_MODEL.md)).
- Refresh-token rotation: using a refresh token issues a new one and invalidates the old one.
- Refresh-token reuse detection: presenting an already-rotated (old) refresh token revokes
  the entire token chain for that user.
- Logout revokes the presented refresh token.
- Logout-all-sessions revokes every refresh token for the user.
- Disabling a user's account revokes their existing refresh tokens and blocks further login.
- Password reset: request issues a single-use hashed token; completion rejects an
  expired/used/invalid token; successful completion revokes all existing sessions.
- Invitation: acceptance rejects an expired/used/invalid token; successful acceptance
  creates the user with the assigned role and marks the invitation accepted.
- Every case above that is expected to emit an audit event is asserted to have done so
  (see [§Audit-log tests](#audit-log-tests)).

## RBAC authorization tests

- For every permission code in [RBAC.md](../08-security/RBAC.md), at least one test proves
  a role that should have it succeeds, and at least one test proves a role that should not
  have it receives `403`.
- A dedicated negative test proves the centralized `require_permission()` dependency is
  actually attached to every non-public route — e.g. by asserting no route is reachable
  without either an explicit permission requirement or an explicit "public route" allowlist
  entry, so a future route can't accidentally ship unprotected.

## Audit-log tests

- Each Sprint 1 audit event (`user.login`, `user.login_failed`, `user.logout`,
  `user.password_reset_requested`, `user.password_reset_completed`, `invitation.accepted`,
  `role.changed`, `session.revoked`) has a test asserting it is written with the correct
  `actor_user_id`, `action`, `entity_type`/`entity_id`, and that no sensitive field
  (password, token) appears in `metadata`.
- A test asserts there is no application code path that updates or deletes an existing
  `audit_logs` row (insert-only).

## Redis rate-limit tests

- A test drives login attempts past the configured threshold and asserts a `429` response,
  then asserts a request from a different key (different email/IP combination) is
  unaffected.
- A test asserts the rate-limit window/counter actually lives in Redis (not in-process
  memory), so it holds correctly across multiple backend worker processes.
- Same coverage applied to the password-reset-request endpoint (T12 in [THREAT_MODEL.md](../08-security/THREAT_MODEL.md)).

## RabbitMQ health-job tests

- An integration test publishes a message to the `grx.system.healthcheck` queue and asserts
  the worker consumes and acknowledges it.
- A test asserts the shared job envelope fields (job_id, idempotency_key, job_type,
  payload, created_at, attempt_count) round-trip correctly through publish → consume.
- No retry/dead-letter test is required yet in Sprint 1 since no failure-prone business job
  exists — that coverage is added when the first real job type is (Slice 3+).

## Frontend component tests

- Framework: component-level tests for the dashboard shell, login form, and company
  settings form (once built) — assert rendering, validation messages, and API-call
  triggering with a mocked API client, not real network calls.
- A component test for a protected layout asserts an unauthenticated state redirects to
  login rather than rendering protected content.

## End-to-end smoke tests

Kept deliberately small in Sprint 1 — a handful of flows through the real Docker Compose
stack and a real browser driver:

1. Load the app, get redirected to login when unauthenticated.
2. Log in with a seeded admin, land on the dashboard shell.
3. Invite a user, accept the invitation, log in as the new user.
4. Attempt an admin-only action as a Viewer-role user and confirm it is blocked in the UI
   and would be blocked server-side even if attempted directly.
5. Save company settings and confirm they persist after reload.

## Security-critical test cases

These map directly to [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) and must exist
before the corresponding feature is marked `DONE`, not added later as a follow-up:

| Threat | Required test |
|---|---|
| T1/T12 Credential stuffing / reset flooding | Rate-limit tests above |
| T2 Session hijacking via token theft | Test asserting tokens are set as HttpOnly cookies, never present in any JSON response body |
| T3 CSRF | Test asserting a state-changing request without the expected CSRF/origin check is rejected |
| T4 Refresh-token replay | Reuse-detection test above |
| T5 RBAC bypass | Negative permission tests above |
| T6 Token guessing | Test asserting reset/invite tokens are high-entropy and stored hashed, never retrievable in plaintext via any API |
| T7 Secret leakage in logs | Test asserting a log-capturing fixture never contains `password_hash`/`token_hash` literals after a login/reset flow |
| T9 SQL injection | Test asserting a crafted string in a search/filter field is treated as data, not executed (covered implicitly by ORM use, verified by one explicit adversarial-input test) |
| T10 Audit log tampering | Insert-only test above |
| T11 Enumeration via error messages | Generic-error test above |

## Required test commands

| Layer | Command (run from the relevant app directory) |
|---|---|
| Backend lint | `ruff check .` |
| Backend format check | `ruff format --check .` |
| Backend type check | `mypy .` |
| Backend unit + integration tests | `pytest` |
| Backend migration check | `alembic upgrade head && alembic downgrade base` against a disposable test DB |
| Frontend lint | `npm run lint` |
| Frontend format check | `npm run format:check` |
| Frontend type check | `npm run typecheck` (`tsc --noEmit`) |
| Frontend unit/component tests | `npm run test` |
| Frontend build | `npm run build` |
| E2E smoke tests | `npm run test:e2e` (or equivalent), run against the Docker Compose stack |

Exact package-script names are finalized when `GRX-FOUND-001` scaffolds each app's tooling
config — this table is the contract those scripts must satisfy.

## Minimum pass criteria

A task cannot be marked `DONE` (per [DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md))
unless, for everything the task touches:

- Lint, format check, and type check all pass with zero errors.
- All unit and integration tests pass, including the negative/security cases listed above
  where applicable to that task.
- Any new or changed Alembic migration passes the upgrade/downgrade check.
- No test was skipped, marked `xfail`, or commented out to make the suite pass.

## CI test stages

Executed in this order on every PR (see `GRX-DEVOPS-001` in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)):

1. Lint (backend + frontend)
2. Format check (backend + frontend)
3. Type check (backend + frontend)
4. Migration check (upgrade + downgrade against a disposable DB)
5. Backend unit + integration tests
6. Frontend unit/component tests
7. Frontend build
8. E2E smoke tests (may run on a reduced schedule once the suite grows beyond Sprint 1, but
   run on every PR while the suite is still small)

CI fails fast on the first failing stage; all stages must be green for a PR to merge.

## Test evidence format

Every task entry in `MASTER_TASK_TRACKER.md` records, in its `Evidence` column: the commit
hash, the exact commands run, and a one-line pass/fail summary per command (e.g.
`ruff check . -> 0 errors`, `pytest -> 14 passed`). `AGENT_HANDOFF.md` carries the same
evidence forward at the end of each work session so the next session doesn't have to
re-derive whether something was actually verified.

## Rules preventing tasks from being marked done with shallow tests

- A test that only asserts an HTTP status code (e.g. "returns 200") without asserting
  response body shape or actual persisted database state does not satisfy this strategy —
  see [DEFINITION_OF_DONE.md §No placeholder completion](../00-project-control/DEFINITION_OF_DONE.md#no-placeholder-completion).
- A test against a mocked repository/service that never touches the real database does not
  satisfy an *integration*-test requirement — it may supplement, never replace, the real-DB test.
- A "happy path only" test suite does not satisfy any row in
  [§Security-critical test cases](#security-critical-test-cases) — the negative case is the
  point of that row, not optional bonus coverage.
- A skipped, `xfail`-marked, or commented-out test is treated as a failing test for
  `DONE` purposes, not as passing.
- Coverage percentage alone is not evidence of correctness — a task reviewer (human or
  agent) must be able to see *which* required case each test covers, matched against the
  lists in this document.
