# Future Scope: Voice Qualification, Licensed Audiences & Contact Enrichment

- Document ID: DOC-FUTURE-SCOPE-LEAD-INTELLIGENCE
- Status: ACTIVE — idea #3 is now under an open product-direction call
  ([DEC-GRX-033](../00-project-control/DECISIONS.md), **PROPOSED**); ideas #1 and #2
  remain idea capture only, not approved, not scheduled
- Version: 1.2
- Last updated: 2026-08-28
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

## Update, 2026-08-15 — idea #3 gate opened (not passed)

The product owner raised idea #3 again and directed that the gate below be worked
properly rather than bypassed. Two of the four preconditions in the next section are now
addressed for idea #3 specifically:

- The business-model/product-direction call is drafted as
  [DEC-GRX-033](../00-project-control/DECISIONS.md) — **`PROPOSED`, awaiting the product
  owner's confirmation.** It proposes a narrow expansion: Growixa ingests
  customer-supplied external contacts with mandatory provenance, does not perform
  acquisition itself in a first version, and does not sell audiences.
- The provenance/consent analysis this document asked for now exists:
  [THREAT_MODEL.md §"Pre-build — External contact acquisition & enrichment"](../08-security/THREAT_MODEL.md)
  (T81–T87). It had no coverage anywhere before this date. T83 is the one to read first —
  scraped-list spam traps degrade sending reputation for *every other customer* on the
  shared Postmark path, which makes this a platform risk rather than an account risk.

One new blocker surfaced that this document did not anticipate: `OQ-020` — whether the
ESP's acceptable-use policy permits externally-sourced lists at all. Most ESPs prohibit
them. That is a question for the vendor, and it can invalidate the capability regardless
of what is decided internally.

**Status is unchanged in the way that matters:** nothing is approved and nothing is
scheduled. Ideas #1 (voice) and #2 (licensed data) are untouched by this and remain fully
gated.

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

## Update, 2026-08-28 — the Find / Understand / Act framing

Recorded from a product-owner brainstorm on how idea #3 (contact extraction &
enrichment) could become a core, visibly-AI-driven differentiator rather than a
plumbing utility, followed by a product-management review pass that corrected
several overconfident technical/legal claims in the first draft before anything gets
carried into a PRD. This section reflects the corrected version. It is idea capture
layered on top of the existing `DEC-GRX-033` proposal — it does not change that
proposal's status (still `PROPOSED`) and does not itself require a new decision to
*record*, but the **Act** layer below touches `DEC-GRX-006` (human-approval rule) and
the scoring/evidence design below tightens `DEC-GRX-033`'s existing provenance
requirement rather than replacing it. Nothing here is scheduled or ticketed.

### The positioning — this is the part worth protecting

> Growixa doesn't just find prospects. It explains who is worth contacting, why they
> fit, and what your next move should be.

Find → Understand → Act is the differentiator, not the enrichment call itself. Any
vendor can return an email address. What Hunter.io, Apollo, and Clearbit do *not* do
is explain fit, generate a narrative grounded in evidence, and hand off directly into
an approval-gated outreach draft inside the same product that sends the campaign.
Reframed: **Apollo/Hunter may supply data. Growixa supplies the intelligence and
action layer.** That is a defensible position even if every data source underneath it
is commodity or licensed — the value is in Understand and Act, not in Find.

### Corrections to the first draft of this brainstorm

The initial framing (recorded earlier in this document's history, now superseded by
this section) made several claims that were too confident to carry into a PRD.
Recorded here so they aren't silently repeated later:

1. **"Company-level V1 needs no provider" is not an absolute.** A meaningful
   company-intelligence V1 can genuinely be self-built — from domains customers
   supply, company websites, permitted registries/open datasets, and Growixa's own
   normalization/scoring. But if Growixa needs to *discover* tens of thousands of new
   businesses by category/location at scale (rather than enrich domains it's already
   given), a licensed discovery/search source may still be necessary. Also: **Google
   Places is not a free, permanently-warehousable lead database** — Google imposes
   storage/caching and attribution restrictions on Places content, so it cannot be
   treated as a source to ingest and keep indefinitely without checking those terms.
