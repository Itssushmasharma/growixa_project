# Feature Catalog

- Document ID: DOC-FEATURE-CATALOG
- Status: ACTIVE (stub — full per-feature docs are created in Phase 2)
- Version: 1.1
- Last updated: 2026-08-15
- Owner: Coding agent
- Related documents: [PRD](../01-product/PRD.md), [MVP_SCOPE](../01-product/MVP_SCOPE.md), [FUTURE_SCOPE_SEO_AEO_GEO](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md)

This is the master list of features and their release/status. Each MVP feature gets its own
detailed spec document in this folder as Phase 2 proceeds (see the "Doc" column). Deferred
features are listed for traceability only — they must not be implemented or scheduled until
their target release, per [DEC-GRX-001](../00-project-control/DECISIONS.md).

## MVP features (Release: MVP)

| Feature ID | Feature | Slice | Doc | Status |
|---|---|---|---|---|
| GRX-FEAT-001 | Authentication | 1 | `AUTHENTICATION.md` | NOT_STARTED |
| GRX-FEAT-002 | User Management | 1 | `USER_MANAGEMENT.md` | NOT_STARTED |
| GRX-FEAT-003 | RBAC | 1 | `RBAC.md` | NOT_STARTED |
| GRX-FEAT-004 | Company Settings | 1 | `COMPANY_SETTINGS.md` | NOT_STARTED |
| GRX-FEAT-005 | Brand Profile | 1 | `BRAND_PROFILE.md` | NOT_STARTED |
| GRX-FEAT-006 | Contact Management | 2 | `CONTACT_MANAGEMENT.md` | NOT_STARTED |
| GRX-FEAT-007 | Contact Import | 2 | `CONTACT_IMPORT.md` | NOT_STARTED |
| GRX-FEAT-008 | Contact Tags | 2 | `CONTACT_TAGS.md` | NOT_STARTED |
| GRX-FEAT-009 | Segmentation | 2 | `SEGMENTATION.md` | NOT_STARTED |
| GRX-FEAT-010 | Suppression and Consent | 2 | `SUPPRESSION_AND_CONSENT.md` | NOT_STARTED |
| GRX-FEAT-011 | Email Providers | 3 | `EMAIL_PROVIDERS.md` | NOT_STARTED |
| GRX-FEAT-012 | Email Templates | 3 | `EMAIL_TEMPLATES.md` | NOT_STARTED |
| GRX-FEAT-013 | Email Campaigns | 3 | `EMAIL_CAMPAIGNS.md` | NOT_STARTED |
| GRX-FEAT-014 | Campaign Scheduling | 4 | `CAMPAIGN_SCHEDULING.md` | NOT_STARTED |
| GRX-FEAT-015 | Email Delivery Tracking | 3/4 | `EMAIL_DELIVERY_TRACKING.md` | NOT_STARTED |
| GRX-FEAT-016 | Email Analytics | 3 | `EMAIL_ANALYTICS.md` | NOT_STARTED |
| GRX-FEAT-017 | Social Account Connections | 5 | `SOCIAL_ACCOUNT_CONNECTIONS.md` | NOT_STARTED |
| GRX-FEAT-018 | Social Posts | 5 | `SOCIAL_POSTS.md` | NOT_STARTED |
| GRX-FEAT-019 | Social Scheduling | 5 | `SOCIAL_SCHEDULING.md` | NOT_STARTED |
| GRX-FEAT-020 | Content Calendar | 5 | `CONTENT_CALENDAR.md` | NOT_STARTED |
| GRX-FEAT-021 | AI Content Assistant | 6 | `AI_CONTENT_ASSISTANT.md` | NOT_STARTED |
| GRX-FEAT-022 | AI Brand Voice | 6 | `AI_BRAND_VOICE.md` | NOT_STARTED |
| GRX-FEAT-023 | Analytics and Reporting | 3/5 | `ANALYTICS_AND_REPORTING.md` | NOT_STARTED |
| GRX-FEAT-024 | Notifications | 1 | `NOTIFICATIONS.md` | NOT_STARTED |
| GRX-FEAT-025 | Usage Metering | 1 | `USAGE_METERING.md` | NOT_STARTED |
| GRX-FEAT-026 | Integrations (management) | 1 | `INTEGRATIONS.md` | NOT_STARTED |
| GRX-FEAT-027 | Audit Logs | 1 | `AUDIT_LOGS.md` | NOT_STARTED |
| GRX-FEAT-028 | Admin Portal | 1 | `ADMIN_PORTAL.md` | NOT_STARTED |
| GRX-FEAT-029 | Multi-Domain Subdomain Routing | 5 (retrofit) | `SUBDOMAIN_ROUTING.md` | NOT_STARTED |
| GRX-FEAT-030 | Email Validation (list hygiene) | post-MVP (ad hoc) | `EMAIL_VALIDATION.md` | BUILT — see note below |

