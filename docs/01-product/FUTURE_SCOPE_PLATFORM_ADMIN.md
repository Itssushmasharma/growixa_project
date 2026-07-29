# Future Scope: Multi-Tenant Customer Platform + IITDEVELOPER Platform Admin

- Document ID: DOC-FUTURE-SCOPE-PLATFORM-ADMIN
- Status: ACTIVE (idea capture only — not approved, not scheduled into any release)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Product owner (Ravi) via coding agent
- Related documents: [PRD](PRD.md), [MVP_SCOPE](MVP_SCOPE.md), [ROADMAP](ROADMAP.md), [DECISIONS §DEC-GRX-002, §DEC-GRX-007, §DEC-GRX-013](../00-project-control/DECISIONS.md), [FUTURE_SCOPE_MULTI_BRAND](FUTURE_SCOPE_MULTI_BRAND.md), [FUTURE_SCOPE_SEO_AEO_GEO](FUTURE_SCOPE_SEO_AEO_GEO.md)

## Purpose

Captures a proposal raised in conversation: turning Growixa into a self-service SaaS
product where customers register directly (no internal-only invite gate), each customer's
data is isolated by an `account_id` (not a visible tenant/workspace concept), and
IITDEVELOPER operates a master **Platform Admin** panel above all customer accounts —
covering user/subscription/provider management, usage tracking, campaign oversight,
infrastructure monitoring, a financial dashboard, and audited "secure support session"
access into a customer's account.

