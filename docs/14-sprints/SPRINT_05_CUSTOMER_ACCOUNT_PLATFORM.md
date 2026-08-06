# Sprint 05 — Multi-Tenant Platform Foundation

- Document ID: DOC-SPRINT-05
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-07
- Owner: Coding agent (on behalf of product owner)
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-017](../00-project-control/DECISIONS.md), [FUTURE_SCOPE_PLATFORM_ADMIN](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md), [ROADMAP](../01-product/ROADMAP.md)

Sprint 5 turns Growixa from the single-tenant MVP (Slices 1–4, [DEC-GRX-002](../00-project-control/DECISIONS.md),
now superseded) into a self-service, multi-tenant SaaS product, per
[DEC-GRX-017](../00-project-control/DECISIONS.md) and the shape captured in
[FUTURE_SCOPE_PLATFORM_ADMIN.md](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md). Unlike
every prior sprint, this one is **not additive** — it's a structural retrofit of the
existing app. Every table, query, and permission check that currently assumes "one
company, ever" has to be re-derived to assume "one of N isolated customer accounts."

**This is the single largest and highest-risk sprint in the project's history.** A missed
scoping filter here is a cross-customer data leak, not a cosmetic bug. Nothing in Phases
B–E may begin before Phase A is `DONE` and independently verified — building on top of
unscoped data isolation just means rebuilding once isolation lands for real.

## Why this sprint is phased, not one task

