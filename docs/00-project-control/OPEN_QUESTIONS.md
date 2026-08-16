# Open Questions

- Document ID: DOC-OPEN-QUESTIONS
- Status: ACTIVE
- Version: 1.1
- Last updated: 2026-08-15
- Owner: Coding agent
- Related documents: [DECISIONS](DECISIONS.md), [ASSUMPTIONS](ASSUMPTIONS.md), [BLOCKERS](BLOCKERS.md)

Questions that block a specific decision gate (see [DECISIONS.md](DECISIONS.md) §"Decision
gates"). A task that depends on an unresolved question here must be marked `BLOCKED`, not
guessed.

| ID | Question | Blocks | Status |
|---|---|---|---|
| OQ-001 | ~~Which authentication approach: self-hosted email/password + sessions, or an external auth provider (e.g. Auth0/Clerk)?~~ | Slice 1 (Foundation) | **RESOLVED** — [DEC-GRX-014](DECISIONS.md): application-managed FastAPI auth, PostgreSQL-backed, adapter boundary for future OIDC/SSO |
| OQ-002 | ~~Which email provider is the one production adapter for MVP (e.g. SES, Postmark, SendGrid, Mailgun)?~~ | Slice 3 (First Email Campaign) | **RESOLVED** — [DEC-GRX-015](DECISIONS.md): Postmark, integrated via its SMTP relay endpoint |
| OQ-003 | ~~Which single social platform is the first integration (LinkedIn, Facebook Pages, Instagram Business, X)?~~ | Slice 5 (Social Publishing) | **RESOLVED** — [DEC-GRX-023](DECISIONS.md): Instagram Business, via the Meta Graph API |
| OQ-004 | ~~Which AI provider(s) and default model(s) for the content assistant?~~ | Slice 6 (AI Assistant) | **RESOLVED** — [DEC-GRX-026](DECISIONS.md): multi-provider adapter (OpenAI, Azure OpenAI, Anthropic, Ollama), platform-admin-configured default + per-account bring-your-own override |
| OQ-005 | ~~Which S3-compatible object storage provider/target for local dev vs. production?~~ | Slice 5 (media); not required for Slice 1 (company profile fields don't require file upload — see SPRINT_01_FOUNDATION.md) | **RESOLVED** — [DEC-GRX-024](DECISIONS.md): Supabase Storage |
| OQ-006 | Production cloud/hosting target? | Production deployment (not Slice 1 local dev) | OPEN — does not block Slice 1 |
| OQ-007 | ~~Is there a billing/payment provider requirement for MVP, or is usage metering internal-only for now (per ASM-008)?~~ | Usage metering scope beyond internal tracking | **RESOLVED** — [DEC-GRX-029](DECISIONS.md): yes, billing is required; vendor is Razorpay (not Stripe), dual-currency (INR + international). Exact plan tiers/pricing/charge model still open — see OQ-013 |
| OQ-008 | Default data-retention periods for contacts, campaign history, AI generation history, audit logs? | Data model, retention policy | OPEN |
| OQ-009 | Email editor: build a minimal rich-text editor, or adopt an existing open-source email-builder library? | Email template feature | OPEN |
| OQ-010 | Social scheduling policy: fixed queue times, user-chosen times only, or AI-suggested times (estimate only, per PRD §19)? | Social scheduling feature | OPEN |
| OQ-011 | Target dependency-aware order for future-release SEO/AEO/GEO work relative to V1.1/V1.2 marketing features — confirm V1.5+ staging in [ROADMAP.md](../01-product/ROADMAP.md) is acceptable. | Long-term roadmap sequencing | OPEN |
| OQ-012 | Scope of the `automation_workflows` module beyond scheduled campaigns/posts (visual workflow builder? trigger-based automations?) | Post-MVP workflow features | OPEN — does not block Slice 1; `automation_workflows` is explicitly out of MVP per FEATURE_CATALOG.md |
| OQ-013 | ~~Given [DEC-GRX-029](DECISIONS.md): which Razorpay billing primitive, do top-up credits expire, is audit retention tiered, is Enterprise self-serve or contact-sales, is platform-admin override/coupon scope included?~~ | `GRX-SAAS-004` (Billing), `GRX-SAAS-006`, `GRX-SAAS-009`, `GRX-SAAS-012` (new) | **RESOLVED (architecture/model)** — [DEC-GRX-030](DECISIONS.md): Razorpay Subscriptions API, non-expiring credits, permanent audit logs (export/API-access tiering instead), contact-sales Enterprise, admin-override UI + coupon engine both in scope. **Still open**: the actual plan quota numbers and Starter/Pro prices in `subscription_plans_matrix.csv` remain a working draft, not yet confirmed final — `GRX-SAAS-004` stays `BLOCKED` on that specific point until the product owner confirms |

## Subdomain routing (`GRX-FEAT-029` / `DEC-GRX-031`)

These three IDs are already cited as blockers by [ROADMAP.md](../01-product/ROADMAP.md),
[FEATURE_CATALOG.md](../02-features/FEATURE_CATALOG.md), and `DEC-GRX-031`, but were never
recorded here. Logged 2026-08-15 during product intake triage so the references resolve.

| ID | Question | Blocks | Status |
|---|---|---|---|
| OQ-SUB-001 | Is the production domain actually `growixa.com`, or something else? Determines DNS records and the `NEXT_PUBLIC_*_URL` values. | `GRX-FEAT-029` (subdomain routing) | OPEN |
| OQ-SUB-002 | Hosting platform for the three domain aliases. | `GRX-FEAT-029` | **EFFECTIVELY ANSWERED** per `DEC-GRX-031` — Netlify (not Render), same deployed stack as `GRX-SAAS-013`. Overlaps [OQ-006](#). Remaining work is documentation, not a decision |
| OQ-SUB-003 | Does `app.<domain>/` show a real overview page after login, or redirect straight to `/campaigns`? | `GRX-FEAT-029` | **LIKELY ANSWERED IN PRACTICE** — `GRX-SAAS-014` shipped a real customer overview dashboard at `/dashboard`; needs product-owner confirmation that this is the intended `app.*` landing page before `GRX-FEAT-029` moves to `READY` |

## Product intake — raised 2026-08-15 (need_review_docs triage)

Questions arising from triaging the local `need_review_docs/` intake folder against the
tracked product docs. Each is a product/architecture call the product owner has not made;
per [AGENT_EXECUTION_RULES.md §Scope discipline](../12-development/AGENT_EXECUTION_RULES.md#scope-discipline-specific-to-this-repository)
none of the features below may be scheduled, scaffolded, or entered into
[MASTER_TASK_TRACKER.md](MASTER_TASK_TRACKER.md) until answered.

| ID | Question | Blocks | Status |
|---|---|---|---|
| OQ-014 | Are the investor/client-facing master guide and decks (`GROWIXA_PRODUCT_MASTER_GUIDE.md`, `GROWIXA_INVESTOR_AND_EXECUTIVE_DECK.pdf`) a statement of *committed* scope, or aspirational positioning? They present Email Warmup, Unified Inbox, Telegram, an 18-tool MCP server, and 4 role-adaptive dashboards as product capabilities; none of those are in the PRD, catalog, or roadmap today. If committed, PRD/ROADMAP must be updated to match; if aspirational, the decks need a forward-looking-statement caveat. | PRD/ROADMAP accuracy; any external circulation of the decks | OPEN |
| OQ-015 | Growixa MCP Server: may an external client holding a scoped API key schedule or send a campaign **without** in-app human approval (`OQ-MCP-003` in the source plan)? This directly conflicts with locked rules `GRX-AI-002`/`GRX-AI-003` (PRD §23) and [DEC-GRX-006](DECISIONS.md) — AI output may never send/publish, a human must approve first. Also open: implementation stack, and whether the server is Pro+ only. | `GRX-FEAT-035` (MCP Server) — cannot be specified, let alone scheduled, until resolved | OPEN |
| OQ-016 | The dashboards plan's "AI Next Best Actions" engine overlaps the *continuous-improvement / next-best-action engine* that [ROADMAP.md](../01-product/ROADMAP.md) stages at **V3**, and sits close to [DEC-GRX-012](DECISIONS.md) (broad autonomous marketing agents deferred). Is the dashboard card a narrow, deterministic SQL-derived suggestion widget (acceptable earlier), or the V3 engine (must stay deferred)? | `GRX-FEAT-036` (role-adaptive dashboards); V3 scope integrity | OPEN |
| OQ-017 | Suppression storage & scope: the DNC plan specifies SHA-256 *hashed* email storage and a platform-wide **global** cross-account suppression list. Shipped reality (`GRX-CONTACT-005/009`, `GRX-SAAS-015`) stores plaintext addresses in `suppression_entries`, scoped per account only. Do we (a) migrate to hashed storage, (b) add a global/cross-account list, (c) neither? (b) has real abuse-list and privacy implications across customer accounts. Related source questions: `OQ-DNC-002`, `OQ-DNC-004` (may customers re-subscribe an unsubscribed contact — legally risky). | Any further suppression work; GDPR posture (PRD §27/§28) | OPEN |
| OQ-018 | Confirm (or reject) the *proposed* release targets for the four unscheduled intake features: Email Warmup → 1.1, Unified Inbox → 1.2, Telegram → 1.2, MCP Server → 1.1/1.2. These targets were proposed in the intake docs, never decided. Nothing may be scheduled until confirmed. | `GRX-FEAT-032`–`036`; ROADMAP 1.1/1.2 contents | OPEN |
| OQ-020 | Does Postmark's acceptable-use policy permit sending to externally-sourced (scraped/purchased) lists on Growixa's shared account, and under what conditions? Most ESPs prohibit it outright. If it does not, `DEC-GRX-033` point 6 cannot be satisfied on the current sending path (`DEC-GRX-015`) and the capability needs a separate sending arrangement — or cannot ship at all. **This is a factual question to put to the vendor, not an internal judgement call**, and it should be asked before `DEC-GRX-033` is approved rather than after the first complaint. See `THREAT_MODEL.md` T83 — the blast radius is every other customer on the shared sending path. | `DEC-GRX-033`; any external contact acquisition work | OPEN |
| OQ-019 | Analytics store for advanced campaign reporting: PostgreSQL (time-partitioned `campaign_events`) or a dedicated ClickHouse/TimescaleDB? (`OQ-RPT-001` in the source plan.) A core-architecture call per [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md) — must not be guessed. Related: raw-event retention, which is [OQ-008](#), not a separate question. | Release 1.1 advanced analytics (heatmaps, trends, cohorts, comparisons) | OPEN |

When a question is resolved, move it into [DECISIONS.md](DECISIONS.md) as a logged decision
and mark it `RESOLVED` here with a link to the decision ID.
