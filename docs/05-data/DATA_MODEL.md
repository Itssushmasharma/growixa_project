# Data Model

- Document ID: DOC-DATA-MODEL
- Status: ACTIVE
- Version: 1.3
- Last updated: 2026-08-07
- Owner: Coding agent
- Related documents: [ERD](ERD.md), [DATABASE_SCHEMA](DATABASE_SCHEMA.md), [MODULE_BOUNDARIES](../04-architecture/MODULE_BOUNDARIES.md), [AUTHENTICATION](../08-security/AUTHENTICATION.md)

## Conventions

- UUID primary keys everywhere, no documented exception yet.
- No `tenant_id`/`workspace_id` on any table — single-tenant per
  [DEC-GRX-002](../00-project-control/DECISIONS.md). Ownership uses `created_by_user_id`,
  `updated_by_user_id`, `assigned_to_user_id` where relevant.
- `created_at` / `updated_at` on every table (UTC timestamps).
- Soft-delete via a nullable `deleted_at` where the feature spec calls for archive-not-delete
  (e.g. contacts); hard rows elsewhere.
- Sensitive fields (password hashes, token hashes, provider secrets) are never returned by
  any API response model, and are excluded from audit-log payloads.

## Sprint 1 entities (full detail)

### `users`

- Purpose: internal application users.
- Primary key: `id` (UUID)
- Required fields: `email` (unique, citext), `password_hash` (Argon2id), `full_name`, `status`
- Status values: `ACTIVE`, `DISABLED`, `PENDING_VERIFICATION` (Sprint 5 Phase C,
  `GRX-SAAS-003` — a self-registered owner starts here; email verification flips it to
  `ACTIVE`; reuses `login()`'s existing `status == "ACTIVE"` gate, see
  [DECISIONS.md §DEC-GRX-019](../00-project-control/DECISIONS.md))
- Optional fields: `last_login_at`
- Sensitive fields: `password_hash` — never serialized, never logged.
- Audit fields: `created_at`, `updated_at`
- Related APIs: `docs/06-api/` user endpoints (Phase 5)
- Related features: `USER_MANAGEMENT.md`, `AUTHENTICATION.md`

### `roles`

- Purpose: named roles (Super Admin, Admin, Marketing Manager, Content Creator, Analyst, Viewer).
- Primary key: `id` (UUID)
- Required fields: `name` (unique), `description`
- Seed data: the six roles above ship as seed data, not user-creatable in Sprint 1.

### `permissions`

- Purpose: granular permission codes (e.g. `users.manage`, `company.settings.edit`, `audit.view`).
- Primary key: `id` (UUID)
- Required fields: `code` (unique), `description`

### `role_permissions`

- Purpose: many-to-many role → permission mapping.
- Primary key: composite (`role_id`, `permission_id`)
- Foreign keys: `role_id` → `roles.id`, `permission_id` → `permissions.id`

### `user_roles`

- Purpose: many-to-many user → role assignment (a user may hold more than one role).
- Primary key: composite (`user_id`, `role_id`)
- Foreign keys: `user_id` → `users.id`, `role_id` → `roles.id`
- Audit fields: `assigned_at`, `assigned_by_user_id`

### `refresh_tokens`

- Purpose: rotating refresh-token sessions (DEC-GRX-014 requirement).
- Primary key: `id` (UUID)
- Required fields: `user_id`, `token_hash` (hashed, never the raw token), `issued_at`, `expires_at`
- Optional fields: `revoked_at`, `replaced_by_token_id` (rotation chain), `user_agent`, `ip_address`
- Sensitive fields: `token_hash`
- Supports: session revocation, "logout all sessions" (revoke all rows for a user)

### `password_reset_tokens`

- Purpose: one-time password reset flow.
- Primary key: `id` (UUID)
- Required fields: `user_id`, `token_hash`, `expires_at`
- Optional fields: `used_at`
- Sensitive fields: `token_hash`

### `user_invitations`

- Purpose: admin-issued invitations for new internal users (no self-service signup — [ASM-009](../00-project-control/ASSUMPTIONS.md)).
- Primary key: `id` (UUID)
- Required fields: `email`, `token_hash`, `role_id`, `invited_by_user_id`, `expires_at`
- Optional fields: `accepted_at`
- Sensitive fields: `token_hash`

### `company_profile`

- Purpose: the single company record (singleton — enforced at the service layer, not a DB constraint that assumes exactly one row exists at migration time, since it starts empty).
- Primary key: `id` (UUID)
- Required fields: `name`
- Optional fields: `logo_url`, `website`, `industry`, `timezone`, `default_language`, `legal_footer`, `contact_details` (JSONB)
- Note: `billing_identity` field from the broader spec is deferred — no billing provider in MVP ([OQ-007](../00-project-control/OPEN_QUESTIONS.md)).

### `brand_profiles`

- Purpose: brand voice and content-safety settings, referenced by the future AI/content modules.
- Primary key: `id` (UUID)
- Required fields: `company_id` (FK → `company_profile.id`)
- Optional fields: `brand_voice` (text), `forbidden_claims` (JSONB), `required_facts` (JSONB)
- Sprint 1 scope: table + basic fields only; not yet consumed by any AI feature (AI is Slice 6).

### `audit_logs`

- Purpose: immutable record of sensitive actions.
- Primary key: `id` (UUID)
- Required fields: `actor_user_id` (nullable for system-initiated events), `action` (e.g. `user.login`, `user.login_failed`, `user.logout`, `user.password_reset_requested`, `user.password_reset_completed`, `invitation.accepted`, `role.changed`, `session.revoked`), `entity_type`, `entity_id`, `created_at`
- Optional fields: `metadata` (JSONB), `ip_address`, `user_agent`
- Retention: not yet decided ([OQ-008](../00-project-control/OPEN_QUESTIONS.md)); table has no auto-expiry in Sprint 1.
- Immutability: no update/delete API — insert-only.

### `usage_records`

- Purpose: foundation ledger for usage metering (PRD §33), even though no cost-generating
  operation exists yet in Sprint 1.
- Primary key: `id` (UUID)
- Required fields: `operation_type`, `quantity`, `unit`, `created_by_user_id`, `created_at`
- Optional fields: `metadata` (JSONB)
- Sprint 1 scope: schema exists; no writer calls it yet (first real writer arrives with
  Slice 3+ features). This avoids retrofitting the metering table later per
  [DEC-GRX-007](../00-project-control/DECISIONS.md).

## Slice 2 entities (full detail)

### `contacts`

- Purpose: a person a company markets to.
- Primary key: `id` (UUID)
- Required fields: `email` (unique, citext), `status` (`ACTIVE` | `ARCHIVED`, default `ACTIVE`)
- Optional fields: `first_name`, `last_name`, `phone`, `source` (e.g. `manual`, `csv_import`)
- Ownership: `created_by_user_id` (nullable — null for CSV-imported contacts not
  attributable to a manual creator)
