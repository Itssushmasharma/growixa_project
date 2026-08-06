# Decision Log

- Document ID: DOC-DECISIONS
- Status: ACTIVE
- Version: 1.1
- Last updated: 2026-07-22
- Owner: Product owner (Ravi) via coding agent
- Related documents: [OPEN_QUESTIONS](OPEN_QUESTIONS.md), [ASSUMPTIONS](ASSUMPTIONS.md), [ROADMAP](../01-product/ROADMAP.md)

Decision statuses: `PROPOSED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `SUPERSEDED`.

---

## DEC-GRX-001: Growixa product positioning and MVP scope reduction

- Status: APPROVED
- Date: 2026-07-22
- Context: Initial discovery produced a PRD for an SEO/AEO/GEO/website-crawler-focused
  "AI Visibility & Growth Platform." A subsequent master specification redefined Growixa
  as a single-tenant email/social marketing automation platform, which read as a full
  product pivot. The product owner corrected this: it is not a pivot.
- Options considered:
  1. Treat the SEO/AEO/GEO/crawler discovery work as a different, unrelated product and drop it.
  2. Treat Growixa as broad from day one and attempt to build all capabilities (SEO + marketing automation) simultaneously.
  3. Keep Growixa's full long-term vision as "AI-powered growth and marketing automation platform" but narrow the **first release** to email/social/contacts/AI-assist/scheduling/analytics, and stage SEO/AEO/GEO/website-intelligence into explicit future releases.
- Decision: Option 3.
- Rationale: A single vertical slice (email + social marketing) is achievable and
  demonstrable quickly; the SEO/crawler/agent-system work is significantly larger and
  depends on infrastructure (crawler, agent orchestration, CMS/repo integrations) that
  isn't needed for the first slice. Deferring avoids parallel half-built modules while
  preserving the original product vision.
- Consequences:
  - Product positioning statement (used verbatim in [PRODUCT_VISION.md](../01-product/PRODUCT_VISION.md)
    and [PRD.md](../01-product/PRD.md)): "Growixa is an AI-powered growth and marketing
    automation platform. It begins with email and social media automation, then expands
    into SEO, AEO, GEO, website intelligence, content optimization, and integrated growth
    workflows."
  - The original SEO/AEO/GEO discovery PRD (`docs/archive/source-prd-seo-aeo-geo-website-intelligence/`)
    is retained as valid source material, not deleted or treated as unrelated.
  - Its requirements are mapped to future Growixa release IDs in
    [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md) and staged
    into releases V1.5–V3 in [ROADMAP.md](../01-product/ROADMAP.md).
  - No SEO/AEO/GEO/crawler/WordPress/GitHub/Search Console capability may enter the MVP
    sprint tracker or Slice 1–6 development plan.
- Related tasks: GRX-DOC-001 and all Phase 1 documentation tasks.
- Supersedes: none (clarifies, does not reverse, the single-tenant MVP decision below).

---

## DEC-GRX-002: Growixa MVP is single-tenant

- Status: SUPERSEDED by [DEC-GRX-017](#dec-grx-017-customer-account-architecture--platform-admin) (2026-08-07)
- Date: 2026-07-22
- Context: Growixa's first customer is one internal marketing team; multi-tenant SaaS
  infrastructure (workspace switching, tenant billing, cross-tenant isolation) adds
  substantial complexity with no near-term buyer.
- Decision: MVP is single-tenant, one company installation, multiple internal users.
- Rationale: Avoids unnecessary `tenant_id`/`workspace_id` scoping on every table; ownership
  fields (`created_by_user_id`, etc.) are sufficient. Architecture stays modular enough to
  add multi-tenancy later without a rewrite.
- Consequences: No tenant model, no workspace switcher, no tenant-scoped billing in MVP.
  **Historical note (accurate as of 2026-07-22 through 2026-08-07):** this decision governed
  Slices 1–4 (Sprints 1–4) — every table/query built during that window correctly assumed
  single-tenancy per this decision. It does not retroactively make those tables wrong; it
  means Sprint 5 (`GRX-SAAS-001`) must retrofit them, per DEC-GRX-017.
- Related tasks: Slice 1 (Foundation).
- Supersedes: none.

## DEC-GRX-003: Modular FastAPI monolith, not microservices

- Status: APPROVED
- Date: 2026-07-22
- Decision: Backend is a modular monolith (FastAPI) with independently scalable Python
  workers, not one microservice per module/agent.
- Rationale: Reduces operational complexity for the current team size; module boundaries
  (see [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md), once created) keep
  a future service split possible.
- Related tasks: Slice 1 (Foundation).

## DEC-GRX-004: Core technology stack

- Status: APPROVED
- Date: 2026-07-22
- Decision: Next.js/TypeScript/React frontend; FastAPI/Python/Pydantic/SQLAlchemy/Alembic
  backend; PostgreSQL (+ pgvector where an approved AI feature needs embeddings); Redis for
  cache/locks/rate-limits; RabbitMQ for durable jobs; S3-compatible object storage; Docker
  Compose for local dev.
- Rationale: Matches team familiarity and the async, job-heavy nature of email/social
  delivery and AI generation. MongoDB explicitly excluded as primary store — Postgres is
  the source of truth.
- Related tasks: Slice 1 (Foundation).

## DEC-GRX-005: Provider integrations use adapter interfaces

- Status: APPROVED
- Date: 2026-07-22
- Decision: `EmailProvider`, `SocialProvider`, `AIModelProvider`, `ObjectStorageProvider`,
  `BillingProvider` are abstracted behind adapter interfaces; concrete providers are
  selected via configuration, not hard-coded.
- Rationale: Provider choice (OQ-002, OQ-003, OQ-004, OQ-005) can be resolved independently
  of interface design; swapping providers later doesn't require rewriting call sites.

## DEC-GRX-006: AI-generated content requires human approval in MVP

- Status: APPROVED
- Date: 2026-07-22
- Decision: AI output is always labeled `AI_GENERATED`; it cannot send email or publish
  social content directly. A human must review and approve before any send/publish.
- Rationale: Matches PRD §17 AI Safety and Approval requirements; avoids reputational/legal
  risk from unreviewed automated outreach.

## DEC-GRX-007: Usage metering exists from the start, even though single-tenant

- Status: APPROVED
- Date: 2026-07-22
- Decision: Every cost-generating operation (email sends, AI generations, social
  publishing, storage, imports, workflow executions) is metered from Slice 1 onward.
- Rationale: Needed for cost control and capacity planning now, and avoids a retrofit if/when
  multi-tenant billing is added later.

## DEC-GRX-008: Suppression, unsubscribe, and consent handling are mandatory, not deferrable

- Status: APPROVED
- Date: 2026-07-22
- Decision: Suppression-list and unsubscribe checks run before every send from Slice 3
  onward; cannot be shipped as a "fast follow."
- Rationale: Legal/compliance requirement for any real email sending; retrofitting after
  real sends have occurred is unacceptable.

## DEC-GRX-009: Provider credentials are encrypted at rest

- Status: APPROVED
- Date: 2026-07-22
- Decision: All third-party provider tokens/secrets (email, social OAuth, AI API keys) are
  encrypted at rest and never inserted into AI prompts.

## DEC-GRX-010: Development proceeds in vertical slices, not parallel module builds

- Status: APPROVED
- Date: 2026-07-22
- Decision: Build order is Slice 1 (Foundation) → Slice 2 (Contacts) → Slice 3 (First Email
  Campaign) → Slice 4 (Scheduled Email) → Slice 5 (Social Publishing) → Slice 6 (AI
  Assistant), each with an explicit end-to-end success condition before the next starts.
- Rationale: Prevents a pile of half-finished, disconnected modules; every slice produces a
  working, demoable increment.

## DEC-GRX-011: No feature is marked DONE without end-to-end evidence

- Status: APPROVED
- Date: 2026-07-22
- Decision: Per [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md), a feature cannot be marked
  complete based on scaffolding, mocked providers, or tests that only check HTTP status.

## DEC-GRX-012: Broad autonomous marketing/growth agents are deferred

- Status: APPROVED
- Date: 2026-07-22
- Decision: The multi-agent orchestration system described in the source SEO PRD
  (Growth Strategist + specialist agents) is deferred to future releases (see
  [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md)). MVP AI features
  are assistive (generate/rewrite/suggest with approval), not autonomous multi-step agents.
- Related: DEC-GRX-001, DEC-GRX-006.

## DEC-GRX-013: Multi-tenancy, customer-facing SaaS signup, and tenant billing are deferred

- Status: SUPERSEDED by [DEC-GRX-017](#dec-grx-017-customer-account-architecture--platform-admin) (2026-08-07) — the business model changed toward external SaaS customers, which this decision itself named as the trigger to revisit
- Date: 2026-07-22
- Decision: Not part of MVP or the currently-planned future releases in ROADMAP.md; revisit
  only if Growixa's business model changes toward external SaaS customers.
- Related: DEC-GRX-002.

---

## DEC-GRX-014: Application-managed authentication in FastAPI (resolves OQ-001)

- Status: APPROVED
- Date: 2026-07-22
- Context: Slice 1 (Foundation) cannot start until the authentication approach is fixed —
  it determines the user/session data model, the auth module's API surface, and how RBAC
  hooks into every other module. [OQ-001](OPEN_QUESTIONS.md) asked whether to build
  application-managed auth or adopt an external provider (e.g. Keycloak, Auth0, Clerk).
- Options considered:
  1. Third-party hosted auth provider (Auth0/Clerk) — fastest to stand up, but adds an
     external dependency, recurring cost, and a data-residency question for a single-tenant
     internal tool that doesn't need social-login breadth.
  2. Self-hosted Keycloak — full OIDC/SSO capability now, but heavy operational surface
     (its own database, admin console, upgrade cadence) for an MVP with no SSO requirement yet.
  3. Application-managed authentication inside FastAPI, PostgreSQL-backed, with an adapter
     boundary that allows OIDC/enterprise SSO to be added later without a rewrite.
- Decision: Option 3.
- Rationale: No documented implementation constraint forces a third-party or Keycloak
  dependency for a single-tenant MVP with only internal users. Application-managed auth
  keeps the operational footprint minimal (no extra service to run/patch) while the adapter
  boundary preserves the ability to add OIDC/SSO in a future release without rearchitecting
  the user/session model. Full requirements:
  - PostgreSQL-backed users
  - Argon2id password hashing
  - Short-lived access tokens
  - Rotating refresh tokens
  - HttpOnly, Secure, SameSite cookies for the browser application
  - Hashed password-reset tokens
  - Hashed user-invitation tokens
  - Session revocation
  - Login rate limiting
  - Account disable and logout-all-sessions support
  - Audit events for: login, logout, failed login, password reset, invitation acceptance,
    role changes, session revocation
  - Centralized authentication and authorization services (not scattered per-endpoint checks)
  - An adapter boundary so external OIDC or enterprise SSO can be added later
- Consequences: Detailed in [`docs/08-security/AUTHENTICATION.md`](../08-security/AUTHENTICATION.md).
  Keycloak or any third-party auth provider must not be introduced in the MVP unless a
  documented implementation constraint makes it necessary — that would itself require a new
  logged decision superseding this one, not a silent substitution.
- Related tasks: Slice 1 (Foundation) — GRX-AUTH-* tasks in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

---

## DEC-GRX-015: Postmark, integrated via its SMTP relay endpoint (resolves OQ-002)

- Status: APPROVED
- Date: 2026-08-01
- Context: Slice 3 (First Email Campaign) cannot start until the production email
  provider is fixed — it determines the sending adapter's interface, credential fields,
  and how bounce/complaint/open/click events reach the platform.
  [OQ-002](OPEN_QUESTIONS.md) asked which provider (e.g. SES, Postmark, SendGrid,
  Mailgun) is the one production adapter for MVP.
- Options considered:
  1. Amazon SES — cheapest at scale, natural fit if already on AWS; more manual setup
     for deliverability (domain/DKIM/warm-up) and a less ergonomic API.
  2. Postmark — best-in-class deliverability and a simple API/SMTP surface;
     historically transactional-focused, but supports marketing sends.
  3. SendGrid — generous free tier, mature marketing-email feature set; deliverability
     reputation has been mixed at times.
  4. Mailgun — developer-friendly, EU-region hosting option for data residency.
  5. A fully generic SMTP relay using the user's own existing mailbox credentials
     (raised mid-decision) — simplest to configure, but standard SMTP has no
     bounce/open/click webhooks, so `MVP_SCOPE.md`'s delivery/bounce/open/click
     tracking requirement would need to be deferred or self-built (tracking pixels,
     link-wrapping, unreliable bounce-message parsing).
- Decision: Postmark (option 2), integrated via **Postmark's SMTP relay endpoint**
  (host/port + a server API token used as the SMTP password) rather than its REST API.
- Rationale: Postmark was picked for deliverability and API/SMTP simplicity. The SMTP
  question that came up mid-decision is resolved by using Postmark's own SMTP relay
  rather than a generic personal-mailbox SMTP server — this gives an actual SMTP
  integration (satisfying `MVP_SCOPE.md`'s "SMTP support" bullet literally) while still
  keeping Postmark's webhook-based bounce/complaint/open/click tracking, which a
  generic mailbox cannot provide. No loss of capability versus using Postmark's REST
  API directly; this is purely a transport choice Postmark supports natively.
- Consequences: The Slice 3 email-provider adapter's config model stores SMTP
  host/port/username(token)/password(token) rather than a bare REST API key — encrypted
  at rest per [DEC-GRX-009](DECISIONS.md). If a future release needs a second provider
  or provider-specific features Postmark's SMTP relay doesn't expose, that requires a
  new logged decision, not a silent substitution.
- Related tasks: Slice 3 (First Email Campaign) — `GRX-EMAIL-*` tasks in
  `MASTER_TASK_TRACKER.md` (to be added).
- Supersedes: none.

## DEC-GRX-016: Add Custom SMTP as a second email provider, via SMTP relay only (fulfills DEC-GRX-015's second-provider clause)

- Status: APPROVED
- Date: 2026-08-06
- Context: User-requested multi-provider support for the Integrations settings page
  (`GRX-EMAIL-011`), after reviewing a design reference showing a provider-card grid
  (Postmark, SendGrid, Resend, AWS SES, Custom SMTP, Mailgun). `DEC-GRX-015`'s own
  consequences clause anticipated this: "a future release [needing] a second provider
  ... requires a new logged decision, not a silent substitution."
- Options considered:
  1. Add all five providers shown in the reference, each via its native API/SDK
     (SendGrid API, AWS SES SDK, etc.) — most "real" per-provider integration, but a
     separate adapter, credential shape, and send code path per provider.
  2. Add all five providers, all via SMTP relay (every one of them supports an SMTP
     relay interface) — no new sending code path, but ships UI for providers nobody
     has asked to actually use yet.
  3. Add just one second provider, Custom SMTP, via the existing SMTP-relay send path
     — the smallest change that still proves out "more than one active connection at a
     time" as a real capability, without speculative UI for unused providers.
- Decision: Option 3 — Custom SMTP only, via SMTP relay (no new sending code).
- Rationale: This codebase's established practice (this session, repeatedly) is to not
  build UI for capabilities that don't exist yet — Options 1 and 2 would both add
  visible cards for SendGrid/Resend/AWS SES/Mailgun with no working backend behind
  them. Custom SMTP costs almost nothing beyond it (same credential shape as Postmark:
  host/port/username/password) while genuinely exercising the harder part of this
  change — the data model moving from "one active connection globally" to "one active
  connection per provider," now a real DB-enforced partial unique index on
  `(provider) WHERE is_active` rather than the app-only convention `DATA_MODEL.md`
  previously described.
- Consequences: `email_provider_connections.provider`'s CHECK constraint becomes
  `IN ('POSTMARK', 'CUSTOM_SMTP')`. Postmark's webhook receiver
  (`POST /webhooks/postmark`) remains Postmark-specific and un-generalized — Custom
  SMTP gets no webhook route at all, since plain SMTP has no bounce/complaint/open/click
  callback mechanism (the same conclusion `DEC-GRX-015`'s own generic-SMTP option
  reached). This means `SPRINT_03_EMAIL_CAMPAIGN.md`'s "explicitly excluded" generic
  multi-provider webhook abstraction stays excluded — a second provider existing
  doesn't require it, since only Postmark ever receives webhook traffic. Adding a
  third provider that also needs webhooks (a real SendGrid/Mailgun/AWS SES
  integration) would need its own new decision, same as this one.
- Related tasks: `GRX-EMAIL-011` (ad hoc, not part of the original Sprint 3 plan) in
  `MASTER_TASK_TRACKER.md`.
- Supersedes: none — fulfills, rather than contradicts, `DEC-GRX-015`'s own
  "requires a new logged decision" consequence.

---

## DEC-GRX-017: Customer Account Architecture & Platform Admin

- Status: APPROVED
- Date: 2026-08-07
- Naming note: this is a shared-application, `account_id`-isolated architecture —
  technically a form of what engineers call "multi-tenant" (multiple customers sharing
  one application/database, isolated by an ownership key), but deliberately **not**
  named that way in this project's docs, since "multi-tenant" is commonly read as
  implying visible organizations, workspace switching, or enterprise account
  hierarchy — none of which this decision includes. See
  [§Explicitly excluded](#explicitly-excluded-from-this-decision) below.
- Context: [FUTURE_SCOPE_PLATFORM_ADMIN.md](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md)
  captured this as idea-capture in 2026-07-27, explicitly not approved or scheduled,
  gated on "revisit [DEC-GRX-002 and DEC-GRX-013] explicitly" as a deliberate
  business-model decision. The product owner confirmed the business model is changing:
  Growixa opens for self-service registration — any company can sign up and use the
  platform — rather than remaining IITDEVELOPER's single internal-install tool. This is
  exactly the trigger DEC-GRX-013 itself named ("revisit only if Growixa's business
  model changes toward external SaaS customers").
- Decision: Adopt the model described in
  [FUTURE_SCOPE_PLATFORM_ADMIN.md](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md#proposed-model-summary-as-given):
  one application, one database, `account_id`-scoped data isolation (no visible
  workspace-switcher concept), self-service customer registration, and a separate
  IITDEVELOPER Platform Admin control plane above all customer accounts. Full phased
  implementation plan: [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md).
- Explicitly excluded from this decision: user-visible organizations/workspaces,
  workspace switching, organization invitations, enterprise account hierarchy, tenant
  selection at login. Customer isolation is an internal data-model concern
  (`account_id` on every row), invisible to the end user, who only ever sees "their
  account" — never a concept of other tenants existing.
- Rationale: This is a business-model decision, not a technical one — the technical shape
  was already scoped in `FUTURE_SCOPE_PLATFORM_ADMIN.md` precisely so that once the
  business decision was made, implementation could start immediately from a concrete
  plan rather than a blank page. `DEC-GRX-007`'s usage-metering-from-the-start decision
  and `PRD.md` §10 Goal 7's "modular enough to add... multi-tenancy later without a
  rewrite" both already anticipated this could happen.
- Consequences: Supersedes `DEC-GRX-002` and `DEC-GRX-013`. Every table and query built
  under single-tenancy (Slices 1–4) must be retrofitted with `account_id` isolation
  before any new account-facing feature is built on top — see
  `SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md` Phase A, which blocks every later phase. This
  is the single largest and highest-risk sprint in the project's history: a missed
  scoping filter is a cross-customer data breach, not a cosmetic bug. Billing requires
  selecting and integrating a payments vendor (none chosen yet — Stripe is the working
  assumption). `ROADMAP.md`'s "Explicitly deferred indefinitely" section and
  `PROJECT_STATUS.md`'s "Deferred indefinitely" framing are both updated to reflect this
  is no longer deferred.
- Related tasks: `GRX-SAAS-001` through `GRX-SAAS-010` in `MASTER_TASK_TRACKER.md`.
- Supersedes: `DEC-GRX-002`, `DEC-GRX-013`.

---

*Decisions DEC-GRX-018 onward will be logged as they are made — e.g., resolutions to
OQ-003 through OQ-011 in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).*