`GRX-FEAT-010` (Suppression and Consent) was extended post-MVP by `GRX-SAAS-015`:
whole-domain blocking, suppression CSV import/export, and the RFC 8058
`List-Unsubscribe` / `List-Unsubscribe-Post` one-click header on outbound campaign mail
(the Gmail/Yahoo 2024 bulk-sender mandate). The catalog entry is unchanged — this is the
same feature, extended, not a new one. Still unbuilt from the source plan, and **not
scheduled**: hashed suppression storage and a global cross-account suppression list — both
gated on `OQ-017`.

`GRX-FEAT-030` was built ad hoc by `GRX-SAAS-016` (free in-house checks: syntax, MX/A,
disposable-domain list, role-account list) and `GRX-SAAS-017` (platform-admin-configurable
multi-vendor real-time verification, paid plans only, Clearout as the first provider). It
predates any catalog/roadmap entry — registered here 2026-08-15 during product intake
triage so the shipped surface is traceable. It is not an MVP Slice 1–6 feature.

`AUTOMATION_WORKFLOWS.md` is intentionally not listed for MVP — general workflow automation
beyond scheduled campaigns/posts is not in MVP scope.

`GRX-FEAT-029` (`DEC-GRX-031`) is outstanding scope from Sprint 5's self-service launch
work, not a Slice 1–6 feature — the app currently runs on one domain with path-based
route groups (`/dashboard/*`, `/platform/*`) instead of the marketing/`app.*`/`platform.*`
subdomain split `DEC-GRX-017` calls for. Blocked on `OQ-SUB-001`/`003` (production domain,
post-login landing behavior) per `AGENT_EXECUTION_RULES.md` — not `READY` yet.

## Deferred features (SEO / AEO / GEO / website intelligence track)

Full requirement mapping: [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md).

| Feature ID | Feature | Target release | Status |
|---|---|---|---|
| GRX-FEAT-SEO-001 | Website Crawling & Intelligence | V1.5 | DEFERRED |
| GRX-FEAT-SEO-002 | Technical & On-Page SEO Audit | V1.5 | DEFERRED |
| GRX-FEAT-SEO-003 | Search Console Integration | V1.5 | DEFERRED |
| GRX-FEAT-SEO-004 | Metadata & Schema Recommendations | V2 | DEFERRED |
| GRX-FEAT-SEO-005 | WordPress Integration | V2 | DEFERRED |
| GRX-FEAT-SEO-006 | GitHub Integration | V2 | DEFERRED |
| GRX-FEAT-SEO-007 | Content Optimization Agent | V2 | DEFERRED |
| GRX-FEAT-SEO-008 | AEO Specialist | V2 | DEFERRED |
| GRX-FEAT-SEO-009 | GEO Specialist | V3 | DEFERRED |
| GRX-FEAT-SEO-010 | Competitive Intelligence Agent | V3 | DEFERRED |
| GRX-FEAT-SEO-011 | Authority & Outreach Manager | V3 | DEFERRED |
| GRX-FEAT-SEO-012 | AI Visibility Monitoring | V3 | DEFERRED |
| GRX-FEAT-SEO-013 | Continuous Improvement / Growth Engine | V3 | DEFERRED |
| GRX-FEAT-SMS-001 | SMS Marketing & Twilio Integration | Release 1.2 | STAGED |

