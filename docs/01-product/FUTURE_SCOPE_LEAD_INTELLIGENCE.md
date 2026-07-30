# Future Scope: Voice Qualification, Licensed Audiences & Contact Enrichment

- Document ID: DOC-FUTURE-SCOPE-LEAD-INTELLIGENCE
- Status: ACTIVE (idea capture only — not approved, not scheduled into any release)
- Version: 1.0
- Last updated: 2026-07-30
- Owner: Product owner (Ravi) via coding agent
- Related documents: [DECISIONS §DEC-GRX-001](../00-project-control/DECISIONS.md), [MVP_SCOPE](MVP_SCOPE.md), [PRD](PRD.md), [FEATURE_CATALOG](../02-features/FEATURE_CATALOG.md), [DESIGN_REFERENCE_REVSPOT](../03-ux-ui/DESIGN_REFERENCE_REVSPOT.md)

## Purpose

Captures three feature ideas surfaced while reviewing a competitor/reference product
(revspot.ai, an AI-led B2C lead-generation platform) at the product owner's request, for
possible future consideration. Checked against the current docs first — none of the
three exist anywhere in `PRD.md`, `MVP_SCOPE.md`, `ROADMAP.md`, or `FEATURE_CATALOG.md`
today.

This is idea capture, not a plan. No `GRX-*` task should be created for any of it, and it
must not enter `MASTER_TASK_TRACKER.md` or any `docs/14-sprints/` file, until the
business-model question in [§Read this before picking any of these up](#read-this-before-picking-any-of-these-up)
is resolved.

## The three ideas

### 1. AI voice qualification agent

An AI agent places (or answers) calls to leads, asks structured qualifying questions in
the lead's own language, and hands back a scored, enriched profile (budget, timeline,
intent) before a human ever talks to them. Revspot runs this in 10+ languages and treats
it as a core stage of their funnel, not an add-on.

**Not covered today.** Growixa's `AI_CONTENT_ASSISTANT.md` (Slice 6, `GRX-FEAT-021`) is
about content generation with human approval — text/social copy, not outbound/inbound
voice calls. There is no telephony integration anywhere in `MODULE_BOUNDARIES.md` or
`DATABASE_SCHEMA.md`.

### 2. Licensed / high-intent audience data

Pre-built, licensed third-party audience segments (e.g. "real-estate intent," "wealth &
investing") sold as a subscription and synced directly into campaigns and CRM — buying
reach into people who aren't already Growixa's own contacts.

**Not covered today.** Growixa's contact/segment features (`GRX-FEAT-006`
Contact Management, `GRX-FEAT-009` Segmentation) operate only on a company's own
first-party contacts. There is no concept of licensed third-party audience data anywhere
in the current docs.

### 3. Contact extraction & enrichment (LinkedIn / CSV → verified contact + 50+ data points)

Given a LinkedIn URL or a bulk CSV of names, return a verified phone number, personal
email, work email, and 50+ enrichment data points (income band, profession, intent
score) per contact.

**Partially adjacent, not covered.** `GRX-FEAT-007` (Contact Import, Slice 2) imports
contacts a company already has — it does not discover or enrich new contacts from an
external source like LinkedIn. This would be a new capability, not an extension of
import.

## A fourth idea, already covered — noted for completeness

Revspot also automatically re-engages dormant leads over WhatsApp. This is **not new** —
`MVP_SCOPE.md §Deferred, not cancelled` already lists "WhatsApp marketing" as deferred
indefinitely, and `FEATURE_CATALOG.md`'s "Deferred features (other, indefinite)" section
already lists it too. No new document needed for this piece; it's recorded here only so
a future reader doesn't think it was missed.

## Why this is a bigger question than "add a feature"

All three ideas assume Growixa acquires *new* leads/contacts the company doesn't already
have (via ads, licensed data, or LinkedIn scraping) and qualifies them via an AI
telephony product. Per [DEC-GRX-001](../00-project-control/DECISIONS.md) and the current
`PRD.md`, Growixa is scoped as **marketing automation for a company's own audience** —
email, social, content, and (later) SEO/AEO/GEO for a company's own contacts and
website — not an outbound lead-generation/voice-AI product for finding net-new buyers.
Adding these would be a meaningful expansion of what kind of product Growixa is, closer
to Revspot's own category (B2C sales lead-gen) than Growixa's stated one (growth/
marketing automation for existing audiences).

That's not a reason to reject them — voice-AI qualification in particular is a strong,
differentiated idea — but it's a product-direction call, not a routine backlog addition.

## Read this before picking any of these up

- Confirm with the product owner whether Growixa's scope should expand from "automate
  marketing to contacts we have" to "also acquire and qualify new contacts we don't have
  yet" — this changes the product's category, not just its feature list.
- Voice AI qualification requires a telephony/voice-AI vendor decision (not evaluated
  here) and a new module boundary (`MODULE_BOUNDARIES.md` has no `voice` module today).
- Licensed audience data requires a data-licensing/vendor relationship and a way to
  attribute cost per audience pack — no billing/procurement model exists in the current
  docs for this.
- Contact extraction/enrichment from LinkedIn raises data-provenance and consent
  questions (scraping/enriching people who never opted into a Growixa-using company's
  list) that `docs/08-security/THREAT_MODEL.md` and any future compliance doc should
  address before this is built, not after.

## Explicitly not staged into any release

Not in the MVP (Slices 1–6), not in V1.5–V3 per [ROADMAP.md](ROADMAP.md).
