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

- Status: APPROVED
- Date: 2026-07-22
- Context: Growixa's first customer is one internal marketing team; multi-tenant SaaS
  infrastructure (workspace switching, tenant billing, cross-tenant isolation) adds
  substantial complexity with no near-term buyer.
- Decision: MVP is single-tenant, one company installation, multiple internal users.
- Rationale: Avoids unnecessary `tenant_id`/`workspace_id` scoping on every table; ownership
  fields (`created_by_user_id`, etc.) are sufficient. Architecture stays modular enough to
  add multi-tenancy later without a rewrite.
- Consequences: No tenant model, no workspace switcher, no tenant-scoped billing in MVP.
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

- Status: APPROVED
- Date: 2026-07-22
- Decision: Not part of MVP or the currently-planned future releases in ROADMAP.md; revisit
  only if Growixa's business model changes toward external SaaS customers.
- Related: DEC-GRX-002.

---

*Decisions DEC-GRX-014 onward will be logged as they are made — e.g., resolutions to
OQ-001 through OQ-011 in [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).*
