# Growixa Documentation

- Document ID: DOC-README
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Product/Architecture (via coding agent)
- Related documents: [PROJECT_STATUS](00-project-control/PROJECT_STATUS.md), [PRD](01-product/PRD.md), [AGENT_EXECUTION_RULES](12-development/AGENT_EXECUTION_RULES.md)

This is the single source of truth for Growixa's product, architecture, and delivery
documentation. Product code must not diverge from what is recorded here without a logged
decision (see [DECISIONS.md](00-project-control/DECISIONS.md)).

## How to use this repository (read this first, every session)

1. Read [`00-project-control/PROJECT_STATUS.md`](00-project-control/PROJECT_STATUS.md) for current state.
2. Read [`00-project-control/MASTER_TASK_TRACKER.md`](00-project-control/MASTER_TASK_TRACKER.md) to find the next `READY` task.
3. Read only the feature/architecture documents relevant to that task — **do not read the whole
   tree for every task**. Use the index below to jump directly to the right file.
4. Follow [`12-development/AGENT_EXECUTION_RULES.md`](12-development/AGENT_EXECUTION_RULES.md) for the required workflow.
5. Update status/changelog files as work completes.

This "read only what's relevant" discipline exists specifically to keep token/context cost
down across sessions — do not load unrelated sections speculatively.

## Folder index

| Folder | Purpose |
|---|---|
| `00-project-control/` | Live project state: status, tracker, risks, decisions, blockers, handoff |
| `01-product/` | Product definition: vision, PRD, scope, personas, roadmap |
| `02-features/` | One document per feature, full spec detail |
| `03-ux-ui/` | Navigation, screens, design system, states |
| `04-architecture/` | System/module architecture, flows, scaling, DR |
| `05-data/` | Data model, ERD, schema, retention, migrations |
| `06-api/` | API standards, endpoint catalog, error model |
| `07-ai/` | AI provider abstraction, prompts, safety, cost tracking |
| `08-security/` | Security architecture, threat model, checklist |
| `09-integrations/` | Email/social provider integration specs |
| `10-testing/` | Test strategy and plans per layer |
| `11-devops/` | Local dev, CI/CD, deployment, observability |
| `12-development/` | Coding standards, repo structure, agent execution rules |
| `13-business/` | Business model, pricing, GTM, support |
| `14-sprints/` | Sprint-by-sprint scope |
| `diagrams/` | Mermaid source files |
| `archive/` | Source discovery material for **deferred future-release** capabilities (SEO/AEO/GEO/website intelligence) — not cancelled, not authoritative for current MVP scope |

## Current document status

Documents are created in phases (see [`AGENT_EXECUTION_RULES.md`](12-development/AGENT_EXECUTION_RULES.md)
for the phase order). This index will be filled in as each phase completes — an empty cell
means the document does not exist yet, not that it was skipped.

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Repository & documentation foundation | MOSTLY DONE (tracker done; matrix/risks/blockers/changelog remain) |
| Phase 1 | Product definition | DONE |
| Phase 2 | Feature specifications | STARTED (catalog stub only; per-feature docs written as each task is picked up) |
| Phase 3 | UX/UI | NOT_STARTED |
| Phase 4 | Architecture | DONE for Slice 1 scope (system, module boundaries, background jobs) |
| Phase 5 | Data and APIs | DATA MODEL DONE for Slice 1; API catalog (`06-api/`) NOT_STARTED |
| Phase 6 | Security and AI | SECURITY DONE for Slice 1; AI safety (`07-ai/`) NOT_STARTED (not needed until Slice 6) |
| Phase 7 | Testing and DevOps | TEST_STRATEGY.md and LOCAL_DEVELOPMENT.md DONE; remaining `10-testing/`/`11-devops/` docs written alongside their owning tasks |
| Phase 8 | Development plan | Sprint 1 plan DONE; remaining sprints NOT_STARTED |

See [`PROJECT_STATUS.md`](00-project-control/PROJECT_STATUS.md) for the authoritative, up-to-date state.
