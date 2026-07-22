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

## Full MVP entity landscape (target slice)

Entities beyond Sprint 1 are named here for continuity with `docs/02-features/` and future
`docs/06-api/` work, but are **not** designed in field-level detail until the slice that
needs them:

| Entity group | Target slice | Notes |
|---|---|---|
| `contacts`, `contact_custom_fields`, `contact_field_values`, `tags`, `contact_tags`, `contact_lists`, `contact_list_members`, `segments`, `segment_rules`, `contact_imports`, `contact_import_rows`, `consent_records`, `suppression_entries` | Slice 2 | Contact & Audience Management |
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
