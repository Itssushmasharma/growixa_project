# Data Model

- Document ID: DOC-DATA-MODEL
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
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

## Full MVP entity landscape (target slice)

Entities beyond Slice 2 are named here for continuity with `docs/02-features/` and future
`docs/06-api/` work, but are **not** designed in field-level detail until the slice that
needs them:

| Entity group | Target slice | Notes |
|---|---|---|
| `email_provider_connections`, `sender_identities`, `email_templates`, `email_template_versions`, `campaigns`, `campaign_versions`, `campaign_recipients`, `campaign_schedules`, `message_deliveries`, `delivery_attempts`, `email_events`, `unsubscribe_events` | Slice 3–4 | Email Marketing |
| `social_provider_connections`, `social_accounts`, `social_posts`, `social_post_targets`, `social_post_media`, `social_publish_attempts`, `content_calendar_items` | Slice 5 | Social Media Automation |
| `ai_prompt_templates`, `ai_prompt_versions`, `ai_generations`, `ai_usage_events` | Slice 6 | AI Content Assistant |
| `notifications` | Slice 1 stub, real writers from Slice 3+ | Notification center |
| `files` | Slice 5 | Media storage, once object storage provider is chosen ([OQ-005](../00-project-control/OPEN_QUESTIONS.md)) |
| `webhook_endpoints`, `webhook_events`, `webhook_deliveries` | Slice 3+ (email provider webhooks) | |
| `feature_entitlements` | Alongside `usage_records`, expanded when a real limit needs enforcing | |
| `analytics_events` | Slice 3+ | Read-side aggregation |
| `system_settings` | Sprint 1 (minimal), expanded over time | |
| `automation_workflows`, `workflow_versions`, `workflow_nodes`, `workflow_edges`, `workflow_executions`, `workflow_step_executions` | Out of MVP ([OQ-012](../00-project-control/OPEN_QUESTIONS.md)) | Not scheduled |

SEO/AEO/GEO-track entities (crawl snapshots, findings, agent runs, etc.) are intentionally
excluded from this document — see
[FUTURE_SCOPE_SEO_AEO_GEO.md](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md) instead.
