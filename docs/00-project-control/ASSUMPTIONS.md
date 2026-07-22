# Assumptions

- Document ID: DOC-ASSUMPTIONS
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [OPEN_QUESTIONS](OPEN_QUESTIONS.md), [DECISIONS](DECISIONS.md)

Assumptions made in the absence of an explicit decision. Each must be revisited before the
area it touches is built, and converted into a logged decision (see [DECISIONS.md](DECISIONS.md))
once confirmed.

| ID | Assumption | Area | Risk if wrong | Status |
|---|---|---|---|---|
| ASM-001 | "Company" in this document always means the single internal Growixa customer installation, never an end customer of that company. | Product | Terminology confusion bleeding into schema/UI | ACTIVE |
| ASM-002 | Internal users are employees/contractors of the one company running Growixa, not external customers. | Product | Wrong access model | ACTIVE |
| ASM-003 | "One production email provider adapter" for MVP means one real provider is fully implemented; other providers may have adapter interfaces but no working credentials/tests. | Architecture | Scope creep into multi-provider work | ACTIVE |
| ASM-004 | The first social platform will be chosen based on OAuth/API maturity and publishing-API availability, not necessarily audience size. | Integrations | Wrong platform selected, rework | ACTIVE — see OQ-003 |
| ASM-005 | Object storage will run against an S3-compatible target in both local dev (e.g. MinIO) and production, not a filesystem-only mode. | DevOps | Divergent local/prod behavior | ACTIVE |
| ASM-006 | AI provider access will be via API key(s) configured per environment, not a self-hosted model, for MVP. | AI | Cost/latency assumptions wrong | ACTIVE — see OQ-004 |
| ASM-007 | "Single-tenant" means one deployed instance serves one company; it does not preclude the company having many contacts/campaigns — those are normal business data, not tenants. | Architecture | Conflating scale limits with tenancy | ACTIVE |
| ASM-008 | No payment/billing provider needs to be integrated for MVP since Growixa MVP is not sold as a subscription yet (usage metering is tracked internally only). | Business | Billing work built prematurely | ACTIVE — see OQ-005 |
| ASM-009 | Users are provisioned by an admin (invite-based), not self-service signup, since this is single-tenant/internal. | Product | Wrong onboarding flow built | ACTIVE |
| ASM-010 | English-only UI and content for MVP. | Product | Localization work built prematurely | ACTIVE |
| ASM-011 | The V1.5/V2/V3 staging of SEO/AEO/GEO capabilities in [FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md) is a reasonable dependency-ordered default, not yet explicitly confirmed release-by-release by the product owner. | Roadmap | Releases resequenced once real dependencies/priorities are clearer | ACTIVE — see OQ-011 |

Assumptions are not permission to guess on high-impact, hard-to-reverse choices (see
[DECISIONS.md](DECISIONS.md) §"Decision gates" list) — those must be logged as `PROPOSED`
decisions and confirmed, not silently assumed.
