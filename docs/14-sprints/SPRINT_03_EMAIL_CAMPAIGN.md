# Sprint 03 — First Email Campaign

- Document ID: DOC-SPRINT-03
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-01
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-010](../00-project-control/DECISIONS.md), [DECISIONS §DEC-GRX-015](../00-project-control/DECISIONS.md)

Sprint 3 is Slice 3 (First Email Campaign) from
[DEC-GRX-010](../00-project-control/DECISIONS.md). Its job is to prove a company can
actually reach its audience by email: configure one provider connection, write a
template, draft a campaign against a segment/list/all contacts, send it for real through
Postmark, and see delivery/open/click/bounce/complaint results come back — nothing about
*scheduling* a future send exists yet, that's Slice 4.

## Included

Per [MVP_SCOPE.md §C](../01-product/MVP_SCOPE.md) (immediate-send subset only):

1. Email provider configuration — one Postmark connection via SMTP relay
   ([DEC-GRX-015](../00-project-control/DECISIONS.md)), credentials encrypted at rest
2. Sender identity (from-email, from-name, reply-to) with a verification-status field
   (verification itself is a manual, out-of-band step in Postmark's own dashboard)
3. Email templates with an insert-only version history
4. Campaign drafts: subject, HTML/text body, recipient targeting (segment, list, or all
   contacts), personalization variables (plain merge-tag substitution against contact
   fields)
5. Test send to a single address
6. Immediate send, queued through the worker (per
   [BACKGROUND_JOB_ARCHITECTURE.md](../04-architecture/BACKGROUND_JOB_ARCHITECTURE.md)),
   never inline in the HTTP request
7. Suppression/consent enforcement at send time — no address on `suppression_entries` or
   withdrawn consent ever receives a send, per
   [DEC-GRX-008](../00-project-control/DECISIONS.md)
8. Delivery/open/click/bounce/complaint tracking via a Postmark-specific, authenticated
   webhook receiver
9. Unsubscribe handling — a recipient unsubscribing both records an `unsubscribe_events`
   row and adds/updates a `suppression_entries` row
10. Campaign report / basic email analytics, computed live from delivery/event data
11. Frontend UI for all of the above, gated by the new `integrations.manage` /
    `campaigns.manage` / `campaigns.send` / `campaigns.view` permissions

Full data model: [DATA_MODEL.md §Slice 3 entities](../05-data/DATA_MODEL.md#slice-3-entities-full-detail),
[DATABASE_SCHEMA.md §Slice 3](../05-data/DATABASE_SCHEMA.md#slice-3-email-marketing-tables),
[ERD.md §Slice 3 additions](../05-data/ERD.md#slice-3-email-marketing-additions). RBAC:
[RBAC.md §Slice 3](../08-security/RBAC.md#slice-3-permission-codes). Threat model:
[THREAT_MODEL.md §Slice 3](../08-security/THREAT_MODEL.md#slice-3-email-marketing-scope).

Full task breakdown with dependencies: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-EMAIL-*`).

## Explicitly excluded from Sprint 3

- Scheduled send, cancellation before execution, and scheduling-specific retry — all
  Slice 4 (`campaign_schedules` doesn't exist yet).
- A generic multi-provider webhook abstraction (`webhook_endpoints`/`webhook_events`/
  `webhook_deliveries`) — premature with exactly one provider; Slice 3 builds a
  Postmark-specific receiver only. Revisit only if a second provider is ever added.
  **Update (`GRX-EMAIL-011` / `DEC-GRX-016`)**: a second provider (Custom SMTP) was
  added, but this exclusion still holds — Custom SMTP has no webhook events at all
  (plain SMTP has no bounce/complaint/open/click callback mechanism), so the trigger
  condition this bullet anticipated didn't actually arise. Revisit only if a provider
  that *does* need webhooks (a real SendGrid/Mailgun/AWS SES API integration) is added.
- A pre-aggregated `analytics_events` table — the campaign report is computed by
  aggregate queries over `message_deliveries`/`email_events`/`campaign_recipients`.
  Revisit only if those queries become a real performance problem.
- An in-app notification (e.g. "your campaign finished sending") — no `notifications`
  writer in Sprint 3.
- Resolving [OQ-009](../00-project-control/OPEN_QUESTIONS.md) (rich-text vs. drag-and-drop
  template editor) at the sprint-planning level — deferred to whichever task actually
  builds the editor; the schema (`body_html`/`body_text`) is editor-agnostic either way.
- Automated sender-identity verification polling against Postmark's API — verification is
  a manual admin action in Sprint 3.
- Any entitlement/limit enforcement on `usage_records` — Slice 3 gives it its first real
  writer (recording), not its first consumer (enforcing).
- A/B testing, send-time optimization, or AI-assisted content — the latter is Slice 6 and
  explicitly must not be reachable from `email_delivery` per
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)'s `ai` module boundary.

If implementing a Sprint 3 task seems to require touching any of the above, stop and flag
it — it means the task is scoped wrong, not that a shortcut through excluded territory is
warranted.

## Sprint 3 acceptance criteria

- An Admin/Marketing Manager/Content Creator can create an email template (subject +
  HTML/text body) and edit it, producing a new version each time — never mutating a past
  version.
- An Admin/Marketing Manager/Content Creator can create a campaign draft: write or start
  from a template, choose a sender identity, and target a segment, a list, or all
  contacts.
- An Admin/Marketing Manager can send a test email to a single address without affecting
  any campaign/recipient/delivery state.
- An Admin/Marketing Manager can trigger an immediate send: recipients are resolved from
  the targeting rule at that moment (not retroactively affected by later segment
  changes), addresses on the suppression list or with withdrawn consent are excluded and
  marked `SUPPRESSED` rather than sent to, and an immutable `campaign_versions` snapshot
  is written.
- Sending enqueues a job for the worker rather than sending synchronously inside the API
  request.
- A Postmark webhook event (delivered/opened/clicked/bounced/complained) updates the
  matching `message_deliveries` row and appends an `email_events` row; a request to the
  webhook endpoint that fails its Basic Auth check is rejected before touching either
  table.
- A recipient clicking unsubscribe records an `unsubscribe_events` row and results in a
  `suppression_entries` row for that address.
- A campaign's report shows sent/delivered/opened/clicked/bounced/complained counts that
  match the underlying `message_deliveries`/`email_events` rows.
- A user with `campaigns.view` only can see templates/campaigns/reports but gets 403
  attempting to create, edit, or send anything (negative test).
- A user with `campaigns.manage` but not `campaigns.send` (Content Creator's exact grant)
  can create and edit a draft campaign but gets 403 attempting to send it — a
  permission-gated action *within* an otherwise-accessible resource, not just a
  whole-resource view/manage split (negative test; new shape of test for this project).
- Only a user with `integrations.manage` (Super Admin) can configure the provider
  connection or a sender identity; every other role, including Admin, gets 403 (negative
  test — the project's first Admin-excluded permission).
- Automated backend and frontend tests pass; CI passes.

## Definition of done for this sprint

[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) applies to every task
in this sprint individually — the sprint itself is done only when every task in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) tagged `GRX-EMAIL-*`
is `DONE`, not merely attempted. Per [DEC-GRX-011](../00-project-control/DECISIONS.md), no
task is marked `DONE` on mocked-provider evidence — send verification must be a real
Postmark send (or, if a live Postmark account isn't available during a given work session,
explicitly flagged as an evidence gap rather than silently assumed).
