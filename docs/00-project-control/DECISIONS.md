# Decision Log

- Document ID: DOC-DECISIONS
- Status: ACTIVE
- Version: 1.8
- Last updated: 2026-08-17
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

## DEC-GRX-026: AI provider strategy — multi-provider adapter, platform default + per-account bring-your-own (resolves OQ-004)

- Status: APPROVED
- Date: 2026-08-12
- Context: Slice 6 (AI Assistant) cannot start until the provider strategy is fixed — it
  determines the adapter interface shape, the credential-storage model, and whether
  generation is even possible before any account configures anything.
  [OQ-004](OPEN_QUESTIONS.md) asked which AI provider(s)/model(s) for the content
  assistant. The product owner's explicit requirement: OpenAI, Azure OpenAI, Anthropic,
  and Ollama (self-hosted) must all be supported; a platform admin configures a
  platform-wide default; any customer account may optionally override it with its own
  "bring your own model" (BYO) credentials.
- Options considered:
  1. Single fixed provider (e.g. OpenAI only) — simplest, but explicitly rejected by the
     product owner; also weaker fit for cost/privacy-conscious customers who want
     self-hosted Ollama.
  2. Multi-provider, but customer-configured only (no platform default) — would leave a
     brand-new account with no working AI features until it configures its own
     credentials, unlike every other provider-backed feature in this codebase
     (email, social) which at minimum boots to a clean "not configured" state without
     blocking unrelated functionality; a platform default avoids AI being dead-on-arrival
     for accounts that haven't set anything up.
  3. Multi-provider, platform-admin-configured default (new pattern — first DB-backed,
     admin-editable platform setting in this codebase; every existing platform-level
     setting today is `.env`-only, restart-required) + per-account BYO override (mirrors
     `email_provider_connections`, `DEC-GRX-016`).
- Decision: Option 3. `AIModelProvider` (already named as an adapter interface in
  [DEC-GRX-005](DECISIONS.md)) gets one concrete implementation per vendor
  (OpenAI/Azure OpenAI/Anthropic/Ollama), all raw-`httpx`-based (this codebase's
  established no-vendor-SDK convention — Postmark, Supabase Storage, and Instagram Graph
  API all integrate this way). Resolution order per generation call: the calling
  account's active `ai_provider_connections` row if one exists, else the platform's
  active `platform_ai_provider_config` row, else a clean "AI not configured" error —
  never a silent hardcoded fallback to one specific vendor.
- Rationale: Matches the product owner's explicit requirement without narrowing it;
  reuses the adapter pattern already decided in principle; the platform-default +
  per-account-override shape is a proven pattern in this codebase
  (`PLATFORM_SMTP_*`/`email_provider_connections`), just promoted from `.env`-only to a
  real DB-backed table on the platform side so a platform admin can change it without a
  redeploy.
- Consequences: `ai_provider_connections`/`platform_ai_provider_config` both store
  credentials Fernet-encrypted via the existing `auth/encryption.py`
  (`encrypt_secret`/`decrypt_secret`), no new crypto (same reasoning as
  [DEC-GRX-025](DECISIONS.md)). Azure OpenAI and Ollama both take a customer/admin-supplied
  `base_url` — a genuine SSRF surface, addressed separately in
  [DEC-GRX-027](DECISIONS.md). BYO connection *management* (entering/rotating a
  third-party API key) reuses the existing `integrations.manage` permission — the same
  class of action as connecting Postmark/Instagram — rather than a new permission; see
  `RBAC.md §Slice 6`.
