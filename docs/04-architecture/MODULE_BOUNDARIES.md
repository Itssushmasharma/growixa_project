# Module Boundaries

- Document ID: DOC-ARCH-MODULES
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [SYSTEM_ARCHITECTURE](SYSTEM_ARCHITECTURE.md), [DATA_MODEL](../05-data/DATA_MODEL.md)

## Internal module structure

Every backend module follows the same internal layout:

```text
module/
├── api/          # FastAPI routers — HTTP boundary only, no business logic
├── schemas/      # Pydantic request/response models
├── models/       # SQLAlchemy ORM models
├── repositories/ # Data-access layer — the only place that writes raw queries
├── services/     # Business logic — orchestrates repositories, other services, events
├── domain/       # Pure domain types/rules with no framework dependency
├── tasks/        # Background job handlers (RabbitMQ consumers)
├── events/       # Domain events this module publishes/subscribes to
├── exceptions/   # Module-specific exception types
└── tests/
```

`api/` never talks to `repositories/` directly — it calls `services/`. `services/` never
constructs raw SQL — it calls `repositories/`. This keeps the module independently
testable and is what would let a module be extracted into its own service later without a
rewrite.

## Module responsibilities and boundaries

| Module | Owns | Depends on | Must not depend on |
|---|---|---|---|
| `auth` | Credentials, sessions, tokens, password/invitation reset flows | `users` (for identity lookup) | `contacts`, `campaigns`, or any business-data module |
| `users` | Internal user records, invitations | `auth` (for account state), `roles` | Business-data modules |
| `roles` | Role definitions | — | Business-data modules |
| `permissions` | Permission definitions, role→permission mapping | `roles` | Business-data modules |
| `company` | Single company profile record | — | Contact/campaign modules |
| `brand` | Brand voice, brand assets, legal footer | `company` | Contact/campaign modules |
| `contacts` | Contact records, custom fields | `tags`, `segments` (read) | `email_delivery`, `social` (contacts must not know how they're contacted) |
| `imports` | CSV import jobs, import rows, validation results | `contacts` | — |
| `tags` | Tag definitions and assignments | `contacts` | — |
| `segments` | Segment definitions and evaluated membership | `contacts`, `tags` | `email_delivery`, `social` |
| `templates` | Email template definitions and versions | `brand` | `campaigns` (templates are used by, not aware of, campaigns) |
| `campaigns` | Campaign drafts, versions, schedules, recipients | `templates`, `segments`, `contacts` (read) | `social` |
| `email_delivery` | Delivery attempts, provider events, bounce/complaint state | `campaigns`, `contacts` (suppression check) | `social`, `ai` |
| `social` | Social account connections, posts, publish attempts | `content_calendar` | `email_delivery` |
| `content_calendar` | Scheduled-content view across email/social | `campaigns`, `social` (read) | — |
| `ai` | Prompt templates, generations, usage/cost tracking | `brand` (voice), `usage` | Must never call `email_delivery`/`social` to send/publish directly — see GRX-AI-002 |
| `automation` | Out of MVP scope — not implemented in Sprint 1–6 | — | — |
| `analytics` | Read-side aggregation/reporting over campaigns, posts, AI usage | All modules (read-only, via repositories or events) | Must not own writes to other modules' data |
| `notifications` | In-app/notification records | Any module (as event consumer) | — |
| `integrations` | Provider connection/credential management, adapter registry | `auth` (encryption), `usage` | — |
| `usage` | Usage/entitlement ledger | — | Nothing — this is a foundational, dependency-free module so every other module can call it |
| `billing` | Out of MVP scope — not implemented (see [DEC-GRX-013](../00-project-control/DECISIONS.md)) | — | — |
| `audit` | Immutable audit event log | — | Nothing — same rationale as `usage` |
| `admin` | Cross-module admin views (users, roles, company, integrations, usage, audit) | Reads from other modules | Must not contain business logic that belongs in another module |
| `files` | Not required until Slice 5; scaffolding only if touched in Sprint 1 | `integrations` (storage adapter) | — |
| `webhooks` | Out of MVP scope for Sprint 1 (no external providers yet to receive webhooks from) | — | — |

## Cross-module communication rules

- Modules call each other's `services/` layer directly for synchronous needs within the
  same request (e.g., `campaigns` calling `contacts` to validate a recipient exists) — this
  is a monolith, not a network call, so direct calls are acceptable as long as the
  dependency direction in the table above is respected.
- Anything that should happen asynchronously as a side effect of another module's action
  (e.g., "create a notification when a role changes") goes through the `events/` mechanism,
  not a direct call, so `notifications` doesn't become a hard dependency of `roles`.
- No module bypasses `auth`/`permissions` checks — authorization is enforced centrally
  (see [DEC-GRX-014](../00-project-control/DECISIONS.md), [AUTHENTICATION.md](../08-security/AUTHENTICATION.md)),
  never re-implemented per module.

## Sprint 1 scope within this structure

Only `auth`, `users`, `roles`, `permissions`, `company`, `brand` (minimal fields only),
`audit`, `usage` (foundation/ledger schema only, no real metered operations yet since no
cost-generating features exist yet), and a minimal `admin` (user list, role assignment,
company settings screen) are implemented with real logic in Sprint 1. All other modules may
exist as empty directory scaffolding at most, explicitly labeled as such — see
[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md).
