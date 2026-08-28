# Growixa — Product Requirements Document

## 1. Document control

- Document ID: DOC-PRD
- Status: ACTIVE — Phase 1 draft, build-ready for MVP scope
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Product owner (Ravi) via coding agent
- Related documents: [PRODUCT_VISION](PRODUCT_VISION.md), [MVP_SCOPE](MVP_SCOPE.md), [FUTURE_SCOPE_SEO_AEO_GEO](FUTURE_SCOPE_SEO_AEO_GEO.md), [FUTURE_SCOPE_MULTI_BRAND](FUTURE_SCOPE_MULTI_BRAND.md), [FUTURE_SCOPE_PLATFORM_ADMIN](FUTURE_SCOPE_PLATFORM_ADMIN.md), [FUTURE_SCOPE_LEAD_INTELLIGENCE](FUTURE_SCOPE_LEAD_INTELLIGENCE.md), [ROADMAP](ROADMAP.md), [DECISIONS](../00-project-control/DECISIONS.md), [ASSUMPTIONS](../00-project-control/ASSUMPTIONS.md), [OPEN_QUESTIONS](../00-project-control/OPEN_QUESTIONS.md), [DEFINITION_OF_DONE](../00-project-control/DEFINITION_OF_DONE.md)

Requirement ID prefixes used throughout: `GRX-FR` (functional), `GRX-NFR` (non-functional),
`GRX-SEC` (security), `GRX-AI` (AI-specific), `GRX-UX` (UX), `GRX-OPS` (operations/DevOps),
`GRX-DATA` (data model), `GRX-INT` (integrations). Full per-feature detail lives in
`docs/02-features/` (created in Phase 2); this PRD is the top-level, traceable summary.

## 2. Executive summary

Growixa is an AI-powered growth and marketing automation platform. The MVP is a
single-tenant, multi-user web application: one company's internal marketing team manages
contacts, runs email campaigns, schedules social posts, and uses an AI content assistant —
with every AI-generated or externally-visible action requiring human approval. The platform
is built to expand later into SEO, AEO, GEO, and website-intelligence capabilities (see
[FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md)) without a rewrite, by
establishing reusable patterns now: provider adapters, usage metering, audit logging, and
AI-approval workflows.

## 3. Product vision

See [PRODUCT_VISION.md](PRODUCT_VISION.md) for the full vision and positioning statement.

## 4. Problem statement

Marketing teams inside a single company typically juggle separate tools for contact lists,
email sending, social scheduling, and content drafting — with no shared audience data,
inconsistent brand voice, and no unified view of what was sent, to whom, and with what
result. AI content tools exist in isolation from the send/publish workflow, creating a
copy-paste gap and no institutional memory of what was generated or approved. Growixa
removes that fragmentation for one company's marketing operation.

## 5. Product opportunity

A single platform that owns the contact/audience data, generates and reviews AI content
in context, and executes sends/posts through the same approval and audit pipeline can
materially reduce coordination overhead for a small-to-mid marketing team, while producing
a trustworthy operational record (what was sent, when, to whom, with what outcome) that
scattered tools cannot.

## 6. Target users

The original MVP (Slices 1–4) targeted internal employees/contractors of the one company
operating Growixa (per the now-superseded [DEC-GRX-002](../00-project-control/DECISIONS.md),
single-tenant). As of [DEC-GRX-017](../00-project-control/DECISIONS.md) (2026-08-07),
Growixa is opening for self-service registration: any company can sign up and use the
platform as its own isolated customer account, with an IITDEVELOPER Platform Admin
control plane operating above all customer accounts — see
[FUTURE_SCOPE_PLATFORM_ADMIN.md](FUTURE_SCOPE_PLATFORM_ADMIN.md) for the full design and
[SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md)
for the phased build plan. This is not the traditional "multi-tenant workspace" pattern —
customers never see or manage other accounts, an organization concept, or a workspace
switcher; isolation is an internal `account_id` data-model concern only.

## 7. Personas

| Persona | Primary job | Key needs |
|---|---|---|
| Super Admin | Owns the installation, users, and integrations | Full control, security oversight, audit visibility |
| Marketing Manager | Owns campaign strategy and performance | Segment building, campaign creation, analytics, approvals |
| Content Creator | Drafts and refines content | AI assistance, brand-voice controls, drafts, media |
| Analyst / Viewer | Reviews results | Trustworthy reporting, no edit access needed |

