# Development Readiness

- Document ID: DOC-DEV-READINESS
- Status: ACTIVE
- Version: 7.0
- Last updated: 2026-08-07
- Owner: Coding agent
- Related documents: [DEFINITION_OF_DONE](DEFINITION_OF_DONE.md), [PROJECT_STATUS](PROJECT_STATUS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [SPRINT_01_FOUNDATION](../14-sprints/SPRINT_01_FOUNDATION.md), [SPRINT_02_CONTACTS](../14-sprints/SPRINT_02_CONTACTS.md), [SPRINT_03_EMAIL_CAMPAIGN](../14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md), [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md)

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
| Test strategy | Yes | PASS | [TEST_STRATEGY.md](../10-testing/TEST_STRATEGY.md) — standalone document |
| Definition of Done | Yes | PASS | [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) |
| Repository setup | Yes | PASS | Git initialized, `.gitignore`, root `README.md` committed |
| Local environment plan | Yes | PASS | [LOCAL_DEVELOPMENT.md](../11-devops/LOCAL_DEVELOPMENT.md) — standalone document |
| Project tracker | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) |
| Sprint 1 plan | Yes | PASS | [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md) |
| Relevant decisions logged | Yes | PASS | [DECISIONS.md](DECISIONS.md) — 14 decisions, including [DEC-GRX-014](DECISIONS.md) resolving the one question ([OQ-001](OPEN_QUESTIONS.md)) that blocked Slice 1 |
| Agent execution rules | Yes | PASS | [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md) |

## Overall status: **READY — all mandatory Slice 1 gates PASS, no distributed-only gaps remain**

Every required Slice 1 readiness item is `PASS` as a standalone document. This closes the
two previously-logged gaps (test strategy, local environment plan) — both now exist at
[`10-testing/TEST_STRATEGY.md`](../10-testing/TEST_STRATEGY.md) and
[`11-devops/LOCAL_DEVELOPMENT.md`](../11-devops/LOCAL_DEVELOPMENT.md) respectively, matching
the master documentation standard in full for Slice 1 scope.

**First task cleared to `READY`: `GRX-FOUND-001` — Repository and development tooling.**
See [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md).

## Deliberately still open (per explicit instruction — do not resolve prematurely)

Email provider ([OQ-002](OPEN_QUESTIONS.md), since **resolved** — see the Slice 3 gate
below), first social platform ([OQ-003](OPEN_QUESTIONS.md)), AI provider/model
([OQ-004](OPEN_QUESTIONS.md)), billing provider ([OQ-007](OPEN_QUESTIONS.md)), production
cloud ([OQ-006](OPEN_QUESTIONS.md)), and advanced workflow scope
([OQ-012](OPEN_QUESTIONS.md)) were all open at Slice 1's gate. None of them gated Slice 1.
Each becomes a hard blocker only for the slice that actually needs it (Slice 3, 5, 6, etc.
respectively) — this snapshot is preserved as a record of what Slice 1's gate deliberately
left open, not a live status (see [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) for current
status).

## Readiness gate — Slice 2 (Contacts)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Data model additions | Yes | PASS | [DATA_MODEL.md §Slice 2 entities](../05-data/DATA_MODEL.md#slice-2-entities-full-detail), [DATABASE_SCHEMA.md §Slice 2](../05-data/DATABASE_SCHEMA.md#slice-2-contacts-tables), [ERD.md §Slice 2 additions](../05-data/ERD.md#slice-2-contacts-additions) |
| RBAC additions | Yes | PASS | [RBAC.md §Slice 2](../08-security/RBAC.md#slice-2-permission-codes) — `contacts.manage`, `contacts.view` |
| Sprint 2 plan | Yes | PASS | [SPRINT_02_CONTACTS.md](../14-sprints/SPRINT_02_CONTACTS.md) |
| Feature specs (`CONTACT_MANAGEMENT.md`, `CONTACT_IMPORT.md`, `CONTACT_TAGS.md`, `SEGMENTATION.md`, `SUPPRESSION_AND_CONSENT.md`) | No (written per-task, not upfront — same practice as Sprint 1) | DEFERRED TO EACH TASK | [FEATURE_CATALOG.md](../02-features/FEATURE_CATALOG.md) |
| Project tracker rows | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) — `GRX-CONTACT-*` |
| AI safety baseline | No (no AI feature in Slice 2) | N/A FOR SLICE 2 | — |
| Email/social/billing provider decisions | No (not needed until Slice 3/5) | N/A FOR SLICE 2 | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |

**Overall status: READY — first task cleared: `GRX-CONTACT-001` (contacts schema + CRUD).**
Mirrors Slice 1's gate structure rather than re-litigating documentation standards from
scratch; only genuinely new items (data model, RBAC, sprint plan) needed a fresh pass.

