# Database Schema

- Document ID: DOC-DB-SCHEMA
- Status: ACTIVE (extended per slice, not redesigned)
- Version: 1.4
- Last updated: 2026-08-07
- Owner: Coding agent
- Related documents: [DATA_MODEL](DATA_MODEL.md), [ERD](ERD.md), [MIGRATION_STRATEGY](MIGRATION_STRATEGY.md)

This is the implementation-level schema reference for tables created via Alembic
migrations, extended per slice as each one is designed. Column types are PostgreSQL
types. All tables use `uuid` primary keys generated application-side (or via
`gen_random_uuid()`), per the UUID convention in [DATA_MODEL.md](DATA_MODEL.md).

## Sprint 1 (Foundation) tables

## `users`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| email | citext | UNIQUE, NOT NULL |
| password_hash | text | NOT NULL |
| full_name | text | NOT NULL |
| status | text | NOT NULL, CHECK IN ('ACTIVE','DISABLED'), DEFAULT 'ACTIVE' |
| last_login_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique index on `email`.

## `roles`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | UNIQUE, NOT NULL |
| description | text | NULL |

Seed rows: `Super Admin`, `Admin`, `Marketing Manager`, `Content Creator`, `Analyst`, `Viewer`.

## `permissions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| code | text | UNIQUE, NOT NULL |
| description | text | NULL |

Seed rows (Sprint 1 minimum set): `users.manage`, `roles.manage`, `company.settings.edit`,
`company.settings.view`, `audit.view`, `admin.access`. Additional permission codes are added
per module as later slices are built.

## `role_permissions`

| Column | Type | Constraints |
|---|---|---|
| role_id | uuid | PK (composite), FK → roles.id ON DELETE CASCADE |
| permission_id | uuid | PK (composite), FK → permissions.id ON DELETE CASCADE |

## `user_roles`

| Column | Type | Constraints |
|---|---|---|
| user_id | uuid | PK (composite), FK → users.id ON DELETE CASCADE |
| role_id | uuid | PK (composite), FK → roles.id ON DELETE RESTRICT |
| assigned_at | timestamptz | NOT NULL, DEFAULT now() |
| assigned_by_user_id | uuid | FK → users.id, NULL |

## `refresh_tokens`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK → users.id ON DELETE CASCADE, NOT NULL |
| token_hash | text | UNIQUE, NOT NULL |
| issued_at | timestamptz | NOT NULL, DEFAULT now() |
| expires_at | timestamptz | NOT NULL |
| revoked_at | timestamptz | NULL |
| replaced_by_token_id | uuid | FK → refresh_tokens.id, NULL |
| user_agent | text | NULL |
| ip_address | inet | NULL |

Indexes: index on `user_id`; index on `expires_at` (for cleanup jobs); unique index on `token_hash`.

## `password_reset_tokens`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| user_id | uuid | FK → users.id ON DELETE CASCADE, NOT NULL |
| token_hash | text | UNIQUE, NOT NULL |
| expires_at | timestamptz | NOT NULL |
| used_at | timestamptz | NULL |

Indexes: index on `user_id`.

## `user_invitations`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| email | citext | NOT NULL |
| token_hash | text | UNIQUE, NOT NULL |
| role_id | uuid | FK → roles.id, NOT NULL |
| invited_by_user_id | uuid | FK → users.id, NOT NULL |
| expires_at | timestamptz | NOT NULL |
| accepted_at | timestamptz | NULL |

Indexes: index on `email`; partial index on `accepted_at IS NULL` for pending-invite lookups.

## `company_profile`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| logo_url | text | NULL |
| website | text | NULL |
| industry | text | NULL |
| timezone | text | NULL |
| default_language | text | NOT NULL, DEFAULT 'en' |
| legal_footer | text | NULL |
| contact_details | jsonb | NOT NULL, DEFAULT '{}' |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Application-level constraint: exactly one row (enforced in `company` service, not a DB
constraint, since the table starts empty pre-onboarding).

## `brand_profiles`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| company_id | uuid | FK → company_profile.id ON DELETE CASCADE, NOT NULL |
| brand_voice | text | NULL |
| forbidden_claims | jsonb | NOT NULL, DEFAULT '[]' |
| required_facts | jsonb | NOT NULL, DEFAULT '[]' |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

## `audit_logs`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| actor_user_id | uuid | FK → users.id, NULL (system events) |
| action | text | NOT NULL |
| entity_type | text | NOT NULL |
| entity_id | uuid | NULL |
| metadata | jsonb | NOT NULL, DEFAULT '{}' |
| ip_address | inet | NULL |
| user_agent | text | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `(entity_type, entity_id)`; index on `actor_user_id`; index on `created_at`
(for time-range queries and future retention jobs). No UPDATE/DELETE grants at the
application layer — insert-only table.

