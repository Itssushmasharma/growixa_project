# Database Schema — Sprint 1 Scope

- Document ID: DOC-DB-SCHEMA
- Status: ACTIVE (Sprint 1 scope only)
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [DATA_MODEL](DATA_MODEL.md), [ERD](ERD.md), [MIGRATION_STRATEGY](MIGRATION_STRATEGY.md)

This is the implementation-level schema reference for the tables Sprint 1 must create via
Alembic migrations. Column types are PostgreSQL types. All tables use `uuid` primary keys
generated application-side (or via `gen_random_uuid()`), per the UUID convention in
[DATA_MODEL.md](DATA_MODEL.md).

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

## Extensions required

- `pgcrypto` or equivalent for `gen_random_uuid()`.
- `citext` for case-insensitive email columns.

Migration order (Alembic): `roles`/`permissions`/`role_permissions` seed migration →
`users` → `user_roles` → `refresh_tokens` / `password_reset_tokens` / `user_invitations` →
`company_profile` → `brand_profiles` → `audit_logs` → `usage_records`.
