# Data Model

- Document ID: DOC-DATA-MODEL
- Status: ACTIVE
- Version: 1.2
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
- Status values: `ACTIVE`, `DISABLED`
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
- Required fields: `email` (citext, **unique** — one active suppression per address),
  `reason` (`UNSUBSCRIBED` | `BOUNCED` | `COMPLAINED` | `MANUAL`), `suppressed_at`
  (default `now()`)
- Optional fields: `contact_id` (nullable FK → `contacts.id` — an address can be
  suppressed even with no matching contact record, e.g. a hard bounce), `suppressed_by_user_id`
  (nullable FK → `users.id`)
- Re-suppressing an already-suppressed email updates `reason`/`suppressed_at` in place
  (upsert on the unique `email` index), it does not create a second row.

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

## Full MVP entity landscape (target slice)

Entities beyond Slice 3 are named here for continuity with `docs/02-features/` and future
`docs/06-api/` work, but are **not** designed in field-level detail until the slice that
needs them. Slice 3's own entities moved to full detail above; `campaign_schedules` stays
here since it's Slice 4:

| Entity group | Target slice | Notes |
|---|---|---|
| `campaign_schedules` | Slice 4 | Scheduled Email — future send-time, cancellation, scheduling-specific retry |
| `social_provider_connections`, `social_accounts`, `social_posts`, `social_post_targets`, `social_post_media`, `social_publish_attempts`, `content_calendar_items` | Slice 5 | Social Media Automation |
| `ai_prompt_templates`, `ai_prompt_versions`, `ai_generations`, `ai_usage_events` | Slice 6 | AI Content Assistant |
| `notifications` | Slice 1 stub, still no real writer after Slice 3 | Notification center |
| `files` | Slice 5 | Media storage, once object storage provider is chosen ([OQ-005](../00-project-control/OPEN_QUESTIONS.md)) |
| `webhook_endpoints`, `webhook_events`, `webhook_deliveries` | Deferred indefinitely — see Slice 3's "explicitly deferred" note | Only revisit with a second email/social provider |
| `feature_entitlements` | Alongside `usage_records`, expanded when a real limit needs enforcing | |
| `analytics_events` | Deferred — see Slice 3's "explicitly deferred" note | Read-side aggregation, computed from existing tables for now |
| `system_settings` | Sprint 1 (minimal), expanded over time | |
| `automation_workflows`, `workflow_versions`, `workflow_nodes`, `workflow_edges`, `workflow_executions`, `workflow_step_executions` | Out of MVP ([OQ-012](../00-project-control/OPEN_QUESTIONS.md)) | Not scheduled |

SEO/AEO/GEO-track entities (crawl snapshots, findings, agent runs, etc.) are intentionally
excluded from this document — see
[FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md) instead.
