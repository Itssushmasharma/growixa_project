# Roadmap

- Document ID: DOC-ROADMAP
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Product owner (Ravi) via coding agent
- Related documents: [MVP_SCOPE](MVP_SCOPE.md), [FUTURE_SCOPE_SEO_AEO_GEO](FUTURE_SCOPE_SEO_AEO_GEO.md), [DECISIONS §DEC-GRX-001](../00-project-control/DECISIONS.md)

Growixa's positioning ("AI-powered growth and marketing automation platform, beginning with
email and social, then expanding into SEO, AEO, GEO, website intelligence, content
optimization, and integrated growth workflows") is realized across these releases. Each
release requires the prior one to be stable — no parallel builds across releases.

## MVP — Email & Social Marketing Foundation

Scope: [MVP_SCOPE.md](MVP_SCOPE.md) §A–E, delivered as Slices 1–6:

1. **Slice 1 — Foundation:** repo/Docker setup, auth, users, RBAC, company settings, audit log, dashboard shell.
2. **Slice 2 — Contacts:** contact CRUD, tags, lists, CSV import, consent/suppression.
3. **Slice 3 — First Email Campaign:** one email provider, templates, campaign draft, test send, immediate send, suppression checks, basic report.
4. **Slice 4 — Scheduled Email:** scheduler, worker, idempotent execution, retry, cancellation, dead-letter handling.
5. **Slice 5 — Social Publishing:** one platform, OAuth, composer, media, immediate/scheduled publish, content calendar.
6. **Slice 6 — AI Assistant:** provider/model config, prompt templates, brand voice, subject/caption generation, rewriting, human approval, usage/cost tracking.

## Release 1.1 — Marketing depth

Content calendar refinement, topic-agnostic content ideas backlog, stronger segmentation,
additional email analytics, team-approval workflows for campaigns.

## Release 1.2 — Marketing breadth

Additional social platform(s), additional email provider option, SMS Marketing & Twilio integration (Admin provider setup, E.164 contact phone formatting, SMS campaign composer, TCPA opt-out webhooks), experiment/A-B testing for subject lines, richer notification center.

## V1.5 — Website Intelligence Foundation (read-only)

First SEO/AEO/GEO-track release. Scope: [FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md)
— website crawling, technical/on-page SEO audit, metadata recommendations (report/export
only, nothing auto-applied), Google Search Console integration for baseline metrics.

## V2 — SEO Execution + Content Optimization + AEO

WordPress and GitHub write integrations for approved changes, schema/internal-link
generation, content refresh & briefs, AEO specialist agent, basic competitor gap view,
SEO/AEO reporting. See [FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md) for full
requirement mapping.

## V3 — GEO + Full Growth Agent System

GEO specialist, authority/outreach manager, competitive intelligence agent, sampled
AI-visibility observation, the continuous-improvement/next-best-action engine, and full
multi-agent orchestration (Growth Strategist coordinating all specialists across both the
marketing and SEO/AEO/GEO tracks).

## Sprint 5 — Customer Account Platform Foundation

**No longer deferred.** Per [DEC-GRX-017](../00-project-control/DECISIONS.md)
(2026-08-07, supersedes `DEC-GRX-002`/`DEC-GRX-013`), Growixa is opening for self-service
customer registration, with a separate IITDEVELOPER Platform Admin control plane above
all customer accounts. This is staged as its own sprint after Slices 1–4 (the
single-tenant MVP) and ahead of the still-unscheduled V1.5–V3 SEO/AEO/GEO track below — it's
a foundational retrofit (customer-account data isolation, platform auth, registration,
billing, platform admin panel), not a feature in the Slice 1–6 sense. Full phased plan:
[SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md),
design source: [FUTURE_SCOPE_PLATFORM_ADMIN.md](FUTURE_SCOPE_PLATFORM_ADMIN.md).

**Outstanding piece of this sprint's scope**: `GRX-FEAT-029` — the marketing/`app.*`/
`platform.*` subdomain split (`DEC-GRX-031`). The app today still separates customer and
platform-admin audiences by path (`/dashboard/*`, `/platform/*`) on one domain, not by
subdomain. Blocked on confirming the production domain and post-login landing behavior
(`OQ-SUB-001`/`003`) before it can move to `READY`.

## Explicitly deferred indefinitely (not on this roadmap)

White-label platform, enterprise workflow builder, multi-region deployment — no trigger
condition named yet; revisit if/when a concrete need arises.
