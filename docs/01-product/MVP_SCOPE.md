# MVP Scope

- Document ID: DOC-MVP-SCOPE
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Product owner (Ravi) via coding agent
- Related documents: [PRD](PRD.md), [FUTURE_SCOPE_SEO_AEO_GEO](FUTURE_SCOPE_SEO_AEO_GEO.md), [ROADMAP](ROADMAP.md), [DECISIONS §DEC-GRX-002](../00-project-control/DECISIONS.md)

Growixa's MVP is a **single-tenant, multi-user, web-based marketing dashboard**. One
company installation; multiple internal users under RBAC. Not multi-tenant — see
[DEC-GRX-002](../00-project-control/DECISIONS.md).

## A. Platform Foundation

- User authentication, user management, RBAC
- Company profile, brand settings, application settings
- Audit logging
- Notification center
- Secure provider credential storage
- Usage metering foundation
- Admin dashboard

## B. Contact and Audience Management

- Contact CRUD (create, edit, delete/archive)
- CSV contact import, import validation, import history
- Contact tags, contact lists, dynamic/saved segments, custom fields
- Consent status, unsubscribe status, suppression list
- Contact activity history, duplicate-contact handling

## C. Email Marketing

- Email provider configuration, SMTP support, one production provider adapter
- Sender identity, email templates with versioning, basic rich-text/visual editor
- Campaign drafts, recipient/segment selection, subject/preview text, personalization variables
- Test email, immediate send, scheduled send, cancellation before execution
- Delivery/open/click/bounce/complaint tracking, unsubscribe handling
- Campaign report, basic email analytics

## D. Social Media Automation

- One approved platform for the first working integration (architecture supports more later)
- Connect account (OAuth), view connection status
- Create post, add media, save draft, publish immediately, schedule
- Content calendar, publishing status, retry failed publishing, provider error visibility

## E. AI Content Assistant

- Generate email subject lines, email body content, social captions, CTA suggestions
- Rewrite tone, shorten, expand, generate content ideas, audience-specific variations
- Apply company brand voice, suggest hashtags, suggest posting time (estimate only)
- Store generation history, track token usage and estimated cost
- Configurable AI providers/models
- **AI-generated content always requires human approval before sending or publishing.**

## Deferred, not cancelled

These are part of Growixa's long-term vision but out of MVP scope. They are staged into
future releases — see [ROADMAP.md](ROADMAP.md) and, for the SEO/AEO/GEO group specifically,
[FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md):

- Full multi-tenancy, customer-facing SaaS signup, tenant-specific billing — a concrete
  proposed shape for this (self-service registration, `account_id` isolation, an
  IITDEVELOPER platform-admin control plane) is captured in
  [FUTURE_SCOPE_PLATFORM_ADMIN.md](FUTURE_SCOPE_PLATFORM_ADMIN.md), not decided or scheduled
- AI voice lead qualification, licensed third-party audience data, and LinkedIn/CSV
  contact enrichment — outbound lead-acquisition ideas captured in
  [FUTURE_SCOPE_LEAD_INTELLIGENCE.md](FUTURE_SCOPE_LEAD_INTELLIGENCE.md); these would
  expand Growixa's product category beyond "automate marketing to contacts we already
  have," so they need an explicit scope decision, not just a backlog slot
- Advanced autonomous marketing agents; AI that publishes without approval
- Full CRM, sales pipeline
- WhatsApp marketing, SMS campaigns, push notifications
- Landing-page builder, form builder, ad campaign automation
- **SEO automation, AEO, GEO, website crawler, website audits, metadata recommendations,
  WordPress integration, GitHub integration, Search Console integration, content
  optimization agents, website improvement workflows** — see
  [FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md) for the full mapping to V1.5–V3
- Ecommerce automation, advanced marketing attribution
- Enterprise workflow builder, multi-region deployment, white-label platform

Nothing in this "deferred" list may enter `MASTER_TASK_TRACKER.md` or any Slice 1–6 sprint
until the corresponding release is actually scheduled.