Roles are formalized in [§20 User roles and permissions](#20-user-roles-and-permissions).

## 8. Jobs to be done

- "When I have a list of new leads, I want to import and segment them without spreadsheet gymnastics."
- "When I need to announce something, I want a drafted, on-brand email ready in minutes, not hours."
- "When a campaign goes out, I want to know it actually reached people and what they did next."
- "When I schedule social content, I want one calendar view instead of five app tabs."
- "When AI drafts something, I want to review it before anything goes out under our name."

## 9. Product positioning

> Growixa is an AI-powered growth and marketing automation platform. It begins with email
> and social media automation, then expands into SEO, AEO, GEO, website intelligence,
> content optimization, and integrated growth workflows.

## 10. Goals

1. Let an admin provision internal users and control access without building a multi-tenant system.
2. Give the marketing team one place to manage contacts, tags, lists, and segments.
3. Support end-to-end email campaigns: draft → template → test → schedule/send → track → report.
4. Support end-to-end social posting for one approved platform: connect → compose → schedule/publish → track.
5. Provide an AI content assistant that drafts, rewrites, and suggests — never sends/publishes unsupervised.
6. Meter every cost-generating operation from day one.
7. Keep the architecture modular enough to add SEO/AEO/GEO capabilities and, later, multi-tenancy, without a rewrite.

## 11. Non-goals

See [MVP_SCOPE.md §Deferred](MVP_SCOPE.md#deferred-not-cancelled) for the full deferred list.
Not goals of Growixa at all, at any stage: guaranteeing rankings, open rates, click rates,
or revenue; sending AI-generated content without human approval; purchasing or generating
spam backlinks.

## 12. Product principles

See [PRODUCT_VISION.md §Product principles](PRODUCT_VISION.md#product-principles).

## 13. MVP scope

See [MVP_SCOPE.md](MVP_SCOPE.md) for the complete breakdown (Platform Foundation, Contact &
Audience Management, Email Marketing, Social Media Automation, AI Content Assistant).

## 14. Future scope

See [FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md) (V1.5–V3: website
intelligence, SEO execution, AEO, GEO, authority/outreach, full growth-agent system) and
[ROADMAP.md](ROADMAP.md) for release staging, including the marketing-side post-MVP
releases (1.1, 1.2).

Also see [FUTURE_SCOPE_LEAD_INTELLIGENCE.md](FUTURE_SCOPE_LEAD_INTELLIGENCE.md) —
company/person contact discovery and enrichment, AI-generated lead qualification, and
approval-gated outreach sequencing. **Idea capture and a `PROPOSED` (not `APPROVED`)
architecture decision only** ([DECISIONS.md §DEC-GRX-033](../00-project-control/DECISIONS.md)) —
would expand Growixa's positioning (§9) beyond automating a company's own existing
audience, so it is not committed scope and must not be treated as such until the
product owner approves the underlying decision.

## 15. Functional requirements

Full detail lives in `docs/02-features/` (Phase 2). Top-level requirement groups and IDs:

| ID range | Area |
|---|---|
| GRX-FR-AUTH-* | Authentication, sessions, password reset |
| GRX-FR-USER-* | Internal user management, invitations |
| GRX-FR-RBAC-* | Roles and permission enforcement |
| GRX-FR-COMPANY-* | Company profile, brand settings, application settings |
| GRX-FR-CONTACT-* | Contact CRUD, tags, lists, segments, custom fields |
| GRX-FR-IMPORT-* | CSV import, validation, duplicate handling, import history |
| GRX-FR-EMAIL-* | Templates, campaigns, sending, tracking |
| GRX-FR-SCHEDULE-* | Scheduled execution, cancellation, retry |
| GRX-FR-SOCIAL-* | Account connection, composing, scheduling, publishing |
| GRX-FR-AI-* | Content generation, rewriting, brand voice, approval |
| GRX-FR-ANALYTICS-* | Campaign/post analytics, dashboards |
| GRX-FR-NOTIFY-* | Notification center |
| GRX-FR-AUDIT-* | Audit logging |
| GRX-FR-USAGE-* | Usage metering |
| GRX-FR-ADMIN-* | Admin dashboard, integration management |

## 16. Non-functional requirements

| ID | Requirement |
|---|---|
| GRX-NFR-001 | Interactive API responses typically under 500 ms; job creation under 2 s. |
| GRX-NFR-002 | Idempotent jobs, durable state, retries, dead-letter handling, resumable workflows. |
| GRX-NFR-003 | WCAG 2.2 AA target for customer-facing (internal-user-facing) UI. |
| GRX-NFR-004 | Full usability on desktop and tablet; mobile view supported for review/approval flows. |
| GRX-NFR-005 | Structured logs, metrics, and traces for all backend services and workers. |
| GRX-NFR-006 | Typed code, documented APIs (OpenAPI), migrations, test suites, feature flags. |
| GRX-NFR-007 | English-only UI/content for MVP (per [ASM-010](../00-project-control/ASSUMPTIONS.md)); architecture does not block future localization. |
| GRX-NFR-008 | Automated backups with a defined, tested restore procedure. |

## 17. User journeys

Primary onboarding: Admin logs in (first-admin setup) → invites internal users → sets
company profile and brand voice → connects one email provider and one social account →
imports contacts → creates a segment → drafts a campaign (optionally AI-assisted) → sends a
test → schedules or sends → reviews delivery/engagement report.

Full journey detail with screen-level flow lives in `docs/03-ux-ui/` (Phase 3).

## 18. Feature priorities

Priority follows the vertical-slice order in [DEC-GRX-010](../00-project-control/DECISIONS.md):
Slice 1 Foundation → Slice 2 Contacts → Slice 3 First Email Campaign → Slice 4 Scheduled
Email → Slice 5 Social Publishing → Slice 6 AI Assistant. See `docs/14-sprints/` (Phase 8)
for sprint-level breakdown.

## 19. Business rules

- AI-generated content is always labeled `AI_GENERATED` and requires human approval before
  send/publish (no exceptions in MVP).
- No email may be sent to a contact on the suppression list or who has unsubscribed,
  regardless of segment membership.
- A scheduled campaign executes at most once (idempotent execution; see
  [§15 Email Delivery Rules in the master spec] — detailed in
  `docs/04-architecture/CAMPAIGN_EXECUTION_FLOW.md`, Phase 4).
- Every cost-generating operation must pass an entitlement/usage check before executing
  (see [§33 Usage and cost controls](#33-usage-and-cost-controls)).
- Provider capabilities are never overstated in the UI — a platform that doesn't support a
  feature (e.g., carousel posts) must not offer it.

## 20. User roles and permissions

| Role | Typical access |
|---|---|
| Super Admin | Full access, including integrations, provider credentials, and user management |
| Admin | User management, company settings, most operational access |
| Marketing Manager | Campaigns, segments, social, analytics — approval authority |
| Content Creator | Drafts, AI generation, media — no send/publish authority |
| Analyst | Read-only analytics and reporting |
| Viewer | Read-only, broadest restriction |

Full permission matrix (action × role) lives in `docs/02-features/RBAC.md` (Phase 2).

## 21. Email requirements

See [MVP_SCOPE.md §C Email Marketing](MVP_SCOPE.md#c-email-marketing) and, once created,
`docs/02-features/EMAIL_CAMPAIGNS.md`, `EMAIL_TEMPLATES.md`, `EMAIL_DELIVERY_TRACKING.md`.
Campaign and recipient state machines are defined in
`docs/04-architecture/EMAIL_DELIVERY_FLOW.md` (Phase 4).

## 22. Social requirements

See [MVP_SCOPE.md §D Social Media Automation](MVP_SCOPE.md#d-social-media-automation).
Exactly one platform is implemented first (decision pending — [OQ-003](../00-project-control/OPEN_QUESTIONS.md));
the architecture supports adding platforms later via `SocialProvider` adapters
([DEC-GRX-005](../00-project-control/DECISIONS.md)). A provider capability matrix (text,
image, video, carousel, scheduling, analytics, OAuth refresh, webhooks) is required before
any platform is presented as supported in the UI.

## 23. AI requirements

See [MVP_SCOPE.md §E AI Content Assistant](MVP_SCOPE.md#e-ai-content-assistant). Mandatory
safety rules (from the governing spec, to be detailed further in `docs/07-ai/AI_SAFETY.md`,
Phase 6):

| ID | Requirement |
|---|---|
| GRX-AI-001 | AI content is always marked `AI_GENERATED`; provenance is retained. |
| GRX-AI-002 | AI output cannot send email or publish social content directly. |
| GRX-AI-003 | A human must review and approve before send/publish. |
| GRX-AI-004 | Authorization/permissions are always deterministic — the model never determines access. |
| GRX-AI-005 | Provider secrets are never inserted into prompts. |
| GRX-AI-006 | Prompt input/output, model, prompt version, token usage, and estimated cost are logged for every generation. |
| GRX-AI-007 | All external/imported content (contacts, uploaded files, provider responses, URLs) is treated as untrusted data, never as instructions. |

## 24. Analytics requirements

Basic analytics for MVP: campaign delivery/engagement (sent, delivered, opened, clicked,
bounced, complained, unsubscribed), social post publishing status and available
platform-reported engagement, AI usage/cost, and an activity dashboard. Evidence
classification (verified / observed / calculated / estimated / AI-generated / user-provided)
applies to every metric shown — see [§19 Evidence Classification in the source discovery
PRD](../archive/source-prd-seo-aeo-geo-website-intelligence/prd/FULL_PRD.md), which this MVP
reuses as a display convention.

## 25. Integration requirements

| ID | Integration | Release |
|---|---|---|
| GRX-INT-EMAIL-001 | One production email provider adapter + SMTP support | MVP |
| GRX-INT-SOCIAL-001 | One social platform (OAuth, publish, schedule) | MVP |
| GRX-INT-AI-001 | Configurable AI provider(s)/model(s) | MVP |
| GRX-INT-STORAGE-001 | S3-compatible object storage | MVP |
| GRX-INT-GSC-001 | Google Search Console | V1.5 (see [FUTURE_SCOPE_SEO_AEO_GEO](FUTURE_SCOPE_SEO_AEO_GEO.md)) |
| GRX-INT-WP-001 | WordPress | V2 |
| GRX-INT-GH-001 | GitHub | V2 |

## 26. Security requirements

See [§20 Security Baseline of the governing spec] — detailed further in
`docs/08-security/` (Phase 6). Non-negotiable for MVP: RBAC enforced server-side, encrypted
provider credentials, input validation, output encoding, SQL injection/XSS/CSRF/SSRF
prevention, webhook signature validation, rate limiting, audit logging, secret redaction in
logs.

## 27. Privacy requirements

Contact consent status and unsubscribe status are first-class fields, not afterthoughts.
Data retention defaults are pending ([OQ-008](../00-project-control/OPEN_QUESTIONS.md)).
Export/deletion of a contact's data must be supportable on request.

## 28. Compliance considerations

Growixa does not claim formal GDPR, SOC 2, or ISO certification. Use the phrase
"compliance-ready controls" where relevant. Unsubscribe compliance and suppression
enforcement are mandatory, not optional (see [DEC-GRX-008](../00-project-control/DECISIONS.md)).

## 29. UX requirements

Full detail in `docs/03-ux-ui/` (Phase 3). Baseline: responsive desktop/tablet layout,
consistent loading/empty/error/success states across all screens, destructive actions
require explicit confirmation.

## 30. Accessibility requirements

WCAG 2.2 AA target (GRX-NFR-003). Full checklist in `docs/03-ux-ui/ACCESSIBILITY_REQUIREMENTS.md` (Phase 3).

## 31. Performance targets

See [§16 Non-Functional Requirements](#16-non-functional-requirements) (GRX-NFR-001).

## 32. Reliability targets

See [§16 Non-Functional Requirements](#16-non-functional-requirements) (GRX-NFR-002).
Availability target and job-degradation behavior to be finalized in
`docs/04-architecture/SCALABILITY_PLAN.md` (Phase 4).

## 33. Usage and cost controls

Every cost-generating operation (email sends, AI generations, social publishing, storage,
media processing, contact imports, workflow executions, large exports) is metered via a
centralized usage service: check entitlement → check limit → check current usage → reserve
→ execute → record actual usage → correct reservation on failure → emit audit event. Required
from Slice 1 onward per [DEC-GRX-007](../00-project-control/DECISIONS.md), even though MVP
is single-tenant with no external billing ([ASM-008](../00-project-control/ASSUMPTIONS.md), [OQ-007](../00-project-control/OPEN_QUESTIONS.md)).

## 34. Risks

See [RISKS.md](../00-project-control/RISKS.md) (to be created) for the live register. Key
risks carried from discovery: unsupervised sending/publishing, low-quality AI content
reaching real recipients without review, provider API changes breaking delivery, prompt
injection via imported/untrusted content, excessive AI/provider cost without metering.

## 35. Dependencies

Slice 3 (first email campaign) depends on OQ-002 (email provider) being resolved. Slice 5
(social) depends on OQ-003 (platform) being resolved. Slice 6 (AI assistant) depends on
OQ-004 (AI provider/model) being resolved. See [OPEN_QUESTIONS.md](../00-project-control/OPEN_QUESTIONS.md).

## 36. Assumptions

See [ASSUMPTIONS.md](../00-project-control/ASSUMPTIONS.md).

## 37. Open questions

See [OPEN_QUESTIONS.md](../00-project-control/OPEN_QUESTIONS.md).

## 38. Release strategy

See [ROADMAP.md](ROADMAP.md): MVP (Slices 1–6) → Release 1.1 → Release 1.2 → V1.5 → V2 → V3.

## 39. Acceptance criteria

Feature-level acceptance criteria live with each feature spec in `docs/02-features/`
(Phase 2) and roll up into `docs/00-project-control/TRACEABILITY_MATRIX.md` (Phase 9).
MVP-level acceptance is defined per slice in [MVP_SCOPE.md](MVP_SCOPE.md).

## 40. Definition of Done

See [DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md).

## 41. Approval section

| Role | Name | Status | Date |
|---|---|---|---|
| Product owner | Ravi | PENDING | — |

This PRD is a living document. Material scope changes must be logged in
[DECISIONS.md](../00-project-control/DECISIONS.md), not made silently.