2. **"Public website = no ToS/data-rights problem" is wrong as a blanket rule.**
   Publicly visible does not mean unrestricted for every commercial reuse. **The
   principle is a V1 requirement: no source is used until its rights are checked.**
   The full six-field Source Registry schema below (crawl/storage/retention/
   attribution/AI-processing/redistribution, per source) is captured for later —
   V1 likely has one or two sources, so a lightweight rights check per source is
   enough to start; the formal registry table is worth building once there are
   enough sources that memory stops being reliable.
3. **WHOIS is not a dependable enrichment source.** Modern domain registration data
   is frequently redacted, including contact details. It can occasionally supplement
   domain metadata but must not be relied on as a core lead source.
4. **"Email pattern generation + SMTP verification" needs to be scoped and relabeled
   more carefully.** Domain-level analysis is fine, and publicly published role
   addresses (`sales@company.com`, `info@company.com`) are genuinely useful,
   company-level evidence. But generating `john.smith@company.com` from a person's
   name is person-level data, not company-level — it does not belong in a
   company-only V1. SMTP probing is also not a reliable "verified" signal: catch-all
   domains, greylisting, anti-enumeration behavior, recipient-validation policies, and
   transient SMTP responses all produce false positives and false negatives. Evidence
   must therefore be classified, never collapsed into a single "verified" bucket —
   see the evidence-type list below.
5. **A licensed person-data provider does not transfer all liability away from
   Growixa.** The earlier framing's claim that a provider "carries that liability
   instead of you" is removed. A provider can supply contractual rights, provenance,
   and reduce collection risk, but Growixa and its customers can still carry
   obligations around processing and direct marketing — e.g. UK ICO guidance
   distinguishes corporate subscribers from sole traders/individual subscribers and
   requires transparency when personal business-contact data is obtained from public
   or third-party sources. This stays a live compliance question for V1.5
   (person intelligence), not something a vendor relationship resolves by itself.
6. **The AI synthesis layer is a subsystem, not "a prompt."** Crawled web content can
   contain malicious or irrelevant instructions and must never be fed directly into
   an agent with tool authority. The pipeline is **crawl → sanitize → structured
   extraction → evidence store → synthesis** — the model reasons over structured,
   sanitized evidence records, never over raw HTML.
7. **LinkedIn stays fully excluded — this was already correct and stands.**
   LinkedIn's terms explicitly prohibit automated crawling without express
   permission. This is a durable architectural rule, not a temporary limitation to
   revisit once a crawler library gets better.

### Evidence classification (replaces "verified" as a single bucket)

**Captured, not locked for V1.** The principle — never collapse evidence into one
"verified" flag — is a V1 requirement. This specific five-way taxonomy is a first
guess and will likely get reshaped once a real provider (e.g. Hunter.io) is actually
integrated and its own status values are seen; V1 could ship correctly with two or
three types (published, provider-verified, inferred) and grow this list from there
rather than committing to five now.

Every fact carries one of these, not a binary verified/unverified flag:

| Type | Meaning |
|---|---|
| `PUBLISHED` | Found as-is on a source the company itself controls (its own website, its own social profile) |
| `PROVIDER_VERIFIED` | Confirmed by a licensed provider under contract (e.g. Hunter.io's own verification) |
| `SMTP_SIGNAL` | An SMTP probe result — a signal, explicitly not proof, given catch-all/greylisting/anti-enumeration behavior |
| `PATTERN_INFERRED` | Generated from a detected naming pattern, not observed directly |
| `REGISTRY` | From a permitted public/open registry or dataset |

This list itself is a field-level provenance attribute (`verification_method` below),
not a separate system.

### Provenance as a first-class data model

`DEC-GRX-033` already requires field-level provenance; this makes the shape concrete
enough to design a migration against:

```
value
source_type          -- e.g. company_website, registry, provider, crawl
source_url / source_id
observed_at
confidence
verification_method  -- PUBLISHED | PROVIDER_VERIFIED | SMTP_SIGNAL | PATTERN_INFERRED | REGISTRY
allowed_usage         -- crawl / storage / retention / attribution / ai_processing / redistribution, per the Source Registry
expires_at
```

One design decision, several payoffs: explainability, deduplication, freshness,
compliance, source replacement, AI grounding, and future enterprise audits all sit on
top of this same table rather than needing their own bespoke mechanism later.

### Understand — corrected shape: scoring and narrative are separate systems

This is probably the most important architecture correction to the first draft. The
earlier version implied one AI step producing both a score and a narrative. Split
them:

```
Evidence
   ↓
Deterministic Signals
   ↓
Explainable Fit Score       (formula, visible, no LLM)
   ↓
AI Qualification Narrative  (LLM, reasons over the score's own evidence)
   ↓
Suggested Marketing Angle
```

The LLM explains the evidence and the already-computed score — it never secretly
manufactures the score. Example of what this looks like to a customer:

```
Fit Score: 82/100
+25 Industry match
+20 Company size match
+15 Target geography
+12 Website indicates B2B sales
+10 Active growth signals

AI Summary:
"Strong fit because this company operates in your target industry
and appears to be actively expanding..."
```

- **Input**: structured, sanitized evidence records (per the crawl → sanitize →
  structured extraction → evidence store → synthesis pipeline above) — never raw
  crawled HTML fed to the model directly.
- **Process**: deterministic scoring is a visible, configurable formula over
  evidence signals (industry match, size match, geography, detected sales/marketing
  posture, growth signals). The narrative is a separate LLM call constrained to
  explain that already-computed score, citing the specific evidence fields behind
  each claim (`company_size_source`, `website_text_source`, `industry_source`,
  `technology_signal_source`, etc.) — never asserting a conclusion the score didn't
  already support. This is what keeps Understand consistent with the "deterministic,
  inspectable scoring" rule `DEC-GRX-033` already adopted, and with PRD §24's
  evidence-classification convention.
- **Output / data model**: `fit_score`, `score_breakdown[]` (signal → weight),
  `qualification_summary`, `evidence_refs[]` (pointers into the provenance ledger),
  `generated_at`, `model_version`. Versioned so a re-run appends rather than silently
  overwriting the previous read.
- **Dependency**: none beyond Find's data model and the provenance ledger existing.
  Does not require `GRX-FEAT-021` to be built first.

### Act — proposed shape (unchanged in substance, dependency claim corrected)

- **Segment fit**: deterministic matching against a company's existing
  `GRX-FEAT-009` Segmentation criteria — not generative, no new AI surface.
- **Recommended angle + drafted sequence**: routes through the AI Assistant's
  existing capability-based generation (`GRX-AI-001..011` tasks `DONE` per
  `MASTER_TASK_TRACKER.md`; a "Generate with AI" affordance is already wired into
  the campaign composer) — Lead Intelligence does not get its own draft/approve
  mechanism; it reuses the one `DEC-GRX-006` already governs (human must approve
  before send, no exceptions in MVP). Note: `FEATURE_CATALOG.md`'s `GRX-FEAT-021` row
  still reads `NOT_STARTED` and `FEATURE_STATUS_MATRIX.md` has no audited row for it
  — those feature-ID-level docs are stale relative to the task tracker and the live
  product; treat the task-tracker/live-product evidence as authoritative here, and
  flag the feature-ID docs as needing reconciliation (separate, pre-existing
  documentation-hygiene gap, not something to silently paper over).
- **Promotion event**: approving the drafted sequence is proposed as the same act as
  the lead→contact promotion, with channel + jurisdiction eligibility (per
  `DEC-GRX-033`'s eligibility engine) checked at that exact moment rather than
  earlier, since eligibility can change between discovery and send.
- **What Act actually still needs to build**: not drafting infrastructure — that
  exists. Act's new work is the lead→draft wiring (pointing existing generation at a
  lead's evidence/narrative instead of a blank campaign) and the promotion/
  eligibility-check mechanism itself, which is new product behavior regardless of
  what's already built. Understand has no dependency on this at all and could ship
  first.

What this should look like to a customer — not a spreadsheet row, a recommendation
card:

```
ACME SOFTWARE
Strong Fit • 82/100

Why Growixa recommends this company
✓ Matches your SaaS ICP
✓ 20–50 employee growth-stage company
✓ Operates in your target region
✓ Website indicates outbound sales motion
✓ No marketing automation detected from available signals

Recommended angle
"Lead with reducing manual follow-up and campaign operations."

Best next action
Create a 3-email introduction sequence

[ View Evidence ]    [ Generate Outreach ]
```

Not: `John Smith · john@company.com · 82%`. The company-level, evidence-first
presentation is both the compliance-correct V1 shape (§below) and the more
marketable one — "explains why" outsells "found an email."

### The full loop this plugs into

**Corrected, 2026-08-28 — SEND and MEASURE already exist and already produce real
data; corrected again same day after independent review found the first correction
misattributed this to the wrong source document.** An earlier draft of this section
assumed Send/Measure were still roadmap items Learn would have to wait on. That was
wrong, but the fix must be grounded accurately: `docs/00-project-control/
FEATURE_STATUS_MATRIX.md` does **not** confirm `GRX-FEAT-013`/`015`/`016` as `DONE`
— it has no individually-audited row for any of them, and its own "Slices 3–6"
section explicitly flags itself stale and says "a full re-audit... is needed."
`GRX-FEAT-023`/`028` *is* individually audited there, and reads `PARTIAL`, not
`DONE` — a customer/platform overview dashboard shipped, but four role-adaptive
lenses and an "AI Next Best Actions" card are explicitly not built or scheduled.
`FEATURE_CATALOG.md` still lists `GRX-FEAT-013`/`015`/`016` as `NOT_STARTED`
(unreconciled stub). What actually supports "Send/Measure are live" is two other,
correctly-cited things: `MASTER_TASK_TRACKER.md` shows the underlying task IDs
(`GRX-EMAIL-001..012`, `GRX-SCHED-*`) reached `DONE`, and a live screenshot of
`growixa.iitdeveloper.com` during this brainstorm showed a real sent campaign with
real sent/delivered/opens/clicks/bounce tracking. Those are the citations to use —
not a "the matrix confirms it" claim the matrix itself does not support. The
feature-ID-level docs (`FEATURE_STATUS_MATRIX.md`, `FEATURE_CATALOG.md`) are simply
out of date relative to the tracker and the live product; that gap is a separate,
pre-existing documentation-hygiene issue, not something this document should paper
over by asserting the wrong source confirmed something it didn't. **LEARN's actual
blocker is still narrower than first thought: it only needs Find + Understand + Act
to exist**, so that an outcome can be tied back to a lead's fit-score breakdown and
narrative — the tracking infrastructure those outcomes flow through is not
something to wait on building, only something to link up to once a lead is in the
pipeline. This still makes LEARN the last piece to build in this sequence, but for a
smaller reason than "the roadmap isn't ready" — it's simply downstream of the rest
of Lead Intelligence by construction.

Act's handoff is not a dead end. Drawn through to what already exists in the
product, plus one new piece:

```
DISCOVER → QUALIFY → GENERATE → APPROVE → SEND → MEASURE → LEARN
                                            ↑                  │
                                            └── improves qualification + messaging ──┘
```

- SEND is the existing, live Email Campaigns capability (`GRX-EMAIL-*` tasks `DONE`
  per `MASTER_TASK_TRACKER.md`; feature-ID row `GRX-FEAT-013` itself unaudited in
  `FEATURE_STATUS_MATRIX.md`) — Act hands off here, nothing new to build.
- MEASURE is existing, live delivery tracking (same task-level evidence) plus a
  `PARTIAL` analytics dashboard (`GRX-FEAT-023`/`028`, confirmed `PARTIAL` in
  `FEATURE_STATUS_MATRIX.md` — basic overview shipped, advanced lenses not built) —
  already capturing sent/delivered/opens/clicks/bounces for every campaign sent
  today. Not yet wired to *lead-level* data because no lead exists yet to link it
  to — that's the actual gap, not the tracking itself.
- LEARN is new and not documented anywhere else prior to this section: campaign
  outcomes (opens, replies, conversions) per lead feed back as a signal into the
  deterministic score's own weights and into what the narrative emphasizes for
  similar leads next. To stay consistent with "explainable, not opaque," Learn must
  adjust **visible weights in the score formula**, never retrain a hidden model
  silently — the score must remain auditable after it learns, not just before. Build
  order: once Find/Understand/Act ship and produce leads that flow into the
  already-live Send/Measure pipeline, Learn can start accumulating real signal
  immediately — there is no separate infrastructure-build phase for it to wait on.

### Recommended V1 — narrower than the first draft, and person-intelligence deferred

```
User provides: industry / location / domain / business criteria
        ↓
Growixa discovers permitted COMPANY data
        ↓
Website intelligence
        ↓
Structured company profile
        ↓
Evidence + provenance
        ↓
Explainable ICP score
        ↓
AI qualification summary
        ↓
Recommended outreach angle
        ↓
Generate campaign draft
        ↓
Human approves
```

Person intelligence (named decision-maker, work email, mobile) is added later as a
licensed-provider adapter behind `LeadEnrichmentProvider` — consistent with
`DEC-GRX-033`'s existing V1 (company) / V1.5 (person) staging, not a change to it.
This keeps Growixa positioned as the intelligence-and-action layer on top of
commodity data providers, rather than competing head-on with Apollo/Hunter as a raw
data source from day one.

### Build sequencing

**Corrected, 2026-08-28** — the AI Assistant tasks (`GRX-AI-001..011`) are `DONE`
per `MASTER_TASK_TRACKER.md`, and are live: capability-based generation with a
"Generate with AI" affordance already wired into the campaign form (click-to-insert,
gated `ai.view`/`ai.manage`). `GRX-FEAT-021`'s own row in `FEATURE_CATALOG.md`/
`FEATURE_STATUS_MATRIX.md` has not been reconciled to this and still reads
`NOT_STARTED`/unaudited — treat the task tracker and the live product as
authoritative here, not the stale feature-ID row. So Act's dependency on AI drafting
exists today too, same as Send/Measure — Act's own new work is the segment-fit/
recommended-angle logic and wiring that generation capability to a lead rather than
a blank campaign, not waiting on drafting infrastructure to be built first.

Find (company-level, per `DEC-GRX-033` and the corrections above) → Understand
(deterministic score first, narrative second — both are a thin build once Find's
data model and provenance ledger exist) → Act (reuses the already-live AI
generation + campaign infrastructure — its new work is the lead-to-draft wiring and
the promotion/eligibility check, not new drafting infrastructure) → Learn (starts
accumulating real signal as soon as Find/Understand/Act produce leads, since
Send/Measure are already live and tracking).

### What would still need to happen before any of this is built

- `DEC-GRX-033` itself moves from `PROPOSED` to `APPROVED` (unchanged precondition).
- The Source Registry's per-source rights profile (crawl/storage/retention/
  attribution/AI-processing/redistribution) is a hard precondition for the *first*
  adapter, not an enhancement added later.
- The evidence-classification types above get written into acceptance criteria when
  `DEC-GRX-033`'s "required controls converted into acceptance criteria" precondition
  is worked.
- Act's "approval of a sequence = promotion + eligibility check" mechanism needs its
  own explicit confirmation, since it is new product behavior that `DEC-GRX-006` did
  not originally anticipate — compatible with that rule's intent, but the specific
  mechanism should be confirmed rather than assumed.
- Learn's "adjust visible weights, never retrain silently" constraint should be
  written down as a rule before any Learn work starts, not decided ad hoc once
  outcome data exists.

## Competitive positioning (research pass, 2026-08-28)

Recorded from a web research pass done to ground this brainstorm in the actual
market rather than assumption, so the selling points below aren't re-litigated from
scratch once building starts. Idea capture only, same status as the rest of this
document — informs positioning if/when `DEC-GRX-033` is approved, is not itself a
decision.

### Landscape as researched, August 2026

| Player | Core value prop | Key gap |
|---|---|---|
| Apollo.io | All-in-one contact DB (230M+) + sequencing + dialer | US-centric, thin/stale EU data; credit system makes real cost opaque |
| Hunter.io | Domain-search email finder + verifier | Shallow — finder/verifier only, no fit-scoring or intelligence layer |
| Clearbit / HubSpot Breeze Intelligence | Firmographic enrichment + visitor ID inside HubSpot | No longer standalone — locked behind HubSpot Pro (~$100+/mo) |
| ZoomInfo | Enterprise contact DB, "95% accuracy" claim | Actual email accuracy 75–85%; opaque pricing ($15K→$30K+, steep renewal hikes) |
| Lusha | Chrome-extension contact reveal, strong US mobile data | Weak email hit-rate (~31%); thin company-level intelligence |
| Clay.com | Spreadsheet UI + multi-provider waterfall + AI research agent + workflow automation | Steep 2–6 week learning curve (top G2 complaint); no proprietary data; opaque credit burn; needs a dedicated RevOps engineer to run — **closest functional analog to Find→Understand→Act** |
| Artisan / 11x ("AI SDR") | Fully autonomous AI rep — finds, writes, sends | Overstated autonomy (11x caught listing fake customers, CEO ousted); agentic-volume sending drops sender reputation ~38pts/90 days, spam-flag rate 8% vs 3% human; ~$24M in 2025–26 AI-outreach-claims settlements industry-wide |
| Revspot.ai | India-focused B2C lead gen + voice AI + WhatsApp, human handoff | Different category (B2C/voice-led), small scale (~50 clients) — not a real analog beyond the qualify-then-handoff pattern |

Sources: [Apollo pricing](https://www.landbase.com/blog/apollo-pricing), [Hunter.io pricing](https://www.rb2b.com/learn/hunter-io-pricing), [Clearbit/Breeze pricing](https://www.cognism.com/blog/clearbit-pricing), [ZoomInfo review](https://blog.gojiberry.ai/blog/zoominfo-review), [Lusha pricing](https://salesintel.io/blog/lusha-pricing/), [Clay pricing](https://www.landbase.com/blog/clay-pricing), [Clay weaknesses](https://www.cleanlist.ai/blog/clay-data-enrichment-review), [Artisan controversy](https://quasa.io/media/artisan-ai-the-most-controversial-ai-sdr-in-tech-from-provocative-billboards-to-linkedin-bans), [11x investigation](https://techcrunch.com/2025/03/24/a16z-and-benchmark-backed-11x-has-been-claiming-customers-it-doesnt-have), [AI SDR deliverability data](https://www.digitalapplied.com/blog/ai-sdr-real-performance-100k-email-analysis-2026), [Revspot](https://pulse2.com/revspot-raises-4-8-million-series-a-to-scale-ai-native-qualified-pipeline-generation-platform/). Verified 2026-08-28; re-check before using in external marketing copy, this category moves fast.

### Ranked selling points (most defensible first)

1. **"No autonomous sending, ever" as a deliverability moat, not a limitation.** The
   AI-SDR category's defining 2026 failure mode is agentic-volume sending destroying
   sender reputation and inviting legal exposure. `DEC-GRX-006`'s human-approval gate
   is a trust argument competitors chasing "autonomous" structurally cannot make.
2. **Explainable, deterministic fit-score vs. every competitor's black box.**
   ZoomInfo's accuracy claims don't hold up under scrutiny; no competitor above shows
   its scoring math. The Evidence → Deterministic Signals → Explainable Fit Score →
   AI Narrative split (already adopted above) is a real procurement/compliance
   selling point nobody else offers.
3. **Company-only, no LinkedIn/person scraping — a legal-risk argument, not just
   ethics.** Lusha/Apollo/ZoomInfo's value depends on person-level data with
   contested provenance (LinkedIn ToS, GDPR person-data risk). Sellable into
   risk-averse legal/procurement teams the others can't touch cleanly.
4. **Native Find→Understand→Act→Contacts→Campaigns, no stitching.** Clay's biggest
   weakness is being a powerful but disconnected layer needing a dedicated GTM
   engineer to wire into a real CRM/sending stack. Growixa already owns Contacts,
   Campaigns, delivery tracking, and AI generation (all `DONE` per
   `FEATURE_STATUS_MATRIX.md`) — "one product, zero integration tax" lands directly
   against Clay's steepest cost.
5. **Field-level provenance + per-source rights checking as a sellable audit trail.**
   None of the six data vendors researched surface this to end users. Answers "where
   did this come from, were we allowed to get it" out of the box.
6. **Simplicity vs. Clay's 2–6 week ramp.** If Growixa's UX targets marketers rather
   than GTM engineers, "usable on day one" is real differentiation against the
   closest functional analog.

### Honest gaps — and which ones must NOT be closed

Two of the four gaps found are the direct cost of the selling points above, not
oversights to fix. Closing them would erase the differentiation they came from:

- **Raw data breadth (Apollo's 230M+ contacts, ZoomInfo, Clay's waterfall).** The
  only way to close this is person-level scraping or buying into the same
  contested-provenance data-broker game the incumbents play — exactly what selling
  point #3 depends on *not* doing. **Do not chase this.** It is a fight Growixa
  cannot win on data volume and should not want to win by compromising the
  provenance story.
- **Speed to first send.** The human-approval gate is what makes selling point #1
  credible. Weakening it to compete on speed is the same trade that put Artisan and
  11x in TechCrunch and cost the category ~$24M in settlements. **Do not close this
  gap.** Improve review-UX speed (e.g. per-sequence rather than per-message
  approval, already the direction Act takes) instead of removing the gate.
- **Claygent-style open-ended AI research.** Worth partially closing *if* kept
  architecturally and visually separate from the core score/narrative — e.g. an
  "Exploratory research (unverified)" tool distinct from "Fit Score
  (evidence-backed)." Adds power-user value without touching the explainability
  promise, as long as the two outputs never blend into one number. Not urgent for
  V1.
- **Ecosystem maturity** (integrations, playbooks, community). Not fillable by
  design work — it accrues from real usage over time. Nothing to build now.

**The strategic point to preserve:** Growixa's pitch is not "as good as Apollo/Clay,
but also trustworthy." It's "the trustworthy, explainable, already-integrated
option, for buyers wary of the other kind" — and that pitch only holds if the
constraints (human approval, company-only, explainable scoring) stay constraints.
Filling the gaps that come from them doesn't strengthen the product; it turns it
into a slower, later version of Clay or Apollo instead of a real alternative to
both. Revisit this section, not just the gap list alone, before any future
"let's also do X" conversation about closing these specific gaps.