[FUTURE_SCOPE_PLATFORM_ADMIN.md §Before this can be implemented](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md#before-this-can-be-implemented)
lists five prerequisites. They have a real dependency order, not just a list order:

```
Phase A (isolation) ──┬─→ Phase B (platform auth) ──┐
                       ├─→ Phase C (registration)  ──┼─→ Phase E (platform admin panel)
                       └─→ Phase D (billing)        ──┘
```

Phase A blocks everything else — B, C, and D all create or touch account-scoped data, so
none of them can be built correctly until every table and query is account-aware. B, C,
and D can proceed in parallel worktrees once A is done and verified (they don't depend on
each other). E depends on B, C, and D existing, since it manages/observes the objects
they create (accounts, subscriptions, registrations).

---

## Phase A — Multi-tenant data isolation (`GRX-SAAS-001`)

The foundation. Nothing else in this sprint is safe to build without it.

### Included

1. New `accounts` table: `id`, `name`, `status` (`ACTIVE`/`SUSPENDED`/`CLOSED`), `plan_id`
   (nullable until Phase D exists), `created_at`. One row per customer.
2. `account_id` (FK → `accounts.id`, `NOT NULL`, indexed) added to every account-owned
   table. Grouped by module, from the current schema:
   - **Users/auth**: `users`, `user_roles`, `user_invitations`, `refresh_tokens`,
     `password_reset_tokens`
   - **Company**: `company_profile`, `brand_profiles` (today's app-enforced "at most one
     row" becomes "at most one row per `account_id`" — the same shape change
     `GRX-EMAIL-011`/`DEC-GRX-016` already did for `email_provider_connections`, just
     applied to these two tables)
   - **Contacts**: `contacts`, `contact_custom_fields`, `contact_field_values`, `tags`,
     `contact_tags`, `contact_lists`, `contact_list_members`, `segments`,
     `segment_rules`, `segment_members`, `contact_imports`, `contact_import_rows`,
     `consent_records`, `suppression_entries`
   - **Email**: `email_templates`, `email_template_versions`, `email_provider_connections`,
     `sender_identities`, `campaigns`, `campaign_versions`, `campaign_recipients`,
     `message_deliveries`, `delivery_attempts`, `email_events`, `unsubscribe_events`
   - **Cross-cutting**: `audit_logs`, `usage_records`
   - **Explicitly NOT account-scoped** (platform-global, seeded, shared reference data —
     unchanged by this sprint): `roles`, `permissions`, `role_permissions`. Per-account
     custom roles are out of scope; every account uses the same seeded role set from
     [RBAC.md](../08-security/RBAC.md).
3. Every repository function in every module gets an `account_id` parameter and an
   `AND account_id = :account_id` clause — no exceptions, no "trusted" queries. Every
   `WHERE`, every `JOIN`, every uniqueness constraint that used to be global (e.g.
   `users.email` unique) becomes `UNIQUE (account_id, email)`.
4. A single `get_current_account_id()` FastAPI dependency (mirrors the existing
   `get_current_user`/`require_permission` dependency pattern in
   `permissions/dependencies.py`), derived from the authenticated user's own
   `account_id` — resolved once per request, threaded through every service call
   alongside the existing `actor_id` pattern already used everywhere
   (`created_by_user_id`, etc.).
5. Migration strategy for existing data: the current single company's rows all get
   backfilled into one new `accounts` row (`id` fixed/known, e.g. via a seed script) so
   the existing dev/prod data doesn't need to be discarded — this sprint retrofits
   isolation, it doesn't reset the database.
6. **Cross-tenant isolation tests are the primary deliverable of this phase, not an
   afterthought.** For every module: two accounts, two sets of otherwise-identical data,
   assert account A's list/get/update/delete calls never see or affect account B's rows,
   even by guessed/enumerated ID. This is a new test category this codebase doesn't have
   yet — write the shared test fixture (two `account_factory`-created accounts, matching
   the existing `user_factory` pattern in `conftest.py`) once, reuse it in every module's
   test file.

### Explicitly excluded from Phase A

- Anything in `accounts` beyond the columns needed for isolation to function
  (`plan_id`, billing fields, etc. arrive with Phase D — this phase adds the column,
  Phase D populates it meaningfully).
- Any UI. Phase A is entirely backend/data-layer. No page changes, no new frontend
  routes.
- Per-account custom roles/permissions — every account shares the same seeded role set.
- Soft-delete or data-export tooling for a closed account (a real requirement eventually,
  not blocking Phase A).

### Acceptance criteria

- Every table listed above has a `NOT NULL account_id` column with a DB-level FK and
  index.
- Every existing integration test still passes, now parameterized with an explicit
  `account_id` fixture instead of implicit single-tenancy.
- A new cross-tenant isolation test exists for every module and fails loudly (not
  silently returns empty) if a scoping filter is ever removed — this is the regression
  guard for every future task in this codebase, not just this sprint.
- `alembic check` clean; the migration is reversible (`downgrade` restores the
  pre-`account_id` schema against the seeded single account).

---

## Phase B — Platform auth boundary (`GRX-SAAS-002`)

### Included

1. A distinct identity class for IITDEVELOPER platform staff, separate from
   `accounts`/`users`. Per
   [FUTURE_SCOPE_PLATFORM_ADMIN.md](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md#proposed-model-summary-as-given),
   proposed roles: `platform.owner`, `platform.admin`, `platform.support`,
   `platform.finance`, `platform.operations`. New `platform_admins` table (mirrors
   `users`, but with no `account_id` — platform admins aren't scoped to any one
   account) + a `platform_permissions`/`platform_role_permissions` pair mirroring the
   existing `permissions`/`role_permissions` shape, namespaced `platform.*` to keep
   these visually and structurally distinct from account-level permission codes
   (`contacts.manage`, etc.) at every call site.
2. A new `require_platform_permission(code)` dependency, structurally parallel to
   `permissions/dependencies.py`'s existing `require_permission(code)` but checking
   `platform_admins`/`platform_role_permissions` instead of the account-scoped tables —
   deliberately not the same function with a flag, since accidentally calling the wrong
   one is exactly the kind of bug that must be structurally hard to make, not just
   documented against.
3. Login: reuse the existing JWT/HttpOnly-cookie mechanism
   ([DEC-GRX-014](../00-project-control/DECISIONS.md)) but a **separate cookie name**
   and a **separate login route** (`POST /platform/auth/login`, distinct from
   `/auth/login`), so a platform-admin session and a customer-account session can never
   be silently confused by a shared cookie name, and a customer-facing XSS can't reach a
   platform session cookie that was never set on that origin/path in the first place.
4. Frontend: a new route group, `apps/web/src/app/(platform)/`, structurally parallel to
   `(admin)/` — **not the same as `(admin)`**. Today's `(admin)/admin` (System Health,
   `GRX-ADMIN-001`) stays exactly where it is and keeps meaning "this one account's
   Super Admin panel." The new `(platform)/` is IITDEVELOPER-only, reached via the
   separate platform login, and is where Phase E's actual Platform Admin panel lives.

### Explicitly excluded from Phase B

- Any actual platform-admin features (user/subscription/provider management, etc.) —
  this phase only builds the identity/auth boundary they'll sit behind. Phase E builds
  the features.
- Self-service platform-admin account creation — platform admins are seeded/provisioned
  directly (like `admin@growixa.local` is today), not signed up.

### Acceptance criteria

- A platform-admin session cookie is never accepted by any `/auth/*` (customer) route,
  and vice versa — verified by an integration test that mints one and calls the other's
  routes, expecting 401 both directions.
- `require_permission` and `require_platform_permission` are separate functions; a route
  accidentally using the wrong one fails a static grep-based test (matching the existing
  route-protection audit test pattern already used for `require_permission` coverage).

---

## Phase C — Self-service registration (`GRX-SAAS-003`)

### Included

1. Public `POST /accounts/register`: creates a new `accounts` row, a `customer.owner`
   user, sends a verification email. Reuses the existing token-generation pattern
   already built for password reset (`auth/tokens.py`'s generic generate/hash
   functions, per its own `GRX-AUTH-005`-era generalization) rather than inventing a
   new token scheme.
2. `POST /accounts/verify-email`: consumes the token, activates the account.
3. Plan selection as part of registration (UI step; actual plan *enforcement* — limits,
   billing — is Phase D). A registered-but-unverified account cannot log in.
4. Frontend: a public signup flow under `(marketing)/` or a new `(auth)/register` route
   (structurally parallel to the existing `(auth)/login`), email-verification
   confirmation page, plan-selection step.
5. Rate limiting on `/accounts/register` and `/accounts/verify-email`, reusing the
   existing `auth/rate_limit.py` limiter already applied to `/auth/login` and
   `/auth/password-reset/request` (`GRX-AUTH-004`) rather than building a second
   limiter.

### Explicitly excluded from Phase C

- Any actual plan enforcement (contact limits, send limits, feature gating by plan) —
  Phase C only records which plan was selected; Phase D and later usage-metering work
  enforce it.
- Social/SSO signup (Google/Microsoft login) — email/password only, matching the
  existing auth model.
- Team invitations from a newly-registered account — `GRX-USER-001`'s existing
  invitation flow already covers "an account's own owner invites more users into that
  same account"; no new invitation logic needed here, just confirm it still works
  correctly once `account_id`-scoped (verified as part of Phase A's isolation tests, not
  rebuilt here).

### Acceptance criteria

- A new visitor can register, verify their email, select a plan, and log in — all
  without any existing account/admin action.
- An unverified account cannot authenticate against any protected route.
- Registering with an email already used in *any* account is rejected (global email
  uniqueness across accounts is a product decision to confirm during implementation —
  default assumption: yes, one email = one platform identity, matching how most
  self-service SaaS products work, but flag this as an explicit open question to
  resolve before writing the migration's uniqueness constraint).

---

## Phase D — Billing (`GRX-SAAS-004`)

### Included

1. Payments vendor integration — Stripe is the default assumption (no vendor is
   currently chosen; confirm before implementation starts, since this is a real
   external dependency, not a design choice this doc can make unilaterally).
2. `subscriptions` table: `account_id`, `plan_id`, `status`
   (`TRIALING`/`ACTIVE`/`PAST_DUE`/`CANCELED`), Stripe customer/subscription IDs,
   period dates.
3. Stripe webhook receiver (structurally similar to the existing Postmark webhook
   receiver's authenticated-callback pattern in `email_delivery/api.py` — signature
   verification instead of Basic Auth, but the same "public route, verify before
   touching any table" shape) handling subscription created/updated/canceled,
   payment-failed events.
4. Plan limits enforcement — wire the plan's limits into the places
   [DEC-GRX-007](../00-project-control/DECISIONS.md)'s existing `usage_records` table
   already tracks (contacts, email sends, etc.), since that table was explicitly built
   "even though single-tenant... so it doesn't need rework when multi-tenant billing is
   added later." This is that later.
5. Trial period handling, payment-failure/dunning state, plan upgrade/downgrade.

### Explicitly excluded from Phase D

- Invoicing PDF generation, tax calculation, multi-currency — use Stripe's own hosted
  invoicing rather than building any of this natively for a first release.
- Usage-based overage billing (metered billing beyond plan limits) — flat-rate plans
  only for the first release; overage billing is a real feature but not required to
  prove the billing loop works end-to-end.
- Any UI beyond what's needed to select a plan (Phase C) and see current
  subscription/invoice status (Phase E's platform admin panel shows the
  IITDEVELOPER-facing financial view; a customer-facing "billing settings" page inside
  `(dashboard)/dashboard/company-settings` is a reasonable fast-follow but not required
  for this sprint's acceptance criteria).

### Acceptance criteria

- A real (test-mode) Stripe subscription can be created, updated, and canceled, and the
  local `subscriptions` row stays in sync via webhook.
- A payment failure transitions the account to `PAST_DUE`, is visible somewhere (even
  just in the DB / an admin query) — a full dunning UI is not required to pass this
  sprint, but the state must be tracked correctly.

---

## Phase E — Platform Admin panel (`GRX-SAAS-005` through `GRX-SAAS-009`)

Built under the `(platform)/` route group from Phase B, gated by `platform.*`
permissions, not `admin.access` (which remains `(admin)`'s existing, unrelated,
per-account permission). Per
[FUTURE_SCOPE_PLATFORM_ADMIN.md §Proposed IITDEVELOPER Platform Admin capabilities](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md#proposed-iitdeveloper-platform-admin-capabilities),
broken into separately shippable tracker rows rather than one task, matching this
project's own "vertical slices, not one big task" convention
([DEC-GRX-010](../00-project-control/DECISIONS.md)):

| Row | Capability |
|---|---|
| `GRX-SAAS-005` | Account/user management — list all accounts, activate/suspend/close, view login/security activity |
| `GRX-SAAS-006` | Subscription management — view/change plans, trial extensions, usage credits (reads Phase D's `subscriptions` table) |
| `GRX-SAAS-007` | Provider management — platform-level provider config, health, credential rotation (extends the existing per-provider pattern from `GRX-EMAIL-011`/integrations, but platform-wide instead of per-account) |
| `GRX-SAAS-008` | Usage tracking + campaign oversight — per-account `usage_records` view, queued/failed campaigns across all accounts, abuse controls |
| `GRX-SAAS-009` | Infrastructure monitoring + financial dashboard — extends `GRX-ADMIN-001`'s existing `/health` + healthcheck-job pattern with RabbitMQ queue-depth introspection (a real gap — no endpoint exposes this today, confirmed via this project's own live debugging sessions needing raw `rabbitmqctl` calls), plus MRR/ARR/churn from Phase D's subscription data |

**Secure support session** (from
[FUTURE_SCOPE_PLATFORM_ADMIN.md](../01-product/FUTURE_SCOPE_PLATFORM_ADMIN.md#proposed-iitdeveloper-platform-admin-capabilities)'s
own description — reason + ticket number required, platform-admin confirmation,
time-limited, visible banner in the customer-facing UI while active, read-only by
default, fully audited, never exposes raw API keys) is its own row,
`GRX-SAAS-010`, deliberately last — it's the highest-trust capability in the whole
sprint and should only be built once every account-isolation guarantee below it has
already been proven correct by every earlier phase's tests.

### Explicitly excluded from Phase E

- "Login as customer" in the traditional sense — every existing SaaS-support-impersonation
  security incident starts here; `GRX-SAAS-010`'s audited, banner-visible, time-limited
  session model is the only support-access mechanism this sprint builds.
- Any capability not listed in the table above (e.g. a full BI/analytics suite beyond
  the financial dashboard) — trim further if a capability turns out to be
  bigger than expected once scoped in detail; do not silently expand scope while
  implementing.

---

## Sprint 5 sequencing rule

No `GRX-SAAS-0XX` task past `001` may move to `READY` until `GRX-SAAS-001` (Phase A) is
`DONE`, per [DEVELOPMENT_READINESS.md](../00-project-control/DEVELOPMENT_READINESS.md)'s
existing gate mechanism — this sprint doc is the readiness gate for itself, since Phase A
*is* the thing every later phase's readiness depends on.

Full task breakdown: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-SAAS-*`).
