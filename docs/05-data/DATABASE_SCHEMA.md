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
| plan_id | uuid | NULL, no FK yet (reserved for Phase D) |
| selected_plan_slug | text | NULL, CHECK IN ('starter', 'growth') |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

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
