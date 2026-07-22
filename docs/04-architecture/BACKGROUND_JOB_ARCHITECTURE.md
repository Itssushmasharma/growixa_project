# Background Job Architecture

- Document ID: DOC-ARCH-JOBS
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [SYSTEM_ARCHITECTURE](SYSTEM_ARCHITECTURE.md), [MODULE_BOUNDARIES](MODULE_BOUNDARIES.md)

## Purpose

Defines the general pattern for asynchronous work in Growixa. Real business workers
(campaign execution, delivery processing, social publishing, AI generation) are built in
Slices 3–6, not Sprint 1 — this document establishes the pattern they will follow so Sprint
1's RabbitMQ connectivity work is built against the right shape from the start.

## Pattern

- **Queue:** RabbitMQ. Each job type gets its own durable queue, named `grx.<module>.<action>`
  (e.g. `grx.email_delivery.send_campaign`, once that module exists).
- **Producer:** A backend API request or scheduler enqueues a job with a unique
  idempotency key, never performs the side-effecting work inline within the HTTP request.
- **Consumer:** A Python worker process consumes from one or more queues, executes the job,
  and acknowledges only after the work (and any DB state change) is durably committed.
- **Idempotency:** Every job carries an idempotency key; a consumer that sees a key it has
  already fully processed must no-op rather than repeat the side effect (critical for
  "don't double-send an email" once `email_delivery` exists).
- **Retry:** Exponential backoff with a maximum retry count per job type. Retries are
  visible in job state, not silent.
- **Dead-letter handling:** A job that exhausts retries moves to a dead-letter queue and
  raises an operator-visible failure, never disappears silently.
- **Observability:** Every job has a unique run ID, structured logs, and timing/outcome
  metrics — an admin must be able to see job state, retries, and failures (PRD §33, AC-13
  equivalent for this platform).

## Sprint 1 scope

Sprint 1 does **not** implement any business job type. It implements only:

- RabbitMQ connectivity from the backend (producer side, unused until a real job exists).
- A worker process skeleton that connects to RabbitMQ and exposes a health check (consumes
  from a `grx.system.healthcheck` queue only).
- The shared job-envelope schema (job ID, idempotency key, type, payload, created_at,
  attempt count) that later job types will reuse — defined once here so Slice 3+ doesn't
  redesign it.

No campaign-execution, delivery, social-publishing, or AI-generation worker logic exists
in Sprint 1 — see [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md) for the
explicit exclusion list.

## Job envelope (shared schema)

| Field | Purpose |
|---|---|
| `job_id` | Unique identifier for this job instance |
| `idempotency_key` | Used to detect and skip duplicate processing |
| `job_type` | Queue/handler routing key, e.g. `grx.system.healthcheck` |
| `payload` | JSON body specific to the job type |
| `created_at` | Enqueue time |
| `attempt_count` | Current retry attempt, for backoff calculation |
| `created_by_user_id` | Ownership field (no `tenant_id`/`workspace_id` — single-tenant, per [DEC-GRX-002](../00-project-control/DECISIONS.md)) |