## `usage_records`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| operation_type | text | NOT NULL |
| quantity | numeric | NOT NULL |
| unit | text | NOT NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| metadata | jsonb | NOT NULL, DEFAULT '{}' |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `(operation_type, created_at)` for future usage aggregation queries.

## Slice 2 (Contacts) tables

## `contacts`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| email | citext | UNIQUE, NOT NULL |
| first_name | text | NULL |
| last_name | text | NULL |
| phone | text | NULL |
| status | text | NOT NULL, CHECK IN ('ACTIVE','ARCHIVED'), DEFAULT 'ACTIVE' |
| source | text | NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique index on `email`; index on `status` (list/segment filtering).

## `contact_custom_fields`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| key | text | UNIQUE, NOT NULL |
| label | text | NOT NULL |
| field_type | text | NOT NULL, CHECK IN ('TEXT','NUMBER','DATE','BOOLEAN') |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

## `contact_field_values`

| Column | Type | Constraints |
|---|---|---|
| contact_id | uuid | PK (composite), FK → contacts.id ON DELETE CASCADE |
| field_id | uuid | PK (composite), FK → contact_custom_fields.id ON DELETE CASCADE |
| value | text | NULL |

## `tags`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | UNIQUE, NOT NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

## `contact_tags`

| Column | Type | Constraints |
|---|---|---|
| contact_id | uuid | PK (composite), FK → contacts.id ON DELETE CASCADE |
| tag_id | uuid | PK (composite), FK → tags.id ON DELETE CASCADE |

## `contact_lists`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| description | text | NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

## `contact_list_members`

| Column | Type | Constraints |
|---|---|---|
| list_id | uuid | PK (composite), FK → contact_lists.id ON DELETE CASCADE |
| contact_id | uuid | PK (composite), FK → contacts.id ON DELETE CASCADE |
| added_at | timestamptz | NOT NULL, DEFAULT now() |

## `segments`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| type | text | NOT NULL, CHECK IN ('DYNAMIC','SAVED') |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

## `segment_rules`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| segment_id | uuid | FK → segments.id ON DELETE CASCADE, NOT NULL |
| field | text | NOT NULL |
| operator | text | NOT NULL |
| value | text | NOT NULL |

Indexes: index on `segment_id`.

## `segment_members`

| Column | Type | Constraints |
|---|---|---|
| segment_id | uuid | PK (composite), FK → segments.id ON DELETE CASCADE |
| contact_id | uuid | PK (composite), FK → contacts.id ON DELETE CASCADE |
| captured_at | timestamptz | NOT NULL, DEFAULT now() |

Used only for `segments.type = 'SAVED'`; empty for `'DYNAMIC'`.

## `contact_imports`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| file_name | text | NOT NULL |
| status | text | NOT NULL, CHECK IN ('PENDING','VALIDATING','IMPORTING','COMPLETED','FAILED'), DEFAULT 'PENDING' |
| total_rows | integer | NULL |
| imported_count | integer | NOT NULL, DEFAULT 0 |
| skipped_count | integer | NOT NULL, DEFAULT 0 |
| error_count | integer | NOT NULL, DEFAULT 0 |
| column_mapping | jsonb | NOT NULL, DEFAULT '{}' |
| created_by_user_id | uuid | FK → users.id, NOT NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| completed_at | timestamptz | NULL |

## `contact_import_rows`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| import_id | uuid | FK → contact_imports.id ON DELETE CASCADE, NOT NULL |
| row_number | integer | NOT NULL |
| raw_data | jsonb | NOT NULL |
| status | text | NOT NULL, CHECK IN ('PENDING','IMPORTED','SKIPPED','ERROR'), DEFAULT 'PENDING' |
| error_message | text | NULL |
| contact_id | uuid | FK → contacts.id, NULL |

Indexes: index on `import_id`.

## `consent_records`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| contact_id | uuid | FK → contacts.id ON DELETE CASCADE, NOT NULL |
| channel | text | NOT NULL, CHECK IN ('EMAIL','SMS') |
| status | text | NOT NULL, CHECK IN ('GRANTED','WITHDRAWN','UNKNOWN'), DEFAULT 'UNKNOWN' |
| source | text | NULL |
| recorded_at | timestamptz | NOT NULL, DEFAULT now() |
| recorded_by_user_id | uuid | FK → users.id, NULL |

Indexes: index on `(contact_id, channel, recorded_at)` — current status is the latest row
per `(contact_id, channel)`. No UPDATE/DELETE grants at the application layer —
insert-only, same pattern as `audit_logs`.