## Readiness gate — Slice 3 (First Email Campaign)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Email provider decision (OQ-002) | Yes — this is the item Slice 2's gate flagged as deferred, not N/A | PASS | [DECISIONS.md §DEC-GRX-015](DECISIONS.md) — Postmark, via its SMTP relay endpoint |
| Data model additions | Yes | PASS | [DATA_MODEL.md §Slice 3 entities](../05-data/DATA_MODEL.md#slice-3-entities-full-detail), [DATABASE_SCHEMA.md §Slice 3](../05-data/DATABASE_SCHEMA.md#slice-3-email-marketing-tables), [ERD.md §Slice 3 additions](../05-data/ERD.md#slice-3-email-marketing-additions) |
| RBAC additions | Yes | PASS | [RBAC.md §Slice 3](../08-security/RBAC.md#slice-3-permission-codes) — `integrations.manage`, `campaigns.manage`, `campaigns.send`, `campaigns.view` |
| Threat model addendum | Yes (new external surface: credential storage, outbound sending, inbound webhooks) | PASS | [THREAT_MODEL.md §Slice 3](../08-security/THREAT_MODEL.md#slice-3-email-marketing-scope) — T13–T19 |
| Sprint 3 plan | Yes | PASS | [SPRINT_03_EMAIL_CAMPAIGN.md](../14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md) |
| Feature specs (`EMAIL_PROVIDERS.md`, `EMAIL_TEMPLATES.md`, `EMAIL_CAMPAIGNS.md`) | No (written per-task, not upfront — same practice as Sprints 1–2) | DEFERRED TO EACH TASK | [FEATURE_CATALOG.md](../02-features/FEATURE_CATALOG.md) |
| Project tracker rows | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) — `GRX-EMAIL-*` |
| AI safety baseline | No (no AI feature in Slice 3) | N/A FOR SLICE 3 | — |
| Social/billing provider decisions (OQ-003, OQ-007) | No (not needed until Slice 5) | N/A FOR SLICE 3 | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |
| Email template editor choice (OQ-009) | No — narrower than a slice-entry blocker; only the specific template-editor task needs it | DEFERRED TO THAT TASK | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |

**Overall status: READY — first task cleared: `GRX-EMAIL-001` (email provider connection +
sender identity).** The one genuinely new prerequisite versus Slice 1/2's gate structure
was OQ-002 itself — every other item follows the same per-slice pattern (data model,
RBAC, threat model, sprint plan).

## Readiness gate — Sprint 5 Phase B (Platform auth boundary, `GRX-SAAS-002`)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Phase A dependency | Yes — nothing in Phases B–E may begin before Phase A is `DONE` and independently verified, per `SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md`'s own sequencing rule | PASS | `GRX-SAAS-001` marked `DONE` in [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md); full apps/api + apps/worker suites green, live-verified against the rebuilt Compose container |
| Data model additions | Yes | PASS | [DATA_MODEL.md §Sprint 5 Phase B entities](../05-data/DATA_MODEL.md#sprint-5-phase-b-entities-customer-account-platform--platform-auth-boundary-full-detail), [DATABASE_SCHEMA.md §Sprint 5 Phase B](../05-data/DATABASE_SCHEMA.md#sprint-5-phase-b-platform-auth-boundary-tables), [ERD.md §Sprint 5 Phase B additions](../05-data/ERD.md#sprint-5-phase-b-platform-auth-boundary-additions) |
| Platform admin schema shape decision | Yes — the sprint doc's own wording ("mirrors `users`... a `platform_permissions`/`platform_role_permissions` pair") was intentionally not fully spelled out | PASS | [DECISIONS.md §DEC-GRX-018](DECISIONS.md) — single `role` column on `platform_admins`, not a `platform_roles` many-to-many join |
| RBAC additions | Yes | PASS | [RBAC.md §Sprint 5 Phase B](../08-security/RBAC.md#sprint-5-phase-b--platform-level-roles-separate-namespace-grx-saas-002) — separate `platform.*` namespace, `platform.access` permission code, `require_platform_permission` enforcement rule |
| Threat model addendum | Yes (new external surface: a second identity class, a second auth boundary, cross-boundary session-confusion risk) | PASS | [THREAT_MODEL.md §Sprint 5 Phase B](../08-security/THREAT_MODEL.md#sprint-5-phase-b-platform-auth-boundary-scope) — T20–T24 |
| Sprint plan | Yes | PASS | [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase B](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-b--platform-auth-boundary-grx-saas-002) |
| Feature specs | No (written per-task, not upfront — same practice as every prior slice/sprint) | DEFERRED TO EACH TASK | — |
| Project tracker row | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) — `GRX-SAAS-002` |
| AI safety baseline | No (no AI feature in Phase B) | N/A FOR PHASE B | — |
| Email/social/billing provider decisions | No (not needed until Phase C/D) | N/A FOR PHASE B | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |

**Overall status: READY — `GRX-SAAS-002` cleared to `READY` in `MASTER_TASK_TRACKER.md`.**
The one genuinely new prerequisite versus Slice 1/2/3's gate structure was the platform
admin schema shape itself (DEC-GRX-018) — everything else follows the same per-slice
pattern (data model, RBAC, threat model, sprint plan) this document already establishes.

## Readiness gate — Sprint 5 Phase C (Self-service registration, `GRX-SAAS-003`)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Phase A dependency | Yes — Phase C depends only on `GRX-SAAS-001`, not Phase B (the two proceed in parallel per the sprint's own dependency graph) | PASS | `GRX-SAAS-001` marked `DONE` |
| Owner role / plan-slug / verification-gate design decisions | Yes — the sprint doc's own wording ("a `customer.owner` user," "plan selection") left the exact shape unspecified | PASS | [DECISIONS.md §DEC-GRX-019](DECISIONS.md) — existing `Super Admin` role reused, `selected_plan_slug` text column (no plans table yet), verification via a third `users.status` value |
| Data model additions | Yes | PASS | [DATA_MODEL.md §Sprint 5 Phase C entities](../05-data/DATA_MODEL.md#sprint-5-phase-c-entities-customer-account-platform--self-service-registration-full-detail), [DATABASE_SCHEMA.md §Sprint 5 Phase C](../05-data/DATABASE_SCHEMA.md#sprint-5-phase-c-self-service-registration-tables), [ERD.md §Sprint 5 Phase C additions](../05-data/ERD.md#sprint-5-phase-c-self-service-registration-additions) |
| RBAC additions | No — register/verify-email are public routes, identity comes from the credential/token itself, same shape as `/auth/login`/`/users/invitations/accept`; no new permission code needed | N/A FOR PHASE C | [RBAC.md](../08-security/RBAC.md)'s existing enforcement rule already covers this shape |
| Threat model addendum | Yes (new external surface: the first fully public write path — anyone can create an account) | PASS | [THREAT_MODEL.md §Sprint 5 Phase C](../08-security/THREAT_MODEL.md#sprint-5-phase-c-self-service-registration-scope) — T25–T29 |
| Sprint plan | Yes | PASS | [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase C](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-c--self-service-registration-grx-saas-003) |
| Feature specs | No (written per-task, not upfront — same practice as every prior slice/sprint) | DEFERRED TO EACH TASK | — |
| Project tracker row | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) — `GRX-SAAS-003` |
| AI safety baseline | No (no AI feature in Phase C) | N/A FOR PHASE C | — |
| Billing provider decision (OQ-007) | No (Phase C only records a plan choice; enforcement/payment is Phase D) | N/A FOR PHASE C | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |

**Overall status: READY — `GRX-SAAS-003` cleared to `READY` in `MASTER_TASK_TRACKER.md`.**
The genuinely new prerequisites versus Phase B's gate were the three schema-shape
decisions in DEC-GRX-019 — everything else follows the same per-slice pattern.

## Readiness gate — Sprint 5 Phase E, Account/user management (`GRX-SAAS-005`)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Phase B dependency | Yes — `GRX-SAAS-005` depends on `GRX-SAAS-002`, not Phase C/D | PASS | `GRX-SAAS-002` marked `DONE` in [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) |
| Permission scope / account-status-enforcement / audit-attribution design decisions | Yes — the tracker's own wording ("activate/suspend/close... view login/security activity") left the permission grant, what suspend/close actually does, and how a platform admin's action gets attributed all unspecified | PASS | [DECISIONS.md §DEC-GRX-020](DECISIONS.md) |
| Data model additions | No new tables/columns — a data-only permission seed plus enforcing an existing column | PASS (LIGHT) | [DATA_MODEL.md §Sprint 5 Phase E entities](../05-data/DATA_MODEL.md#sprint-5-phase-e-entities-customer-account-platform--accountuser-management-grx-saas-005), [DATABASE_SCHEMA.md's Phase E migration-order note](../05-data/DATABASE_SCHEMA.md#migration-order-alembic) |
| RBAC additions | Yes | PASS | [RBAC.md §Sprint 5 Phase E permission codes](../08-security/RBAC.md#sprint-5-phase-e-permission-codes-grx-saas-005) — `platform.accounts.manage`, granted only to `platform.owner`/`platform.admin` |
| Threat model addendum | Yes (first Phase E capability with cross-account reach: a platform admin can now act on accounts it doesn't belong to) | PASS | [THREAT_MODEL.md §Sprint 5 Phase E](../08-security/THREAT_MODEL.md#sprint-5-phase-e--accountuser-management-grx-saas-005-scope) — T30–T33 |
| Sprint plan | Yes | PASS | [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase E](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-e--platform-admin-panel-grx-saas-005-through-grx-saas-009) |
| Feature specs | No (written per-task, not upfront — same practice as every prior slice/sprint) | DEFERRED TO EACH TASK | — |
| Project tracker row | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) — `GRX-SAAS-005` |
| AI safety baseline | No (no AI feature in this task) | N/A FOR GRX-SAAS-005 | — |
| Billing/provider decisions | No (out of this task's scope — `GRX-SAAS-004`/`006`/`007`) | N/A FOR GRX-SAAS-005 | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |

**Overall status: READY — `GRX-SAAS-005` cleared to `READY` in `MASTER_TASK_TRACKER.md`.**
This is the first Phase E task to actually need a `(platform)/` frontend — Phase B
deliberately shipped none ("the frontend arrives naturally with Phase E's actual panel"),
so this task's frontend scope includes the platform login page and a minimal shell
alongside the accounts list/detail pages themselves, not just the accounts feature.

## Readiness gate — Sprint 5 Phase E, Usage & campaign oversight (`GRX-SAAS-008`)

| Readiness item | Required | Status | Evidence |
|---|---|---|---|
| Phase B dependency | Yes — `GRX-SAAS-008` depends on `GRX-SAAS-002`, not billing (`GRX-SAAS-004`) | PASS | `GRX-SAAS-002` marked `DONE` in [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) |
| Permission scope / pause-semantics / usage-view-shape design decisions | Yes — the tracker's own wording ("abuse controls (pause suspicious sending)", "usage view") left the permission grant, what "pause" does to a campaign, and whether usage is a raw or aggregated view all unspecified | PASS | [DECISIONS.md §DEC-GRX-021](DECISIONS.md) |
| Data model additions | No new tables/columns — a data-only permission seed plus read/aggregate queries over existing `usage_records`/`campaigns` | PASS (LIGHT) | [DATA_MODEL.md §Sprint 5 Phase E entities (usage/campaign oversight)](../05-data/DATA_MODEL.md#sprint-5-phase-e-entities-customer-account-platform--usage--campaign-oversight-grx-saas-008), [DATABASE_SCHEMA.md's Phase E migration-order note](../05-data/DATABASE_SCHEMA.md#migration-order-alembic) |
| RBAC additions | Yes | PASS | [RBAC.md §Sprint 5 Phase E permission codes](../08-security/RBAC.md#sprint-5-phase-e-permission-codes-grx-saas-005-grx-saas-008) — `platform.usage.manage`, granted to `platform.owner`/`platform.admin`/`platform.support` |
| Threat model addendum | Yes (second cross-account reach: read access to every account's usage/campaigns, plus one mutating action) | PASS | [THREAT_MODEL.md §Sprint 5 Phase E — Usage & campaign oversight](../08-security/THREAT_MODEL.md#sprint-5-phase-e--usage--campaign-oversight-grx-saas-008-scope) — T34–T37 |
| Sprint plan | Yes | PASS | [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase E](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-e--platform-admin-panel-grx-saas-005-through-grx-saas-009) |
| Feature specs | No (written per-task, not upfront — same practice as every prior slice/sprint) | DEFERRED TO EACH TASK | — |
| Project tracker row | Yes | PASS | [MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) — `GRX-SAAS-008` |
| AI safety baseline | No (no AI feature in this task) | N/A FOR GRX-SAAS-008 | — |
| Billing/provider decisions | No (out of this task's scope — `GRX-SAAS-004`/`006`/`007`) | N/A FOR GRX-SAAS-008 | [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md) |

**Overall status: READY — `GRX-SAAS-008` cleared to `READY` in `MASTER_TASK_TRACKER.md`.**
The genuinely new prerequisite versus GRX-SAAS-005's gate was the pause-semantics
decision (reusing `cancel_campaign`'s existing terminal state rather than inventing a
resumable one) — everything else follows the same per-task pattern this document already
establishes.

## Gate for later slices/phases

Slice 4 (Scheduled Email) onward, and Sprint 5 Phase D and the remaining Phase E rows
(`GRX-SAAS-006`, `GRX-SAAS-007`, `GRX-SAAS-009`, `GRX-SAAS-010`), will each need their own
readiness pass (data model additions, feature specs, etc.) before becoming `READY` — this
table will be extended per slice/phase rather than re-litigated from scratch.
