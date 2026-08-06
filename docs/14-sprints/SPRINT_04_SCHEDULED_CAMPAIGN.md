# Sprint 04 — Scheduled Email Campaigns

- Document ID: DOC-SPRINT-04
- Status: ACTIVE (Planning)
- Version: 1.0
- Last updated: 2026-08-06
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [SPRINT_03_EMAIL_CAMPAIGN](SPRINT_03_EMAIL_CAMPAIGN.md), [BACKGROUND_JOB_ARCHITECTURE](../04-architecture/BACKGROUND_JOB_ARCHITECTURE.md)

Sprint 4 is Slice 4 (Scheduled Email Campaigns). It builds upon Slice 3's core email sending pipeline (`email_delivery`, `campaigns`) to add **automated future-scheduled dispatches, RabbitMQ background worker queues, idempotency, exponential backoff retries, cancellation before execution, and Dead-Letter Queue (DLQ) handling**.

---

## 1. Included Scope

Per [MVP_SCOPE.md §C](../01-product/MVP_SCOPE.md) (scheduled dispatches & worker execution):

1. **Campaign Schedule Schema & Migration** (`GRX-SCHED-001`):
   - Extend `campaigns` table with `scheduled_at`, `status` (`DRAFT`, `SCHEDULED`, `DISPATCHING`, `SENT`, `CANCELLED`, `FAILED`), `idempotency_key`, and `cancelled_at`.
   - Migration `4a92b8107c12_scheduled_campaigns_schema.py`.
2. **Campaign Scheduler Ticker & Dispatch Engine** (`GRX-SCHED-002`):
   - Fast, resilient ticker service in `growixa_api.jobs` that queries due campaigns (`scheduled_at <= NOW()` and `status = 'SCHEDULED'`), atomically transitions state to `DISPATCHING`, and publishes dispatch payloads to RabbitMQ queue `grx.campaigns.dispatch`.
3. **RabbitMQ Worker Dispatcher & Batch Processing** (`GRX-SCHED-003`):
   - `apps/worker` consumer that consumes `grx.campaigns.dispatch` jobs, evaluates recipient segments, checks suppression list (`suppression_entries`), and executes dispatches via `email_delivery`.
4. **Idempotency & Retry Engine** (`GRX-SCHED-004`):
   - Redis-backed idempotency check ([redis.py](../04-architecture/SYSTEM_ARCHITECTURE.md)) preventing duplicate dispatches on worker restarts.
   - Exponential backoff retry handler (1m, 5m, 15m) for transient SMTP or network failures.
5. **Campaign Cancellation & Dead-Letter Queue (DLQ)** (`GRX-SCHED-005`):
   - Endpoint `POST /campaigns/{id}/cancel` (permission-gated `campaigns.manage`) to halt scheduled campaigns before execution.
   - RabbitMQ Dead-Letter Queue `grx.campaigns.dlq` for non-retryable or repeatedly failing dispatch jobs.
6. **Automated Scheduler & Worker Integration Tests** (`GRX-SCHED-006`):
   - Integration tests covering scheduled dispatch claims, cancellation, retry backoff, and DLQ message routing.

---

## 2. Task Breakdown & Git Branch Strategy

Every task must be implemented on a dedicated backend feature branch following the project's standard naming convention:

| Task ID | Task Summary | Assigned Branch | Dependencies | Priority |
|---|---|---|---|---|
| `GRX-SCHED-001` | Scheduled campaigns database schema & migration | `feature/BACKEND/GRX-SCHED-001` | `GRX-EMAIL-004` (DONE) | P0 |
| `GRX-SCHED-002` | Campaign scheduler ticker & dispatch publisher | `feature/BACKEND/GRX-SCHED-002` | `GRX-SCHED-001` | P0 |
| `GRX-SCHED-003` | RabbitMQ worker campaign consumer & batch sender | `feature/BACKEND/GRX-SCHED-003` | `GRX-SCHED-002` | P0 |
| `GRX-SCHED-004` | Redis-backed idempotency & exponential backoff retries | `feature/BACKEND/GRX-SCHED-004` | `GRX-SCHED-003` | P0 |
| `GRX-SCHED-005` | Campaign cancellation endpoint & Dead-Letter Queue (DLQ) | `feature/BACKEND/GRX-SCHED-005` | `GRX-SCHED-004` | P0 |
| `GRX-SCHED-006` | Integration tests for scheduler, retry backoff, and DLQ | `feature/BACKEND/GRX-SCHED-006` | `GRX-SCHED-005` | P0 |

---

## 3. Co-Author & Git Commit Guidelines

Every commit across Sprint 4 tasks must query git config and append the co-author trailer:

```text
<type>(<scope>): <summary>

Co-Authored-By: <User Name> <<User Email>>
```
Example:
```text
feat(campaigns): add scheduled_at and cancellation schema (GRX-SCHED-001)

Co-Authored-By: Ravi Kant Yadav <ravikantyadav1918@gmail.com>
```