- Related tasks: `GRX-AI-002`, `GRX-AI-003`, `GRX-AI-004`, `GRX-AI-005` in
  `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

## DEC-GRX-027: SSRF-safe validation for customer/admin-supplied AI provider `base_url`, applied uniformly

- Status: APPROVED
- Date: 2026-08-12
- Context: Azure OpenAI and Ollama (per [DEC-GRX-026](DECISIONS.md)) both require a
  custom `base_url` — unlike OpenAI/Anthropic's fixed official hostnames, this field is
  fully attacker-or-customer-controlled. A malicious or careless `base_url` (a cloud
  metadata endpoint, an internal service address) sent through the API server's own
  outbound `httpx` call is a real SSRF vector.
- Options considered:
  1. Restrict custom `base_url` to platform-admin-only configuration (trusted actor),
     limit customer-level BYO to OpenAI/Anthropic only (fixed, safe base URLs) —
     removes the surface for customer-supplied URLs, but silently disappoints a real use
     case (self-hosted Ollama for cost/privacy-conscious customers) without actually
     fixing the underlying class of risk, only narrowing who can trigger it.
  2. Validate every custom `base_url`, regardless of who supplies it: reject non-http(s)
     schemes; resolve the hostname and reject private/loopback/link-local/multicast IP
     ranges and the `169.254.169.254` metadata address specifically; re-resolve and
     re-check at **call time**, not only at connection-save time (defeats DNS
     rebinding — a hostname that resolves safely at save time but to an internal address
     later); don't follow a redirect without re-validating the redirect target's
     resolved IP.
- Decision: Option 2, implemented once in `ai/providers/base.py` and applied uniformly
  to both `platform_ai_provider_config.base_url` and `ai_provider_connections.base_url`
  — no asymmetry between platform-admin and customer-supplied values.
- Rationale: Properly fixes the vulnerability class rather than narrowing who can trigger
  it; keeps Ollama available as genuine per-account BYO, which the product owner's own
  requirement calls for; the call-time re-check specifically closes the DNS-rebinding gap
  a save-time-only validator would miss.
- Consequences: Every AI provider call through a custom-`base_url` adapter
  (`azure_openai_provider.py`/`ollama_provider.py`) pays one extra DNS resolution + IP
  check per call — accepted cost for closing a real SSRF path. See `THREAT_MODEL.md
  §Slice 6` for the full threat entry.
- Related tasks: `GRX-AI-003` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

## DEC-GRX-028: AI prompt templates are code-defined, not a customer-editable database table, in MVP

- Status: APPROVED
- Date: 2026-08-12
- Context: `DATA_MODEL.md`'s Slice 6 placeholder speculatively named four tables,
  including `ai_prompt_templates`/`ai_prompt_versions` — a fully versioned,
  presumably-editable prompt-template system. Nothing in `MVP_SCOPE.md §E` actually
  calls for customer-facing prompt template editing; the scope is generate/rewrite/
  suggest capabilities with a human-reviewed output, not a prompt-engineering UI.
- Options considered:
  1. Build `ai_prompt_templates`/`ai_prompt_versions` as designed in the placeholder —
     a real versioned-template system with no UI to actually edit templates in MVP,
     making it exactly the kind of speculative table this codebase already has one
     unused cautionary example of (`usage_records`, built Sprint 1 per
     [DEC-GRX-007](DECISIONS.md), zero writers anywhere until this same slice).
  2. Keep prompts as plain code in `ai/prompts/templates.py` (one prompt-builder
     function per capability), and log which one produced a given generation via a
     single `prompt_template_key` string column (e.g. `"subject_line.v1"`) on
     `ai_generations` — still fully satisfies `GRX-AI-006`'s "prompt version... logged
     for every generation" requirement, with no unused schema.
- Decision: Option 2.
- Rationale: Avoids repeating a known mistake in this exact codebase; a versioned
  template table only earns its complexity once there's an actual UI/workflow that
  edits templates, which is explicitly out of MVP scope.
- Consequences: `ai_usage_events` is also collapsed into token/cost columns directly on
  `ai_generations` (strict 1:1 with a generation, no concrete case yet for a
  non-generation usage event) — Slice 6 ships 3 new tables total
  (`ai_generations`, `ai_provider_connections`, `platform_ai_provider_config`), not the
  4 the placeholder named. If template editing becomes a real requirement later, adding
  a versioned-template table then is additive, not a rewrite — `prompt_template_key`
  already gives every past generation a stable reference to migrate onto.
- Related tasks: `GRX-AI-002` in `MASTER_TASK_TRACKER.md`.
- Supersedes: none.
- Supersedes: none.

## DEC-GRX-029: Payment gateway for billing (`GRX-SAAS-004`) is Razorpay, not Stripe, with dual-currency support and a usage top-up concept — plan tiers/pricing/charge model still pending

- Status: PARTIALLY APPROVED — resolves the vendor/currency/shape question; the exact
  plan tiers, prices, subscription charge type, and top-up calculation rules are
  explicitly deferred by the product owner (see Open item below), tracked as
  [OQ-013](OPEN_QUESTIONS.md).
- Date: 2026-08-13
- Context: `GRX-SAAS-004`'s tracker row shipped with "Stripe assumed, confirm before
  starting" as an explicit placeholder — [OQ-007](OPEN_QUESTIONS.md) asked whether
  there's a billing requirement for MVP at all, or whether usage stays internal-only
  (per `ASM-008`). The product owner confirmed directly: they already hold a Razorpay
  account, and billing must support **both** Indian (₹) and international ($) customers
  from one integration. They also want, in addition to recurring subscriptions, a
  **usage top-up/credit** purchase path, and confirmed that **feature availability, not
  just usage limits, varies by plan tier** (some features exist only on higher tiers).
  Exact plan names, prices, which Razorpay billing primitive to use (Subscriptions API
  vs. self-managed Orders), and how top-ups are priced/consumed are all still
  unspecified — the product owner will provide these later, not guessed here.
- Options considered (vendor):
  1. Stripe, as the tracker row's original placeholder assumed — global reach, mature
     Subscriptions API and docs, but the product owner has no existing Stripe account
     and does hold a working Razorpay account; standing up a second vendor relationship
     for no stated benefit is wasted setup cost.
  2. Razorpay, INR-only — matches the vendor's native currency and is the simplest
     integration, but shuts out the international customers the product owner
     explicitly wants to bill, and doesn't match the marketing site's existing
     $-denominated pricing (`(marketing)/pricing-section.tsx`, built under
     `GRX-WEB-002`).
  3. Razorpay, dual-currency (INR for Indian customers, USD for international via
     Razorpay's international payment methods) — matches the product owner's explicit
     requirement directly, keeps a single vendor integration.
- Decision: Option 3 for the vendor/currency shape. The exact billing primitive
  (Razorpay Subscriptions vs. self-managed Orders + own renewal tracking), plan
  tiers/pricing, and top-up mechanics remain **open** — see
  [OQ-013](OPEN_QUESTIONS.md). `GRX-SAAS-004`'s schema/threat-model design work may
  proceed on the *shape* implied here (multi-currency, subscription + top-up ledger,
  plan→feature mapping), but no plan-limit values, prices, or Razorpay Plan IDs may be
  hardcoded until OQ-013 resolves.
- Rationale: Directly matches the product owner's own account and stated dual-market
  requirement; avoids maintaining two payment-vendor integrations for one product.
- Consequences:
  1. The `subscriptions` (and any top-up/credit ledger) table needs a `currency` column
     — no assumption of a single global currency anywhere in the billing schema.
  2. Razorpay webhook signature verification is the one authenticated inbound path,
     built once and reused regardless of currency (mirrors the existing Postmark
     webhook's "verify before touching any table" shape, per `GRX-SAAS-004`'s own
     tracker description).
  3. The eventual schema needs a plan→feature-flag mapping, not just a plan→price
     mapping, since the product owner confirmed some features are tier-gated, not only
     usage limits — worth designing the join shape for now even before the actual flags
     are named, so `GRX-SAAS-006`/`GRX-SAAS-009` (both of which read this schema) aren't
     built against a shape that has to change later.
  4. A top-up/credit concept sits alongside recurring subscriptions, not instead of
     them — likely its own ledger table (e.g. a `credit_balance` + `credit_transactions`
     shape) rather than overloading `subscriptions`, but the exact mechanic (what
     top-ups buy — AI generation credits? email sends? something else?) is unspecified
     pending OQ-013.
  5. `GRX-SAAS-004`, and its dependents `GRX-SAAS-006`/`GRX-SAAS-009`, move from
     `BACKLOG` to `BLOCKED` in `MASTER_TASK_TRACKER.md`, per this doc's own stated rule
     that a task depending on an unresolved `OPEN_QUESTIONS.md` entry must be marked
     `BLOCKED`, not guessed at.
- Related tasks: `GRX-SAAS-004`, `GRX-SAAS-006`, `GRX-SAAS-009` in
  `MASTER_TASK_TRACKER.md`.
- Supersedes: none.

## DEC-GRX-030: Billing architecture — Razorpay Subscriptions API, non-expiring credits, permanent audit logs, contact-sales Enterprise, admin override UI, coupon engine (resolves `OQ-013`)

- Status: APPROVED
- Date: 2026-08-13
- Context: `DEC-GRX-029` confirmed the vendor (Razorpay, dual-currency) but left the
  billing primitive, credit-expiry policy, audit-retention behavior, and the
  Enterprise tier's sales model open as `OQ-013`. The product owner was asked four
  direct questions and answered all four with the recommended option; two further
  scope confirmations (platform-admin override UI, coupon/discount codes) were given
  in the same conversation. This decision also corrects two internal inconsistencies
  found in `BILLING_SYSTEM_ARCHITECTURE.md`'s working draft, which had drifted out of
  sync with the answers given here (still showing tiered audit deletion and a
  self-serve-priced Enterprise tier).
- Decisions (five, each independently confirmed):
  1. **Billing primitive: Razorpay Subscriptions API**, not self-managed Orders.
     Razorpay owns the recurring charge and auto-billing; Growixa reacts to webhook
     events (`subscription.activated`/`charged`/`cancelled`/`halted`) rather than
     initiating charges itself. Trade-off accepted: renewal-cycle timing is partly
     defined by Razorpay's own Plan objects, not purely our DB.
  2. **Top-up credits never expire.** One running balance per
     `(account_id, credit_type)` (`account_credit_balances`), not per-purchase batches
     with expiry dates. A separate `account_credit_purchases` table still exists, but
     purely as a receipt/audit trail — it is never read by the quota evaluator, which
     only ever touches the summed balance. This also resolves the earlier
     multi-batch-FIFO bug (a single atomic `UPDATE ... SET remaining_credits =
     remaining_credits - :needed WHERE remaining_credits >= :needed` is now correct
     with no batch-spanning logic needed).
  3. **Audit logs stay permanent for every plan tier — no tiered deletion, no purge
     job.** This matches the "insert-only audit log" compliance feature already
     advertised on the public marketing site (`(marketing)/security-section.tsx`);
     silently deleting a paying (or free) customer's compliance trail after 7–365 days
     was never something the product actually promised, and building a job whose sole
     purpose is permanently destroying audit data is a real liability to get wrong.
     `subscription_plans.audit_retention_days` and the `purge_audit_logs` worker job
     are both **removed** from the architecture. Tier differentiation on this feature
     row is replaced with **audit log export/API access** (Free: UI view only;
     Starter+: CSV export; Pro+: programmatic API access) — a real, safe way to keep
     this as a paid-tier value driver without deleting anyone's data.
  4. **Enterprise is contact-sales / platform-admin-activated, not a self-serve
     Razorpay checkout tier.** Matches the marketing site's existing "Custom pricing /
     Contact Sales" framing (`pricing-section.tsx`, `GRX-WEB-002`) rather than the
     draft's fixed `$149`/`₹11,999` self-serve price. A platform admin sets an
     account's plan to Enterprise directly (see decision 5) — `subscriptions.plan_id`
     can point at the Enterprise `subscription_plans` row with
     `razorpay_subscription_id` left `NULL` (no recurring Razorpay charge object at
     all), or with one if the admin separately arranges Razorpay billing for that
     specific enterprise customer. Either is valid; the schema doesn't force a choice.
  5. **Platform-admin subscription management is in scope — and it isn't new scope.**
     It's exactly what `GRX-SAAS-006`'s tracker row already describes ("View/change
     plans, trial extensions, usage credits"). This decision makes it concrete: a
     platform admin (`platform.finance`/`platform.admin` role, per that row's own
     acceptance criterion) can, for any account, at any time: override the plan
     directly (no payment/webhook required), grant free top-up credits, change
     subscription status (`ACTIVE`/`PAST_DUE`/`HALTED`/`CANCELED`), and edit a plan's
     quotas/prices platform-wide. All four are additive to the customer-facing
     Razorpay checkout flow, not a replacement for it.
  6. **Coupon/discount codes are new, additional scope** — not previously in
     `MASTER_TASK_TRACKER.md` under any task. Percentage discount, fixed-amount
     discount, and free-credit-grant coupon types, redeemable at Razorpay checkout
     time, admin-managed (create/disable/track redemptions), account- or plan-
     eligibility-restricted. Tracked as new task `GRX-SAAS-012`.
- Rationale: Every choice here is the one the product owner picked directly (four via
  explicit A/B question, two by direct confirmation) except the audit-retention
  reversal, which is a correction — the working draft's tiered-deletion design
  contradicted the product owner's own answer in the same conversation, and
  contradicted this codebase's own already-shipped compliance positioning.
- Consequences:
  1. `BILLING_SYSTEM_ARCHITECTURE.md` is rewritten to match all six points exactly,
     replacing the inconsistent working draft.
  2. `subscription_plans_matrix.csv`'s "Audit Log Retention" row is replaced with
     "Audit Log Export/API Access"; the Enterprise pricing cells read "Custom / Contact
     Sales" instead of fixed `$149`/`₹11,999`.
  3. `OQ-013` moves from `OPEN` to `RESOLVED` for the *architecture/model* questions.
     The specific plan quota numbers and Starter/Pro prices in the CSV remain a working
     draft, not yet confirmed as final by the product owner — `GRX-SAAS-004` stays
     `BLOCKED` until that final confirmation, at which point it can move to `READY`.
  4. `GRX-SAAS-006`'s row is extended with the four concrete admin-override endpoints
     from decision 5. New task `GRX-SAAS-012` (Coupon/discount engine) is added,
     depending on `GRX-SAAS-004`.
- Related tasks: `GRX-SAAS-004`, `GRX-SAAS-006`, `GRX-SAAS-009`, `GRX-SAAS-012` (new) in
  `MASTER_TASK_TRACKER.md`.
- Supersedes: none (refines `DEC-GRX-029`, does not replace it).

---

## DEC-GRX-031: Multi-domain subdomain architecture (feature captured, not yet implemented)

- Status: PARTIALLY APPROVED — architecture locked, three deployment specifics still open
- Date: 2026-08-14
- Context: Growixa runs today as one Next.js app on a single domain
  (`growixa.netlify.app`), with `(dashboard)`/`(platform)` route groups separating
  customer and platform-admin audiences by path (`/dashboard/*`, `/platform/*`), not by
  domain. This was workable for the MVP build but doesn't match `DEC-GRX-017`'s
  self-service SaaS positioning — a real product launch needs a clean marketing site
  separated from the logged-in product, and clean URLs (`/campaigns`, not
  `/dashboard/campaigns`). Captured here as a locked product/architecture decision, per
  product-owner review of the standalone plan; implementation is separately tracked, not
  bundled into this decision.
- Decisions locked:
  1. Three subdomains, one single deployment (no separate apps/servers, routing handled
     by `middleware.ts` reading the `Host` header): `<domain>` → marketing site only
     (public); `app.<domain>` → the entire customer product (auth pages + every
     feature page, not just "the dashboard"); `platform.<domain>` → platform admin only.
  2. Route group rename in code: `(dashboard)` → `(customer)`.
  3. Clean URL paths on `app.*` — the `/dashboard` prefix is dropped (`/campaigns`, not
     `/dashboard/campaigns`).
  4. Both `app.*` and `platform.*` get their own home/overview page at `/` after login,
     rather than redirecting straight into a feature page.
- Still open (blocks implementation, not just detail-level): `OQ-SUB-001` (is the
  production domain actually `growixa.com`, or something else — not yet confirmed by the
  product owner), `OQ-SUB-002` (hosting platform for the domain aliases — now
  **effectively answered** as Netlify, since `GRX-SAAS-013`/this same session confirmed
  Hugging Face + Netlify, not Render, is the real deployed stack; the alias-configuration
  detail in the plan still needs updating to match), `OQ-SUB-003` (does `app.<domain>/`
  show a real overview page after login, or redirect straight to `/campaigns` — determines
  whether a new home-overview page needs building as part of this work, or can reuse the
  one `GRX-SAAS-013`'s dashboards work is about to build for `GRX-FEAT-023`/`028`).
- Consequences:
  1. `docs/02-features/FEATURE_CATALOG.md` gains `GRX-FEAT-029 — Multi-Domain Subdomain
     Routing`, status `NOT_STARTED` — captured as a real, scoped feature, not
     implemented by this decision.
  2. `docs/01-product/ROADMAP.md`'s "Sprint 5 — Customer Account Platform Foundation"
     section gains a note that this piece of Sprint 5's self-service launch scope
     remains outstanding.
  3. Not started: no `middleware.ts`, no route-group rename, no DNS/hosting alias
     configuration. `OQ-SUB-001`/`002`/`003` must be resolved before any of that begins
     (per `AGENT_EXECUTION_RULES.md`'s "no task below READY may be started").
- Related tasks: none yet in `MASTER_TASK_TRACKER.md` — create a `GRX-SAAS-*` row once
  `OQ-SUB-001`/`003` are answered and this becomes `READY`.
- Supersedes: none.

## DEC-GRX-032: Lightweight multi-agent independent-review workflow (Phase 1)

- Status: APPROVED
- Date: 2026-08-15
- Context: Growixa is developed in parallel by multiple coding agents/tools (Claude
  Code, OpenAI Codex, Antigravity, GitHub Copilot, more later), coordinated by the
  product owner, who
  also personally reviews and merges every branch today (per `WORKTREE_TRACKER.md`'s
  existing merge protocol). A live example this session (`feature/FRONTEND/GRX-AI-STUDIO-001`)
  showed real value in independent review — a same-session review caught a genuinely
  fabricated AI quality-score feature before merge. The product owner asked whether the
  full team-scale review-workflow design (a `pr_reviews/pending/in_review/
  changes_requested/approved/archived` state machine with atomic reviewer-claiming and
  stale-approval detection) was needed now. Evaluated against actual repo state: only
  one worktree is active at a time in practice, and every handoff is already
  human-mediated — the collision problem the full state machine defends against does not
  yet exist. Decision: adopt a lightweight Phase 1 now, defer the full state machine
  until concurrency actually requires it.
- Decisions locked:
  1. One handoff file per branch at `pr_reviews/<branch-name-with-slashes-as-dashes>.md`
     (no `pending/`/`in_review/`/etc. subfolders yet). Template, review process, and
     merge rules are in [AGENT_EXECUTION_RULES.md §Independent
     review](../12-development/AGENT_EXECUTION_RULES.md#independent-review-mandatory-before-merge).
  2. No agent may merge or approve its own work; independent review from a different
     agent/tool is required where practical before every merge.
  3. `Reviewed Code Commit` (the SHA whose code was actually reviewed, distinct from
     `Review Record Commit` — the later commit that records the verdict itself, since
     writing `APPROVED` into the handoff file necessarily happens after the code it
     describes) must have no changes outside `pr_reviews/**` between it and the branch's
     current HEAD before merge — any later source/test/config/migration/docs/dependency
     change, including a substantive conflict-resolution, invalidates the approval and
     forces re-review. (Corrected post-rollout: a naive `Reviewed Commit == HEAD` check
     is self-contradicting, since recording the review verdict is itself a commit that
     advances HEAD past the code it reviewed — it could never pass.)
  4. Independent-agent `APPROVED` is required for every merge. Product-owner approval is
     additionally required, recorded in the same file, for UI/UX, customer-facing, or
     high-risk (auth/RBAC/billing/migrations) changes; optional for backend-only/internal
     changes.
  5. Existing conventions are reused, not replaced: branch naming
     (`feature/BACKEND|FRONTEND/<TASK-ID>`), commit/co-author format,
     `DEFINITION_OF_DONE.md`, `RBAC.md`, `THREAT_MODEL.md` as the review bar.
     `MASTER_TASK_TRACKER.md`'s status enum is **unchanged** — `IN_REVIEW` covers the
     whole review/fix/re-review cycle; `READY_FOR_REVIEW`/`CHANGES_REQUESTED`/`APPROVED`
     are review states scoped to the per-branch `pr_reviews/` file only, never new task
     statuses.
  6. Reviewer preference: a different agent/tool is preferred; a fresh same-tool session
     with no memory of the developer's work is an explicitly documented fallback when no
     other tool is available (recorded in the handoff file's `Reviewer` field).
  7. Explicit upgrade triggers to the full folder-state system are documented in
     `AGENT_EXECUTION_RULES.md` rather than adopting it preemptively (e.g. 3–5+ worktrees
     regularly active at once, agents self-assigning tasks, multiple simultaneous
     reviewers, branches no longer trackable from memory).
  8. Root `AGENTS.md` (not `.agents/AGENTS.md`) is the single canonical, tool-neutral
     governance file. This corrects the original rollout of this decision, which placed
     the file at `.agents/AGENTS.md` — verified afterward, by direct research into each
     tool's actual auto-discovery behavior, to be a location that Codex, Antigravity, and
     GitHub Copilot do not automatically read (they walk for a file literally named
     `AGENTS.md` at the repo root, not nested inside a differently-named subfolder).
     Every tool-specific file is a thin adapter pointing at root `AGENTS.md` — none
     duplicates the shared rules:
     - **Claude Code** — root `CLAUDE.md` containing an `@AGENTS.md` import (Claude Code's
       native import syntax; auto-loaded every session).
     - **OpenAI Codex CLI** — reads root `AGENTS.md` directly; no adapter file needed.
     - **Google Antigravity** — reads root `AGENTS.md` directly, plus a thin workspace
       rule at `.agents/rules/growixa-governance.md` (Antigravity's current default
       workspace-rules path) pointing back at root `AGENTS.md` and
       `AGENT_EXECUTION_RULES.md`.
     - **GitHub Copilot coding agent** — reads root `AGENTS.md` directly (Copilot added
       native `AGENTS.md` support in 2025), plus a thin `.github/copilot-instructions.md`
       explaining the one real structural difference: Copilot's coding agent runs in a
       GitHub-hosted cloud sandbox on a real branch/PR, not this repo's local
       `.worktrees/` model — while still following the same DoD, review-handoff,
       independent-review, `Reviewed Code Commit`/no-changes-outside-`pr_reviews/**`,
       no-self-approve, and no-self-merge rules as every other agent.
  9. `.agents/AGENTS.md` is deleted, not kept as a legacy pointer — verified first that
     nothing programmatically depends on it (`.agents/hooks.json` and
     `.agents/scripts/*.sh` reference only their own script paths;
     `stop_guard.sh`'s "AGENTS.md rule #3" text is a human-readable reminder string, not
     a file-path dependency). `.agents/hooks.json` and `.agents/scripts/` are otherwise
     unchanged.
- Consequences:
  1. `pr_reviews/` created (flat, no subfolders) with a short `README.md`.
  2. `AGENT_EXECUTION_RULES.md` gains an "Independent review" section (template, process,
     human-approval rule, upgrade triggers).
  3. Root `AGENTS.md` created as the canonical file (migrated from `.agents/AGENTS.md`,
     which is deleted); root `CLAUDE.md`, `.agents/rules/growixa-governance.md`, and
     `.github/copilot-instructions.md` created as thin per-tool adapters.
  4. `WORKTREE_TRACKER.md`'s merge protocol now requires an `APPROVED` handoff file (with
     no changes outside `pr_reviews/**` since `Reviewed Code Commit`) in addition to the
     existing user-confirms-`localhost:3001` step for UI/UX work.
  5. The in-flight `feature/FRONTEND/GRX-AI-STUDIO-001` branch is **not** retroactively
     forced into this system — it already went through an informal review/fix cycle this
     session and finishes under that process. The new process applies to tasks started
     after this decision.
- Related tasks: none yet — applies process-wide, not to a single `MASTER_TASK_TRACKER.md`
  row.
- Supersedes: none (extends `WORKTREE_TRACKER.md`'s existing merge protocol, doesn't
  replace it).

---

*Decisions DEC-GRX-033 onward will be logged as they are made — e.g., resolutions to
OQ-004, OQ-006 through OQ-011 in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).*

## DEC-GRX-033: External contact acquisition — scope expansion beyond first-party audiences

- Status: **PROPOSED** — requires the product owner's explicit confirmation. Nothing may
  be built, scaffolded, or entered into `MASTER_TASK_TRACKER.md` while this is `PROPOSED`.
- Date: 2026-08-15
- Context: `FUTURE_SCOPE_LEAD_INTELLIGENCE.md` (2026-07-30) captured three ideas from a
  revspot.ai review, and gated all three behind one unresolved business-model question.
  Idea #3 — contact extraction & enrichment from external sources — has now been raised
  again by the product owner, who directed (2026-08-15) that the gate be opened properly
  rather than bypassed: resolve the business-model call and write the missing
  provenance/consent analysis *first*, then build. This entry is that call, drafted for
  confirmation. It is deliberately `PROPOSED`, not `APPROVED` — an agent may not decide
  the product's category on the product owner's behalf.
- The actual question: does Growixa's scope expand from **"automate marketing to contacts
  a company already has"** to **"also acquire contacts a company does not have yet"**?
  Per `DEC-GRX-001` and `PRD.md` §9, the former is Growixa's stated positioning. The
  latter is a different product category — closer to outbound lead-gen than to marketing
  automation. This is a positioning change, not a feature addition.

### Proposed decision (for confirmation)

1. **Scope does expand**, but narrowly: Growixa may ingest and manage externally-sourced
   contacts. It is a marketing-automation platform that can *accept* external contact
   data, not a lead-generation product that *sells* leads or audiences.
2. **Growixa does not perform acquisition on the customer's behalf in a first version.**
   The customer supplies the data; Growixa ingests it with mandatory provenance. This
   keeps collection liability (T84) with the party that chose the source, and it is
   reversible — Growixa-operated acquisition can be added later, whereas an
   acquisition-as-a-service posture is very hard to walk back.
3. **The customer is the data controller** for contacts they supply, and warrants a
   lawful basis at ingest. Growixa is the processor. This must be reflected in the terms
   of service before the capability ships — it is not merely an internal position.
4. **Externally-sourced contacts are not sendable by default** (T82). They enter a
   distinct, non-sendable consent state; promotion requires an explicit, audited action.
5. **Inferred enrichment attributes (income band, intent score) are out of scope** for a
   first version (T87). Verified factual attributes only.
6. **Sending reputation is ring-fenced** (T83). The specific mechanism — mandatory
   pre-send validation, separate IP pool/subaccount, volume caps, or some combination —
   is deferred to a design task, but *some* mechanism is mandatory, not optional.

### Preconditions before any `GRX-*` task may be created

- This decision moves to `APPROVED` by the product owner.
- `THREAT_MODEL.md` §"Pre-build — External contact acquisition & enrichment" (T81–T87,
  added 2026-08-15) has its required controls converted into acceptance criteria.
- `OQ-020` is answered (ESP AUP position — see below).
- `OQ-008` (retention) and `OQ-017` (suppression storage/provenance) are resolved, since
  both are load-bearing for T81 and T85.

### Consequences if APPROVED

1. `PRD.md` §9 positioning and §6 target users need amending — the current text describes
   a first-party-audience product, and would become inaccurate.
2. `MVP_SCOPE.md` §"Deferred, not cancelled" currently lists "LinkedIn/CSV contact
   enrichment" as requiring "an explicit scope decision, not just a backlog slot." This
   is that decision; that bullet must be updated to reference it.
3. `FUTURE_SCOPE_LEAD_INTELLIGENCE.md` idea #3 leaves idea-capture status and becomes a
   real feature entry in `FEATURE_CATALOG.md`. Ideas #1 (voice) and #2 (licensed data)
   are **not** unlocked by this decision and stay gated.
4. A data-model change (mandatory provenance columns, new consent state) plus a terms-of-
   service change. The ToS change is the long pole and is not an engineering task.

### Consequences if REJECTED

`FUTURE_SCOPE_LEAD_INTELLIGENCE.md` stays idea-capture only. Customers who want external
contacts continue to use the existing `GRX-FEAT-007` Contact Import, which already works
for a CSV the customer sourced themselves — no new capability, no scope change, and the
existing suppression/unsubscribe/footer machinery already covers the sending obligations.
This is a genuinely viable "do nothing" path, not a strawman.

- Related: `FUTURE_SCOPE_LEAD_INTELLIGENCE.md`, `THREAT_MODEL.md` T81–T87, `OQ-020`,
  `DEC-GRX-001` (positioning), `DEC-GRX-008` (suppression/consent mandatory),
  `DEC-GRX-015` (shared Postmark sending path — the T83 blast radius).
- Supersedes: none. Narrows, but does not supersede, `DEC-GRX-001` if approved.

### Addendum, 2026-08-16 — Lead Intelligence module shape

Recorded after an extended product discussion. Kept as an addendum rather than a rewrite
so the original proposal above stays auditable. Still `PROPOSED` — none of this is
approved, and the addendum raises two questions that must be answered *before* approval
(`OQ-021`, `OQ-023`).

**`OQ-020` is now answered, and it constrains everything below.** Postmark's published
Terms of Service require permission-based subscription lists with explicit opt-in and
prohibit purchased, rented, free, acquired, and cross-branded lists, with suspension or
termination as the stated remedy; their "sending on behalf of others" guidance states that
customers wanting to send to acquired lists are not a good fit for the platform. Verified
directly against the vendor's own terms, not inferred.

Three consequences:

1. **Enrichment is not permission.** A contact being discovered, enriched, and verified
   says nothing about whether it may be emailed. These must be separate states in the data
   model, never collapsed. This becomes a core product rule, not an implementation detail.
2. **Channel eligibility is mandatory architecture** (point 6 above), enforced server-side
   at campaign-recipient selection. Per channel — email, SMS, WhatsApp, voice — each
   independently `ELIGIBLE` / `NOT_ELIGIBLE` / `UNKNOWN`, defaulting to `UNKNOWN`, with
   `UNKNOWN` non-sendable.
3. **Eligibility is evaluated per sending path, not globally.** *(Corrected 2026-08-16 —
   an earlier draft of this addendum claimed V1 ships with its email channel closed
   outright. That was wrong: it overlooked `DEC-GRX-016`, which added `CUSTOM_SMTP`
   alongside Postmark.)* The two paths differ materially:
   - **Postmark** — closed for acquired contacts, per `OQ-020`. Growixa's own vendor
     relationship is at stake and every account on this path shares the reputation, so
     T83's blast radius is other customers.
   - **`CUSTOM_SMTP`** — the customer sends through their own server or ESP account.
     Postmark's AUP is irrelevant to it; the binding constraints become the customer's
     own provider's AUP, the recipient's jurisdiction, and Growixa's terms of service.
     **T83's cross-customer blast radius does not exist on this path** — a spam trap
     damages the sending customer's own domain and IP, not anyone else's.

   This makes `CUSTOM_SMTP` the architecturally honest home for externally-sourced
   sending, and it means Lead Intelligence V1 does have a viable outbound path rather
   than being research-only. Whether Growixa *permits* that, and on what attestation, is
   `OQ-024` — still open. The eligibility engine must be path-aware from the first
   commit; retrofitting a per-path dimension onto a global flag later is exactly the kind
   of rework this decision exists to avoid.

#### Adopted into the proposal

- **A distinct `Lead Intelligence` module**, not 50 more columns on `contacts`. Keeps the
  existing Contacts module simple and gives enrichment, verification, provenance,
  eligibility, scoring, and (later) qualification one owning boundary.
- **Discovery / Extraction / Enrichment are three separate stages**, not one thing called
  "scraping". Different sources, different rights, different risk. Two distinct provider
  interfaces — `LeadSourceProvider` (discovers/imports a base entity) and
  `LeadEnrichmentProvider` (adds attributes to an existing entity) — never one generic
  provider doing both.
- **A Source Registry with a per-source rights profile**, checked before any acquisition
  runs: source type, access method, approval status, permitted operations (discovery /
  enrichment / commercial use / redistribution), attribution and permission requirements,
  and the date the policy was last verified. The crawler must never be able to conclude
  on its own that "public page = safe to scrape." This is the strongest idea to come out
  of the discussion and it should be built before the first adapter, not after.
- **Field-level provenance**, not record-level. Each significant attribute carries its own
  value, provider, provider record ID, confidence, verification status and timestamp,
  source type and source timestamp. Source value, provider prediction, verified value, and
  customer-entered value must never collapse into one indistinguishable field. This is the
  same evidence-classification convention PRD §24 already requires for metrics.
- **No LinkedIn scraping, in any version.** LinkedIn's User Agreement prohibits crawlers,
  bots, scripts, and browser extensions used to copy profile data. Where a LinkedIn URL is
  useful, it is an *input identifier* handed to a licensed enrichment provider — never a
  page Growixa fetches itself. Also excluded permanently: authenticated-session scraping,
  CAPTCHA bypass, and scraping behind access controls.
- **Deterministic, inspectable scoring.** Where lead or qualification scores exist, the
  formula is visible and configurable and each input cites its evidence — not an opaque
  model output presented as a percentage. Consistent with `DEC-GRX-011`'s refusal of
  unevidenced completion claims and PRD §24's evidence classification.

#### Proposed staging

- **V1 — Company Intelligence.** Business entities only, per `OQ-023`. Source registry and
  rights gate, provider interfaces, customer CSV/URL import, business-website extraction,
  normalization, deduplication, provenance ledger, verification, channel eligibility, UI.
- **V1.5 — Person Intelligence.** Named decision-makers, work email/phone via licensed
  enrichment provider. Separate gate; this is where personal-data obligations begin in
  earnest and where T81–T87 apply in full.
- **V2 — AI voice qualification** (`FUTURE_SCOPE_LEAD_INTELLIGENCE.md` idea #1). Slots
  into this module cleanly once provenance, phone, and eligibility exist. Needs its own
  telephony vendor decision, its own module boundary, its own threat-model section
  (call recording and consent-to-record law are untouched by anything written so far),
  and jurisdiction-aware voice rules — India's TRAI regime treats promotional voice calls
  differently depending on explicit consent.
- **V3+ — Licensed audiences** (idea #2) remains gated, and if ever built should be an
  audience *partner marketplace* rather than Growixa owning and reselling personal data.
  Unchanged by this addendum.

#### Existing research data

The ~35k directory records already collected are **`QUARANTINED_RESEARCH_DATA`**: not
exposed to customers, not searchable as production leads, not emailed, not resold, and not
used as Growixa's commercial dataset, unless and until source rights are confirmed to
permit that use. Directory terms of this kind commonly prohibit automated access and
commercial exploitation of extracted data, so the permissive reading cannot be assumed.
Engineering and tests use synthetic fixtures with the same schema rather than depending on
those records. The scraper's *reusable components* — pagination, parsing, website
discovery, normalization — may be generalized into provider adapters; the source-specific
scraper is not promoted into the production pipeline.

#### Still open before approval

`OQ-021` (does Growixa acquire, or only ingest — this addendum's discovery engine
contradicts point 2 of the original proposal), `OQ-022` (customer-facing product or
Growixa's own sales tooling), `OQ-023` (company-level-only V1). `OQ-008` and `OQ-017`
remain preconditions as stated above.

#### Entity model — and why this is not `contacts` (added 2026-08-16)

The product owner listed the attributes wanted on a lead: name, email, number, website,
LinkedIn, role, business name, social accounts (Instagram/Telegram/other), address, sector
category. That list is not one entity — it is two, and separating them is what makes
`OQ-023`'s company-level V1 coherent rather than arbitrary:

| Company / business entity | Person entity |
|---|---|
| Business name | Name |
| Website | Role / job title |
| Address | Work email |
| Sector / category | Direct number / mobile |
| Business phone | LinkedIn URL |
| Business email (`info@`, `sales@`) | Personal social handles |
| Social accounts (Instagram, Telegram, …) | — |

Two things follow directly.

**The compliance weight sits almost entirely in the right-hand column.** A school's name,
published office number, and `info@` address are business-entity data. A named
individual's role, work email, and mobile are personal data, and that is where T81, T85,
T87 and T89 bite. `OQ-023`'s proposal — company-level V1, person-level behind a later gate
— is exactly this table cut down the middle. It is also, in practice, close to the whole
of what directory-sourced records like the ~35k already collected actually contain: the
left column is populated, the right column is mostly empty. The compliance-expensive half
is the half that is not there yet.

**It also validates the Discovery/Enrichment split.** The left column is what discovery and
extraction produce. The right column is what an enrichment provider adds. They come from
different sources with different rights, arrive at different times, and carry different
confidence — which is the argument for field-level provenance rather than one flat record.

**This does not go in the `contacts` table.** `contacts` is Growixa's first-party audience
model — people the customer already has a relationship with, carrying consent status and
suppression state built for exactly that (`GRX-FEAT-010`, `DEC-GRX-008`). Widening it with
enrichment columns would collapse the very distinction this decision exists to preserve:
that an enriched lead is *not* a contact you may email. Lead Intelligence gets its own
entities, and promotion from lead to contact is an explicit, audited, eligibility-checked
transition — the one place the two modules touch.

The list above is also not the full set to design against; it omits, at minimum, the
provenance and eligibility fields that every entity needs regardless of channel
(source, source URL, collection method, collected-at, provider, purpose, owning account,
consent status, lawful basis, retention status, per-channel eligibility). Those are not
optional extras — they are what makes the record defensible, and they must exist from the
first migration rather than being added once the data is already in.

#### Addendum 2, 2026-08-16 — the three layers, and which of them is a different business

The product owner described Lead Intelligence as a customer-facing product with three
capabilities. They carry very different risk and should not be approved as one thing.

**Layer A — Real-time provider pass-through.** The customer specifies a filter ("software
companies in Noida", "schools in Sharjah"); Growixa queries a licensed provider on demand
and returns matching records to that customer. Growixa is a router. The provider holds the
data, the collection chain, and the redistribution rights. **Lowest risk, and this should
be V1's shape.** It also aligns with the provider-abstraction design already adopted above.

**Layer B — A pooled Growixa-owned dataset.** Records Growixa has acquired (by discovery,
crawling, or provider calls) accumulate into a shared pool that any customer can search.
**This is not a bigger version of Layer A. It is a different business with its own
regulatory regime**, and it is the single highest-risk item in this decision:

- *It meets the working definition of a data broker* — a business that collects and sells,
  licenses, or transfers personal information about individuals with whom it has no direct
  relationship, assembled from third-party sources, public records, or purchased data.
  Four US states (California, Texas, Vermont, Oregon) require data brokers to register with
  a state agency, with annual fees and deadlines; California's Delete Act adds the DROP
  platform, through which a consumer deletes their data across every registered broker in
  one request, and registered brokers must honor those requests. Verified 2026-08-16.
- *Access rights are not redistribution rights.* Most directory and provider terms permit a
  subscriber to use data; far fewer permit redistributing it onward to that subscriber's own
  customers, which is exactly what a pooled dataset does. Directory terms commonly prohibit
  bulk extraction and building or enhancing a competing dataset outright — which is what
  Layer B is, by construction. **The ~35k already-collected records cannot seed this pool**
  under their source's terms (`QUARANTINED_RESEARCH_DATA`, above).
- *Two mitigations make a legitimate version possible.* First, **company-level only**: data
  broker regimes target personal information about individuals; business-entity records
  (company name, published office number, `info@`) largely fall outside them. Nearly every
  regime defines its subject matter the same way — personal data means data relating to an
  identified or identifiable *natural person* — so the company/person cut narrows exposure
  under all of them at once rather than under one country's rules. Second, **source
  redistribution rights as a hard gate**: only sources whose terms explicitly permit onward
  distribution may feed the pool, enforced by the Source Registry (T88) rather than by
  anyone's memory.

  This is the third distinct reason `OQ-023`'s company-level V1 has paid for itself, which
  is a strong signal it is the right cut.

**Layer C — Autonomous conversion.** Analyze a prospect from their website, predict
likelihood of converting, generate a personalized message, send it, follow up
automatically, and keep going until the lead converts.

This is the most differentiated idea of the three, and it **directly contradicts rules this
project has locked**, so it cannot be adopted implicitly:

- `GRX-AI-002` and `GRX-AI-003` (PRD §23): AI output cannot send email or publish, and a
  human must review and approve before send/publish.
- `DEC-GRX-006`: human approval required for AI content, "no exceptions in MVP".
- `DEC-GRX-012`: broad autonomous marketing agents are deferred.
- `PRD.md` §11 Non-goals lists "sending AI-generated content without human approval" as
  **not a goal of Growixa at all, at any stage** — not deferred, rejected. Layer C as
  described is that.

**There is a version that does not require tearing any of that up**, and it is close to the
same product: AI drafts the whole sequence — analysis, message, follow-up ladder — and a
human approves *the sequence* once, after which execution proceeds automatically against
that approved plan. That is approval-gated automation, not autonomy. It preserves the
principle (a human authorized what goes out under the company's name) while delivering
almost all of the leverage. Moving from per-message to per-sequence approval is still a
change to `DEC-GRX-006` and needs its own decision — but it is a narrow amendment rather
than a reversal of the product's founding safety position.

Whatever is built, conversion prediction must be deterministic and inspectable, with each
input citing its evidence, per the scoring rule already adopted above. "AI says 93%" with
no defensible calculation is not acceptable output for a product that also promises
evidence classification on its metrics (PRD §24).

**Proposed staging across the three layers:** Layer A in V1 (company-level, pass-through).
Layer B only after `OQ-025` is answered and only from redistribution-cleared sources.
Layer C's approval-gated form after `OQ-026`; its fully autonomous form is not proposed at
all, and would require amending PRD §11.

#### Addendum 3, 2026-08-16 — global scope, and jurisdiction as a first-class field

The product owner clarified that Lead Intelligence targets **global business**, not a
single market. The UAE dataset was sample data, not the scope.

This makes the design harder, not easier, and in one specific way: **"global" does not mean
one permissive rule. It means the strictest applicable rule, determined per record by where
the recipient is.** A single lead table sent under a single policy will be simultaneously
lawful for some recipients and unlawful for others, and nothing in the system would show
which is which.

The regimes are genuinely divergent on the exact question this product asks — may you
contact someone you have no prior relationship with?

- **United States** is the most permissive for email: unsolicited commercial email is
  lawful with identification, a physical postal address, and a working opt-out — all of
  which Growixa already ships (`GRX-SAAS-015`). But the US is also where the *data broker*
  registration regimes live, which bear on Layer B rather than on sending.
- **Canada (CASL)** is effectively opt-in for commercial electronic messages, with limited
  business-relationship exceptions and significant penalties. Among the strictest.
- **EU/UK (GDPR)** requires a lawful basis and, for data not collected from the person, a
  notice obligation at first contact (Art. 14). Legitimate interest is available for B2B
  but is a documented assessment, not an assumption.
- **India (DPDP)** is in active implementation with its own consent architecture.
- Others — Brazil, China, Japan, Australia, UAE — each add their own variation.

**Design consequences, none of which are optional for a global product:**

1. **Jurisdiction is a mandatory, resolved field on every lead** — not inferred at send
   time from a phone prefix or a TLD guess, but resolved at ingest, stored with its own
   confidence and provenance like any other enriched field, and re-resolvable. A lead whose
   jurisdiction is `UNKNOWN` is not sendable, the same way `UNKNOWN` eligibility is not.
2. **Channel eligibility is evaluated per channel *and* per jurisdiction *and* per sending
   path.** Three dimensions, not one flag. `OQ-024` established the sending-path dimension;
   this addendum adds the jurisdiction one. All three must exist in the first migration —
   this is precisely the kind of dimension that cannot be retrofitted onto a boolean once
   millions of rows exist.
3. **Policy is data, not code.** Per-jurisdiction rules change, and they change on
   legislative timelines rather than release timelines. They belong in a configurable
   policy table with an effective-date and a review date, alongside the Source Registry —
   not in `if country == "CA"` branches scattered through the send path.
4. **The company-level V1 cut (`OQ-023`) gets stronger, not weaker, at global scope.**
   Business-entity records sit outside the personal-data definition in essentially every
   one of these regimes simultaneously. It is the one design choice that reduces exposure
   under all of them at once, rather than requiring a per-country analysis before the
   product can ship anywhere. **At global scope this stops being a cost-saving measure and
   becomes the thing that makes a V1 shippable at all.**
5. **Growixa cannot carry this as legal advice.** A global product asserting per-country
   sending lawfulness needs external counsel to validate the policy table before launch —
   not an agent's reading of secondary sources, including this one. Every jurisdictional
   claim recorded in these documents should be treated as a research starting point for
   that review, not as a cleared position.

### Addendum 4, 2026-08-28 — Understand and Act layers (Find/Understand/Act framing)

Recorded from a product-owner brainstorm on positioning this module as core and
visibly AI-driven, not just an enrichment utility. Full detail lives in
`FUTURE_SCOPE_LEAD_INTELLIGENCE.md` §"Update, 2026-08-28" to keep this entry short;
summarized here for traceability. **Still `PROPOSED`** — this addendum adds scope, it
does not move anything toward `APPROVED`.

Reframes the module as three layers: **Find** (discovery/enrichment/provenance —
everything already specified above), **Understand** (a new, evidence-citing AI
qualification narrative generated from Find's provenance-tagged fields — not a new
data source, a synthesis step), and **Act** (segment fit + a drafted outreach
sequence that reuses `GRX-FEAT-021`'s draft/approve pipeline under the existing
`DEC-GRX-006` human-approval rule, with the approval doubling as the lead→contact
promotion event this decision already requires to be explicit and audited).

Understand has no new preconditions beyond this decision's existing ones and could
ship before Act. **Corrected, 2026-08-28, after independent review flagged this
addendum contradicted `FUTURE_SCOPE_LEAD_INTELLIGENCE.md`'s own "Build sequencing"
section written the same day** — this entry originally said Act "cannot ship before
`GRX-FEAT-021` (AI Content Assistant, currently `NOT_STARTED`) exists." That was
wrong: `MASTER_TASK_TRACKER.md` shows the underlying `GRX-AI-001..011` tasks reached
`DONE`, and AI-generated drafting is live in the campaign composer today.
`GRX-FEAT-021`'s own row in `FEATURE_CATALOG.md`/`FEATURE_STATUS_MATRIX.md` is
simply unreconciled to that (still reads `NOT_STARTED`/unaudited) — a pre-existing
documentation-hygiene gap, not evidence the capability doesn't exist. Act's real new
work is the lead→draft wiring and the promotion/eligibility-check mechanism itself,
not waiting on drafting infrastructure to be built. That mechanism — "approving a
sequence = promotion + eligibility check" — is new product behavior that needs its
own explicit confirmation before build regardless, since `DEC-GRX-006` did not
originally anticipate a sequence being drafted before the contact relationship
exists.

## DEC-GRX-034: Contact soft deletion — `deleted_at`, enforced invisibility, and re-import behaviour

- Status: **APPROVED** — confirmed by the product owner 2026-08-16, after considering and
  rejecting the suppress-as-delete alternative recorded in §4a.
- Date: 2026-08-16
- Requirement, as stated by the product owner: a customer can delete a contact; Growixa
  retains the row in the database; **the customer cannot see that data anywhere.** Not
  erasure — retention with enforced invisibility. Hard erasure for data-subject requests
  stays separate (`GRX-CONTACT-013`), and the retention/purge window is explicitly
  deferred (`OQ-008`, `OQ-028`).

### 1. `deleted_at`, not a third `status` value

Add a nullable `contacts.deleted_at TIMESTAMPTZ`. Do **not** add `DELETED` to the existing
`status` CHECK constraint.

`status` and deletion answer different questions and must stay orthogonal:

| | `status` (`ACTIVE` / `ARCHIVED`) | `deleted_at` (NULL / timestamp) |
|---|---|---|
| Answers | may we mail this contact? | may the customer see this contact? |
| Already enforced | yes — worker filters `status == 'ACTIVE'` in all four recipient queries; `count_active_contacts` excludes `ARCHIVED` from `max_contacts` | new |

Collapsing them into one enum forces a false choice — a contact deleted while `ARCHIVED`
would lose the fact that it was archived, so restore could not put it back correctly. With
two fields, restore is simply `deleted_at = NULL` and the prior `status` is still there.
It is also the conventional soft-delete shape, which matters for a codebase worked by
several agents: `deleted_at IS NULL` is recognised on sight; a third enum value is not.

### 2. Invisibility must be enforced structurally, not by remembering to filter

This is the part that decides whether the feature holds up. Per-query filtering is how soft
delete fails in practice — someone adds a query six months later, omits the predicate, and
deleted contacts reappear in one screen.

Proposed, reusing patterns this repository already trusts:

1. **One shared selectable** in `contacts/repositories.py` (e.g. `visible_contacts()`) that
   every customer-facing read path goes through. Including deleted rows requires calling a
   separate, explicitly-named function — the unsafe thing must be the one you have to type
   deliberately.
2. **An audit test**, modelled directly on the existing `test_protected_routes_audit.py`,
   that fails when a `select(Contact)` in a customer-facing path does not go through the
   shared selectable. This project already uses an audit test to keep RBAC honest across
   every route; the same technique keeps deletion honest across every query. Without this,
   item 1 is a convention, and conventions decay.
3. **Worker paths inherit it too** — `apps/worker/.../recipients.py` resolves recipients
   independently of the API's repositories, so its four queries need the `deleted_at IS
   NULL` predicate added alongside their existing `status == 'ACTIVE'` filter. A deleted
   contact must not receive mail even though the row still exists.

### 3. Re-import collision — the concrete bug this design must not ship with

`ux_contacts_account_id_email` is a plain unique constraint on `(account_id, email)`. If a
contact is soft-deleted and hidden, and the customer then re-imports that same address, the
insert violates a constraint **against a row the customer cannot see** — surfacing as
"contact already exists" for a contact that is, as far as they can tell, gone. This will
happen on the first CSV re-import after the feature ships.

Proposed: replace it with a **partial unique index** on `(account_id, email) WHERE
deleted_at IS NULL`. Re-importing a deleted address then creates a clean new contact and
leaves the deleted record deleted. This repository already uses exactly this pattern —
`ux_suppression_entries_account_id_domain ... postgresql_where=text("domain IS NOT NULL")`
(`GRX-SAAS-015`).

Rejected alternative: silently resurrecting the soft-deleted row on re-import. It brings
back the old tags, custom fields and list memberships the customer believed they had
deleted, which is surprising in the wrong direction.

### 4. What "cannot see any of this data" cannot cover — and why

Two deliberate exceptions. Both should be stated in the UI rather than discovered:

1. **Suppression entries stay visible.** `suppression_entries` is keyed on `email`/`domain`
   with only a nullable `contact_id`, so a deleted contact who had unsubscribed still
   appears on the suppression page as an address. This is required, not a leak —
   `DEC-GRX-008` makes suppression non-deletable, and losing it would let that address be
   re-imported and mailed. **Deleting a contact must never un-suppress them.**
2. **Historical campaign reports keep their numbers.** `campaign_recipients.contact_id` is
   `NOT NULL`; a past campaign's sent/opened/clicked totals must not change because a
   contact was later deleted, or every historical report becomes unreproducible. The rows
   stay; drill-down to a deleted recipient renders a neutral placeholder ("Deleted
   contact") instead of PII.

### 4a. Deletion and suppression stay separate — with one optional prompt

Considered and rejected: using suppression *as* the delete mechanism ("move the address to
Suppress instead of building soft delete"). It fails on three counts. It does not deliver
the stated requirement — the contact stays visible in the list and the address additionally
appears on the suppression page, so *more* data is visible, not less. It degrades the
suppression list's purpose: that list is the evidence of opt-out (`DEC-GRX-008`), and
mixing in records that were merely tidied away makes "this person unsubscribed"
indistinguishable from "someone cleaned up their CSV". And it makes an everyday action
irreversible through the most dangerous available control — suppression entries are
permanent by design, so undoing an accidental delete would require un-suppressing, which is
the legally sensitive action `OQ-DNC-004` flags as unresolved.

The legitimate need behind the idea is real, though: a contact is often deleted *because*
they should not be contacted. Proposed instead — the delete confirmation offers an optional,
unchecked "also add to the suppression list" control, described in terms of intent ("do this
if they asked not to be contacted"). Two independent actions, one prompt. The customer gets
the safe outcome when it genuinely applies, and the suppression list keeps holding only real
opt-outs.

### 5. Consequences

1. One migration: add `contacts.deleted_at`, swap the unique constraint for the partial
   unique index. No data backfill — existing rows get `NULL`.
2. `count_active_contacts` (`max_contacts`, `GRX-BILL-005`) must also exclude deleted rows,
   or a customer stays billed against contacts they deleted. Restore must re-check the cap
   rather than silently exceeding it.
3. Segment membership, contact search, CSV export, and dashboard counts all read through
   the shared selectable and therefore exclude deleted rows with no per-feature work.
4. `GRX-CONTACT-013` (hard erasure) is unaffected and still required for data-subject
   requests — soft deletion retains the PII and does not satisfy an erasure request.
5. Nothing here creates a retention window. Deleted rows persist until a purge policy is
   decided (`OQ-008`), which the product owner has deferred.

- Related: `GRX-CONTACT-010` (implements this), `GRX-CONTACT-013` (hard erasure),
  `DEC-GRX-008` (suppression non-deletable), `GRX-BILL-005` (contact quota), `OQ-008`.
- Supersedes: none.

## DEC-GRX-035: Multiple active Custom SMTP connections, routed per sender identity, gated on SPF alignment

- Status: **APPROVED** — confirmed by the product owner 2026-08-17, including the
  plan-availability decision in point 9. Amends `DEC-GRX-016`.
- Date: 2026-08-17
- Context: A customer wants several SMTP relays on one account — e.g. a transactional relay,
  a marketing relay, and a support relay on different providers. `DEC-GRX-016` deliberately
  allowed only **one active connection per provider per account**, DB-enforced by the
  partial unique index `ux_email_provider_connections_active_per_provider` on
  `(account_id, provider) WHERE is_active`. Lifting that is a change to an `APPROVED`
  decision and a database constraint, so it needs its own decision rather than a quiet
  index drop.

### What already exists (verified 2026-08-17, not assumed)

Most of the routing is built, which makes this much smaller than it first appears:

- `sender_identities.email_provider_connection_id` is a real FK — identities already point
  at a specific connection.
- The worker already routes on it: `send_campaign.py:113` does
  `session.get(EmailProviderConnection, identity.email_provider_connection_id)`. It does
  **not** resolve "the account's active connection". Per-identity routing works today.
- `dnspython>=2.6` is already a dependency (added by `GRX-SAAS-016`), so the SPF check
  below needs no new package.

The only true blocker is the unique index. The feature is therefore: relax one constraint,
add a name, add a guardrail, expose it in the UI.

### Proposed decision

1. **Multiple active `CUSTOM_SMTP` connections per account are allowed.** The partial
   unique index is narrowed so it no longer caps `CUSTOM_SMTP` at one active row per
   account. `POSTMARK` keeps its single-active-connection rule — it is a platform-managed
   provider with one credential set, and nothing asks for several.
2. **Connections gain a required, account-unique `name`** (e.g. "Transactional — GoCheapWeb",
   "Marketing — SES"). Without a label, a list of hosts is unusable in a selector. Default
   it to the host on migration so existing rows stay valid.
3. **Routing stays per sender identity.** No campaign-level relay picker: a campaign chooses
   a sender identity, and the identity's connection determines the relay. One routing
   concept, not two. This matches how Brevo assigns senders to dedicated IP pools rather
   than choosing transport per send.
4. **Assignment is gated on an SPF alignment check.** Before an identity may be bound to a
   connection, resolve the identity's domain SPF record and check whether the connection's
   host is authorised to send for it. A failing check **warns and requires explicit
   override**, recorded in the audit event — it does not silently proceed. Rationale: this
   is the whole risk of multi-relay routing. Sending `hello@brandA.com` through a relay
   that `brandA.com` does not authorise produces SPF failure and DMARC rejection, and the
   damage is invisible until deliverability collapses.
5. **No automatic failover between relays.** If an identity's connection fails, the send
   fails and surfaces the error. Silently retrying through another relay is precisely the
   misalignment in point 4, arrived at by accident instead of by configuration.
6. **No silent fallback to "an active connection of that provider."** Once several are
   active, that phrase has no single referent. An identity pointing at an inactive
   connection is an error to surface, not a condition to paper over.
7. **Deleting a connection is blocked while any sender identity references it.**
   `sender_identities.email_provider_connection_id` is `NOT NULL` with no `ondelete`, so an
   unguarded delete either raises an FK violation or orphans identities — the same failure
   class as the bug that prompted this work. The API returns a clear error naming the
   identities that must be reassigned first.
8. **`create_connection`'s auto-reassignment must narrow.** It currently reassigns *every*
   identity of that provider to the newest connection, which was correct when only one
   could be active. Under this decision it must reassign only identities that pointed at
   **the specific connection being replaced**. Left as-is, adding a marketing relay would
   silently repoint every transactional identity to it — destroying the routing this
   decision exists to create.
9. **Available on every subscription plan initially — no tier gating.** Confirmed by the
   product owner 2026-08-17. Multi-SMTP is a deliverability capability that Brevo gates at
   Enterprise, so gating it later is defensible, but withholding it at launch would mean
   the cheapest customers — the ones most likely to already own an SMTP relay and least
   able to pay per email — are the ones locked out of the capability that makes Growixa
   cheaper than Brevo. Gating is deliberately left as a **future** option rather than a
   never: revisit alongside `OQ-013`'s plan-tier work if multi-relay usage turns out to
   concentrate in larger accounts. Nothing in this decision's schema or API design
   presumes ungated access, so adding a tier check later is a service-layer change, not a
   migration.

### Deliberately out of scope

- **A `sending_domains` entity.** Brevo makes the domain a first-class object because
  authentication lives there, and that is the right long-term shape — a persisted
  verification status, periodic re-checks, a domains page. This decision uses a live
  per-assignment SPF check instead, which delivers the guardrail without a new entity and
  new UI. Revisit when customers need managed domain verification rather than a warning.
- **DKIM verification.** The customer's own relay signs the message, and Growixa does not
  know their selector, so DKIM alignment cannot be checked reliably from here. SPF is what
  is verifiable without the customer telling us more.
- **Tier gating at launch** — decided against in point 9, not left open. Revisit later if
  usage data justifies it.

### Consequences

1. One migration: add `name`, narrow the partial unique index. No backfill beyond
   defaulting `name` to the existing host.
2. `DEC-GRX-016`'s "one active connection per provider" is amended for `CUSTOM_SMTP` only
   and stands unchanged for `POSTMARK`.
3. New/changed endpoints: `PATCH` a sender identity's connection, `DELETE` a connection
   (guarded per point 7). Both gated on the existing `integrations.manage` — no new
   permission code.
4. `DATA_MODEL.md`'s singleton-by-convention note needs updating; it currently describes
   the rule this decision changes.

- Related: `DEC-GRX-016` (amended), `DEC-GRX-015`, `GRX-EMAIL-011`/`012`,
  `THREAT_MODEL.md` T14 (webhook credentials per connection).
- Supersedes: none. Amends `DEC-GRX-016` in part.

## DEC-GRX-036: Personalization tokens — one channel-agnostic renderer, two token scopes, no template engine

- Status: **APPROVED** — confirmed by product owner (2026-08-23).
- Date: 2026-08-17
- Context: `MVP_SCOPE.md` §C promises "personalization variables". The template editor
  advertises an "Insert Personalization Token" control offering `{{first_name}}`,
  `{{last_name}}`, `{{company_name}}`. **No substitution exists anywhere** — verified in
  both send paths; `send_campaign.py`'s own comment states "no merge-tag infrastructure
  exists yet", and `publish_social_post.py` has none either. Tokens are delivered to
  recipients as literal text. This is promised MVP scope, advertised in the UI, and unbuilt
  — and unlike the other placeholder UI found this week, its output reaches **the
  customer's own customers**, damaging their reputation rather than ours.

### Two token scopes — this is what "works for any campaign" means

The product owner asked for personalization across **any campaign type**, not email only.
That requires separating two kinds of token, because they have different availability:

| Scope | Source | Example tokens | Available on |
|---|---|---|---|
| **Recipient** | the `contacts` row + its custom field values | `{{first_name}}`, `{{last_name}}`, `{{school_name}}` | per-recipient channels only — email, later SMS and Telegram bot DM |
| **Account / sender** | `company_profile`, the sending `sender_identity` | `{{company_name}}`, `{{website_url}}`, `{{sender_name}}` | **every** channel, including broadcast |

Broadcast channels (an Instagram post, a Telegram channel post) have **no individual
recipient**, so recipient tokens cannot resolve there and must be rejected at save time
rather than silently rendering blank. Account/sender tokens work everywhere, which is what
makes "personalization for any campaign" meaningful rather than email-only.

This also resolves the `{{company_name}}` button, which today resolves to nothing:
`contacts` has no company column, but `company_profile.name` does exist. It is an
**account-scope** token that was never wired, not a missing contact field.

### Proposed decision

1. **One shared renderer, not one per channel.** A channel-agnostic module owns tokenising,
   resolution, escaping, and validation. Email and social both call it; SMS and Telegram
   call the same one later. Both the API (test-send, preview) and the worker (real send)
   use it — the worker resolves data independently of the API, so a renderer living inside
   either one would have to be duplicated.
2. **No template engine — restricted substitution only.** Jinja2, Mako and similar are
   **rejected**: templates are user-supplied content, and a full engine on user input is a
   server-side template injection surface (arbitrary attribute access, sandbox escapes).
   The renderer recognises a fixed token grammar via a bounded pattern and nothing else. No
   expressions, no logic, no loops, no attribute traversal.
3. **Allowlist, never "all contact data".** Recipient scope exposes `first_name`,
   `last_name`, `email`, `phone`, plus that account's custom fields. Internal columns are
   never exposed — `id`, `account_id`, `created_by_user_id`, `status`, `deleted_at`,
   timestamps, and specifically **`source`**, which can contain acquisition provenance that
   must never render into a message to the person it describes.
4. **Custom fields may be excluded per field.** Custom fields are user-named and can hold
   internal commentary ("budget estimate", "notes"). A per-field "usable in personalization"
   flag prevents an internal note rendering to the recipient. Default for new fields is a
   product-owner call; the safer default is opt-in.
5. **A `default` filter is required, not optional.** `{{first_name | default:"there"}}`.
   Missing values are highly visible in outbound — "Hi ," — and cold campaigns are exactly
   where they occur. This is the only filter in scope; no others, per point 2.
6. **Values are HTML-escaped in HTML bodies.** Contact values arrive from CSV import and are
   untrusted (`GRX-AI-007`'s framing applies). Escaping is on by default with no opt-out in
   this decision.
7. **Unknown tokens block the send, they do not render.** A typo (`{{shcool_name}}`) fails
   validation at save and at send with a clear message naming the token. Rendering it
   literally is the current bug; rendering it blank silently corrupts copy at scale.
8. **A pre-send preview is part of the feature, not a follow-up.** Render against a real
   recipient, and report how many recipients are missing a value for each token used.
   Discovering that 40 of 300 rendered blank *after* sending is the expensive way to learn,
   and this is the check that makes bulk personalization trustworthy.

### Consequences

1. New shared module; email and social send paths call it. `MVP_SCOPE.md` §C's
   "personalization variables" becomes genuinely satisfied rather than nominally.
2. Custom fields gain a "usable in personalization" flag — one migration.
3. The template editor's token control must be driven by the **real** available tokens for
   that account and channel, not a hardcoded list of three.
4. Until this ships, the advertised token buttons are actively misleading and are removed
   or disabled (`GRX-BUG-005`, filed separately and not blocked by this decision).

- Related: `MVP_SCOPE.md` §C, `GRX-AI-007` (untrusted external content), `DEC-GRX-011`
  (no DONE without evidence), `GRX-FEAT-SMS-001` and `GRX-FEAT-034` (future channels that
  reuse the same renderer).
- Supersedes: none.