## Proposed features (product intake — NOT confirmed, NOT scheduled)

Raised 2026-08-15 from triaging the local `need_review_docs/` intake folder. These are
**ID reservations plus a pointer to the source discussion** — nothing more. None has a
confirmed release target, an approved spec, or a `MASTER_TASK_TRACKER.md` row, and none
may acquire one until its blocking question in
[OPEN_QUESTIONS.md](../00-project-control/OPEN_QUESTIONS.md) is answered by the product
owner. Listing them here is traceability, not scheduling — the same discipline the
deferred tables above follow.

| Feature ID | Feature | Proposed target (unconfirmed) | Blocking question | Status |
|---|---|---|---|---|
| GRX-FEAT-032 | Email Warmup & deliverability health | Release 1.1 | `OQ-018` (+ build-vs-buy warmup network, per-mailbox add-on pricing) | PROPOSED |
| GRX-FEAT-033 | Unified Inbox (reply management) | Release 1.2 | `OQ-018` (+ reply-ingestion mechanism: Gmail API vs IMAP vs forwarding) | PROPOSED |
| GRX-FEAT-034 | Telegram Integration (channel / group / bot DM) | Release 1.2 | `OQ-018` (+ own-bot vs shared-bot model). Architecturally a `SocialProvider` adapter per [DEC-GRX-005](../00-project-control/DECISIONS.md) — no new pattern needed | PROPOSED |
| GRX-FEAT-035 | Growixa MCP Server | Release 1.1/1.2 | **`OQ-015`** — the plan's direct-scheduling mode conflicts with `GRX-AI-002`/`GRX-AI-003` and [DEC-GRX-006](../00-project-control/DECISIONS.md) (human approval before send/publish). Must be resolved before any spec is written | PROPOSED — BLOCKED |
| GRX-FEAT-036 | Role-adaptive dashboard views (4 lenses) + AI Next Best Actions | Release 1.1 | **`OQ-016`** — the "Next Best Actions" engine overlaps the V3 next-best-action engine and [DEC-GRX-012](../00-project-control/DECISIONS.md) | PROPOSED — BLOCKED |

**ID note:** the intake docs proposed `GRX-FEAT-029`–`032` for Warmup / Validation /
Unified Inbox / Telegram. `GRX-FEAT-029` was already taken (Multi-Domain Subdomain
Routing, `DEC-GRX-031`) and `GRX-FEAT-030` is now the shipped Email Validation feature, so
the remaining four were reassigned to `032`–`034` (plus `035`/`036` for the MCP server and
role-adaptive dashboards). The intake `INDEX.md` records the same mapping. This catalog is
the authority on feature IDs — allocate the next free ID here, never in an intake doc.

## Deferred features (other, indefinite)

Full multi-tenancy, customer-facing SaaS signup, tenant billing, full CRM, sales pipeline,
WhatsApp/push marketing (SMS staged in Release 1.2), landing-page/form builders, ad campaign automation, ecommerce
automation, white-label platform, enterprise workflow builder, multi-region deployment. See
[MVP_SCOPE.md §Deferred, not cancelled](../01-product/MVP_SCOPE.md#deferred-not-cancelled).

AI voice lead qualification, licensed third-party audience data, and LinkedIn/CSV contact
enrichment — idea capture only, not scheduled — see
[FUTURE_SCOPE_LEAD_INTELLIGENCE.md](../01-product/FUTURE_SCOPE_LEAD_INTELLIGENCE.md).
