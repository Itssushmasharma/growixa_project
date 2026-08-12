# Sprint 07 — AI Assistant

- Document ID: DOC-SPRINT-07
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-12
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-026/027/028](../00-project-control/DECISIONS.md)

This is the 7th sprint *file* chronologically, and it implements product **Slice 6** (AI
Assistant) — the last unbuilt slice of the original 6-slice MVP roadmap. Its job is
assistive, human-reviewed AI content generation (subject lines, body copy, social
captions, rewriting, hashtag/posting-time suggestions), available to any Growixa customer
account either through a platform-admin-configured default provider or the account's own
"bring your own model" credentials.

## Included

Per [MVP_SCOPE.md §E](../01-product/MVP_SCOPE.md):

1. Multi-provider AI adapter: OpenAI, Azure OpenAI, Anthropic, Ollama (self-hosted),
   selected via configuration per [DEC-GRX-005](../00-project-control/DECISIONS.md)/
   [DEC-GRX-026](../00-project-control/DECISIONS.md)
2. Platform-admin-configured default AI provider (new: the first DB-backed,
   admin-editable platform setting in this codebase, editable without a redeploy)
3. Per-account "bring your own model" override, reusing the existing
   `integrations.manage` permission for connection management
4. Six generation capabilities: subject lines, email body copy, social captions,
   rewrite (tone/shorten/expand), hashtag suggestions, posting-time suggestions
   (estimate only)
5. Brand voice applied automatically from the existing `brand_profiles.brand_voice`
6. Generation history with token usage and estimated cost logged for every call
   (`GRX-AI-006`), plus a `usage_records` write per call — the platform admin's existing
   usage view finally has a real writer
7. Frontend "Generate with AI" affordance inside the existing campaign and social post
   composers (click-to-insert only — output is never auto-applied), a generation-history
   page, an account AI-provider connection card, and a platform-admin AI-config page,
   gated by the new `ai.manage` / `ai.view` permissions

Full data model: [DATA_MODEL.md §Slice 6 entities](../05-data/DATA_MODEL.md#slice-6-entities-full-detail),
[DATABASE_SCHEMA.md §Slice 6](../05-data/DATABASE_SCHEMA.md#slice-6-ai-assistant-tables),
[ERD.md §Slice 6 additions](../05-data/ERD.md#slice-6-ai-assistant-additions). RBAC:
[RBAC.md §Slice 6](../08-security/RBAC.md#slice-6-permission-codes). Threat model:
[THREAT_MODEL.md §Slice 6](../08-security/THREAT_MODEL.md#slice-6-ai-assistant-scope).

Full task breakdown with dependencies: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-AI-*`).

## Explicitly excluded from Sprint 7

- **Autonomous multi-step agents and LangGraph adoption** — per
  [DEC-GRX-012](../00-project-control/DECISIONS.md), MVP AI is assistive single-shot
  generate/rewrite/suggest, not autonomous. Every capability is a synchronous,
  in-request call (no worker/queue involvement), structured with a clean
  input/provider/output contract specifically so a future multi-agent slice can wrap
  these same capabilities as tools/graph nodes without a rewrite — but that adoption is
  not this sprint's job.
- **A customer-facing prompt-template editor** — per
  [DEC-GRX-028](../00-project-control/DECISIONS.md), prompts are code-defined in
  `ai/prompts/templates.py`, referenced by a plain `prompt_template_key` string. A
  versioned, editable template table is additive later if a real need for it appears.
- **Proactive cost-cap or rate-limit enforcement** — this sprint gives the platform
  admin visibility (`ai_generations` token/cost detail + `usage_records`), not
  enforcement. Same "recording, not enforcing" posture Slice 3 established for
  `usage_records` originally.
- **Per-generation model/temperature picker in the UI** — the connection's configured
  `default_model` is what's used; no inference-parameter UI beyond what
  `MVP_SCOPE.md §E` actually asks for.
- **Platform-admin oversight of individual accounts' AI generation content** — the
  platform admin configures the platform *default provider*, not a per-account content
  review surface; that would be a future capability comparable to `GRX-SAAS-007`, not
  in scope here.
- **A multi-Page/multi-provider picker per account** — an account brings *one* BYO
  connection at a time (`ux_ai_provider_connections_active_per_account`), matching
  Slice 5's single-active-connection precedent, not per-provider multiplicity like
  email's.

If implementing a Sprint 7 task seems to require touching any of the above, stop and flag
it — it means the task is scoped wrong, not that a shortcut through excluded territory is
warranted.

## Sprint 7 acceptance criteria

- A platform admin (`platform.ai.manage`) can configure a default AI provider (any of
  the four) and model; this becomes usable by every customer account with no
  configuration of their own.
- A customer account holder with `integrations.manage` can connect their own AI
  provider credentials (any of the four), which then takes precedence over the platform
  default for that account's generation calls.
- A user with `ai.manage` can generate a subject line, body copy, social caption, a
  rewrite (tone/shorten/expand) of existing text, hashtag suggestions, and a
  posting-time suggestion — each call is logged in `ai_generations` with token
  usage/estimated cost, and a `usage_records` row is written alongside it.
- Generated content is never sent or published automatically — it only appears as a
  suggestion the user must explicitly click to insert into a campaign/social post
  composer field (negative test: no code path calls `campaigns.send`/`social.publish`
  from anywhere in the `ai` module).
- A user with `ai.view` only can see generation history but gets 403 attempting to
  generate anything (negative test).
- A user with neither `ai.manage` nor `ai.view`, and a user without
  `integrations.manage` attempting to manage an AI provider connection, both get 403
  (negative tests).
- Attempting to save an Azure OpenAI/Ollama connection with a `base_url` pointing at a
  private/loopback/link-local IP or the `169.254.169.254` metadata address is rejected
  at save time; a connection whose hostname resolves safely at save time but not at
  call time is rejected at call time too (negative tests, per
  [DEC-GRX-027](../00-project-control/DECISIONS.md)).
- A cross-account attempt to read or act on another account's `ai_generations`/
  `ai_provider_connections` row 404s, added to `test_cross_tenant_isolation.py`.
- Brand voice, when configured on `brand_profiles`, is reflected in generated content's
  prompt construction (verified via the constructed prompt in a test, not by asserting
  on live model output).
- Automated backend and frontend tests pass; CI passes.

## Definition of done for this sprint

[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) applies to every
task in this sprint individually — the sprint itself is done only when every task in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) tagged `GRX-AI-*`
is `DONE`, not merely attempted. Per
[DEC-GRX-011](../00-project-control/DECISIONS.md), no task is marked `DONE` on
mocked-provider evidence — a real generation call against at least one real, live
provider (whichever the product owner can supply credentials for) is required before the
provider-adapter and capability-generation tasks are marked `DONE`; if no live
credentials are available during a given work session, that is explicitly flagged as an
evidence gap rather than silently assumed, same convention Slice 5 used for its
Instagram/Supabase credentials.
