# Entity-Relationship Diagram — Sprint 1 Scope

- Document ID: DOC-ERD
- Status: ACTIVE (Sprint 1 scope only — expanded per slice)
- Version: 1.0
- Last updated: 2026-07-22
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

Entities for `contacts`, `campaigns`, `social`, and `ai` are added to this diagram as their
owning slice is designed (Slice 2, 3–4, 5, 6 respectively) — see
[DATA_MODEL.md §Full MVP entity landscape](DATA_MODEL.md#full-mvp-entity-landscape-target-slice).
