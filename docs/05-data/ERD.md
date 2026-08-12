# Entity-Relationship Diagram

- Document ID: DOC-ERD
- Status: ACTIVE (expanded per slice, not redesigned)
- Version: 1.4
- Last updated: 2026-08-07
- Owner: Coding agent
- Related documents: [DATA_MODEL](DATA_MODEL.md), [DATABASE_SCHEMA](DATABASE_SCHEMA.md)

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : "assigned via"
    ROLES ||--o{ ROLE_PERMISSIONS : has
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : "granted via"
    USERS ||--o{ REFRESH_TOKENS : owns
    USERS ||--o{ PASSWORD_RESET_TOKENS : owns
    USERS ||--o{ USER_INVITATIONS : "invited by"
    ROLES ||--o{ USER_INVITATIONS : "assigned on accept"
    COMPANY_PROFILE ||--o| BRAND_PROFILES : has
    USERS ||--o{ AUDIT_LOGS : "acts in"
    USERS ||--o{ USAGE_RECORDS : "attributed to"

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string status
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }
    ROLES {
        uuid id PK
        string name UK
        string description
    }
    PERMISSIONS {
        uuid id PK
        string code UK
        string description
    }
    ROLE_PERMISSIONS {
        uuid role_id FK
        uuid permission_id FK
    }
    USER_ROLES {
        uuid user_id FK
        uuid role_id FK
        timestamp assigned_at
        uuid assigned_by_user_id
    }
    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK
        string token_hash
        timestamp issued_at
        timestamp expires_at
        timestamp revoked_at
        uuid replaced_by_token_id
        string user_agent
        string ip_address
    }
    PASSWORD_RESET_TOKENS {
        uuid id PK
        uuid user_id FK
        string token_hash
        timestamp expires_at
        timestamp used_at
    }
    USER_INVITATIONS {
        uuid id PK
        string email
        string token_hash
        uuid role_id FK
        uuid invited_by_user_id FK
        timestamp expires_at
        timestamp accepted_at
    }
    COMPANY_PROFILE {
        uuid id PK
        string name
        string logo_url
        string website
        string industry
        string timezone
        string default_language
        string legal_footer
        jsonb contact_details
    }
    BRAND_PROFILES {
        uuid id PK
        uuid company_id FK
        text brand_voice
        jsonb forbidden_claims
        jsonb required_facts
    }
    AUDIT_LOGS {
        uuid id PK
        uuid actor_user_id FK
        string action
        string entity_type
        uuid entity_id
        jsonb metadata
        string ip_address
        string user_agent
        timestamp created_at
    }
    USAGE_RECORDS {
        uuid id PK
        string operation_type
        numeric quantity
        string unit
        uuid created_by_user_id FK
        jsonb metadata
        timestamp created_at
    }
```

Source: [`docs/diagrams/er-diagram.mmd`](../diagrams/er-diagram.mmd).

## Slice 2 (Contacts) additions

```mermaid
erDiagram
    CONTACTS ||--o{ CONTACT_FIELD_VALUES : has
    CONTACT_CUSTOM_FIELDS ||--o{ CONTACT_FIELD_VALUES : defines
    CONTACTS ||--o{ CONTACT_TAGS : tagged
    TAGS ||--o{ CONTACT_TAGS : "applied via"
    CONTACTS ||--o{ CONTACT_LIST_MEMBERS : "belongs to"
    CONTACT_LISTS ||--o{ CONTACT_LIST_MEMBERS : contains
    SEGMENTS ||--o{ SEGMENT_RULES : "defined by"
    SEGMENTS ||--o{ SEGMENT_MEMBERS : "captures (SAVED only)"
    CONTACTS ||--o{ SEGMENT_MEMBERS : "matched by"
    CONTACTS ||--o{ CONTACT_IMPORT_ROWS : "created/matched by"
    CONTACT_IMPORTS ||--o{ CONTACT_IMPORT_ROWS : contains
    CONTACTS ||--o{ CONSENT_RECORDS : has
    CONTACTS ||--o| SUPPRESSION_ENTRIES : "may be"

    CONTACTS {
        uuid id PK
        string email UK
        string first_name
        string last_name
        string phone
        string status
        string source
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    CONTACT_CUSTOM_FIELDS {
        uuid id PK
        string key UK
        string label
        string field_type
    }
    CONTACT_FIELD_VALUES {
        uuid contact_id FK
        uuid field_id FK
        string value
    }
    TAGS {
        uuid id PK
        string name UK
    }
    CONTACT_TAGS {
        uuid contact_id FK
        uuid tag_id FK
    }
    CONTACT_LISTS {
        uuid id PK
        string name
        string description
        uuid created_by_user_id FK
    }
    CONTACT_LIST_MEMBERS {
        uuid list_id FK
        uuid contact_id FK
        timestamp added_at
    }
    SEGMENTS {
        uuid id PK
        string name
        string type
        uuid created_by_user_id FK
    }
    SEGMENT_RULES {
        uuid id PK
        uuid segment_id FK
        string field
        string operator
        string value
    }
    SEGMENT_MEMBERS {
        uuid segment_id FK
        uuid contact_id FK
        timestamp captured_at
    }
    CONTACT_IMPORTS {
        uuid id PK
        string file_name
        string status
        integer total_rows
        integer imported_count
        integer skipped_count
        integer error_count
        jsonb column_mapping
        uuid created_by_user_id FK
        timestamp created_at
        timestamp completed_at
    }
    CONTACT_IMPORT_ROWS {
        uuid id PK
        uuid import_id FK
        integer row_number
        jsonb raw_data
        string status
        string error_message
        uuid contact_id FK
    }
    CONSENT_RECORDS {
        uuid id PK
        uuid contact_id FK
        string channel
        string status
        string source
        timestamp recorded_at
        uuid recorded_by_user_id FK
    }
    SUPPRESSION_ENTRIES {
        uuid id PK
        string email UK
        string reason
        uuid contact_id FK
        timestamp suppressed_at
        uuid suppressed_by_user_id FK
    }
```

## Slice 3 (Email Marketing) additions

```mermaid
erDiagram
    EMAIL_PROVIDER_CONNECTIONS ||--o{ SENDER_IDENTITIES : "used by"
    EMAIL_TEMPLATES ||--o{ EMAIL_TEMPLATE_VERSIONS : "versioned by"
    EMAIL_TEMPLATES ||--o{ CAMPAIGNS : "may seed"
    SENDER_IDENTITIES ||--o{ CAMPAIGNS : "sends as"
    SEGMENTS ||--o{ CAMPAIGNS : "may target"
    CONTACT_LISTS ||--o{ CAMPAIGNS : "may target"
    CAMPAIGNS ||--o{ CAMPAIGN_VERSIONS : "frozen at send"
    CAMPAIGNS ||--o{ CAMPAIGN_RECIPIENTS : resolves
    CONTACTS ||--o{ CAMPAIGN_RECIPIENTS : "targeted as"
    CAMPAIGN_RECIPIENTS ||--o| MESSAGE_DELIVERIES : "tracked by"
    MESSAGE_DELIVERIES ||--o{ DELIVERY_ATTEMPTS : has
    MESSAGE_DELIVERIES ||--o{ EMAIL_EVENTS : "receives"
    CAMPAIGNS ||--o{ UNSUBSCRIBE_EVENTS : "may trigger"
    CONTACTS ||--o{ UNSUBSCRIBE_EVENTS : "may cause"

    EMAIL_PROVIDER_CONNECTIONS {
        uuid id PK
        string provider
        string smtp_host
        int smtp_port
        string smtp_username
        string smtp_password_encrypted
        boolean is_active
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    SENDER_IDENTITIES {
        uuid id PK
        uuid email_provider_connection_id FK
        string from_email
        string from_name
        string reply_to_email
        string verification_status
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    EMAIL_TEMPLATES {
        uuid id PK
        string name
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    EMAIL_TEMPLATE_VERSIONS {
        uuid id PK
        uuid template_id FK
        int version_number
        string subject
        string body_html
        string body_text
        uuid created_by_user_id FK
        timestamp created_at
    }
    CAMPAIGNS {
        uuid id PK
        string name
        string subject
        string body_html
        string body_text
        uuid template_id FK
        uuid sender_identity_id FK
        string recipient_type
        uuid recipient_segment_id FK
        uuid recipient_list_id FK
        string status
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
        timestamp sent_at
    }
    CAMPAIGN_VERSIONS {
        uuid id PK
        uuid campaign_id FK
        string subject
        string body_html
        string body_text
        int recipient_count
        timestamp created_at
    }
    CAMPAIGN_RECIPIENTS {
        uuid id PK
        uuid campaign_id FK
        uuid contact_id FK
        string email
        string status
        timestamp created_at
    }
    MESSAGE_DELIVERIES {
        uuid id PK
        uuid campaign_recipient_id FK
        string provider_message_id
        string status
        timestamp sent_at
        timestamp delivered_at
        timestamp bounced_at
        timestamp created_at
        timestamp updated_at
    }
    DELIVERY_ATTEMPTS {
        uuid id PK
        uuid message_delivery_id FK
        int attempt_number
        string status
        string error_message
        timestamp attempted_at
    }
    EMAIL_EVENTS {
        uuid id PK
        uuid message_delivery_id FK
        string event_type
        timestamp occurred_at
        jsonb metadata
        timestamp created_at
    }
    UNSUBSCRIBE_EVENTS {
        uuid id PK
        uuid contact_id FK
        uuid campaign_id FK
        string email
        timestamp occurred_at
        timestamp created_at
    }
```

`campaign_schedules` (Slice 4) and generic `webhook_*` tables (deferred indefinitely) are
intentionally absent — see [DATA_MODEL.md §Explicitly deferred, not designed in Slice
3](DATA_MODEL.md#explicitly-deferred-not-designed-in-slice-3).

Entities for `social` and `ai` are added to this diagram as their owning slice is designed
(Slice 5, 6 respectively) — see
[DATA_MODEL.md §Full MVP entity landscape](DATA_MODEL.md#full-mvp-entity-landscape-target-slice).

## Sprint 5 Phase B (Platform auth boundary) additions

Deliberately its own diagram, not merged into the entities above — `platform_admins` has
no relationship to `accounts`, `users`, or any account-scoped entity by design (see
[DATA_MODEL.md §Sprint 5 Phase B entities](DATA_MODEL.md#sprint-5-phase-b-entities-customer-account-platform--platform-auth-boundary-full-detail)).

```mermaid
erDiagram
    PLATFORM_ADMINS ||--o{ PLATFORM_ROLE_PERMISSIONS : "role grants via"
    PLATFORM_PERMISSIONS ||--o{ PLATFORM_ROLE_PERMISSIONS : "granted via"

    PLATFORM_ADMINS {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        string role
        string status
        timestamp last_login_at
        timestamp created_at
        timestamp updated_at
    }
    PLATFORM_PERMISSIONS {
        uuid id PK
        string code UK
        string description
    }
    PLATFORM_ROLE_PERMISSIONS {
        string role
        uuid permission_id FK
    }
```

## Sprint 5 Phase C (Self-service registration) additions

Unlike Phase B, this connects directly to `accounts`/`users` (Sprint 1's diagram) — the
registration flow creates real rows there. Shown as its own fragment since Sprint 1's
diagram predates `accounts` existing at all (Phase A never added it retroactively; see
[DATA_MODEL.md's note](DATA_MODEL.md#accounts-documented-here-for-the-first-time)).

```mermaid
erDiagram
    ACCOUNTS ||--o{ USERS : owns
    ACCOUNTS ||--o{ ACCOUNT_VERIFICATION_TOKENS : issues
    USERS ||--o{ ACCOUNT_VERIFICATION_TOKENS : "verifies"

    ACCOUNTS {
        uuid id PK
        string name
        string status
        uuid plan_id
        string selected_plan_slug
        timestamp created_at
    }
    ACCOUNT_VERIFICATION_TOKENS {
        uuid id PK
        uuid account_id FK
        uuid user_id FK
        string token_hash
        timestamp expires_at
        timestamp used_at
    }
```

## Slice 5 (Social Publishing) additions

```mermaid
erDiagram
    ACCOUNTS ||--o{ SOCIAL_CONNECTIONS : owns
    SOCIAL_CONNECTIONS ||--o{ SOCIAL_POSTS : "publishes through"
    SOCIAL_POSTS ||--o{ SOCIAL_POST_MEDIA : has
    SOCIAL_POSTS ||--o{ SOCIAL_POST_VERSIONS : "frozen at publish"

    SOCIAL_CONNECTIONS {
        uuid id PK
        uuid account_id FK
        string provider
        string ig_business_account_id
        string ig_username
        string facebook_page_id
        string access_token_encrypted
        timestamp token_expires_at
        boolean is_active
        string last_error
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    SOCIAL_POSTS {
        uuid id PK
        uuid account_id FK
        uuid social_connection_id FK
        string caption
        string status
        timestamp scheduled_at
        timestamp cancelled_at
        timestamp published_at
        uuid idempotency_key
        string ig_media_id
        string ig_permalink
        string last_error
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    SOCIAL_POST_MEDIA {
        uuid id PK
        uuid account_id FK
        uuid social_post_id FK
        string media_type
        string storage_path
        string public_url
        int position
        timestamp created_at
    }
    SOCIAL_POST_VERSIONS {
        uuid id PK
        uuid account_id FK
        uuid social_post_id FK
        string caption
        jsonb media_snapshot
        string ig_media_id
        timestamp created_at
    }
```

## Slice 6 (AI Assistant) additions

```mermaid
erDiagram
    ACCOUNTS ||--o{ AI_GENERATIONS : requests
    ACCOUNTS ||--o{ AI_PROVIDER_CONNECTIONS : "brings own model"
    PLATFORM_ADMINS ||--o{ PLATFORM_AI_PROVIDER_CONFIG : configures

    AI_GENERATIONS {
        uuid id PK
        uuid account_id FK
        uuid created_by_user_id FK
        string capability
        string prompt_template_key
        jsonb input_context
        jsonb output
        string provider
        string model
        int prompt_tokens
        int completion_tokens
        numeric estimated_cost_usd
        string status
        string error_message
        string linked_entity_type
        uuid linked_entity_id
        timestamp created_at
    }
    AI_PROVIDER_CONNECTIONS {
        uuid id PK
        uuid account_id FK
        string provider
        string api_key_encrypted
        string base_url
        string default_model
        boolean is_active
        uuid created_by_user_id FK
        timestamp created_at
        timestamp updated_at
    }
    PLATFORM_AI_PROVIDER_CONFIG {
        uuid id PK
        string provider
        string api_key_encrypted
        string base_url
        string default_model
        boolean is_active
        uuid created_by_platform_admin_id FK
        timestamp created_at
        timestamp updated_at
    }
```

`AI_PROVIDER_CONNECTIONS` (account-level) is checked first when resolving which provider
a generation call actually uses; `PLATFORM_AI_PROVIDER_CONFIG` (platform-level, no
`account_id`) is the fallback. Neither table has a direct FK to the other — the
resolution is a runtime lookup (`ai/providers/factory.py`), not a schema relationship.
