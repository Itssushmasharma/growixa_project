# Future Scope: Multi-Brand Profiles & Brand-Tiered Subscriptions

- Document ID: DOC-FUTURE-SCOPE-MULTI-BRAND
- Status: ACTIVE (idea capture only — not approved, not scheduled into any release)
- Version: 1.0
- Last updated: 2026-07-27
- Owner: Product owner (Ravi) via coding agent
- Related documents: [DECISIONS §DEC-GRX-002, §DEC-GRX-013](../00-project-control/DECISIONS.md), [MVP_SCOPE](MVP_SCOPE.md), [PRD](PRD.md), [DATABASE_SCHEMA §brand_profiles](../05-data/DATABASE_SCHEMA.md)

## Purpose

Captures an idea raised in conversation: letting one company account manage multiple
distinct Brand Profiles (e.g. an agency running several client brands, or one company with
sub-brands), with brand-scoped social accounts, AI voice, and content calendar, plus
brand-count limits tied to paid subscription tiers (a "Starter/Growth/Agency" style plan
structure with per-brand upgrade prompts).

This is idea capture, not a plan. No `GRX-*` task should be created for it, and it must not
enter `MASTER_TASK_TRACKER.md` or any `docs/14-sprints/` file, until the decisions in
[§If this is ever picked up](#if-this-is-ever-picked-up) are made explicitly.

## What's actually in the current docs vs. what was proposed

The idea arrived already framed as "this is already fully planned in your PRD and
architecture docs," citing `MODULE_BOUNDARIES.md` and `DATABASE_SCHEMA.md` directly. On
checking against this repo, that framing did not hold up:

- `DATABASE_SCHEMA.md`'s `brand_profiles` table, and the actual `brand/repositories.py`
  implementation shipped in `GRX-COMPANY-001`/`GRX-COMPANY-002`, are hard-wired **1:1**
  with `company_profile` (`get_brand_profile()` does `.limit(1)`, `upsert_brand_profile()`
  always updates the same row) — not "1 to N Brand Profiles" as described.
- `MODULE_BOUNDARIES.md` describes `brand` in a single table row ("Brand voice, brand
  assets, legal footer") — there is no brand-switcher, per-brand social-account binding,
  or subscription-tier brand-limit language anywhere in it.
- `PRD.md` and `MVP_SCOPE.md` contain no subscription-tier, billing, or brand-limit
  language at all.

This document is the first place this idea is actually captured in the project.

## Why this is a bigger change than it first looks

1. **Multi-brand data model.** `brand_profiles` would need to become a real 1:N
   relationship (name, logo, per-brand social-account bindings, per-brand AI voice applied
   at generation time), and every module that currently assumes "the one company"
   (contacts, campaigns, AI, templates, social) would need brand-scoping added.
2. **Subscription tiers require billing.** No billing/subscription system exists today.
   Per [DEC-GRX-013](../00-project-control/DECISIONS.md), multi-tenancy, customer-facing
   SaaS signup, and tenant billing are explicitly **deferred indefinitely** — not "later,"
   not currently roadmapped at all. A brand-tiered subscription model is a variant of
   exactly what that decision deferred.
3. **Business-model mismatch.** Per [DEC-GRX-002](../00-project-control/DECISIONS.md), the
   MVP's whole premise is one internal company account, not external paying customers. The
   proposed "customer" framing (self-service signup, plan enforcement, upgrade prompts)
   assumes a different business model than what Growixa is currently built as.

## If this is ever picked up

- Revisit [DEC-GRX-002](../00-project-control/DECISIONS.md) and
  [DEC-GRX-013](../00-project-control/DECISIONS.md) explicitly first — whether Growixa
  becomes externally sold with billing is a business-model decision, not a schema change,
  and deserves its own `DECISIONS.md` entry before any implementation starts.
- Data model: drop the implicit 1:1 constraint on `brand_profiles.company_id`; add `name`,
  `logo_url`, and social-account bindings scoped per brand (today the `social` module has
  no brand awareness at all).
- UX: a brand-switcher in the dashboard shell.
- RBAC: decide whether roles become brand-scoped or stay company-wide with brand as a data
  filter only.
- Billing: pick and integrate a subscription/billing provider — not started, no vendor
  chosen, no cost model defined.

## Explicitly not staged into any release

Not in the MVP (Slices 1–6), not in V1.5–V3 per [ROADMAP.md](ROADMAP.md).
