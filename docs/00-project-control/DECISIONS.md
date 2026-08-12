# Decision Log

- Document ID: DOC-DECISIONS
- Status: ACTIVE
- Version: 1.2
- Last updated: 2026-08-07
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

## DEC-GRX-018: Platform admins hold a single `role` column, not a `platform_roles` many-to-many join

- Status: APPROVED
- Date: 2026-08-07
- Context: `SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md`'s Phase B (`GRX-SAAS-002`) readiness
  gate needed the exact `platform_admins` schema shape specified before it could be
  marked `READY`. The sprint doc itself only says "New `platform_admins` table (mirrors
  `users`...) + a `platform_permissions`/`platform_role_permissions` pair mirroring the
  existing `permissions`/`role_permissions` shape" — deliberately not fully spelled out,
  since Phase B's own scope is the auth boundary, not the full feature set.
- Options considered:
  1. Mirror the customer-side shape exactly: `platform_admins` ⟷ `platform_admin_roles`
     ⟷ `platform_roles` ⟷ `platform_role_permissions` ⟷ `platform_permissions` — five
     tables, supporting a platform admin holding more than one role, symmetrical with
     `users`/`user_roles`/`roles`/`role_permissions`/`permissions`.
  2. `platform_admins.role` as a plain column (one of the five proposed values:
     `platform.owner`/`platform.admin`/`platform.support`/`platform.finance`/
     `platform.operations`), with `platform_role_permissions` keyed by that role value
     directly — three tables total (`platform_admins`, `platform_permissions`,
     `platform_role_permissions`), matching the sprint doc's literal "a ... pair"
     wording (two new tables beyond `platform_admins` itself).
- Decision: Option 2 — single `role` column, three tables total.
- Rationale: `FUTURE_SCOPE_PLATFORM_ADMIN.md`'s proposed platform roles read as mutually
  exclusive job functions (owner/admin/support/finance/operations), not overlapping
  grants a person accumulates the way a customer user can hold both "Marketing Manager"
  and "Analyst." No requirement anywhere in Phase B through Phase E's spec calls for a
  platform admin holding more than one role at once. Option 1's extra join table and
  role-catalog table would be speculative complexity for a multi-role need nobody has
  asked for — this codebase's established practice (RBAC.md's own "extended, not
  redesigned" convention, `DEC-GRX-016`'s Custom-SMTP-only choice, etc.) is to build the
  minimum that's actually needed and extend later, not the maximum that's theoretically
  symmetrical.
- Consequences: If a genuine multi-role need for platform admins ever arises, migrating
  from a single `role` column to a full many-to-many join is a real (if mechanical)
  schema change, not free — accepted, since Phase B's acceptance criteria don't require
  it and speculative symmetry isn't a substitute for an actual requirement.
  `platform_role_permissions.role` is a plain `CHECK`-constrained text column, not a
  foreign key to a `platform_roles` table, since no such table exists.
- Related tasks: `GRX-SAAS-002` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

---

## DEC-GRX-019: Phase C registration shape — owner role, plan slug without a plans table, verification via a third `users.status` value

- Status: APPROVED
- Date: 2026-08-07
- Context: `SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md`'s Phase C (`GRX-SAAS-003`) says
  registration "creates... a `customer.owner` user" and includes "plan selection... as
  part of registration," but neither is specified precisely enough to write a migration
  from — there is no `customer.owner` role anywhere in `RBAC.md`'s seeded role set, and
  no `plans` catalog table exists yet (`accounts.plan_id` is a bare nullable `UUID` with
  no FK, explicitly "nullable until Phase D... creates the subscriptions/plans model").
