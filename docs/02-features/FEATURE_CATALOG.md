# Feature Catalog

- Document ID: DOC-FEATURE-CATALOG
- Status: ACTIVE (stub — full per-feature docs are created in Phase 2)
- Version: 1.0
- Last updated: 2026-07-22
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

## Deferred features (other, indefinite)

Full multi-tenancy, customer-facing SaaS signup, tenant billing, full CRM, sales pipeline,
WhatsApp/push marketing (SMS staged in Release 1.2), landing-page/form builders, ad campaign automation, ecommerce
automation, white-label platform, enterprise workflow builder, multi-region deployment. See
[MVP_SCOPE.md §Deferred, not cancelled](../01-product/MVP_SCOPE.md#deferred-not-cancelled).

AI voice lead qualification, licensed third-party audience data, and LinkedIn/CSV contact
enrichment — idea capture only, not scheduled — see
[FUTURE_SCOPE_LEAD_INTELLIGENCE.md](../01-product/FUTURE_SCOPE_LEAD_INTELLIGENCE.md).
