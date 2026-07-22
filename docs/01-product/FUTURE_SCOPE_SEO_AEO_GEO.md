# Future Scope: SEO, AEO, GEO & Website Intelligence

- Document ID: DOC-FUTURE-SCOPE-SEO
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Product owner (Ravi) via coding agent
- Related documents: [PRODUCT_VISION](PRODUCT_VISION.md), [ROADMAP](ROADMAP.md), [DECISIONS §DEC-GRX-001](../00-project-control/DECISIONS.md), source doc: [`docs/archive/source-prd-seo-aeo-geo-website-intelligence/prd/FULL_PRD.md`](../archive/source-prd-seo-aeo-geo-website-intelligence/prd/FULL_PRD.md)

## Purpose

This document extracts the SEO, AEO, GEO, website-crawler, and integration requirements
from the original discovery PRD and maps each capability group to a future Growixa release
ID and staging. The original document had no formal requirement-ID scheme (it used
narrative section numbers, referenced below as `Src §n`); this mapping assigns new
`GRX-FR-*` / `GRX-INT-*` / `GRX-AGENT-*` IDs consistent with the ID scheme defined in
[PRD.md](PRD.md).

None of these capabilities are in the MVP. None may enter `MASTER_TASK_TRACKER.md` or any
`docs/14-sprints/` sprint file until the email/social MVP (Slices 1–6) is stable in
production, per [DEC-GRX-001](../00-project-control/DECISIONS.md) and
[DEC-GRX-012](../00-project-control/DECISIONS.md).

## Release staging rationale

Staging follows dependency order, not just capability grouping: you cannot generate SEO
fixes before you can crawl and understand a website, and you cannot run a coordinated
multi-agent growth loop before the individual specialist capabilities exist and are
trustworthy on their own.

- **V1.5 — Website Intelligence Foundation (read-only):** crawling, technical/on-page audit,
  metadata recommendations, baseline Search Console metrics. Report/export only — nothing
  is auto-applied to a website yet.
- **V2 — SEO Execution + Content Optimization + AEO:** WordPress/GitHub write integrations,
  approved technical fixes, schema/internal-link generation, content refresh & briefs, AEO
  specialist, basic competitor gap view, SEO/AEO reporting.
- **V3 — GEO + Full Growth Agent System:** GEO specialist, authority/outreach manager,
  competitive intelligence agent, sampled AI-visibility observation, the continuous
  improvement / next-best-action engine, and full multi-agent orchestration (Growth
  Strategist coordinating all specialists).

## Mapping

| New ID | Capability | Source | Target release | Notes |
|---|---|---|---|---|
| GRX-FR-WEB-001 | Website crawling (HTTP + browser rendering), robots.txt handling | Src §7.4 | V1.5 | Foundation for all later SEO/AEO/GEO work |
| GRX-FR-WEB-002 | Page inventory, duplicates, thin/orphan pages, broken links, redirect chains | Src §7.4 | V1.5 | |
| GRX-FR-WEB-003 | Crawl snapshots for change detection over time | Src §7.4 | V1.5 | |
| GRX-FR-SEO-001 | Technical/on-page SEO finding generation with evidence, severity, priority | Src §7.5 | V1.5 (detect) / V2 (act) | Detection in V1.5; generated fixes in V2 |
| GRX-FR-SEO-002 | Priority scoring (impact/confidence/effort/risk), configurable goal weighting | Src §7.5 | V1.5 | |
| GRX-FR-SEO-003 | Metadata, headings, FAQ, structured data (JSON-LD), internal-link generation | Src §7.6, §7.8 | V2 | Requires human approval per DEC-GRX-006 pattern |
| GRX-FR-SEO-004 | Redirect maps, robots/sitemap change proposals | Src §7.6 | V2 | High-risk — approval mandatory (mirrors PRD §10.2 rollback rules) |
| GRX-INT-WP-001 | WordPress CMS draft creation for approved content/metadata changes | Src §7.8, §10 | V2 | First CMS integration |
| GRX-INT-GH-001 | GitHub branch/PR creation for approved code changes | Src §7.8, §10 | V2 | First repository integration |
| GRX-FR-CONTENT-OPT-001 | Topic clusters, content calendar, briefs/drafts, refresh candidates | Src §7.7 | V2 | Builds on MVP's AI content assistant patterns |
| GRX-FR-CONTENT-OPT-002 | Duplication/cannibalization/low-value content detection | Src §7.7 | V2 | |
| GRX-AGENT-AEO-001 | AEO specialist: direct-answer sections, FAQs, comparison/answer-ready structure | Src §8 | V2 | First specialist agent beyond content assistant |
| GRX-AGENT-GEO-001 | GEO specialist: entity clarity, citation readiness, freshness, AI parseability | Src §8 | V3 | Depends on AEO patterns being proven first |
| GRX-FR-COMPETITIVE-001 | Competitor page/keyword/change tracking, gap view | Src §7.9, §8 | V2 (basic) / V3 (full agent) | |
| GRX-AGENT-COMPETITIVE-001 | Competitive Intelligence Agent (automated, continuous) | Src §8 | V3 | |
| GRX-FR-AUTH-001 | Legitimate authority/outreach opportunity discovery, outreach drafts (approval required) | Src §7.9 | V3 | Explicitly excludes spam/purchased links per Src §7.9 |
| GRX-AGENT-AUTHORITY-001 | Authority & Outreach Manager agent | Src §8 | V3 | |
| GRX-FR-GEO-VISIBILITY-001 | Sampled AI-answer visibility observation (query/engine/date/citation), clearly labeled as sampled | Src §7.10 | V3 | Must never be presented as universal visibility (Src §7.10, §17.3 of source) |
| GRX-INT-GSC-001 | Google Search Console integration (impressions, clicks, CTR, position) | Src §10 | V1.5 | Verified-data source, lowest integration risk |
| GRX-INT-GSC-002 | Bing Webmaster Tools, optional rank/SERP providers | Src §10 | V2+ | |
| GRX-FR-REPORT-SEO-001 | Executive/technical/AEO-GEO/competitor report views and exports | Src §7.11 | V2 | Reuses MVP reporting/export infrastructure |
| GRX-AGENT-STRATEGIST-001 | Growth Strategist agent coordinating all specialists into a prioritized roadmap | Src §8, §9 | V3 | Requires all specialist agents to exist first |
| GRX-FR-GROWTH-ENGINE-001 | Continuous improvement engine: next-best-action scheduler, experiment lifecycle (hypothesis → baseline → measure → decide) | Src §9 | V3 | The "closed-loop" capability from the original vision |
| GRX-FR-SEO-PUBLISH-001 | Publishing safety levels (suggest-only → draft → approval-publish → policy-based automation) for SEO/content changes | Src §10.1 | V2 (levels 0–2) / V3 (level 3) | Mirrors MVP's AI-approval pattern (DEC-GRX-006), applied to website changes |

## Explicitly not carried forward

The following from the source document are not part of Growixa's plan and are not staged
into any release: guaranteeing rankings/traffic/citations, mass low-quality content
generation, automated backlink purchasing, and any unsupervised production edit to a
customer's live codebase (matches PRD §4.2 non-goals in the source, and remains a non-goal
here).