- Audit fields: `created_at`, `updated_at`
- Soft-delete: archive via `status = 'ARCHIVED'`, never a hard delete, per this doc's
  conventions.
- Duplicate handling: `email` is the sole dedup key. A CSV import or manual create that
  matches an existing email **updates** that contact rather than creating a second row —
  no fuzzy/name-based dedup in Slice 2.
- Activity history: reuses the existing `audit_logs` table (`entity_type = 'contact'`)
  rather than a new table — `contact.created`, `contact.updated`, `contact.archived`,
  `contact.tagged`, `contact.list_added`, `contact.consent_changed`,
  `contact.suppressed` extend the audit action vocabulary. No separate
  `contact_activity` table.

### `contact_custom_fields`

- Purpose: company-defined extra fields on a contact (e.g. "Company size").
- Primary key: `id` (UUID)
- Required fields: `key` (unique, machine name), `label`, `field_type`
  (`TEXT` | `NUMBER` | `DATE` | `BOOLEAN`)
- Audit fields: `created_at`

### `contact_field_values`

- Purpose: the value of one custom field for one contact.
- Primary key: composite (`contact_id`, `field_id`)
- Foreign keys: `contact_id` → `contacts.id` ON DELETE CASCADE, `field_id` →
  `contact_custom_fields.id` ON DELETE CASCADE
- Required fields: `value` (text) — stored as text regardless of `field_type` and cast at
  read time; avoids a polymorphic-column design for an MVP feature set this small.

### `tags` / `contact_tags`

- `tags`: `id` (UUID PK), `name` (unique), `created_at`.
- `contact_tags`: composite PK (`contact_id`, `tag_id`), both FKs `ON DELETE CASCADE`.
  Simple many-to-many, no tag hierarchy/color/scoping in Slice 2.

### `contact_lists` / `contact_list_members`

- `contact_lists`: purpose is a manually curated, user-named group of contacts (add/remove
  one at a time, or in bulk from an import). `id` (UUID PK), `name`, `description`
  (nullable), `created_by_user_id` (nullable FK → `users.id`), `created_at`, `updated_at`.
- `contact_list_members`: composite PK (`list_id`, `contact_id`), both FKs
  `ON DELETE CASCADE`, `added_at` (default `now()`).

### `segments` / `segment_rules` / `segment_members`

- Purpose: a **rule-defined** audience, distinct from a manually curated list.
- `segments`: `id` (UUID PK), `name`, `type` (`DYNAMIC` | `SAVED`), `created_by_user_id`
  (nullable FK → `users.id`), `created_at`, `updated_at`.
  - `DYNAMIC`: membership is evaluated live from `segment_rules` every time the segment is
    used (e.g. opened, or referenced by a future campaign in Slice 3+).
  - `SAVED`: membership is evaluated once and frozen into `segment_members` at save time;
    re-evaluating requires an explicit user action (not built as an automatic job in
    Slice 2 — no scheduler exists yet for that).
- `segment_rules`: `id` (UUID PK), `segment_id` (FK → `segments.id` ON DELETE CASCADE),
  `field` (e.g. `tag`, `custom_field:<key>`, `consent_status`, `created_at`), `operator`
  (e.g. `equals`, `contains`, `before`, `after`, `in`), `value` (text, interpreted per
  field/operator at query time).
  - **Simplification, stated explicitly**: all rules on a segment are AND-combined only.
    OR logic / rule grouping is not in Slice 2 scope — revisit only if a real need
    surfaces, per this project's stated anti-speculation practice.
- `segment_members` (`SAVED` segments only): composite PK (`segment_id`, `contact_id`),
  both FKs `ON DELETE CASCADE`, `captured_at` (default `now()`). Empty/unused for
  `DYNAMIC` segments.

### `contact_imports` / `contact_import_rows`