## `suppression_entries`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| email | citext | UNIQUE, NOT NULL |
| reason | text | NOT NULL, CHECK IN ('UNSUBSCRIBED','BOUNCED','COMPLAINED','MANUAL') |
| contact_id | uuid | FK → contacts.id, NULL |
| suppressed_at | timestamptz | NOT NULL, DEFAULT now() |
| suppressed_by_user_id | uuid | FK → users.id, NULL |

Indexes: unique index on `email` (upsert target — re-suppressing updates the existing row).

## Slice 3 (Email Marketing) tables

## `email_provider_connections`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| provider | text | NOT NULL, CHECK IN ('POSTMARK', 'CUSTOM_SMTP') |
| smtp_host | text | NOT NULL |
| smtp_port | integer | NOT NULL |
| smtp_username | text | NOT NULL |
| smtp_password_encrypted | text | NOT NULL |
| webhook_username | text | NULL |
| webhook_password_encrypted | text | NULL |
| is_active | boolean | NOT NULL, DEFAULT true |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `ux_email_provider_connections_active_per_provider`, a **unique** partial index
on `(provider) WHERE is_active` (GRX-EMAIL-011 / DEC-GRX-016) — DB-enforces at most one
active connection per provider; replaces the earlier non-unique `(is_active)` partial
index from when there was only ever one provider. `smtp_password_encrypted` and
`webhook_password_encrypted` are Fernet-encrypted application-side before insert — never
plaintext columns, never selected into a log statement. `webhook_username`/
`webhook_password_encrypted` (added by `GRX-EMAIL-005`, per `THREAT_MODEL.md`'s T14) are
only ever consulted for the active `POSTMARK` connection, by `POST /webhooks/postmark` —
`CUSTOM_SMTP` connections get them generated too (for schema uniformity) but nothing
reads them, since plain SMTP has no webhook mechanism.

## `sender_identities`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| email_provider_connection_id | uuid | FK → email_provider_connections.id, NOT NULL |
| from_email | citext | NOT NULL |
| from_name | text | NOT NULL |
| reply_to_email | citext | NULL |
| verification_status | text | NOT NULL, CHECK IN ('PENDING','VERIFIED','FAILED'), DEFAULT 'PENDING' |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

## `email_templates`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

## `email_template_versions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| template_id | uuid | FK → email_templates.id ON DELETE CASCADE, NOT NULL |
| version_number | integer | NOT NULL |
| subject | text | NOT NULL |
| body_html | text | NOT NULL |
| body_text | text | NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique index on `(template_id, version_number)`. No UPDATE/DELETE grants at the
application layer — insert-only, same pattern as `consent_records`.

## `campaigns`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| subject | text | NOT NULL |
| body_html | text | NOT NULL |
| body_text | text | NULL |
| template_id | uuid | FK → email_templates.id, NULL |
| sender_identity_id | uuid | FK → sender_identities.id, NOT NULL |
| recipient_type | text | NOT NULL, CHECK IN ('SEGMENT','LIST','ALL_CONTACTS') |
| recipient_segment_id | uuid | FK → segments.id, NULL |
| recipient_list_id | uuid | FK → contact_lists.id, NULL |
| status | text | NOT NULL, CHECK IN ('DRAFT','SENDING','SENT','FAILED'), DEFAULT 'DRAFT' |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |
| sent_at | timestamptz | NULL |

Constraints: application-layer check that exactly one of `recipient_segment_id` /
`recipient_list_id` is set per `recipient_type` (not a DB CHECK constraint — mirrors how
`contact_imports`' `column_mapping` validation lives in the service layer, not SQL).

## `campaign_versions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| campaign_id | uuid | FK → campaigns.id, NOT NULL |
| subject | text | NOT NULL |
| body_html | text | NOT NULL |
| body_text | text | NULL |
| recipient_count | integer | NOT NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `campaign_id`. Exactly one row per campaign, written when sending
starts — not one row per draft edit.

## `campaign_recipients`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| campaign_id | uuid | FK → campaigns.id ON DELETE CASCADE, NOT NULL |
| contact_id | uuid | FK → contacts.id, NOT NULL |
| email | citext | NOT NULL |
| status | text | NOT NULL, CHECK IN ('PENDING','SENT','FAILED','SUPPRESSED'), DEFAULT 'PENDING' |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `(campaign_id, status)`.

## `message_deliveries`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| campaign_recipient_id | uuid | FK → campaign_recipients.id ON DELETE CASCADE, NOT NULL |
| provider_message_id | text | NULL |
| status | text | NOT NULL, CHECK IN ('QUEUED','SENT','DELIVERED','BOUNCED','COMPLAINED','FAILED'), DEFAULT 'QUEUED' |
| sent_at | timestamptz | NULL |
| delivered_at | timestamptz | NULL |
| bounced_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `provider_message_id` (webhook lookups arrive keyed by this).

## `delivery_attempts`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| message_delivery_id | uuid | FK → message_deliveries.id ON DELETE CASCADE, NOT NULL |
| attempt_number | integer | NOT NULL |
| status | text | NOT NULL |
| error_message | text | NULL |
| attempted_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `message_delivery_id`.

## `email_events`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| message_delivery_id | uuid | FK → message_deliveries.id ON DELETE CASCADE, NOT NULL |
| event_type | text | NOT NULL, CHECK IN ('DELIVERED','OPENED','CLICKED','BOUNCED','COMPLAINED') |
| occurred_at | timestamptz | NOT NULL |
| metadata | jsonb | NOT NULL, DEFAULT '{}' |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `message_delivery_id`. No UPDATE/DELETE grants at the application
layer — insert-only, same pattern as `audit_logs`.

## `unsubscribe_events`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| contact_id | uuid | FK → contacts.id, NULL |
| campaign_id | uuid | FK → campaigns.id, NULL |
| email | citext | NOT NULL |
| occurred_at | timestamptz | NOT NULL, DEFAULT now() |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: index on `email`.

## Sprint 5 Phase B (Platform auth boundary) tables

Deliberately not scoped by `account_id` — see [DATA_MODEL.md §Sprint 5 Phase B
entities](DATA_MODEL.md#sprint-5-phase-b-entities-customer-account-platform--platform-auth-boundary-full-detail)
and [DEC-GRX-018](../00-project-control/DECISIONS.md).

## `platform_admins`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| email | citext | UNIQUE, NOT NULL |
| password_hash | text | NOT NULL |
| full_name | text | NOT NULL |
| role | text | NOT NULL, CHECK IN ('platform.owner','platform.admin','platform.support','platform.finance','platform.operations') |
| status | text | NOT NULL, CHECK IN ('ACTIVE','DISABLED'), DEFAULT 'ACTIVE' |
| last_login_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique index on `email`. No `account_id` column — platform admins are not
account-owned data, deliberately outside `GRX-SAAS-001`'s isolation retrofit.

## `platform_permissions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| code | text | UNIQUE, NOT NULL |
| description | text | NULL |

Seed rows (Phase B minimum): `platform.access`. Additional codes are added per Phase E
feature as it's built, same convention as `permissions`.

## `platform_role_permissions`

| Column | Type | Constraints |
|---|---|---|
| role | text | PK (composite), CHECK IN the same five values as `platform_admins.role` |
| permission_id | uuid | PK (composite), FK → platform_permissions.id ON DELETE CASCADE |

Seed rows (Phase B minimum): all five roles → `platform.access`.

## Sprint 5 Phase C (Self-service registration) tables

`accounts` gains one column here (`selected_plan_slug`); `users` gains one CHECK value
(`PENDING_VERIFICATION`) — both documented in place below, alongside the one new table.
See [DATA_MODEL.md §Sprint 5 Phase C entities](DATA_MODEL.md#sprint-5-phase-c-entities-customer-account-platform--self-service-registration-full-detail)
and [DECISIONS.md §DEC-GRX-019](../00-project-control/DECISIONS.md).

## `accounts` (documented here for the first time — see DATA_MODEL.md's note)

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| name | text | NOT NULL |
| status | text | NOT NULL, CHECK IN ('ACTIVE','SUSPENDED','CLOSED'), DEFAULT 'ACTIVE' |
| selected_plan_slug | text | NULL, CHECK IN ('free', 'starter', 'pro') — registration-time intent signal only, not real entitlement (see `account_subscriptions` below) |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

The speculative `plan_id` column reserved for Phase D (added in `3186b6c66a6d`, never used) is
**dropped** by `GRX-BILL-002`'s migration — real entitlement lives in
`account_subscriptions.plan_id` below instead, which needs `status`/`currency`/period
counters/Razorpay IDs that don't belong on the core `accounts` identity table.

## `account_verification_tokens`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| user_id | uuid | FK → users.id ON DELETE CASCADE, NOT NULL |
| token_hash | text | UNIQUE, NOT NULL |
| expires_at | timestamptz | NOT NULL |
| used_at | timestamptz | NULL |

## `users` (amended)

`status`'s CHECK constraint becomes `IN ('ACTIVE', 'DISABLED', 'PENDING_VERIFICATION')` —
see the Sprint 1 `users` table above for the rest of its columns, unchanged.

## Sprint 5 Phase E (Secure support session, `GRX-SAAS-010`) tables

See [DATA_MODEL.md §Sprint 5 Phase E entities (Secure support session)](DATA_MODEL.md#sprint-5-phase-e-entities-customer-account-platform--secure-support-session-grx-saas-010)
and [DECISIONS.md §DEC-GRX-022](../00-project-control/DECISIONS.md).

## `support_sessions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| platform_admin_id | uuid | FK → platform_admins.id ON DELETE RESTRICT, NOT NULL |
| reason | text | NOT NULL |
| ticket_number | text | NOT NULL |
| access_level | text | NOT NULL, CHECK IN ('READ','WRITE'), DEFAULT 'READ' |
| started_at | timestamptz | NOT NULL, DEFAULT now() |
| expires_at | timestamptz | NOT NULL |
| ended_at | timestamptz | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`, `platform_admin_id`; a partial index on `account_id WHERE ended_at
IS NULL` to make the customer-facing "is a session currently active on my account" check
(T42) cheap. Two new `platform_permissions` seed rows in the same migration:
`platform.support_session.create` (all of `platform.owner`/`platform.admin`/`platform.support`)
and `platform.support_session.write` (`platform.owner`/`platform.admin` only).

## Slice 5 (Social Publishing) tables

See [DATA_MODEL.md §Slice 5 entities](DATA_MODEL.md#slice-5-entities-full-detail) and
[DECISIONS.md §DEC-GRX-023/024/025](../00-project-control/DECISIONS.md).

## `social_connections`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| provider | text | NOT NULL, CHECK IN ('INSTAGRAM_BUSINESS') |
| ig_business_account_id | text | NOT NULL |
| ig_username | text | NULL |
| facebook_page_id | text | NOT NULL |
| access_token_encrypted | text | NOT NULL |
| token_expires_at | timestamptz | NULL |
| is_active | boolean | NOT NULL, DEFAULT true |
| last_connected_at | timestamptz | NOT NULL, DEFAULT now() |
| last_error | text | NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`; unique partial index `ux_social_connections_active_per_provider` on
`(account_id, provider) WHERE is_active`. Same migration seeds `social.manage` /
`social.publish` / `social.view` permission codes and their role grants (see
[RBAC.md](../08-security/RBAC.md)).

## `social_posts`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| social_connection_id | uuid | FK → social_connections.id, NOT NULL |
| caption | text | NOT NULL, DEFAULT '' |
| status | text | NOT NULL, CHECK IN ('DRAFT','SCHEDULED','DISPATCHING','PUBLISHING','PUBLISHED','CANCELLED','FAILED'), DEFAULT 'DRAFT' |
| scheduled_at | timestamptz | NULL |
| cancelled_at | timestamptz | NULL |
| published_at | timestamptz | NULL |
| idempotency_key | uuid | NOT NULL, UNIQUE, DEFAULT gen_random_uuid() |
| ig_media_id | text | NULL |
| ig_permalink | text | NULL |
| last_error | text | NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`; composite `(status, scheduled_at)` for the scheduler's claim query
— same rationale as `ix_campaigns_status_scheduled_at`.

## `social_post_media`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| social_post_id | uuid | FK → social_posts.id ON DELETE CASCADE, NOT NULL |
| media_type | text | NOT NULL, CHECK IN ('IMAGE') |
| storage_path | text | NOT NULL |
| public_url | text | NOT NULL |
| position | integer | NOT NULL, DEFAULT 0 |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`, `social_post_id`.

## `social_post_versions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| social_post_id | uuid | FK → social_posts.id, NOT NULL |
| caption | text | NOT NULL |
| media_snapshot | jsonb | NOT NULL |
| ig_media_id | text | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`, `social_post_id`.

## Slice 6 (AI Assistant) tables

See [DATA_MODEL.md §Slice 6 entities](DATA_MODEL.md#slice-6-entities-full-detail) and
[DECISIONS.md §DEC-GRX-026/027/028](../00-project-control/DECISIONS.md).

## `ai_generations`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| created_by_user_id | uuid | FK → users.id, NULL |
| capability | text | NOT NULL, CHECK IN ('SUBJECT_LINE','BODY_COPY','SOCIAL_CAPTION','REWRITE','HASHTAGS','POSTING_TIME') |
| prompt_template_key | text | NOT NULL |
| input_context | jsonb | NOT NULL |
| output | jsonb | NULL |
| provider | text | NOT NULL |
| model | text | NOT NULL |
| prompt_tokens | integer | NULL |
| completion_tokens | integer | NULL |
| estimated_cost_usd | numeric | NULL |
| status | text | NOT NULL, CHECK IN ('COMPLETE','FAILED') |
| error_message | text | NULL |
| linked_entity_type | text | NULL |
| linked_entity_id | uuid | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`; `(account_id, capability)` for history filtering. Same migration
seeds `ai.manage` / `ai.view` (customer RBAC) and `platform.ai.manage` (platform RBAC)
permission codes and their role grants (see [RBAC.md](../08-security/RBAC.md)).

## `ai_provider_connections`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| provider | text | NOT NULL, CHECK IN ('OPENAI','AZURE_OPENAI','ANTHROPIC','OLLAMA') |
| api_key_encrypted | text | NULL |
| base_url | text | NULL |
| default_model | text | NOT NULL |
| is_active | boolean | NOT NULL, DEFAULT true |
| created_by_user_id | uuid | FK → users.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: `account_id`; unique partial index
`ux_ai_provider_connections_active_per_account` on `(account_id) WHERE is_active`.

## `platform_ai_provider_config`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| provider | text | NOT NULL, CHECK IN ('OPENAI','AZURE_OPENAI','ANTHROPIC','OLLAMA') |
| api_key_encrypted | text | NULL |
| base_url | text | NULL |
| default_model | text | NOT NULL |
| is_active | boolean | NOT NULL, DEFAULT true |
| created_by_platform_admin_id | uuid | FK → platform_admins.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique partial index `ux_platform_ai_provider_config_active` on `WHERE
is_active`.

## Slice 7 (Billing) tables

See [DATA_MODEL.md §Slice 7 entities](DATA_MODEL.md#slice-7-entities-full-detail),
[BILLING_SYSTEM_ARCHITECTURE.md](../04-architecture/BILLING_SYSTEM_ARCHITECTURE.md), and
[DECISIONS.md §DEC-GRX-029/030](../00-project-control/DECISIONS.md).

## `subscription_plans`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| slug | text | NOT NULL, UNIQUE, CHECK `slug ~ '^[a-z0-9_-]+$'` |
| name | text | NOT NULL |
| price_usd | numeric(10,2) | NULL |
| price_inr | numeric(10,2) | NULL |
| max_contacts | integer | NULL |
| max_monthly_emails | integer | NULL |
| max_monthly_ai_runs | integer | NULL |
| max_social_accounts | integer | NULL |
| max_user_seats | integer | NULL |
| allow_byo_ai_key | boolean | NOT NULL, DEFAULT false |
| allow_byo_smtp | boolean | NOT NULL, DEFAULT false |
| audit_export_enabled | boolean | NOT NULL, DEFAULT false |
| audit_api_enabled | boolean | NOT NULL, DEFAULT false |
| razorpay_plan_id_usd | text | NULL |
| razorpay_plan_id_inr | text | NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Migration `e3e939e991f4` (`GRX-SAAS-006`) widened `slug`'s CHECK from a fixed 4-value
whitelist (`IN ('free','starter','pro','enterprise')`) to this plain format check — a
platform admin can genuinely create new tiers via `POST /platform/subscription-plans`
now, not just edit the four seeded ones.

Same migration seeds `billing.manage`/`billing.view` (customer RBAC) and
`platform.billing.manage` (platform RBAC) permission codes, their role grants, and the
four `subscription_plans` rows (`free`/`starter`/`pro`/`enterprise` — see
`BILLING_SYSTEM_ARCHITECTURE.md §2` for the working-draft quota/price values).

## `credit_packs`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| slug | text | NOT NULL, UNIQUE |
| name | text | NOT NULL |
| credit_type | text | NOT NULL, CHECK IN ('AI_RUNS','EMAIL_SENDS','CONTACT_SLOTS','SOCIAL_POSTS') |
| credits | integer | NOT NULL |
| price_usd | numeric(10,2) | NULL |
| price_inr | numeric(10,2) | NULL |
| is_active | boolean | NOT NULL, DEFAULT true |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Migration `b6eed962fd56` (`GRX-BILL-004`) seeds five draft packs, all with
`price_usd = NULL` — international payments aren't yet approved on the Razorpay
account (`BILLING_SYSTEM_ARCHITECTURE.md §8`). Read by `get_credit_pack_by_slug`
(filtered to `is_active`) at `POST /billing/topup` checkout time; no FK from any other
billing table.

## `account_subscriptions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL, UNIQUE |
| plan_id | uuid | FK → subscription_plans.id, NOT NULL |
| status | text | NOT NULL, CHECK IN ('PENDING','ACTIVE','PAST_DUE','CANCELED','HALTED') |
| currency | text | NOT NULL, CHECK IN ('USD','INR') |
| current_period_start | timestamptz | NOT NULL |
| current_period_end | timestamptz | NOT NULL |
| period_email_used | integer | NOT NULL, DEFAULT 0 |
| period_ai_used | integer | NOT NULL, DEFAULT 0 |
| razorpay_customer_id | text | NULL |
| razorpay_subscription_id | text | NULL |
| set_by_platform_admin_id | uuid | FK → platform_admins.id, NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique on `account_id` (exactly one row per account — created automatically at
registration, `GRX-BILL-003`, never left absent per
`BILLING_SYSTEM_ARCHITECTURE.md §3.4`). Every metered request takes
`SELECT ... FOR UPDATE` on this row before reading/writing `period_email_used`/
`period_ai_used`.

Migration `60f7c30ff18a` (`GRX-BILL-004`) added `PENDING` to the `status` CHECK — set
the instant `POST /billing/subscribe` creates the Razorpay Subscription and stores its
id, before the customer completes Razorpay's Checkout widget (the webhook handler looks
up this row by `razorpay_subscription_id`, which must already be populated when
`subscription.activated`/`charged` arrives). `plan_id`/`currency` point at the *target*
plan while `PENDING`; nothing is granted until a webhook moves status to `ACTIVE`. The
quota evaluator (`GRX-BILL-005`) must only honor `ACTIVE`/`PAST_DUE`.

## `account_credit_balances`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| credit_type | text | NOT NULL, CHECK IN ('AI_RUNS','EMAIL_SENDS','CONTACT_SLOTS','SOCIAL_POSTS') |
| remaining_credits | integer | NOT NULL, DEFAULT 0 |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique on `(account_id, credit_type)` — the atomic
`UPDATE ... WHERE remaining_credits >= :needed` the quota evaluator runs depends on this
constraint. Credits never expire (`DEC-GRX-030`); no expiry column by design.

## `account_credit_purchases`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| credit_type | text | NOT NULL |
| credits_added | integer | NOT NULL |
| purchased_at | timestamptz | NOT NULL, DEFAULT now() |
| razorpay_payment_id | text | NULL, UNIQUE (when set) |
| granted_by_platform_admin_id | uuid | FK → platform_admins.id, NULL |

Indexes: `account_id`; unique on `razorpay_payment_id` where not null — the webhook-
replay idempotency guard (`THREAT_MODEL.md` T61). Receipt/audit table only; never read
by the quota evaluator.

## `coupon_codes`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| code | text | NOT NULL, UNIQUE |
| discount_type | text | NOT NULL, CHECK IN ('PERCENTAGE','FIXED_AMOUNT','CREDIT_GRANT') |
| discount_value | numeric(10,2) | NOT NULL |
| credit_type | text | NULL |
| applicable_plan_slugs | jsonb | NULL |
| max_redemptions | integer | NULL |
| redemption_count | integer | NOT NULL, DEFAULT 0 |
| expires_at | timestamptz | NULL |
| is_active | boolean | NOT NULL, DEFAULT true |
| created_by_platform_admin_id | uuid | FK → platform_admins.id, NOT NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |
| updated_at | timestamptz | NOT NULL, DEFAULT now() |

## `coupon_redemptions`

| Column | Type | Constraints |
|---|---|---|
| id | uuid | PK |
| coupon_code_id | uuid | FK → coupon_codes.id ON DELETE CASCADE, NOT NULL |
| account_id | uuid | FK → accounts.id ON DELETE CASCADE, NOT NULL |
| redeemed_at | timestamptz | NOT NULL, DEFAULT now() |

Indexes: unique on `(coupon_code_id, account_id)` — one redemption per account per
code (`THREAT_MODEL.md` T65).

## Extensions required

- `pgcrypto` or equivalent for `gen_random_uuid()`.
- `citext` for case-insensitive email columns.

## Migration order (Alembic)

Sprint 1: `roles`/`permissions`/`role_permissions` seed migration → `users` →
`user_roles` → `refresh_tokens` / `password_reset_tokens` / `user_invitations` →
`company_profile` → `brand_profiles` → `audit_logs` → `usage_records`.

Slice 2: `contacts` → `contact_custom_fields` → `contact_field_values` → `tags` →
`contact_tags` → `contact_lists` → `contact_list_members` → `segments` →
`segment_rules` → `segment_members` → `contact_imports` → `contact_import_rows` →
`consent_records` → `suppression_entries`. Also a seed migration adding the new
`contacts.manage` / `contacts.view` permission codes and their role grants (see
[RBAC.md](../08-security/RBAC.md)).

Slice 3: `email_provider_connections` → `sender_identities` → `email_templates` →
`email_template_versions` → `campaigns` → `campaign_versions` → `campaign_recipients` →
`message_deliveries` → `delivery_attempts` → `email_events` → `unsubscribe_events`. Also
a seed migration adding `campaigns.manage` / `campaigns.send` / `campaigns.view` /
`integrations.manage` and their role grants (see [RBAC.md](../08-security/RBAC.md)), and
a settings addition for `ENCRYPTION_KEY` (Fernet key for
`email_provider_connections.smtp_password_encrypted`, per
[DEC-GRX-009](../00-project-control/DECISIONS.md)).

Sprint 5 Phase B: `platform_admins` → `platform_permissions` → `platform_role_permissions`.
Independent of every `GRX-SAAS-001` migration — no FK to `accounts` or any account-owned
table, so this can land in any order relative to Phase A's migrations (though Phase A
merges first per the sprint's own dependency order).

Sprint 5 Phase C: `users.status` CHECK widened to add `PENDING_VERIFICATION` →
`accounts.selected_plan_slug` added → `account_verification_tokens`. Depends on
`GRX-SAAS-001`'s `accounts`/`users` tables existing; independent of Phase B.

Sprint 5 Phase E (`GRX-SAAS-005`): no new tables or columns — a data-only migration
seeds one `platform_permissions` row (`platform.accounts.manage`) and grants it to
`platform.owner`/`platform.admin` in `platform_role_permissions`. Depends on Phase B's
tables existing. See [DATA_MODEL.md §Sprint 5 Phase E entities](DATA_MODEL.md#sprint-5-phase-e-entities-customer-account-platform--accountuser-management-grx-saas-005)
and [DECISIONS.md §DEC-GRX-020](../00-project-control/DECISIONS.md).

Sprint 5 Phase E (`GRX-SAAS-008`): also no new tables or columns — a second data-only
migration seeds `platform_permissions.code = 'platform.usage.manage'`, granted to
`platform.owner`/`platform.admin`/`platform.support`. Reads existing `usage_records` and
`campaigns` tables (see [DATA_MODEL.md §Sprint 5 Phase E entities (usage/campaign oversight)](DATA_MODEL.md#sprint-5-phase-e-entities-customer-account-platform--usage--campaign-oversight-grx-saas-008))
and [DECISIONS.md §DEC-GRX-021](../00-project-control/DECISIONS.md).

Sprint 5 Phase E (`GRX-SAAS-010`): one new table, `support_sessions`, plus two
`platform_permissions` seed rows (`platform.support_session.create`,
`platform.support_session.write`). Depends on Phase B's `platform_admins` table and
Phase A's `accounts` table both existing. See [DATA_MODEL.md §Sprint 5 Phase E entities (Secure support session)](DATA_MODEL.md#sprint-5-phase-e-entities-customer-account-platform--secure-support-session-grx-saas-010)
and [DECISIONS.md §DEC-GRX-022](../00-project-control/DECISIONS.md).

Slice 5: `social_connections` (+ seed migration adding `social.manage` / `social.publish`
/ `social.view` and their role grants) → `social_posts` → `social_post_media` →
`social_post_versions`. Depends on `GRX-SAAS-001`'s `accounts` table existing. See
[DATA_MODEL.md §Slice 5 entities](DATA_MODEL.md#slice-5-entities-full-detail) and
[DECISIONS.md §DEC-GRX-023/024/025](../00-project-control/DECISIONS.md).

Slice 6: `ai_generations` → `ai_provider_connections` → `platform_ai_provider_config` (+
seed migration adding `ai.manage` / `ai.view` and their role grants, and
`platform.ai.manage` granted to `platform.owner`/`platform.admin`). Depends on
`GRX-SAAS-001`'s `accounts` table and Phase B's `platform_admins` table both existing.
See [DATA_MODEL.md §Slice 6 entities](DATA_MODEL.md#slice-6-entities-full-detail) and
[DECISIONS.md §DEC-GRX-026/027/028](../00-project-control/DECISIONS.md).

Slice 7: same migration also drops `accounts.plan_id` (the unused Phase-D placeholder
from `3186b6c66a6d`) and widens `accounts.selected_plan_slug`'s CHECK from
`('starter', 'growth')` to `('free', 'starter', 'pro')` to match the real plan catalog
— then creates `subscription_plans` (+ seed migration adding `billing.manage` /
`billing.view` and their role grants, `platform.billing.manage` granted to
`platform.owner`/`platform.finance`, and the four `free`/`starter`/`pro`/`enterprise`
plan rows) → `account_subscriptions` → `account_credit_balances` →
`account_credit_purchases` → `coupon_codes` → `coupon_redemptions`. Depends on
`GRX-SAAS-001`'s `accounts` table and Phase B's `platform_admins` table both existing.
The same migration backfills a `Free`-tier `account_subscriptions` row for every
pre-existing account (new accounts get one automatically at registration going
forward, `BILLING_SYSTEM_ARCHITECTURE.md §3.4`).

`GRX-BILL-004` adds two more migrations on top: `60f7c30ff18a` widens
`account_subscriptions.status`'s CHECK to add `PENDING`; `b6eed962fd56` creates
`credit_packs` (+ seeds five draft packs). `GRX-SAAS-006` adds one more:
`e3e939e991f4` widens `subscription_plans.slug`'s CHECK from a fixed 4-value whitelist
to a plain format check. All three depend only on the Slice 7 migration above.

See
[DATA_MODEL.md §Slice 7 entities](DATA_MODEL.md#slice-7-entities-full-detail) and
[DECISIONS.md §DEC-GRX-029/030](../00-project-control/DECISIONS.md).
