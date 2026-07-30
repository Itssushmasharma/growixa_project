# RBAC

- Document ID: DOC-SEC-RBAC
- Status: ACTIVE
- Version: 1.1
- Last updated: 2026-07-30
- Owner: Coding agent
- Related documents: [AUTHENTICATION](AUTHENTICATION.md), [DATA_MODEL](../05-data/DATA_MODEL.md), [PRD §20](../01-product/PRD.md#20-user-roles-and-permissions)

## Model

`users` ⟷ `user_roles` ⟷ `roles` ⟷ `role_permissions` ⟷ `permissions`. A user may hold more
than one role; effective permissions are the union of all permissions granted by all roles
held. No per-user permission overrides in Sprint 1 — role membership is the only lever.

## Roles (seeded, not user-creatable in Sprint 1)

| Role | Intended scope |
|---|---|
| Super Admin | Full access, including integrations, provider credentials, and user management |
| Admin | User management, company settings, most operational access |
| Marketing Manager | Campaigns, segments, social, analytics — approval authority (once those modules exist) |
| Content Creator | Drafts, AI generation, media — no send/publish authority (once those modules exist) |
| Analyst | Read-only analytics and reporting |
| Viewer | Read-only, broadest restriction |

## Sprint 1 permission codes

| Code | Meaning |
|---|---|
| `users.manage` | Create/invite/disable users, assign roles |
| `roles.manage` | View role/permission assignments (role definitions themselves are seed data in Sprint 1, not editable via UI) |
| `company.settings.edit` | Edit company profile and brand settings |
| `company.settings.view` | View company profile and brand settings |
| `audit.view` | View audit log |
| `admin.access` | Access the admin dashboard shell |

Additional permission codes are added per module as later slices are built (e.g.
`contacts.manage`, `campaigns.approve`) — this table is extended, not redesigned.

## Slice 2 permission codes

| Code | Meaning |
|---|---|
| `contacts.manage` | Create/edit/archive contacts; manage tags, lists, segments, custom fields; run CSV imports; record consent; suppress addresses |
| `contacts.view` | Read-only access to contacts, tags, lists, and segments |

Kept to the same edit/view granularity as `company.settings.*` in Sprint 1, rather than
splitting into many fine-grained codes (e.g. a separate `contacts.import`) not called for
by `MVP_SCOPE.md §B`.

## Sprint 1 role → permission matrix

| Permission | Super Admin | Admin | Marketing Manager | Content Creator | Analyst | Viewer |
|---|---|---|---|---|---|---|
| `users.manage` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `roles.manage` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `company.settings.edit` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `company.settings.view` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `audit.view` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `admin.access` | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

This matrix seeds `role_permissions` in the Sprint 1 migration.

## Slice 2 role → permission matrix

| Permission | Super Admin | Admin | Marketing Manager | Content Creator | Analyst | Viewer |
|---|---|---|---|---|---|---|
| `contacts.manage` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `contacts.view` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |

Marketing Manager gets full `contacts.manage` per its stated scope ("campaigns, segments,
social, analytics"). Analyst gets `contacts.view` only, matching its stated "read-only
analytics and reporting" scope. Content Creator and Viewer get neither in Slice 2 — no
Slice 2 requirement calls for it, and per Sprint 1's own precedent (Viewer only received
`company.settings.view`, not a blanket view grant across every module), access is granted
explicitly per module, never assumed from a role's name. Extend later if a real need
surfaces (e.g. Content Creator needing segment context for Slice 6's "audience-specific
variations").

## Enforcement rule

Every API route that isn't explicitly public (login, invitation-acceptance, password-reset
flows) requires an authenticated session and passes through the centralized
`require_permission(...)` dependency described in [AUTHENTICATION.md](AUTHENTICATION.md).
Enforcement lives in the backend only — the frontend hiding a button is a UX nicety, never
the actual access control.
