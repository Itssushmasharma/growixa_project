# Development Readiness

- Document ID: DOC-DEV-READINESS
- Status: ACTIVE
- Version: 2.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [DEFINITION_OF_DONE](DEFINITION_OF_DONE.md), [PROJECT_STATUS](PROJECT_STATUS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [SPRINT_01_FOUNDATION](../14-sprints/SPRINT_01_FOUNDATION.md)

No product feature implementation may begin until every item below is `PASS` for Slice 1
(Sprint 1 — Foundation).

## Readiness gate — Slice 1 (Foundation)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Product vision | Yes | PASS | [PRODUCT_VISION.md](../01-product/PRODUCT_VISION.md) |
| Main PRD | Yes | PASS | [PRD.md](../01-product/PRD.md) |
| MVP scope | Yes | PASS | [MVP_SCOPE.md](../01-product/MVP_SCOPE.md) |
| Architecture baseline | Yes | PASS | [SYSTEM_ARCHITECTURE.md](../04-architecture/SYSTEM_ARCHITECTURE.md) |
| Module boundaries | Yes | PASS | [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md) |
| Background job architecture | Yes (RabbitMQ is in Sprint 1 scope) | PASS | [BACKGROUND_JOB_ARCHITECTURE.md](../04-architecture/BACKGROUND_JOB_ARCHITECTURE.md) |
| Data model baseline | Yes | PASS | [DATA_MODEL.md](../05-data/DATA_MODEL.md), [ERD.md](../05-data/ERD.md), [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) |
| Security baseline | Yes | PASS | [SECURITY_ARCHITECTURE.md](../08-security/SECURITY_ARCHITECTURE.md), [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) |
| Authentication design | Yes | PASS | [AUTHENTICATION.md](../08-security/AUTHENTICATION.md) — implements [DEC-GRX-014](DECISIONS.md) |
| RBAC design | Yes | PASS | [RBAC.md](../08-security/RBAC.md) |
| AI safety baseline | No (no AI feature in Sprint 1) | N/A FOR SPRINT 1 | Interim rules recorded at PRD §23 (GRX-AI-001–007); dedicated `07-ai/AI_SAFETY.md` required before Slice 6, not before Slice 1 |
| Usage-metering strategy | Partial (foundation schema only; not an active Sprint 1 feature) | PASS (foundation) | `usage_records` table defined in [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) per [DEC-GRX-007](DECISIONS.md); no Sprint 1 task consumes it yet — first real writer arrives with a cost-generating feature (Slice 3+) |
| Test strategy | Yes | PASS (distributed, not a standalone doc yet) | Required tests are specified per task in [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) and per criterion in [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) and [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md); a standalone `10-testing/TEST_STRATEGY.md` can be written alongside implementation without blocking start |
| Definition of Done | Yes | PASS | [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) |
| Repository setup | Yes | PASS | Git initialized, `.gitignore`, root `README.md` committed |
| Local environment plan | Yes | PASS (covered by task, not yet a standalone doc) | Docker Compose is itself GRX-FOUND-002 in [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md); `11-devops/LOCAL_DEVELOPMENT.md` can be written as that task's documentation output |
| Project tracker | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) |
| Sprint 1 plan | Yes | PASS | [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md) |
| Relevant decisions logged | Yes | PASS | [DECISIONS.md](DECISIONS.md) — 14 decisions, including [DEC-GRX-014](DECISIONS.md) resolving the one question ([OQ-001](OPEN_QUESTIONS.md)) that blocked Slice 1 |
| Agent execution rules | Yes | PASS | [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md) |

## Overall status: **READY — Slice 1 (Sprint 1: Foundation) may begin**

Every required Slice 1 readiness item is `PASS`. Two items (test strategy, local
environment plan) are satisfied in distributed form rather than as a dedicated document —
that is an acceptable, explicitly logged gap, not a silent one; write the dedicated files
as part of the tasks that implement them (`GRX-TEST-001`/`GRX-TEST-002`, `GRX-FOUND-002`).

**First task cleared to `READY`: `GRX-FOUND-001` — Repository and development tooling.**
See [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md).

## Deliberately still open (per explicit instruction — do not resolve prematurely)

Email provider ([OQ-002](OPEN_QUESTIONS.md)), first social platform ([OQ-003](OPEN_QUESTIONS.md)),
AI provider/model ([OQ-004](OPEN_QUESTIONS.md)), billing provider ([OQ-007](OPEN_QUESTIONS.md)),
production cloud ([OQ-006](OPEN_QUESTIONS.md)), and advanced workflow scope ([OQ-012](OPEN_QUESTIONS.md))
remain open. None of them gate Slice 1. Each becomes a hard blocker only for the slice that
actually needs it (Slice 3, 5, 6, etc. respectively) — do not resolve them early just because
this gate passed.

## Gate for later slices

Slice 2 (Contacts) onward will each need their own readiness pass (data model additions,
feature specs, etc.) before becoming `READY` — this table will be extended per slice rather
than re-litigated from scratch.