- Purpose: CSV import job tracking, validation, and history (`MVP_SCOPE.md §B`'s "import
  validation, import history" requirement).
- `contact_imports`: `id` (UUID PK), `file_name`, `status`
  (`PENDING` | `VALIDATING` | `IMPORTING` | `COMPLETED` | `FAILED`, default `PENDING`),
  `total_rows` / `imported_count` / `skipped_count` / `error_count` (integers),
  `column_mapping` (jsonb, CSV column → contact field), `created_by_user_id` (FK →
  `users.id`, not null), `created_at`, `completed_at` (nullable).
- `contact_import_rows`: `id` (UUID PK), `import_id` (FK → `contact_imports.id` ON DELETE
  CASCADE), `row_number`, `raw_data` (jsonb, the original CSV row), `status`
  (`PENDING` | `IMPORTED` | `SKIPPED` | `ERROR`, default `PENDING`), `error_message`
  (nullable), `contact_id` (nullable FK → `contacts.id`, set once imported or matched to
  an existing contact by email).

### `consent_records`

- Purpose: an **insert-only compliance history** of consent grants/withdrawals — mirrors
  `audit_logs`'s insert-only pattern, since "who consented, to what, when" must never be
  editable after the fact.
- Primary key: `id` (UUID)
- Required fields: `contact_id` (FK → `contacts.id` ON DELETE CASCADE), `channel`
  (`EMAIL` | `SMS` — SMS included now even though SMS marketing itself is Release 1.2, so
  this table doesn't need a schema change later), `status`
  (`GRANTED` | `WITHDRAWN` | `UNKNOWN`, default `UNKNOWN`), `recorded_at` (default `now()`)
- Optional fields: `source` (e.g. `import`, `manual`, future `unsubscribe_link`),
  `recorded_by_user_id` (nullable FK → `users.id` — null for contact-initiated events,
  none of which exist yet in Slice 2)
- Current consent status for a contact+channel is derived as "most recent row," not
  stored as separate mutable state.

### `suppression_entries`

- Purpose: a fast, current-state "never contact this address" list — distinct from
  `consent_records`'s append-only history, because its only job is a fast lookup before
  any future send (Slice 3+).
- Primary key: `id` (UUID)
- Row shape (`GRX-SAAS-015`, ad hoc): each row is *either* an exact-email entry (`email`
  set, `domain` NULL) *or* a whole-domain block (`domain` set, `email` NULL, e.g. suppress
  every `*@competitor.com` address) — never both, enforced by
  `ck_suppression_entries_email_xor_domain`. Domain rows are always `reason='MANUAL'`;
  there's no such thing as an automatic whole-domain unsubscribe/bounce/complaint event.
- Required fields: `reason` (`UNSUBSCRIBED` | `BOUNCED` | `COMPLAINED` | `MANUAL`),
  `suppressed_at` (default `now()`)
- Optional fields (exactly one of the two set per row, per the XOR constraint above):
  `email` (citext), `domain` (text). Also: `contact_id` (nullable FK → `contacts.id` — an
  address can be suppressed even with no matching contact record, e.g. a hard bounce; always
  NULL on domain rows), `suppressed_by_user_id` (nullable FK → `users.id`)
- Re-suppressing an already-suppressed email updates `reason`/`suppressed_at` in place
  (upsert on the unique `(account_id, email)` index), it does not create a second row.
  Re-blocking an already-blocked domain returns the existing row unchanged (idempotent,
  enforced by the partial unique index on `(account_id, domain) WHERE domain IS NOT NULL`
  — a plain `(account_id, domain)` unique constraint wouldn't work here since Postgres
  treats every NULL `domain` value as mutually distinct).
- A campaign send checks both: the exact recipient email against the unique index, and the
  recipient's `@`-suffix domain against the domain rows — a domain block has no exact-email
  row to match, so it's checked as a second, separate query.

## Slice 3 entities (full detail)

Per [DEC-GRX-010](../00-project-control/DECISIONS.md), Slice 3 (First Email Campaign) is
immediate-send only — no scheduling, cancellation, or scheduled retry (that's Slice 4).
Module ownership follows [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md):
`integrations`, `templates`, `campaigns`, `email_delivery`.

### `email_provider_connections`

- Purpose: production email-sending configuration. Postmark per
  [DEC-GRX-015](../00-project-control/DECISIONS.md); a generic Custom SMTP option was
  added alongside it per [DEC-GRX-016](../00-project-control/DECISIONS.md) — both via
  SMTP relay, so they share one schema.
- Primary key: `id` (UUID)
- Required fields: `provider` (`POSTMARK` or `CUSTOM_SMTP` — kept as an enum column
  rather than a free string, per DEC-GRX-015's original framing, so a further provider
  is a data migration, not a schema rewrite), `smtp_host`, `smtp_port`, `smtp_username`
  (Postmark server token, or the Custom SMTP account's username), `smtp_password_encrypted`
  (the same token/password, encrypted at rest per
  [DEC-GRX-009](../00-project-control/DECISIONS.md) — for Postmark, stored twice under
  different field names because its SMTP auth uses the token as both), `is_active`
  (boolean, default `true`)
- Audit fields: `created_by_user_id`, `created_at`, `updated_at`
- One active connection **per provider**, not one globally (revised by
  [DEC-GRX-016](../00-project-control/DECISIONS.md) — previously "singleton by
  convention," app-enforced only, matching `company_profile`'s pattern): a
  `ux_email_provider_connections_active_per_provider` partial unique index on
  `(provider) WHERE is_active` makes this a real DB constraint. A new connection for a
  given provider deactivates that provider's previous one and is created fresh rather
  than overwriting in place, so the credential history isn't silently lost — a
  different provider's active connection is untouched.
- Webhooks: only Postmark connections' `webhook_username`/`webhook_password_encrypted`
  are ever consulted (by `POST /webhooks/postmark`) — Custom SMTP has no webhook route
  at all, since plain SMTP has no bounce/complaint/open/click callback mechanism.
- Encryption: a new `ENCRYPTION_KEY` setting (Fernet symmetric key, distinct from
  `JWT_SIGNING_KEY`) encrypts `smtp_password_encrypted` before it's written and decrypts it
  only at send time inside the worker — never logged, never returned by any API response
  model per this doc's conventions.

### `sender_identities`

- Purpose: the verified "from" address/name a campaign sends as. Postmark requires sender
  signature verification before a domain/address can send.
- Primary key: `id` (UUID)
- Foreign keys: `email_provider_connection_id` → `email_provider_connections.id`
- Required fields: `from_email`, `from_name`, `verification_status`
  (`PENDING` | `VERIFIED` | `FAILED`, default `PENDING`)
- Optional fields: `reply_to_email`
- Audit fields: `created_by_user_id`, `created_at`, `updated_at`
- Verification is a manual, out-of-band step in Slice 3 (an admin verifies the sender in
  Postmark's own dashboard, then flips `verification_status`) — no automated verification
  polling in Slice 3; revisit only if Postmark's API for this becomes a real need.

### `email_templates` / `email_template_versions`

- Purpose: a reusable, named email template with an edit history.
- `email_templates`: `id` (UUID PK), `name`, `created_by_user_id`, `created_at`, `updated_at`.
- `email_template_versions`: `id` (UUID PK), `template_id` (FK →
  `email_templates.id` ON DELETE CASCADE), `version_number` (int, increments per template,
  starting at 1), `subject`, `body_html`, `body_text` (nullable — a plain-text fallback;
  not auto-derived from HTML in Slice 3), `created_by_user_id`, `created_at`.
  - The "current" version is the row with the highest `version_number` for that template —
    an insert-only history (same philosophy as `consent_records`/`audit_logs`), not a
    mutable pointer column. Editing a template creates a new version; nothing is ever
    updated in place.
  - Editor implementation ([OQ-009](../00-project-control/OPEN_QUESTIONS.md), open) is
    deliberately not decided here — `body_html`/`body_text` accept whatever a future
    rich-text or drag-and-drop editor produces, so resolving OQ-009 doesn't require a
    schema change.
  - Personalization variables (e.g. `{{first_name}}`) are plain string substitution
    resolved at send time against the recipient contact's fields — no separate
    variable-registry table in Slice 3.

### `campaigns` / `campaign_versions`

- Purpose: a single email send-out, targeting a segment/list/all contacts.
- `campaigns`: `id` (UUID PK), `name` (internal label), `subject`, `body_html`,
  `body_text` (nullable), `template_id` (nullable FK → `email_templates.id` — a campaign
  may start from a template or be written ad hoc; editing a campaign's content never
  writes back to the template), `sender_identity_id` (FK → `sender_identities.id`),
  `recipient_type` (`SEGMENT` | `LIST` | `ALL_CONTACTS`), `recipient_segment_id` (nullable
  FK → `segments.id`), `recipient_list_id` (nullable FK → `contact_lists.id` — exactly one
  of `recipient_segment_id`/`recipient_list_id` is set, matching `recipient_type`; neither
  is set for `ALL_CONTACTS`), `status`
  (`DRAFT` | `SENDING` | `SENT` | `FAILED`, default `DRAFT` — no `SCHEDULED`/`CANCELLED`
  until Slice 4), `created_by_user_id`, `created_at`, `updated_at`, `sent_at` (nullable).
  Draft content (`subject`/`body_html`/`body_text`) is mutable up until `status` leaves
  `DRAFT` — enforced at the service layer, not the schema.
- `campaign_versions`: `id` (UUID PK), `campaign_id` (FK → `campaigns.id`), `subject`,
  `body_html`, `body_text`, `recipient_count` (int), `created_at`. Exactly **one** row is
  written per campaign, at the moment it starts sending — an immutable "what was actually
  sent" snapshot for compliance/reporting, distinct from the mutable draft on `campaigns`
  itself. This is deliberately not full edit-history versioning (a new row per draft save)
  — nothing in `MVP_SCOPE.md §C` asks for draft revision history, only for the sent
  content to be verifiably fixed once sending starts.

### `campaign_recipients`

- Purpose: the resolved, concrete recipient list for one campaign — materializes whatever
  the segment/list/all-contacts targeting rule matched at send time, so a `DYNAMIC`
  segment changing later doesn't retroactively alter who a past campaign was sent to.
- Primary key: `id` (UUID)
- Foreign keys: `campaign_id` → `campaigns.id` ON DELETE CASCADE, `contact_id` →
  `contacts.id`
- Required fields: `email` (denormalized snapshot of the contact's email at send time),
  `status` (`PENDING` | `SENT` | `FAILED` | `SUPPRESSED`, default `PENDING` — `SUPPRESSED`
  means the suppression check at send time excluded this contact even though the
  targeting rule matched it)
- Audit fields: `created_at`
- Per [DEC-GRX-008](../00-project-control/DECISIONS.md)'s suppression rule (enforced from
  Slice 3 onward, cannot be a fast-follow): every row is checked against
  `suppression_entries` before a `message_deliveries` row is created for it.

### `message_deliveries` / `delivery_attempts`

- Purpose: per-recipient delivery status, and the retry history behind it — owned by the
  `email_delivery` module per `MODULE_BOUNDARIES.md`, not `campaigns`.
- `message_deliveries`: `id` (UUID PK), `campaign_recipient_id` (FK →
  `campaign_recipients.id` ON DELETE CASCADE), `provider_message_id` (nullable — Postmark's
  `MessageID`, populated once accepted), `status`
  (`QUEUED` | `SENT` | `DELIVERED` | `BOUNCED` | `COMPLAINED` | `FAILED`, default
  `QUEUED`), `sent_at` / `delivered_at` / `bounced_at` (all nullable), `created_at`,
  `updated_at`.
- `delivery_attempts`: `id` (UUID PK), `message_delivery_id` (FK →
  `message_deliveries.id` ON DELETE CASCADE), `attempt_number` (int, starting at 1),
  `status`, `error_message` (nullable), `attempted_at`. Follows
  [BACKGROUND_JOB_ARCHITECTURE.md](../04-architecture/BACKGROUND_JOB_ARCHITECTURE.md)'s
  baseline retry pattern (exponential backoff, bounded attempt count) for the send job
  itself — this is worker-level send retry (e.g. a transient SMTP error), not Slice 4's
  user-facing "reschedule/cancel" feature, which is a different concern layered on top
  later.

### `email_events`

- Purpose: the raw, append-only ledger of provider webhook events — feeds
  `message_deliveries`'s current status and, later, campaign analytics.
- Primary key: `id` (UUID)
- Foreign keys: `message_delivery_id` → `message_deliveries.id` ON DELETE CASCADE
- Required fields: `event_type` (`DELIVERED` | `OPENED` | `CLICKED` | `BOUNCED` |
  `COMPLAINED`), `occurred_at` (from the webhook payload, not `created_at`)
- Optional fields: `metadata` (JSONB — e.g. clicked URL, user agent, bounce type)
- Audit fields: `created_at`
- Insert-only, same philosophy as `audit_logs`/`consent_records` — a webhook redelivery of
  an already-recorded event is a new row, not deduplicated in Slice 3 (Postmark's
  `MessageID` + `event_type` + `occurred_at` is available for later dedup if double-counted
  analytics becomes a real problem).

### `unsubscribe_events`

- Purpose: an analytics/audit trail of unsubscribe actions tied to a specific send —
  distinct from `suppression_entries`, which remains the sole enforcement mechanism
  checked before any send.
- Primary key: `id` (UUID)
- Foreign keys: `contact_id` (nullable — the address may not match a contact),
  `campaign_id` (nullable FK → `campaigns.id` — which send triggered it, if any)
- Required fields: `email` (citext), `occurred_at`
- Audit fields: `created_at`
- Recording an unsubscribe event also writes a `suppression_entries` row
  (`reason = 'UNSUBSCRIBED'`) in the same transaction — reuses Slice 2's suppression
  infrastructure rather than duplicating the enforcement check.

### `usage_records` — first real writer

- No schema change (table already exists per Sprint 1's `DEC-GRX-007` foundation work).
- Slice 3 is this table's first real writer: one row per campaign send,
  `operation_type = 'email.sent'`, `quantity` = the campaign's resolved recipient count
  (after suppression), `unit = 'email'`, `created_by_user_id` = the campaign's sender.
  Recording only — no entitlement/limit enforcement yet (`feature_entitlements` remains
  unbuilt until a real limit needs enforcing, per this doc's existing landscape note).

## Explicitly deferred, not designed in Slice 3

- `campaign_schedules` — Slice 4 (Scheduled Email). Slice 3 campaigns send immediately or
  not at all; no future send-time field exists on `campaigns` yet.
- Generic multi-provider `webhook_endpoints`/`webhook_events`/`webhook_deliveries` tables —
  premature with exactly one provider (Postmark, per `MVP_SCOPE.md`'s "one production
  provider adapter"). Slice 3 builds a Postmark-specific webhook receiver that writes
  directly to `email_events`/`message_deliveries`. Revisit only when a second provider is
  actually added.
- `analytics_events` — Slice 3's "campaign report/basic analytics"
  (`MVP_SCOPE.md §C`) is computed by aggregate queries over `message_deliveries` /
  `email_events` / `campaign_recipients`, not a separate pre-aggregated events table. This
  is a read-side optimization to revisit only if those aggregate queries become a real
  performance problem.
- `notifications` — no Slice 3 requirement calls for an in-app notification (e.g. "notify
  me when a send completes"); still just the Slice 1 stub with no writer.
- `feature_entitlements` — `usage_records` gets its first writer this slice, but no limit
  is enforced against it yet.

## Sprint 5 Phase B entities (Customer Account Platform — Platform auth boundary, full detail)

Deliberately not "Slice 4/5" — those numbers are already used above for Scheduled Email
and Social Media Automation respectively (the original single-tenant roadmap). This is
`GRX-SAAS-002` per [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase B](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-b--platform-auth-boundary-grx-saas-002).
Phase B builds only the identity/auth boundary — no actual platform-admin *features* sit
behind it yet (that's Phase E) — so these entities are deliberately minimal.

### `platform_admins`

- Purpose: IITDEVELOPER staff identities, structurally separate from `accounts`/`users` —
  a platform admin is not scoped to, and does not belong to, any customer account.
- Primary key: `id` (UUID)
- Required fields: `email` (unique, citext), `password_hash` (Argon2id, same scheme as
  `users`), `full_name`, `role` (one of the five values below), `status`
- Status values: `ACTIVE`, `DISABLED` (same shape as `users.status`)
- Optional fields: `last_login_at`
- Sensitive fields: `password_hash` — never serialized, never logged (same rule as `users`).
- Audit fields: `created_at`, `updated_at`
- Provisioning: seeded/provisioned directly, no self-service signup — mirrors how
  `admin@growixa.local` is created today. See [DEC-GRX-018](../00-project-control/DECISIONS.md)
  for why this holds a single `role` value directly rather than the `users`/`roles`/
  `user_roles` many-to-many shape.

### `platform_permissions`

- Purpose: granular `platform.*`-namespaced permission codes, structurally parallel to
  `permissions` but never checked by `require_permission()` — only by the separate
  `require_platform_permission()` dependency, so an account-scoped route can never
  accidentally accept a platform permission code or vice versa.
- Primary key: `id` (UUID)
- Required fields: `code` (unique, always `platform.`-prefixed), `description`
- Seed data (Phase B minimum): `platform.access` — the minimal gate proving a platform
  admin session can reach *a* platform-only route at all, structurally analogous to
  Sprint 1's `admin.access`. Every actual Phase E capability (user management, billing,
  provider config, etc.) adds its own code here when that feature is built, per the same
  "extended, not redesigned" convention `RBAC.md` already documents for `permissions`.

### `platform_role_permissions`

- Purpose: role → permission mapping for platform admins. Keyed by the `role` value
  directly (not a `role_id` FK) since `platform_admins.role` is a plain column, not a row
  in a separate roles table — see [DEC-GRX-018](../00-project-control/DECISIONS.md).
- Primary key: composite (`role`, `permission_id`)
- Foreign keys: `permission_id` → `platform_permissions.id`
- Seed data (Phase B minimum): all five roles (`platform.owner`, `platform.admin`,
  `platform.support`, `platform.finance`, `platform.operations`) granted `platform.access`
  — Phase B proves the boundary works, it doesn't yet differentiate what each role can do
  once inside; that differentiation arrives with each Phase E feature's own permission
  code(s).

## Sprint 5 Phase C entities (Customer Account Platform — Self-service registration, full detail)

`GRX-SAAS-003` per [SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase C](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-c--self-service-registration-grx-saas-003).
Design decisions (owner role, plan slug without a plans table, verification via a third
`users.status` value) are in [DECISIONS.md §DEC-GRX-019](../00-project-control/DECISIONS.md)
— not repeated here.

### `accounts` (documented here for the first time)

`accounts` has existed since Phase A (`GRX-SAAS-001`) but was never given its own entity
entry — this section closes that gap for the one field Phase C actually touches, not a
full Phase A retrospective.

- Purpose: the customer-account isolation boundary every account-owned table's
  `account_id` points at.
- Primary key: `id` (UUID)
- Required fields: `name`, `status`
- Status values: `ACTIVE`, `SUSPENDED`, `CLOSED` (Phase A) — unrelated to a user's own
  `PENDING_VERIFICATION` status; see DEC-GRX-019 for why the two aren't conflated.
- Optional fields: `plan_id` (nullable `UUID`, no FK yet — reserved for Phase D's real
  `plans`/`subscriptions` model), `selected_plan_slug` (Phase C, nullable `text`, `CHECK
  IN ('starter', 'growth')` — the self-service plan picked at registration, recorded
  only; no enforcement until Phase D)
- Audit fields: `created_at`

### `account_verification_tokens`

- Purpose: one-time email verification for a self-registered account's first user —
  structurally identical to `password_reset_tokens`.
- Primary key: `id` (UUID)
- Required fields: `account_id`, `user_id`, `token_hash`, `expires_at`
- Optional fields: `used_at`
- Sensitive fields: `token_hash`

## Sprint 5 Phase E entities (Customer Account Platform — Account/user management, `GRX-SAAS-005`)

No new tables. `GRX-SAAS-005` adds one seed row (`platform_permissions.code =
'platform.accounts.manage'`, granted to `platform.owner`/`platform.admin` in
`platform_role_permissions`) and, per [DECISIONS.md §DEC-GRX-020](../00-project-control/DECISIONS.md),
finally makes `accounts.status` (documented above since Phase C, existing since Phase A)
an actually-enforced field: `auth/services.py`'s `login()`/`refresh()` now reject a
non-`ACTIVE` account the same way they already reject a non-`ACTIVE` user. No schema
change was needed for "view login/security activity" either — it reads the existing
`audit_logs` table (scoped by `account_id`, filtered to a fixed security-action
allow-list), and a platform admin's own suspend/activate/close action is recorded there
too, with the acting admin's id/email in `event_metadata` rather than `actor_user_id`
(which stays a `users.id` FK and cannot reference `platform_admins`).

## Sprint 5 Phase E entities (Customer Account Platform — Usage & campaign oversight, `GRX-SAAS-008`)

No new tables. Adds one seed row (`platform_permissions.code =
'platform.usage.manage'`, granted to `platform.owner`/`platform.admin`/`platform.support`
in `platform_role_permissions`). Per [DECISIONS.md §DEC-GRX-021](../00-project-control/DECISIONS.md):
the per-account usage view is a `GROUP BY account_id, operation_type` aggregate over the
existing `usage_records` table (no new column, no new query surface beyond the grouping);
the cross-account campaign oversight view reads the existing `campaigns` table filtered to
in-flight (`SCHEDULED`/`DISPATCHING`/`SENDING`) or `FAILED` status, without the usual
`account_id` scoping (a deliberate, narrow exception — see `THREAT_MODEL.md` T36/T37 for
why the response shape stays metadata-only); "pausing" a campaign reuses the existing
`cancel_campaign` state transition (`DRAFT`/`SCHEDULED` → `CANCELLED`) rather than adding a
new `PAUSED` status.

## Sprint 5 Phase E entities (Customer Account Platform — Secure support session, `GRX-SAAS-010`)

One new table, `support_sessions` — the system of record for every audited support
session, per [DECISIONS.md §DEC-GRX-022](../00-project-control/DECISIONS.md):

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `account_id` | UUID FK → `accounts.id`, `ON DELETE CASCADE` | The one account this session grants access to |
| `platform_admin_id` | UUID FK → `platform_admins.id`, `ON DELETE RESTRICT` | Who opened it — every session-scoped route requires the *caller's own* id to match this, not just a valid session id |
| `reason` | text, NOT NULL | Required free-text justification |
| `ticket_number` | text, NOT NULL | Required external ticket reference |
| `access_level` | text, NOT NULL, `CHECK IN ('READ','WRITE')`, default `'READ'` | `WRITE` additionally requires `platform.support_session.write` at creation time |
| `started_at` | timestamptz, default `now()` | |
| `expires_at` | timestamptz, NOT NULL | `started_at` + `support_session_ttl_minutes` (new setting, default 60) — re-checked on every access, not just at creation |
| `ended_at` | timestamptz, nullable | Set when the opening admin ends it early; an active session is `ended_at IS NULL AND expires_at > now()` |
| `created_at`/`updated_at` | timestamptz | Standard pair |

Two new seed rows in `platform_permissions`/`platform_role_permissions`:
`platform.support_session.create` (`platform.owner`/`platform.admin`/`platform.support`)
and `platform.support_session.write` (`platform.owner`/`platform.admin` only). No new
tables for the session's read data (company profile, contacts, audit trail) or its one
gated write action (editing a contact) — both read the existing `company`/`contacts`/
`audit` tables directly, scoped by the session's own `account_id`. `contacts.services.update_contact`'s
`actor_id` parameter widened from `uuid.UUID` to `uuid.UUID | None` (plus a new optional
`audit_metadata` parameter) so a platform admin's edit through a session can record
`actor_user_id=None` with the acting admin's identity in `audit_logs.event_metadata` —
the same pattern `DEC-GRX-020` established, now reused by a second module.

## Slice 5 entities (full detail)

Per `DEC-GRX-023`/`DEC-GRX-024`/`DEC-GRX-025`. Module ownership follows
[MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md): `social`, `files`. No
`content_calendar` module this slice — the calendar is a `social`-owned read endpoint
(`GET /social/posts/calendar`), not a separate cross-module entity; see
`SPRINT_06_SOCIAL_PUBLISHING.md`'s exclusions. No separate `social_publish_attempts` table
either — a post's `status`/`last_error` columns and its `social_post_versions` snapshot
together cover the "publishing status, provider error visibility" requirement without a
second table, mirroring how `campaigns` never needed one beyond `campaign_versions`.

### `social_connections`

- Purpose: one customer account's link to its own Instagram Business Account, via the
  Meta Graph API OAuth flow.
- Primary key: `id` (UUID)
- Required fields: `account_id` (FK → `accounts.id`, `ON DELETE CASCADE`), `provider`
  (`CHECK IN ('INSTAGRAM_BUSINESS')` — enum-via-CHECK, mirrors `email_provider_
  connections.provider`, forward-compatible with a second platform later),
  `ig_business_account_id` (the Graph API `ig-user-id` used in every publish call),
  `facebook_page_id` (the linked Page — source of the Page access token),
  `access_token_encrypted` (Fernet-encrypted per `DEC-GRX-025`), `is_active` (boolean,
  default `true`)
- Optional fields: `ig_username` (cached handle for UI display), `token_expires_at`
  (long-lived token's ~60-day expiry — drives the inline-refresh check), `last_error`
- Audit fields: `created_by_user_id`, `created_at`, `updated_at`, `last_connected_at`
- One active connection per account (per provider): a
  `ux_social_connections_active_per_provider` partial unique index on
  `(account_id, provider) WHERE is_active` — identical shape to `email_provider_
  connections`'s per-provider unique index. Reconnecting deactivates the prior row and
  creates a fresh one, same convention as email provider reconnection.

### `social_posts` / `social_post_media` / `social_post_versions`

- Purpose: a single Instagram post — draft, scheduled, or published — and its media.
- `social_posts`: `id` (UUID PK), `account_id` (FK → `accounts.id` CASCADE),
  `social_connection_id` (FK → `social_connections.id`), `caption` (text, default `''` —
  Instagram allows empty captions), `status` (`DRAFT` | `SCHEDULED` | `DISPATCHING` |
  `PUBLISHING` | `PUBLISHED` | `CANCELLED` | `FAILED`, default `DRAFT` — mirrors
  `campaigns.status`'s shape, substituting SENDING/SENT → PUBLISHING/PUBLISHED),
  `scheduled_at`/`cancelled_at`/`published_at` (nullable), `idempotency_key` (UUID,
  unique, default-generated — identical role to `campaigns.idempotency_key`),
  `ig_media_id`/`ig_permalink` (nullable, populated after a successful publish),
  `last_error` (nullable — provider-error-visibility requirement), `created_by_user_id`,
  `created_at`, `updated_at`. Draft content (`caption`, media) is mutable only while
  `status = 'DRAFT'`, enforced at the service layer — same convention as `campaigns`.
- `social_post_media`: `id` (UUID PK), `account_id` (denormalized, same rationale as
  `campaign_versions.account_id`), `social_post_id` (FK → `social_posts.id` CASCADE),
  `media_type` (`CHECK IN ('IMAGE')` — column is carousel/video-ready, but only `IMAGE` is
  valid this slice per `DEC-GRX-023`'s no-text-only-posts constraint and the media-scope
  decision to ship a single image only), `storage_path`/`public_url` (the Supabase object
  key and its public URL — the latter is what's handed to Instagram's `image_url` param),
  `position` (default 0, forward-compat for carousel ordering), `created_at`. Exactly one
  row per post is an app-level rule (`social/services.py`), not a schema constraint, so
  lifting it for carousel later needs no migration.
- `social_post_versions`: `id` (UUID PK), `account_id`, `social_post_id` (FK →
  `social_posts.id`), `caption`, `media_snapshot` (JSONB — `[{storage_path, public_url,
  media_type}]` at publish time), `ig_media_id`, `created_at`. Immutable
  "what was actually published" snapshot, mirrors `campaign_versions` exactly — and
  doubles as the worker's idempotency guard (its existence for a post is the authoritative
  "already published" check), same role `CampaignVersion` plays in `handle_send_campaign`.

## Slice 6 entities (full detail)

Per `DEC-GRX-026`/`DEC-GRX-027`/`DEC-GRX-028`. Module ownership follows
[MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md): `ai`. Deliberately 3
tables, not the 4 the placeholder below originally speculated — see `DEC-GRX-028` for why
`ai_prompt_templates`/`ai_prompt_versions` collapse into a plain string column, and why
`ai_usage_events` collapses into columns on `ai_generations` directly.

### `ai_generations`

- Purpose: one row per AI generation call — the full record of what was asked, what came
  back, and what it cost, satisfying `GRX-AI-006`'s logging requirement in one table.
- Primary key: `id` (UUID)
- Required fields: `account_id` (FK → `accounts.id` CASCADE), `capability` (`CHECK IN
  ('SUBJECT_LINE', 'BODY_COPY', 'SOCIAL_CAPTION', 'REWRITE', 'HASHTAGS',
  'POSTING_TIME')`), `prompt_template_key` (text — e.g. `"subject_line.v1"`, a
  code-defined reference per `DEC-GRX-028`, not a table FK), `input_context` (JSONB — the
  brief/topic/existing-text-to-rewrite and any other capability-specific input),
  `provider`/`model` (the vendor and model actually used for this call — resolved at
  call time, may differ per generation if the account's BYO connection changes),
  `status` (`CHECK IN ('COMPLETE', 'FAILED')`)
- Optional fields: `output` (JSONB — the generated variation(s); null if `FAILED`),
  `prompt_tokens`/`completion_tokens`/`estimated_cost_usd` (null if `FAILED`),
  `error_message` (populated only if `FAILED`), `linked_entity_type`/`linked_entity_id`
  (nullable provenance — which campaign/social_post this generation was made from, set by
  the frontend, no FK constraint since it can reference either table)
- Audit fields: `created_by_user_id`, `created_at`
- No update path — a generation row is write-once (mirrors `social_post_versions`'
  immutability), never edited after creation.

### `ai_provider_connections` / `platform_ai_provider_config`

- Purpose: the two-level AI provider configuration per `DEC-GRX-026` — an account's own
  "bring your own model" override, and the platform-wide default a brand-new account
  falls back to.
- `ai_provider_connections` (account-level): `id` (UUID PK), `account_id` (FK →
  `accounts.id` CASCADE), `provider` (`CHECK IN ('OPENAI', 'AZURE_OPENAI', 'ANTHROPIC',
  'OLLAMA')`), `api_key_encrypted` (nullable — Fernet-encrypted per `DEC-GRX-026`;
  Ollama typically needs none), `base_url` (nullable — required for `AZURE_OPENAI`/
  `OLLAMA`, validated per `DEC-GRX-027`), `default_model`, `is_active` (default `true`),
  `created_by_user_id`, `created_at`, `updated_at`. One active connection per account: a
  `ux_ai_provider_connections_active_per_account` partial unique index on `(account_id)
  WHERE is_active` — an account brings *one* model at a time, unlike
  `email_provider_connections`'s legitimate per-provider multiplicity (there's no
  equivalent to "generate some content via OpenAI and some via Anthropic" as a standing
  per-account choice). Reconfiguring deactivates the prior row and inserts a fresh one,
  same convention as every other provider-connection table in this codebase.
- `platform_ai_provider_config` (platform-level, new pattern — the first DB-backed,
  admin-editable platform setting in this codebase): same columns minus `account_id`,
  plus a `ux_platform_ai_provider_config_active` partial unique index on `WHERE
  is_active` (at most one active platform default at a time).

### `platform_email_provider_config` (ad hoc, `GRX-SAAS-013`)

- Purpose: the platform-wide default outbound-email SMTP configuration (system/
  transactional email — e.g. registration verification links), admin-editable without a
  redeploy. Added after a real production incident: the previous `.env`-only
  `PLATFORM_SMTP_*` settings pointed at an SMTP relay that turned out to be unreachable
  from the deployed environment, with no way to switch providers or rotate credentials
  short of a redeploy.
- Primary key: `id` (UUID)
- Required fields: `provider` (`CHECK IN ('POSTMARK', 'CUSTOM_SMTP')` — same vocabulary
  as `email_provider_connections`, reused deliberately, not a new type), `smtp_host`,
  `smtp_port`, `smtp_username`, `smtp_password_encrypted` (Fernet-encrypted, same as
  every other stored credential in this codebase), `from_email`, `from_name`, `is_active`
  (default `true`)
- Audit fields: `created_by_platform_admin_id` (FK → `platform_admins.id`), `created_at`,
  `updated_at`
- One active config at a time: `ux_platform_email_provider_config_active` partial unique
  index on `WHERE is_active`. Reconfiguring deactivates the prior row and inserts a fresh
  one, same convention as `platform_ai_provider_config`/`ai_provider_connections`.
- Deliberately a separate table from `email_provider_connections`, not a nullable
  `account_id` on it: that table's uniqueness is `(account_id, provider) WHERE
  is_active`, and Postgres treats `NULL account_id` values as always-distinct from each
  other, so a nullable-`account_id` reuse would not actually enforce "one active platform
  config" the way a dedicated `WHERE is_active` index does. It also carries account-only
  columns (`webhook_username`/`webhook_password_encrypted`, `SenderIdentity` linkage)
  that don't apply at platform level, and its RBAC is account-scoped
  (`integrations.manage`) rather than platform-scoped. The application code still reuses
  everything reusable: the same `provider` vocabulary and the same
  `integrations/smtp_transport.py` `send_email`/`test_connection` functions — no new
  Postmark HTTP-API adapter, Postmark is used purely as an SMTP relay via its Server API
  Token as both username and password.
- Resolution order at send time (`notifications/email.py`): this table's active row, else
  the legacy `.env` `PLATFORM_SMTP_*` settings, else skip sending (logged) — never a hard
  failure, matching the "best-effort, never blocks the caller" contract
  `send_verification_email` already had.

## Slice 7 entities (full detail)

Per `DEC-GRX-029`/`DEC-GRX-030`. Module ownership follows
[MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md): `billing`. Full
narrative design (billing flow, atomic quota evaluator, webhook event mapping,
platform-admin overrides, coupon engine, AI-credit-metering/BYO-bypass interaction) is
in [BILLING_SYSTEM_ARCHITECTURE.md](../04-architecture/BILLING_SYSTEM_ARCHITECTURE.md)
— this section is the entity summary; see `DATABASE_SCHEMA.md §Slice 7` for full
column-level detail.

### `subscription_plans`

- Purpose: the platform-wide plan catalog — one row per tier (`free`/`starter`/`pro`/
  `enterprise` are the four seeded rows; a platform admin can create genuinely new
  tiers beyond these four via `POST /platform/subscription-plans`, `GRX-SAAS-006`),
  create/editable by a platform admin (`platform.billing.manage`) without a redeploy,
  same "DB-backed admin-editable setting" pattern `platform_ai_provider_config`
  established in Slice 6.
- Primary key: `id` (UUID)
- Required fields: `slug` (unique; CHECK is a plain format check —
  `slug ~ '^[a-z0-9_-]+$'` — not a fixed whitelist, since `GRX-SAAS-006`'s migration
  `e3e939e991f4` widened it specifically to allow new tiers; immutable once created,
  since it's referenced by string literal elsewhere, e.g. the Free-plan bootstrap
  lookup), `name`
- Optional fields: `price_usd`/`price_inr` (nullable — `NULL` for Enterprise's
  contact-sales tier, no fixed self-serve price), `max_contacts`/`max_monthly_emails`/
  `max_monthly_ai_runs`/`max_social_accounts`/`max_user_seats` (nullable — `NULL` =
  unlimited), `allow_byo_ai_key`/`allow_byo_smtp`/`audit_export_enabled`/
  `audit_api_enabled` (booleans), `razorpay_plan_id_usd`/`razorpay_plan_id_inr`
  (nullable — the Razorpay Plan object to attach a new subscription to; `NULL` for
  Free/Enterprise, neither of which self-serve-checkouts through Razorpay)

### `account_subscriptions`

- Purpose: one row per account (created automatically at registration, `GRX-BILL-003`),
  tracking the active plan, billing status, currency, and a running counter for the
  current period's metered usage (email sends, AI runs) — the counter the atomic quota
  evaluator reads and locks (`with_for_update`) on every metered call.
- Primary key: `id` (UUID)
- Required fields: `account_id` (FK → `accounts.id` CASCADE, **unique** — exactly one
  row per account, never zero, never more than one), `plan_id` (FK →
  `subscription_plans.id`), `status` (`CHECK IN ('PENDING', 'ACTIVE', 'PAST_DUE',
  'CANCELED', 'HALTED')`), `currency` (`CHECK IN ('USD', 'INR')`),
  `current_period_start`/`current_period_end`, `period_email_used`/`period_ai_used`
  (default `0`, reset to `0` on each `subscription.charged` webhook)
- Optional fields: `razorpay_customer_id`/`razorpay_subscription_id` (nullable — `NULL`
  for accounts on an admin-assigned plan with no real Razorpay object, e.g. most
  Enterprise accounts), `set_by_platform_admin_id` (FK → `platform_admins.id`,
  nullable — set when the current plan came from an admin override, not a real
  checkout)
- `PENDING` (`GRX-BILL-004`): set the instant `POST /billing/subscribe` creates the
  Razorpay Subscription and stores its id, before the customer completes Razorpay's
  Checkout widget — required because the webhook handler looks up this row by
  `razorpay_subscription_id`, which must already be populated when
  `subscription.activated`/`charged` arrives. `plan_id`/`currency` point at the
  *target* plan while `PENDING`, but nothing is granted; the quota evaluator
  (`GRX-BILL-005`) must only honor `ACTIVE`/`PAST_DUE`.

### `credit_packs`

- Purpose: the platform-wide top-up catalog — one row per purchasable credit pack
  (e.g. "250 AI Runs"), editable by a platform admin (`platform.billing.manage`)
  without a redeploy, the same admin-editable-table shape as `subscription_plans`
  above (a priced catalog, not developer-authored text — corrected during
  `GRX-BILL-004` from an earlier code-defined-dict draft).
- Primary key: `id` (UUID)
- Required fields: `slug` (unique), `name`, `credit_type` (`CHECK IN ('AI_RUNS',
  'EMAIL_SENDS', 'CONTACT_SLOTS', 'SOCIAL_POSTS')`), `credits` (int), `is_active`
  (default `true`)
- Optional fields: `price_usd`/`price_inr` (nullable — `NULL` for a currency not yet
  priced; today every seeded pack has `price_usd = NULL` since international payments
  aren't yet approved on the Razorpay account, `BILLING_SYSTEM_ARCHITECTURE.md §8`)
- Read by `billing/repositories.py`'s `get_credit_pack_by_slug` (filtered to
  `is_active`) at checkout time (`POST /billing/topup`); no FK relationship to any
  other billing table — a purchase against it is only ever recorded in
  `account_credit_purchases`/`account_credit_balances` via the `payment.captured`
  webhook, keyed by the pack's `credit_type`/`credits`, not by a foreign key.

### `account_credit_balances`

- Purpose: the number the quota evaluator actually reads once the monthly plan
  allowance is exhausted — one running, non-expiring balance per account per credit
  type (`DEC-GRX-030`: credits never expire, no per-purchase-batch FIFO).
- Primary key: `id` (UUID)
- Required fields: `account_id` (FK → `accounts.id` CASCADE), `credit_type` (`CHECK IN
  ('AI_RUNS', 'EMAIL_SENDS', 'CONTACT_SLOTS', 'SOCIAL_POSTS')`), `remaining_credits`
  (default `0`)
- Constraint: unique on `(account_id, credit_type)` — the atomic
  `UPDATE ... WHERE remaining_credits >= :needed` this table exists for depends on
  there being exactly one row per account per credit type.

### `account_credit_purchases`

- Purpose: receipt/audit history of individual top-up purchases and admin-granted
  credits. **Never read by the quota evaluator** — purely a record; `remaining_credits`
  above is the only value that gates anything.
- Primary key: `id` (UUID)
- Required fields: `account_id` (FK → `accounts.id` CASCADE), `credit_type`,
  `credits_added`, `purchased_at`
- Optional fields: `razorpay_payment_id` (nullable, **unique** when set — the
  idempotency guard against webhook replay, `THREAT_MODEL.md` T61; `NULL` for an
  admin-granted credit rather than a real purchase), `granted_by_platform_admin_id`
  (FK → `platform_admins.id`, nullable — set when `razorpay_payment_id` is `NULL`)

### `coupon_codes` / `coupon_redemptions`

- Purpose: platform-admin-managed discount/free-credit codes, redeemable once per
  account.
- `coupon_codes`: `id` (UUID PK), `code` (unique text, e.g. `WELCOME20`),
  `discount_type` (`CHECK IN ('PERCENTAGE', 'FIXED_AMOUNT', 'CREDIT_GRANT')`),
  `discount_value` (numeric — meaning depends on `discount_type`), `credit_type`
  (nullable, only set when `discount_type = 'CREDIT_GRANT'`), `applicable_plan_slugs`
  (JSONB array, nullable — `NULL` = all plans), `max_redemptions` (nullable —
  `NULL` = unlimited), `redemption_count` (default `0`), `expires_at` (nullable),
  `is_active` (default `true`), `created_by_platform_admin_id` (FK →
  `platform_admins.id`)
- `coupon_redemptions`: `id` (UUID PK), `coupon_code_id` (FK → `coupon_codes.id`),
  `account_id` (FK → `accounts.id`), `redeemed_at`. Unique on
  `(coupon_code_id, account_id)` — the one-redemption-per-account enforcement
  (`THREAT_MODEL.md` T65).

## Full MVP entity landscape (target slice)

Entities beyond Slice 5/6/7 are named here for continuity with `docs/02-features/` and
future `docs/06-api/` work, but are **not** designed in field-level detail until the slice
that needs them. Slice 3/5/6/7's own entities moved to full detail above; `campaign_schedules`
stays here since it's Slice 4:

| Entity group | Target slice | Notes |
|---|---|---|
| `campaign_schedules` | Slice 4 | Scheduled Email — future send-time, cancellation, scheduling-specific retry |
| `notifications` | Slice 1 stub, still no real writer after Slice 3 | Notification center |
| `webhook_endpoints`, `webhook_events`, `webhook_deliveries` | Deferred indefinitely — see Slice 3's "explicitly deferred" note | Only revisit with a second email/social provider |
| `analytics_events` | Deferred — see Slice 3's "explicitly deferred" note | Read-side aggregation, computed from existing tables for now |
| `system_settings` | Sprint 1 (minimal), expanded over time | |
| `automation_workflows`, `workflow_versions`, `workflow_nodes`, `workflow_edges`, `workflow_executions`, `workflow_step_executions` | Out of MVP ([OQ-012](../00-project-control/OPEN_QUESTIONS.md)) | Not scheduled |

SEO/AEO/GEO-track entities (crawl snapshots, findings, agent runs, etc.) are intentionally
excluded from this document — see
[FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md) instead.
