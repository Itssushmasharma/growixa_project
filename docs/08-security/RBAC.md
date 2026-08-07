# RBAC

- Document ID: DOC-SEC-RBAC
- Status: ACTIVE
- Version: 1.3
- Last updated: 2026-08-07
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

## Slice 3 permission codes

| Code | Meaning |
|---|---|
| `integrations.manage` | Configure the email provider connection (SMTP host/credentials) and sender identities |
| `campaigns.manage` | Create/edit email templates and campaign drafts (subject, body, recipient targeting) — does not include sending |
| `campaigns.send` | Send a test email or trigger a campaign's immediate send |
| `campaigns.view` | Read-only access to templates, campaigns, and delivery/analytics reports |

Unlike Slice 2's single `.manage`/`.view` pair, Slice 3 splits drafting from sending
(`campaigns.manage` vs `campaigns.send`) and carves out `integrations.manage` separately
from both. Neither split is new invention — both were already implied by this document's
own **Roles** table, written in Sprint 1 before any of these modules existed:
- Content Creator's stated scope is "Drafts, AI generation, media — **no send/publish
  authority**." A single combined `campaigns.manage` permission would force an
  all-or-nothing grant that can't honor that boundary; splitting is what actually lets
  Content Creator's long-documented scope be granted for the first time.
- Super Admin's stated scope explicitly separates "integrations, provider credentials"
  from Admin's "most operational access," which doesn't mention either — `integrations.manage`
  being Super-Admin-only (see matrix below) is the first Slice/Sprint permission where
  Admin does not automatically get what Super Admin gets, following that existing
  distinction rather than the Slice 1/2 precedent of Admin mirroring Super Admin on
  every code.

## Slice 3 role → permission matrix

| Permission | Super Admin | Admin | Marketing Manager | Content Creator | Analyst | Viewer |
|---|---|---|---|---|---|---|
| `integrations.manage` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `campaigns.manage` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `campaigns.send` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `campaigns.view` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

- `integrations.manage`: Super Admin only, per the Roles-table distinction above — this
  gates SMTP credentials, which are encrypted at rest per
  [DEC-GRX-009](../00-project-control/DECISIONS.md) and must have the narrowest possible
  access.
- `campaigns.manage`: everyone with a real drafting need — Admin (operational access),
  Marketing Manager (its literal "campaigns" scope), and now Content Creator (its literal
  "drafts" scope, finally exercised). Analyst and Viewer get none, matching their
  read-only scopes.
- `campaigns.send`: Admin and Marketing Manager only — Content Creator is deliberately
  excluded, honoring "no send/publish authority" exactly as written. This is the
  project's first real approval-gate permission; Slice 6's AI-content approval
  requirement ([DEC-GRX-006](../00-project-control/DECISIONS.md)) will reuse this same
  shape (draft vs. send/publish) rather than inventing a new one.
- `campaigns.view`: everyone except Viewer — Analyst's "read-only analytics and
  reporting" scope is exactly what campaign delivery reports are, so (unlike Slice 2,
  where Analyst only got `contacts.view`) this is Analyst's clearest fit yet.

## Sprint 5 Phase B — platform-level roles (separate namespace, `GRX-SAAS-002`)

This is a **distinct identity class**, not an addition to the roles/permissions above.
Platform admins (IITDEVELOPER staff) are not `users`, hold no `account_id`, and are
governed by an entirely separate table set (`platform_admins` /
`platform_permissions` / `platform_role_permissions` — see
[DATABASE_SCHEMA.md §Sprint 5 Phase B](../05-data/DATABASE_SCHEMA.md#sprint-5-phase-b-platform-auth-boundary-tables))
and a separate enforcement dependency (`require_platform_permission`, see below) —
never the `require_permission(...)` used for every code above. Per
[SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase B](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-b--platform-auth-boundary-grx-saas-002),
this split is deliberate: a route accidentally checking the wrong permission class must
be structurally impossible, not just documented against.

| Role | Intended scope |
|---|---|
| `platform.owner` | Full platform control, including provisioning other platform admins |
| `platform.admin` | Account/user management, support session access, day-to-day operations |
| `platform.support` | Customer support tooling (secure support sessions, Phase E) — no billing/provider config |
| `platform.finance` | Subscription/billing visibility and changes (Phase D/E) — no customer data access |
| `platform.operations` | Infrastructure monitoring, provider health/config (Phase E) — no customer or billing data |

Unlike the account-level roles above, a platform admin holds exactly one `role` value
directly on `platform_admins` (not a many-to-many join) — see
[DEC-GRX-018](../00-project-control/DECISIONS.md) for why.

## Sprint 5 Phase B permission codes

| Code | Meaning |
|---|---|
| `platform.access` | The minimal gate proving a platform-admin session can reach a platform-only route at all — structurally analogous to `admin.access` above |

This is deliberately the *only* code Phase B defines. Phase B builds the auth boundary,
not any actual platform-admin feature — each Phase E capability (user management,
billing, provider config, support sessions, etc.) adds its own `platform.*` code when
that feature is actually built, same "extended, not redesigned" convention this document
already follows for account-level codes.

## Sprint 5 Phase B role → permission matrix

| Permission | platform.owner | platform.admin | platform.support | platform.finance | platform.operations |
|---|---|---|---|---|---|
| `platform.access` | ✅ | ✅ | ✅ | ✅ | ✅ |

All five roles get the one Phase B code — it only proves the boundary works, it doesn't
yet differentiate what each role can do once inside. That differentiation is exactly what
each Phase E feature's own permission code(s) will encode (e.g. a future
`platform.billing.manage` granted only to `platform.owner`/`platform.finance`).

## Sprint 5 Phase E permission codes (`GRX-SAAS-005`)

| Code | Meaning |
|---|---|
| `platform.accounts.manage` | List every customer account, view an account's users and login/security activity, activate/suspend/close an account |

Per [DEC-GRX-020](../00-project-control/DECISIONS.md), this is granted only to
`platform.owner` and `platform.admin` — matching `platform.admin`'s own stated scope in
the Phase B role table above ("Account/user management... day-to-day operations"). No
other Phase E capability (billing, provider config, usage tracking, support sessions)
gets anything from this code; each adds its own `platform.*` code when its own task
begins, same convention as Phase B's `platform.access`.

## Sprint 5 Phase E role → permission matrix

| Permission | platform.owner | platform.admin | platform.support | platform.finance | platform.operations |
|---|---|---|---|---|---|
| `platform.accounts.manage` | ✅ | ✅ | ❌ | ❌ | ❌ |

## Enforcement rule

Every API route that isn't explicitly public (login, invitation-acceptance, password-reset
flows) requires an authenticated session and passes through the centralized
`require_permission(...)` dependency described in [AUTHENTICATION.md](AUTHENTICATION.md).
Enforcement lives in the backend only — the frontend hiding a button is a UX nicety, never
the actual access control.

Every route under `apps/api/src/growixa_api/platform_auth/` and any future
`platform_admin/`-style module follows the identical rule with
`require_platform_permission(...)` instead — never `require_permission(...)`. A static
route-audit test (mirroring the existing `require_permission` coverage test) enforces
that no route in a platform-only module ever imports the account-level dependency, and
vice versa.
