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

## Slice 5 permission codes

| Code | Meaning |
|---|---|
| `social.manage` | Create/edit social post drafts, upload/remove media |
| `social.publish` | Publish a post immediately, schedule a post for later, cancel a scheduled post, retry a failed post |
| `social.view` | Read-only access to posts, connection status, and the content calendar |

Connecting/reconnecting the Instagram Business account itself reuses the **existing**
`integrations.manage` code from Slice 3 — it's the same conceptual action (configuring a
provider connection) as the Postmark/SMTP connection, not a new permission.

Slice 5 deliberately mirrors Slice 3's `.manage`/`.send`-shaped split
(`social.manage`/`social.publish`) rather than inventing new vocabulary — see the Slice 3
section above for the "draft vs. send/publish" rationale, which applies identically here
("draft vs. publish"). One divergence worth calling out: Slice 4's shipped campaign
scheduling route checks `campaigns.manage` rather than `campaigns.send`, which
inadvertently lets a Content Creator schedule a send despite not holding send authority.
Social's schedule/cancel/retry routes are gated on `social.publish`, not `social.manage`,
so this same gap is not replicated here.

## Slice 5 role → permission matrix

| Permission | Super Admin | Admin | Marketing Manager | Content Creator | Analyst | Viewer |
|---|---|---|---|---|---|---|
| `social.manage` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `social.publish` | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `social.view` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

- `social.manage`: same grant shape as `campaigns.manage` — everyone with a real drafting
  need, honoring Content Creator's "drafts, AI generation, media — no send/publish
  authority" scope.
- `social.publish`: same grant shape as `campaigns.send` — Admin and Marketing Manager
  only, Content Creator deliberately excluded.
- `social.view`: same grant shape as `campaigns.view` — everyone except Viewer.

## Slice 6 permission codes

| Code | Meaning |
|---|---|
| `ai.manage` | Generate/rewrite AI content (subject lines, body copy, social captions, hashtags, posting-time suggestions) |
| `ai.view` | Read-only access to generation history |

Connecting/rotating an account's own "bring your own model" AI provider credentials
reuses the **existing** `integrations.manage` code from Slice 3 — the same conceptual
action (configuring a third-party provider connection with an encrypted credential) as
the Postmark/SMTP or Instagram connection, not a new permission
([DEC-GRX-026](../00-project-control/DECISIONS.md)).

Slice 6 deliberately does **not** add an `ai.publish`/`ai.send`-shaped third code. Per
[DEC-GRX-006](../00-project-control/DECISIONS.md), AI output can never send email or
publish social content directly — it lands in a campaign/social draft, and the
*existing* `campaigns.send`/`social.publish` permissions already gate the actual
send/publish of whatever that draft becomes. Content Creator's long-documented scope
("Drafts, AI generation, media — no send/publish authority," from this document's
Sprint-1-era Roles table) is honored by simply not granting `campaigns.send`/
`social.publish` — Slice 6 needs no approval-gate permission of its own, only
`ai.manage` (generate) and `ai.view` (read history).

## Slice 6 role → permission matrix

| Permission | Super Admin | Admin | Marketing Manager | Content Creator | Analyst | Viewer |
|---|---|---|---|---|---|---|
| `ai.manage` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| `ai.view` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

Same grant shape as `social.manage`/`social.view` — everyone with a real drafting need
gets `ai.manage` (including Content Creator, honoring its "AI generation" scope
explicitly), and everyone except Viewer gets `ai.view`. Unlike `social.publish`/
`campaigns.send`, there is no restricted third tier here — see the rationale above.

## Slice 7 (Billing) permission codes

| Code | Meaning |
|---|---|
| `billing.manage` | Subscribe/change the account's plan, buy top-up credit packs, redeem a coupon code — any action that actually charges (or credits) the account via Razorpay |
| `billing.view` | View the account's current plan, usage/quota bars, and billing history |

`billing.manage` is Super-Admin-only, kept to the same trust tier as
`integrations.manage` (`DEC-GRX-030`) rather than `company.settings.edit`'s
Admin-inclusive grant — unlike editing a company profile, this code authorizes a real
charge against the account's payment method, the same class of action as connecting a
third-party credential. `billing.view` is granted broadly, matching
`company.settings.view`'s all-roles precedent — knowing how much of the plan's quota
is left (emails, AI runs, contacts) is routine operational information every role
benefits from, not administrative-only data.

## Slice 7 (Billing) role → permission matrix

| Permission | Super Admin | Admin | Marketing Manager | Content Creator | Analyst | Viewer |
|---|---|---|---|---|---|---|
| `billing.manage` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `billing.view` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Slice 7 (Billing) platform permission codes (`GRX-SAAS-004`/`006`/`012`)

| Code | Meaning |
|---|---|
| `platform.billing.manage` | View/change any account's plan, subscription status, and credit balance without a payment; edit plan-wide quotas/prices; create/manage coupon codes |