- Decisions:
  1. **Owner role**: the newly-registered account's first user gets the existing seeded
     `Super Admin` role, not a new `customer.owner` role. Phase C's own "Included" list
     never lists a role-taxonomy change, and `FUTURE_SCOPE_PLATFORM_ADMIN.md`'s
     `customer.owner`/`customer.admin`/etc. naming is explicitly a *future* renaming
     proposal ("Proposed customer-level roles"), not a Phase C requirement. `Super
     Admin` already means "full access within one account" — exactly what a new
     account's first user needs — so registration reuses it rather than inventing a
     second name for the same thing.
  2. **Plan selection**: `accounts` gains `selected_plan_slug` (nullable `text`, `CHECK
     IN ('starter', 'growth')`) — deliberately a plain string, not a `plan_id` FK,
     since there is no `plans` table to point at yet. The two allowed values are the
     two self-service plans already live on the public pricing page
     (`apps/web/.../pricing-section.tsx`'s `Starter`/`Growth` cards) — `Enterprise` is
     excluded on purpose, since its own button already reads "Contact Sales," not a
     self-service action. Recorded only, per Phase C's own "actual plan enforcement is
     Phase D" exclusion — Phase D reads this value (or its absence) when creating the
     first real subscription, and may migrate it into a proper FK at that point.
  3. **Verification gate**: `users.status`'s `CHECK` constraint gains a third value,
     `PENDING_VERIFICATION` — the newly-registered owner starts here instead of
     `ACTIVE`; verifying flips it to `ACTIVE`. This reuses `auth/services.py`'s
     existing `login()` check (`user.status == "ACTIVE"`) with zero new login-path
     code — a `PENDING_VERIFICATION` user already can't log in today, before writing
     a single line of Phase C code, satisfying "an unverified account cannot
     authenticate" for free. `accounts.status` (`ACTIVE`/`SUSPENDED`/`CLOSED`) is left
     untouched — conflating "not yet verified" with "administratively suspended" would
     blur a distinction Phase E's platform-admin suspend/close actions need to stay
     meaningful.
  4. **Email uniqueness across accounts**: confirmed as already resolved, not newly
     decided — Phase A (`GRX-SAAS-001`'s users/auth slice) already made `users.email`
     globally unique on purpose ("login resolves a user by email before any account is
     known"). Registration inherits this for free: a duplicate email fails the same
     `EmailAlreadyRegisteredError` path `invite_user`/`accept_invitation` already use.
     This directly confirms Phase C's own flagged assumption ("one email = one
     platform identity") rather than opening a new question.
  5. **Verification token**: a new `account_verification_tokens` table, structurally
     identical to `password_reset_tokens` (`id`/`account_id`/`user_id`/`token_hash`/
     `expires_at`/`used_at`) — reuses `auth/tokens.py`'s existing `generate_token`/
     `hash_token` functions per Phase C's own instruction, rather than a new token
     table shape.
- Consequences: A future real `plans` catalog (Phase D) will need its own migration to
  either keep `selected_plan_slug` as a soft hint alongside a proper `plan_id` FK, or
  migrate existing values into it — a real but small follow-up cost, accepted since
  inventing a `plans` table now (with only two placeholder rows and no billing
  attached) would be schema speculation ahead of an actual requirement. If a future
  need for `customer.owner` as a genuinely distinct role from `Super Admin` (e.g.
  per-account role customization) ever arrives, that is a real, separate RBAC change,
  not something this decision forecloses.
- Related tasks: `GRX-SAAS-003` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

---

## DEC-GRX-020: Phase E account/user management shape — permission scope, enforcing `accounts.status` at login, and auditing a platform admin's actions without an `actor_user_id`

- Status: APPROVED
- Date: 2026-08-07
- Context: `GRX-SAAS-005` (`SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md` §Phase E) says "Account/user
  management — list all accounts, activate/suspend/close, view login/security activity."
  Three things this leaves unspecified: which `platform.*` role(s) get the new permission,
  what actually happens on suspend/close (`accounts.status` has existed since Phase A but
  nothing has ever read it), and how a platform admin's action gets recorded given
  `audit_logs.actor_user_id` is a FK to `users.id` — a `platform_admins.id` cannot go there.
- Decisions:
  1. **Permission code and role grant**: one new code, `platform.accounts.manage`, granted
     only to `platform.owner` and `platform.admin` — matching `platform.admin`'s own
     stated scope in `RBAC.md`'s Phase B role table ("Account/user management, support
     session access, day-to-day operations"). `platform.support`/`finance`/`operations`
     get nothing from this task; `platform.support`'s eventual account visibility, if any,
     belongs to `GRX-SAAS-010`'s own permission gate, not a side effect of this one.
  2. **`accounts.status` is now actually enforced, not just stored**: discovered while
     scoping this task that `auth/services.py`'s `login()` and `refresh()` have only ever
     checked `user.status == "ACTIVE"` — `accounts.status` (`ACTIVE`/`SUSPENDED`/`CLOSED`,
     present since Phase A/`DEC-GRX-017`) was written on account creation but never read
     anywhere. This is a real, pre-existing gap, not new scope creep: `GRX-SAAS-005`'s own
     acceptance criterion ("a suspended account's users cannot log in") cannot be true
     without it. Both `login()` and `refresh()` gain an `account.status == "ACTIVE"` check,
     folded into the same generic failure path as the existing `user.status` check — no new
     distinguishable error message, preserving `THREAT_MODEL.md` T11's posture. On a
     transition to `SUSPENDED` or `CLOSED`, every active refresh token for every user in
     the account is revoked immediately (reusing `auth/services.py`'s existing
     `revoke_all_active_sessions`, looped per user) — mirroring `GRX-USER-002`'s existing
     per-user disable behavior, now at the account level, so a suspension takes effect
     immediately rather than only at a user's next token refresh.
  3. **Auditing without `actor_user_id`**: rather than adding a nullable
     `actor_platform_admin_id` column to `audit_logs` (a real schema change, out of this
     task's scope and not required by its acceptance criteria), a platform admin's
     `account.suspended`/`account.reactivated`/`account.closed` action is recorded the same
     way `login()` already records an unresolvable actor (`actor_user_id=None`), with the
     acting platform admin's id and email placed in the event's `metadata` JSON instead.
     This keeps a real, queryable trail of who suspended an account and when without
     touching `audit_logs`' schema — the same trade-off `GRX-SAAS-002`'s own evidence
     entry already flagged and deferred ("no audit-log entry is written for platform
     login/logout... extending that schema is out of Phase B's boundary-only scope").
  4. **"Login/security activity" is a filtered view over the existing `audit_logs` table**,
     not a new table or a raw dump of every event. `audit_logs` already carries
     non-security business events (e.g. contact CRUD) for a busy account, which would bury
     the actual login/security signal a platform admin is looking for. `platform_admin`'s
     account-detail read filters to a fixed allow-list of security-relevant actions
     (`user.login`, `user.login_failed`, `user.logout`, `session.revoked`,
     `user.password_reset_requested`, `user.password_reset_completed`, `role.changed`,
     `account.registered`, `user.email_verified`, `account.suspended`,
     `account.reactivated`, `account.closed`), reusing `audit/services.py`'s existing
     `list_events(account_id=...)` read path unmodified (a neutral read utility, safe to
     reuse across the platform/customer module boundary per this project's established
     reuse policy) rather than adding a parallel query path.
- Consequences: If a future Phase E feature (e.g. `GRX-SAAS-010`'s secure support session)
  needs to attribute an action to a specific platform admin in a genuinely queryable
  (not just metadata-JSON) way, that is a real, separate schema decision at that point —
  this decision does not foreclose it, it only avoids speculatively widening `audit_logs`
  now for a need only this one task has. The security-activity allow-list in point 4 will
  need a one-line addition whenever a future action is judged "security-relevant" (e.g. a
  future MFA event) — a small, expected maintenance cost of filtering rather than dumping.
- Related tasks: `GRX-SAAS-005` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

---

## DEC-GRX-021: Phase E usage/campaign oversight shape — permission scope, "pause" as reused cancellation (not a new resumable state), and an aggregated (not raw) usage view

- Status: APPROVED
- Date: 2026-08-07
- Context: `GRX-SAAS-008` (`SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md` §Phase E) says "Per-account
  `usage_records` view across all accounts; queued/failed campaigns across all accounts;
  abuse controls (pause suspicious sending)." Three things left unspecified: which
  `platform.*` role(s) get the new permission, what "pause" actually does to a campaign's
  state machine (`campaigns.status` has no `PAUSED` value, and the only existing
  transition mechanism — `campaigns/services.py`'s `cancel_campaign` — is terminal), and
  whether "usage view" means a raw cross-account `usage_records` dump or something
  smaller.
- Decisions:
  1. **Permission code and role grant**: one new code, `platform.usage.manage`, granted
     to `platform.owner`, `platform.admin`, and `platform.support` — matching the
     tracker's own stated actor ("A `platform.support`/`platform.admin` user can see any
     account's usage and pause a suspicious campaign"); `platform.owner` gets it too per
     its "full platform control" scope. `platform.finance`/`platform.operations` get
     nothing from this task — usage/campaign oversight is support-facing, not
     billing/infra-facing, per `RBAC.md`'s own role-scope table.
  2. **"Pause" reuses the existing `CANCELLED` terminal state — it is not a new,
     resumable `PAUSED` status.** `campaigns/services.py`'s `cancel_campaign` already
     does exactly the "abuse control" job the tracker describes: it stops a `DRAFT` or
     `SCHEDULED` campaign before the worker ever claims it, which is the only point at
     which stopping a campaign is actually safe — once a campaign is `DISPATCHING` or
     `SENDING`, the worker has already claimed and is actively processing it, and no
     existing mechanism (in `apps/worker`'s dispatch consumer or anywhere else) checks
     campaign status mid-send, so there is nothing today for a `PAUSED` status to
     interrupt. Building genuine send-interruption would mean adding a status re-check
     into the worker's active send loop — a real, separate piece of infrastructure the
     tracker's own wording doesn't ask for and Phase E's own "trim further if a
     capability turns out to be bigger than expected... do not silently expand scope"
     instruction argues against speculatively building now. The platform-admin `pause`
     endpoint therefore calls the exact same `cancel_campaign` function customers
     already use, with the exact same `DRAFT`/`SCHEDULED`-only constraint — a platform
     admin's "pause" and a customer's "cancel" are the same action, just invoked by a
     different, higher-trust actor.
  3. **Usage view is a per-account aggregate, not a raw cross-account row dump.** A
     literal cross-account `SELECT * FROM usage_records` would return every individual
     send event across every account with no ceiling, which is neither what "usage
     tracking per customer" (the source language in
     `FUTURE_SCOPE_PLATFORM_ADMIN.md#proposed-iitdeveloper-platform-admin-capabilities`)
     asks for nor useful to look at. `GET /platform/usage` instead returns one row per
     `(account_id, operation_type)` pair with a summed `quantity` — a single grouped
     query, extensible to future `operation_type` values (AI credits, SMS, etc.) without
     any schema or query-shape change, since nothing about the grouping is hardcoded to
     `email.sent` (`usage_records`' only real writer today, per `GRX-EMAIL-004`).
  4. **Platform-admin campaign audit attribution follows the exact `DEC-GRX-020` pattern**:
     `audit_logs.actor_user_id` cannot reference a `platform_admins.id`, so a pause
     records `actor_user_id=None` with the acting admin's id/email in `metadata` — no new
     reasoning needed here, this is `DEC-GRX-020` point 3 applied to a second action type.
- Consequences: If a genuine mid-send interruption capability is ever required (e.g. a
  compliance mandate to stop an in-flight send), that is a real, separate piece of worker
  infrastructure — a status re-check inside the active send loop plus a new `PAUSED`
  status — and this decision does not foreclose it, it only declines to build it
  speculatively now. The usage aggregate's `GROUP BY` shape will need a `created_at`
  range filter once `usage_records` volume grows enough that an unbounded per-account sum
  stops being cheap; not needed yet at this project's current data volume.
- Related tasks: `GRX-SAAS-008` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

---

## DEC-GRX-022: Secure support session as a dedicated platform-side read/write surface, not literal customer impersonation

- Status: APPROVED
- Date: 2026-08-07
- Context: `GRX-SAAS-010` (`SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md`, deliberately last —
  "highest-trust capability in the sprint") calls for "audited, time-limited,
  banner-visible, read-by-default support access into a customer account — reason +
  ticket number required, platform-admin confirmation, full audit log, no raw API key
  exposure, separate permission gate for write access." Two implementation shapes were
  considered: (a) literal impersonation — issue a platform admin a token that lets them
  browse the customer's real `/dashboard/*` UI as if logged in as that account, or (b) a
  dedicated, purpose-built platform-side view of a curated slice of the account's data,
  with the customer's own dashboard showing a banner while a session is active. User
  confirmed (b) when asked directly.
- Decisions:
  1. **New `support_sessions` table** (`account_id`, `platform_admin_id`, `reason`,
     `ticket_number`, `access_level` ∈ `{READ, WRITE}` default `READ`, `started_at`,
     `expires_at`, `ended_at`) — the system of record for every session: who, why, which
     ticket, how much access, and for how long. `expires_at` is computed at creation time
     from a new `support_session_ttl_minutes` setting (default 60); every read/write
     action re-checks `ended_at IS NULL AND expires_at > now()` at call time, not only at
     creation, so a session cannot be used past its window just because it was valid when
     opened.
  2. **Two new platform-namespace permission codes**: `platform.support_session.create`
     (start a session, default read access, view the session's data, end it early —
     granted to `platform.owner`/`platform.admin`/`platform.support`, matching
     `platform.support`'s own stated scope "Customer support tooling (secure support
     sessions, Phase E)") and `platform.support_session.write` (additionally required to
     start a session with `access_level=WRITE` or perform the one gated write action
     through an active one — granted only to `platform.owner`/`platform.admin`, the same
     higher-trust owner/admin-only shape `DEC-GRX-020` already used for
     `platform.accounts.manage`). This is the literal "separate permission gate for write
     access" the tracker asks for: two independent checks (route-level permission +
     session-level `access_level`) both have to pass, not one.
  3. **Read scope for this checkpoint**: company profile, the account's contacts, and its
     full audit trail (not the security-action-filtered subset `GRX-SAAS-005`'s
     account-detail view already uses — support needs day-to-day operational context, not
     just security events). **Write scope for this checkpoint**: exactly one action,
     editing a contact record, reusing `contacts/services.py`'s existing
     `update_contact` directly rather than duplicating its validation/dedup logic. Neither
     list is meant to be exhaustive forever — matching this project's own "don't build
     ahead of need" practice, more read surfaces or write actions are added the same way
     (a new platform_admin-side route calling the owning module's existing service) as
     real support needs surface, not spelled out speculatively now.
  4. **`update_contact`'s `actor_id` parameter widened from `uuid.UUID` to
     `uuid.UUID | None`, plus a new optional `audit_metadata` parameter.** A platform
     admin has no `users.id` to pass as the audit event's actor — the exact same gap
     `DEC-GRX-020` closed for `platform_admin`'s own module by recording
     `actor_user_id=None` with the acting admin's id/email in `metadata`. Rather than
     re-implement contact-update logic inside `platform_admin` to work around this, the
     one call site that needs it now passes `actor_id=None` and an `audit_metadata` dict
     carrying the platform admin's id/email plus the support session's id — existing
     customer-side callers are unaffected (they keep passing a real `actor_id`, and
     `audit_metadata` defaults to `None`, preserving current behavior exactly).
  5. **No raw API key exposure is satisfied structurally, not by a special case**: no
     support-session route reads or writes `integrations`/`email_provider_connections` at
     all in this checkpoint, and every existing read endpoint for that table already never
     returns a decrypted or even encrypted secret to any caller (`GRX-EMAIL-001`) — there
     is nothing for a support session to leak here even if it were extended to touch that
     module later.
  6. **"Banner-visible" is implemented without touching customer auth**: a new endpoint,
     gated only by the customer's own existing `require_permission`-equivalent
     authentication (any logged-in user of the account, no new permission needed — a
     customer should always be able to see that support currently has eyes on their own
     account), returns whether an active session exists for the caller's `account_id`.
     The customer dashboard shell polls it and renders a persistent banner while one is
     active. This is deliberately the *only* place a support session's existence is
     visible from the customer side — the session itself never causes the customer's own
     UI or API responses to change in any other way.
- Consequences: Support staff see a purpose-built read surface, not the exact pixels of
  the customer's real dashboard — extending *what* is visible is additive (a new route),
  not a re-architecture. The rejected alternative (literal impersonation) would have
  required extending the core `get_current_user`/`require_permission` dependency chain
  used by every existing customer route to recognize a second token shape — a much larger
  blast radius for the sprint's own "highest-trust capability," and a real risk of
  reopening the cross-account leakage class of bug `GRX-SAAS-001`'s account-isolation work
  spent significant effort closing. If true impersonation is genuinely needed later (e.g.
  because the read-surface approach proves insufficient for some support workflow), that
  is a new, separately-considered decision, not a silent extension of this one.
- Related tasks: `GRX-SAAS-010` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

## DEC-GRX-023: Instagram Business is the first (and for MVP, only) social platform (resolves OQ-003)

- Status: APPROVED
- Date: 2026-08-12
- Context: Slice 5 (Social Publishing) cannot start until the first social platform is
  fixed — it determines the OAuth scope, the publishing API shape, and the media
  constraints the rest of the slice is built around. [OQ-003](OPEN_QUESTIONS.md) asked
  which single platform (LinkedIn, Facebook Pages, Instagram Business, X) is first.
- Options considered:
  1. LinkedIn — strong B2B fit, but its content API is materially more restrictive for
     automated/scheduled posting than Meta's.
  2. Facebook Pages — broadest reach, mature Graph API; product owner's audience is more
     visual/Instagram-first.
  3. Instagram Business — visual-first, matches the product's target audience; requires
     an underlying Facebook Page + Meta Developer App (same platform family as option 2).
  4. X (Twitter) — real-time fit, but API access is paid and materially more restrictive
     than Meta's for this use case.
- Decision: Instagram Business (option 3), via the Meta Graph API (Facebook Login for
  Business OAuth → resolve the linked Instagram Business Account through the connected
  Facebook Page). The product owner already has a Meta Developer App with a test
  Instagram Business Account linked to a Facebook Page.
- Rationale: Best fit for Growixa's target customer (visual marketing), and picking it
  keeps the whole Meta family (Facebook Pages later, if ever) on one adapter/app
  registration rather than a second unrelated vendor integration.
- Consequences: Per [DEC-GRX-005](DECISIONS.md), the concrete provider is abstracted
  behind a `SocialProvider`-shaped adapter (`social/instagram_client.py` on the API side,
  `growixa_worker/instagram_client.py` on the worker side) so a second platform later is
  an additive adapter, not a rewrite. Instagram's Content Publishing API has **no
  text-only posts** — every post requires at least one image or video — which is a hard
  constraint the whole post/media data model is built around (see `DATA_MODEL.md` §Slice
  5). Production-scale use (beyond the developer's own test users) requires Meta's App
  Review process for the `instagram_content_publish` permission — a rollout timeline
  concern, not a build blocker, documented in `SPRINT_06_SOCIAL_PUBLISHING.md`.
- Related tasks: `GRX-SOCIAL-*` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

## DEC-GRX-024: Supabase Storage for social post media (resolves OQ-005)

- Status: APPROVED
- Date: 2026-08-12
- Context: Instagram's Content Publishing API has no text-only posts and fetches media by
  plain HTTP(S) URL (it cannot accept a raw upload or an authenticated request), so an
  S3-compatible object storage target is now a hard MVP requirement for Slice 5, not the
  deferred-until-Slice-5 item [OQ-005](OPEN_QUESTIONS.md) originally framed it as.
- Options considered:
  1. Cloudflare R2 — S3-compatible, no egress fees.
  2. AWS S3 — most common choice, most tooling, slightly pricier egress.
  3. Supabase Storage — the project already uses Supabase for production Postgres
     ([render.yaml](../../render.yaml)), so this adds no new vendor account.
  4. Defer/self-host — rejected outright; Instagram's URL-fetch requirement makes some
     public-reachable object storage non-optional for this slice.
- Decision: Supabase Storage (option 3).
- Rationale: One fewer vendor relationship to manage since Supabase is already the
  production database provider; its Storage REST API is simple enough to call directly
  via `httpx` (this codebase's established pattern for provider integrations — see
  `integrations/smtp_transport.py`), with no new SDK dependency.
- Consequences: The bucket that holds post media **must be public-read**, since
  Instagram's Graph API fetches the image by URL with no auth header support — this is
  documented as an accepted risk (`THREAT_MODEL.md` T48), scoped explicitly to this one
  bucket, mitigated by non-enumerable UUID-random object paths, and never reused for
  private/sensitive file storage later. `growixa_api.files.storage_client` is the one
  place that talks to Supabase Storage — per `MODULE_BOUNDARIES.md`, the `files` module
  was already scaffolded in anticipation of exactly this.
- Related tasks: `GRX-SOCIAL-005` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

## DEC-GRX-025: Social OAuth tokens reuse the existing Fernet encryption, no new KMS

- Status: APPROVED
- Date: 2026-08-12
- Context: Instagram's long-lived Page access token must be stored at rest to publish
  posts (including scheduled ones, dispatched later by the worker) and needs the same
  "encrypted at rest, decryptable by both api and worker" property `email_provider_
  connections.smtp_password_encrypted` already has.
- Options considered:
  1. A dedicated secrets-manager/KMS integration (e.g. AWS KMS, Vault) — stronger
     key-rotation story, but a new infrastructure dependency for a threat model
     identical to a credential this codebase already encrypts a simpler way.
  2. Reuse the existing Fernet-based `encrypt_secret`/`decrypt_secret` helpers in
     `auth/encryption.py` ([DEC-GRX-009](DECISIONS.md)), keyed by the same
     `Settings.encryption_key` the worker already mirrors for SMTP passwords.
- Decision: Option 2 — reuse `auth/encryption.py` as-is for
  `social_connections.access_token_encrypted`.
- Rationale: Identical trust and threat model to the SMTP credential already encrypted
  this way; a second encryption scheme would be pure duplication with no security benefit
  at this scale, and it keeps the worker's existing key-mirroring setup (`growixa_worker/
  encryption.py`) valid for a second table with zero new configuration.
- Consequences: No new settings beyond what `DEC-GRX-009` already introduced. If a future
  compliance requirement forces a real KMS, that migration affects both credential types
  (SMTP and social) together, not just one.
- Related tasks: `GRX-SOCIAL-002` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

---

*Decisions DEC-GRX-026 onward will be logged as they are made — e.g., resolutions to
OQ-004, OQ-006 through OQ-011 in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).*
