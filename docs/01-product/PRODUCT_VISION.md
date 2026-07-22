# Product Vision

- Document ID: DOC-PRODUCT-VISION
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Product owner (Ravi) via coding agent
- Related documents: [PRD](PRD.md), [MVP_SCOPE](MVP_SCOPE.md), [ROADMAP](ROADMAP.md), [DECISIONS §DEC-GRX-001](../00-project-control/DECISIONS.md)

## Positioning statement

> Growixa is an AI-powered growth and marketing automation platform. It begins with email
> and social media automation, then expands into SEO, AEO, GEO, website intelligence,
> content optimization, and integrated growth workflows.

## Vision

Give a company one platform where its marketing team can run and improve everything that
drives growth — audience communication, content, and eventually website/search
performance — without stitching together disconnected tools, and without giving up human
control over what actually gets sent, published, or changed.

## Why start with email and social

Email and social automation are the fastest path to a working, valuable, end-to-end
product: the data model is simpler (contacts, campaigns, posts) than website crawling and
multi-agent SEO analysis, the integrations are narrower (one email provider, one social
platform to start), and the value is immediately visible to a marketing team. It also
establishes the platform's core patterns — provider adapters, AI-assisted content with
human approval, usage metering, audit logging — that the later SEO/AEO/GEO/website
intelligence capabilities will reuse rather than reinvent.

## Where the platform is going

Once email/social/contacts/AI-assist/scheduling/analytics are stable in production, Growixa
expands into the capabilities captured in the original discovery work — see
[FUTURE_SCOPE_SEO_AEO_GEO.md](FUTURE_SCOPE_SEO_AEO_GEO.md) for the detailed mapping and
[ROADMAP.md](ROADMAP.md) for release staging (V1.5–V3):

- Website crawling and technical SEO auditing
- On-page SEO and metadata recommendations
- AEO (answer-engine optimization) and GEO (generative-engine optimization)
- WordPress and GitHub integration for applying approved technical changes
- Search Console integration and AI-visibility observation
- Competitive intelligence and authority/outreach workflows
- A coordinated multi-agent growth system, building on the human-approval and provider-adapter
  patterns established in the MVP

## Product principles

| Principle | Meaning |
|---|---|
| Outcome-first | Prioritize real engagement, delivery, and conversion outcomes over vanity metrics. |
| Human control | AI assists; it does not independently send, publish, or apply changes. Every consequential action requires approval. |
| Evidence before claims | Clearly distinguish verified provider data, observed activity, calculated scores, and AI-generated content — never blur them (see PRD §19 evidence classification). |
| Safe automation | Use drafts, previews, validation, retries, rollback where applicable, and audit trails for anything that reaches a real recipient or a real website. |
| Build the smallest working slice | Ship one vertical slice end to end before starting the next; no parallel half-finished modules. |
| Provider-agnostic by design | Email, social, AI, storage, and (later) SEO/CMS integrations sit behind adapters so a provider swap doesn't require a rewrite. |
| Single-tenant now, modular for later | The MVP is one company, multiple internal users — but module boundaries don't foreclose multi-tenancy if the business model changes. |
| Don't overpromise | Never guarantee open rates, click rates, rankings, citations, or revenue outcomes — Growixa reports what happened, with appropriate confidence and evidence class. |