This is the `platform.billing.manage` code `platform.finance`'s Sprint 5 Phase B role
description already named in advance ("Subscription/billing visibility and changes").
Granted to `platform.owner`/`platform.finance` only — deliberately **not**
`platform.admin`, unlike `platform.accounts.manage`/`platform.ai.manage` — billing is
`platform.finance`'s stated domain specifically, and `platform.admin`'s own scope is
explicitly "no billing" per its role description. Coupon management reuses this same
code rather than a separate `platform.coupons.manage` — it's the same class of action
(a financial lever affecting subscription price/credits), not a conceptually distinct
capability.

## Slice 7 (Billing) platform role → permission matrix

| Permission | platform.owner | platform.admin | platform.support | platform.finance | platform.operations |
|---|---|---|---|---|---|
| `platform.billing.manage` | ✅ | ❌ | ❌ | ✅ | ❌ |

## Sprint 7 — Platform AI config (`GRX-AI-005`)

| Code | Meaning |
|---|---|
| `platform.ai.manage` | View/edit the platform-wide default AI provider configuration (`platform_ai_provider_config`) |

Mirrors `platform.usage.manage`'s existing wiring exactly (`require_platform_permission`,
never `require_permission`). Granted to `platform.owner`/`platform.admin` only — matching
`platform.accounts.manage`'s higher-trust shape, since this gates an encrypted
credential (an AI provider API key), not just an operational view.

| Permission | platform.owner | platform.admin | platform.support | platform.finance | platform.operations |
|---|---|---|---|---|---|
| `platform.ai.manage` | ✅ | ✅ | ❌ | ❌ | ❌ |

## Ad hoc — Platform email provider config (`GRX-SAAS-013`)

| Code | Meaning |
|---|---|
| `platform.email.manage` | View/edit the platform-wide email provider configuration used for system/transactional email (`platform_email_provider_config`) |

Same wiring and trust shape as `platform.ai.manage` (`require_platform_permission`,
`platform.owner`/`platform.admin` only — gates an encrypted SMTP credential). Added
after a real production incident: the previous `.env`-only `PLATFORM_SMTP_*` config
could only be changed by redeploying, and had no admin-facing way to switch providers
or rotate credentials. Resolution order at send time: this DB config if an active row
exists, else the legacy `.env` settings (so an existing deployment isn't broken), else
skip sending (logged).

| Permission | platform.owner | platform.admin | platform.support | platform.finance | platform.operations |
|---|---|---|---|---|---|
| `platform.email.manage` | ✅ | ✅ | ❌ | ❌ | ❌ |

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

## Sprint 5 Phase E permission codes (`GRX-SAAS-005`, `GRX-SAAS-008`)

| Code | Meaning |
|---|---|
| `platform.accounts.manage` | List every customer account, view an account's users and login/security activity, activate/suspend/close an account |
| `platform.usage.manage` | View per-account usage summaries and cross-account campaign oversight (queued/failed); pause a suspicious campaign |

Per [DEC-GRX-020](../00-project-control/DECISIONS.md), `platform.accounts.manage` is
granted only to `platform.owner` and `platform.admin` — matching `platform.admin`'s own
stated scope in the Phase B role table above ("Account/user management... day-to-day
operations"). Per [DEC-GRX-021](../00-project-control/DECISIONS.md),
`platform.usage.manage` is additionally granted to `platform.support` — usage/campaign
oversight is support-facing, matching the tracker's own stated actor. Neither code is
granted to `platform.finance`/`platform.operations`. Each remaining Phase E capability
(billing, provider config, support sessions) adds its own `platform.*` code when its own
task begins, same convention as Phase B's `platform.access`.

## Sprint 5 Phase E role → permission matrix

| Permission | platform.owner | platform.admin | platform.support | platform.finance | platform.operations |
|---|---|---|---|---|---|
| `platform.accounts.manage` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `platform.usage.manage` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `platform.support_session.create` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `platform.support_session.write` | ✅ | ✅ | ❌ | ❌ | ❌ |

## Sprint 5 Phase E permission codes (`GRX-SAAS-010`)

| Code | Meaning |
|---|---|
| `platform.support_session.create` | Start an audited, time-limited support session into a customer account (default `access_level=READ`); view that account's data through an active session it started; end a session early |
| `platform.support_session.write` | Additionally required to start a session with `access_level=WRITE`, and to perform the one gated write action (editing a contact) through an active `WRITE` session |

Per [DEC-GRX-022](../00-project-control/DECISIONS.md), `platform.support_session.create`
is granted to `platform.owner`/`platform.admin`/`platform.support` — matching
`platform.support`'s own stated scope ("Customer support tooling (secure support
sessions, Phase E)"). `platform.support_session.write` is owner/admin-only, the same
higher-trust shape `platform.accounts.manage` already uses — the literal "separate
permission gate for write access" the tracker's own wording calls for: a session can
only be opened (or written through) at `WRITE` level if the acting admin holds *both*
codes, not just `.create`.

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