This is idea capture, not a plan. No `GRX-*` task should be created for it, and it must not
enter `MASTER_TASK_TRACKER.md` or any `docs/14-sprints/` file, until
[§Before this can be implemented](#before-this-can-be-implemented) is resolved.

## Relationship to current architecture decisions

This proposal is a direct, well-reasoned counter-proposal to the current MVP's shape, so it
needs to be read against what's already decided rather than in isolation:

- [DEC-GRX-002](../00-project-control/DECISIONS.md): "MVP is single-tenant, one company
  installation, multiple internal users" — "Growixa's first customer is one internal
  marketing team." This proposal describes external, self-registering customers instead.
- [DEC-GRX-013](../00-project-control/DECISIONS.md): multi-tenancy, customer-facing SaaS
  signup, and tenant billing are **deferred indefinitely** — explicitly not just "later."
  This proposal is a concrete design for exactly that.
- [DEC-GRX-007](../00-project-control/DECISIONS.md): usage metering exists from the start
  "even though single-tenant," specifically so it doesn't need rework "when multi-tenant
  billing is added later." This proposal is consistent with that forward-compatible intent
  — it's the kind of future this decision was already hedging for.
- `PRD.md` §10 Goal 7 already states the architecture should stay "modular enough to add
  SEO/AEO/GEO capabilities and, later, multi-tenancy, without a rewrite" — so multi-tenancy
  was always an acknowledged *possible* future, just not decided or scheduled. This document
  is the first place a concrete shape for it is captured.

**Net effect**: this proposal doesn't reverse any decision by itself, but acting on it
requires explicitly revisiting DEC-GRX-002 and DEC-GRX-013 first — see
[§Before this can be implemented](#before-this-can-be-implemented).

## How this relates to the existing roadmap

The proposal's own 5-phase roadmap substantially overlaps with what's already planned —
the real new content is Phase 1. Phases 2–5 largely restate existing scope in different
words:

| Proposal phase | Corresponds to |
|---|---|
| Phase 1 — Platform foundation (auth, customer accounts, platform admin, subscriptions, usage tracking, audit logs, provider config, infra monitoring) | **New.** No equivalent exists today — see below. |
| Phase 2 — Marketing MVP (business profile, brand voice, contacts, segments, email, social calendar, AI assistant, approval, analytics) | Already `ROADMAP.md` Slices 1–6 (this project's actual current MVP) |
| Phase 3 — Automation (sequences, workflow engine, lead scoring, follow-ups, failure recovery) | Already implied by `ROADMAP.md`'s later slices and `MODULE_BOUNDARIES.md`'s `automation` module (explicitly out of MVP scope, not yet detailed) |
| Phase 4 — Channel expansion (direct social publishing, WhatsApp, SMS, DLT, more email providers) | Overlaps with `FEATURE_SMS_MARKETING.md` (in progress elsewhere in this repo) and natural email/social provider expansion |
| Phase 5 — Website Growth (SEO, AEO, GEO, crawling, content optimization) | Already fully mapped in [FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md) (V1.5–V3) |

In other words: this proposal is mostly a **deployment/business-model change** (self-service
multi-tenant SaaS with a platform-admin control plane) wrapped around the *same* product
feature set already planned — not a request for new marketing/growth features.

## Proposed model summary (as given)

- One Growixa application, one main API, one PostgreSQL database, one Platform Admin panel,
  specialized workers — explicitly *not* "complex multi-tenant workspace SaaS" in the
  traditional sense (no visible "create organization / create tenant / create workspace /
  select workspace / tenant switcher" UX for normal users).
- Customer flow: register → verify email → select plan → add business details → import
  contacts → connect channels → start campaigns. A small customer can operate with a single
  `customer.owner` user.
- Data isolation via a plain `account_id` (or `customer_account_id`) column on every
  customer-owned table (`users`, `contacts`, `campaigns`, `subscriptions`, etc.) — described
  as sufficient to prevent cross-customer data access without introducing a
  workspace-switcher concept.
- Proposed platform-level roles: `platform.owner`, `platform.admin`, `platform.support`,
  `platform.finance`, `platform.operations`.
- Proposed customer-level roles (initial release): `customer.owner`, `customer.admin`,
  `marketing.manager`, `content.editor`, `analyst`, `viewer` — broadly consistent with this
  project's existing Sprint 1 role set (Super Admin/Admin/Marketing Manager/Content
  Creator/Analyst/Viewer per [RBAC.md](../08-security/RBAC.md)), renamed to fit a
  customer/platform split.

## Proposed IITDEVELOPER Platform Admin capabilities

- **User management**: view all registered users/account status; activate, suspend,
  restrict, or close accounts; reset verification state; view login/security activity;
  manage support access.
- **Subscription management**: view/upgrade/downgrade plans; trial extensions; custom usage
  credits; suspend expired accounts; view invoices/payment failures; configure plan limits.
- **Provider management**: configure platform-level OpenAI/Claude/email/SMS/WhatsApp
  providers; set default models and fallback providers; view provider health; rotate
  credentials; disable a failing provider; set provider-level limits.
- **Usage tracking** per customer: AI credits, tokens, email sends, contact count, social
  posts, storage, campaigns, automations, SMS/WhatsApp usage, provider costs.
- **Campaign oversight**: campaign status, queued/failed campaigns, pause suspicious
  sending, bounce/complaint inspection, restrict abusive accounts, social publishing
  failures. Platform Admin should not freely edit customer content unless support access
  has been explicitly opened (see below).
- **Infrastructure monitoring**: API/Postgres/Redis health, RabbitMQ queue depth, worker
  status, scheduled/failed jobs, API latency, error rates, storage status.
- **Financial dashboard**: MRR, ARR, active subscriptions, trials, churn, payment failures,
  AI/email/SMS/WhatsApp provider costs, estimated contribution margin.
- **Secure support access**: not an unrestricted "login as customer." An "Open Secure
  Support Session" flow requiring a support reason, ticket number, platform-admin
  confirmation, a time-limited session, a visible support banner, read-only by default, a
  complete audit log, no visibility of raw API keys, and a separate permission gate for
  making changes. This is a strong pattern — if platform-admin support access is ever
  built, it should look like this rather than a plain impersonation login, regardless of
  when/whether the rest of this proposal is adopted.

## Provider flow (as given)

```
Does customer have their own provider configured?
        |
        ├── Yes → Use customer provider
        |
        └── No → Use Growixa platform provider
```

First release could skip BYOK (bring-your-own-key) entirely and use only Growixa-managed
providers, adding "platform default + optional customer override" later.

## Before this can be implemented

- **Revisit [DEC-GRX-002](../00-project-control/DECISIONS.md) and
  [DEC-GRX-013](../00-project-control/DECISIONS.md) explicitly.** Whether Growixa becomes an
  externally-sold, self-registering SaaS product is a business-model decision that has to be
  made deliberately — this document doesn't make it, it only records what the shape would
  look like if that decision is made later.
- **Billing.** Subscription plans, invoices, and payment-failure handling require a
  payments/billing vendor — none is chosen, none is integrated, and DEC-GRX-013 lists this
  as an explicit reason multi-tenancy was deferred in the first place.
- **Schema migration.** Every customer-owned table needs an `account_id` column and every
  query needs to be scoped by it — a mechanical but pervasive change touching every module
  in [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md), not just user/auth.
- **Auth boundary.** Platform-admin identity and permissions are a distinct concern from
  customer-account identity/RBAC — likely a separate permission namespace (`platform.*`)
  and possibly a separate login surface, not just new rows in the existing `roles` table.
- **Registration flow.** Self-service signup + email verification + plan selection is new
  surface area; today the only way into the system is an admin-issued invitation
  (`GRX-USER-001`), which assumes the inviter is already inside a trusted single company.

## Explicitly not staged into any release

Not in the MVP (Slices 1–6), not in V1.5–V3 per [ROADMAP.md](ROADMAP.md). No `GRX-*` task
exists for any part of this proposal.
