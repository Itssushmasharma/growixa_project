# Growixa Billing & Feature Metering Architecture

- Document ID: DOC-BILLING-ARCH
- Status: ACTIVE (design complete; plan quota/price numbers are a working draft —
  `GRX-SAAS-004` stays `BLOCKED` until final numbers are confirmed, per
  [OPEN_QUESTIONS.md](../00-project-control/OPEN_QUESTIONS.md) `OQ-013`)
- Last updated: 2026-08-13
- Owner: Coding agent (on behalf of product owner)
- Related documents: [DEC-GRX-029](../00-project-control/DECISIONS.md),
  [DEC-GRX-030](../00-project-control/DECISIONS.md),
  [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) (`GRX-SAAS-004`,
  `GRX-SAAS-006`, `GRX-SAAS-009`, `GRX-SAAS-012`),
  [subscription_plans_matrix.csv](../01-product/subscription_plans_matrix.csv)

This document defines the implementation design for Growixa's billing, subscription,
and feature-metering system: **Razorpay Subscriptions API** integration
(`DEC-GRX-029`), **dual-currency pricing** (USD $ and INR ₹), **atomic credit
metering** with non-expiring top-up credits, a **platform-admin override UI**, and a
**coupon/discount engine** (`DEC-GRX-030`). Planning only — no implementation has
started; this is the design `GRX-SAAS-004`/`006`/`009`/`012` will follow once
`GRX-SAAS-004` is unblocked.

---

## 1. Architecture & billing flow

```
                      ┌──────────────────────────────────────────┐
                      │      Razorpay Subscriptions webhook       │
                      │           (POST /billing/razorpay)         │
                      └────────────────────┬─────────────────────┘
                                           │ signature-verified events
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Growixa Billing Engine                                 │
│                                                                                 │
│  ┌───────────────────────────┐    ┌───────────────────────────┐                 │
│  │   Account Subscriptions   │    │  Account Credit Balances  │                 │
│  │   (running period meter)  │    │ (summed, non-expiring)    │                 │
│  └─────────────┬─────────────┘    └─────────────┬─────────────┘                 │
│                │                                │                               │
│                └────────────────┬───────────────┘                               │
│                                 ▼                                               │
│             ┌───────────────────────────────────────┐                           │
│             │   Atomic feature quota evaluator      │                           │
│             └───────────────────┬───────────────────┘                           │
└─────────────────────────────────┼───────────────────────────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
                 ▼                                 ▼
   🟢 Allow operation (pass)         🔴 Block — HTTP 402 Payment Required
   (execute & log usage_record)      (prompt: upgrade plan or buy credits)
```

A platform admin can act on `Account Subscriptions` and `Account Credit Balances`
directly, bypassing Razorpay entirely (§6) — the webhook is one path in, not the only
one.

---

## 2. Dual-currency pricing tiers (USD $ & INR ₹)

Plans carry native prices in both currencies (not a dynamic exchange-rate
conversion) — an account picks one currency at subscribe time and stays on it.

| Plan Tier | Price (USD) | Price (INR) | Monthly Email Quota | Monthly AI Quota | Audit Log Access | BYO AI Key? | BYO SMTP? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Free / Trial** | $0 | ₹0 | 1,000 emails | 10 AI runs | UI view only | ❌ | ❌ |
| **Starter** | $19/mo | ₹1,499/mo | 15,000 emails | 150 AI runs | + CSV export | ❌ | Custom SMTP |
| **Pro** | $49/mo | ₹3,999/mo | 100,000 emails | 1,000 AI runs | + API access | ✅ (unlimited) | Postmark + Custom |
| **Enterprise** | Custom — Contact Sales | Custom — Contact Sales | Unlimited | Unlimited | + API access | ✅ (unlimited) | Dedicated IPs |

**These quota/price numbers are a working draft, not yet confirmed final** by the
product owner (`OQ-013` remains open on this point specifically). Everything else on
this page — the architecture, schema, and mechanics — is decided.

Audit logs are **never deleted for any tier** (`DEC-GRX-030` point 3) — the
differentiator across tiers is *export/API access to* the (always-permanent) log, not
retention length.

Enterprise has no fixed self-serve price by design (`DEC-GRX-030` point 4) — it is
contact-sales, activated by a platform admin (§6), matching the existing marketing
site's "Custom pricing / Contact Sales" framing (`(marketing)/pricing-section.tsx`,
`GRX-WEB-002`).

---

## 3. Core database schemas (`apps/api/src/growixa_api/billing/`)

### Table 1: `subscription_plans`

Platform-wide plan catalog — one row per tier, editable by a platform admin (§6.4).

- `id` (UUID, PK)
- `slug` (Text: `free`, `starter`, `pro`, `enterprise`)
- `name` (Text)
- `price_usd` (Numeric(10, 2), nullable — `NULL` for Enterprise's contact-sales tier)
- `price_inr` (Numeric(10, 2), nullable — same)
- `max_contacts` (Integer, nullable — `NULL` = unlimited)
- `max_monthly_emails` (Integer, nullable)
- `max_monthly_ai_runs` (Integer, nullable)
- `max_social_accounts` (Integer, nullable)
- `max_user_seats` (Integer, nullable)
- `allow_byo_ai_key` (Boolean)
- `allow_byo_smtp` (Boolean)
- `audit_export_enabled` (Boolean)
- `audit_api_enabled` (Boolean)
- `created_at` / `updated_at`

No `audit_retention_days` column — audit logs are never purged (`DEC-GRX-030`).

### Table 2: `account_subscriptions`

One row per account (created automatically at registration — see §3.4), tracking the
active plan and a running usage counter for the current billing period.

- `id` (UUID, PK)
- `account_id` (UUID, FK → `accounts.id`, **unique**)
- `plan_id` (UUID, FK → `subscription_plans.id`)
- `status` (Text: `PENDING`, `ACTIVE`, `PAST_DUE`, `CANCELED`, `HALTED` — `PENDING` added
  in `GRX-BILL-004`: set the instant checkout creates the Razorpay Subscription and
  stores its id here, before the customer has actually authorized payment; `plan_id`
  already points at the *target* plan while `PENDING`, but nothing is granted — the
  quota evaluator (§4) only honors `ACTIVE`/`PAST_DUE`)
- `currency` (Text: `USD` or `INR`)
- `current_period_start` / `current_period_end` (DateTime)
- `period_email_used` / `period_ai_used` (Integer, default 0 — running counters, reset
  on each successful `subscription.charged` webhook)
- `razorpay_customer_id` (Text, nullable — `NULL` for Enterprise accounts billed
  outside Razorpay)
- `razorpay_subscription_id` (Text, nullable — same)
- `set_by_platform_admin_id` (UUID, FK → `platform_admins.id`, nullable — set when the
  current plan was assigned by an admin override rather than a real Razorpay checkout,
  mirroring `GRX-SAAS-005`'s `metadata`-based platform-admin-attribution pattern)
- `created_at` / `updated_at`

### Table 3: `account_credit_balances` (the number the quota evaluator reads)

One row per `(account_id, credit_type)` — a plain running balance, never expires.

- `id` (UUID, PK)
- `account_id` (UUID, FK → `accounts.id`)
- `credit_type` (Text: `AI_RUNS`, `EMAIL_SENDS`, `CONTACT_SLOTS`, `SOCIAL_POSTS`)
- `remaining_credits` (Integer, default 0)
- `updated_at` (DateTime)
- Unique constraint on `(account_id, credit_type)`

### Table 4: `account_credit_purchases` (receipt history — audit only, never read by the evaluator)

- `id` (UUID, PK)
- `account_id` (UUID, FK → `accounts.id`)
- `credit_type` (Text)
- `credits_added` (Integer)
- `purchased_at` (DateTime)
- `razorpay_payment_id` (Text, nullable — `NULL` for admin-granted credits, see §6.2)
- `granted_by_platform_admin_id` (UUID, FK → `platform_admins.id`, nullable — set when
  §6.2 was used instead of a real purchase)

### Table 5: `credit_packs` (the top-up catalog — DB-backed, not code-defined)

One row per purchasable top-up pack, editable by a platform admin
(`platform.billing.manage`) without a redeploy — same pattern as `subscription_plans`.
Originally scoped as a code-defined constant (mirroring `DEC-GRX-028`'s prompt-template
precedent); reconsidered before shipping, since a priced catalog is the same *shape* of
thing as `subscription_plans`, not developer-authored text, and the product owner
explicitly wants it admin-editable the same way (`GRX-SAAS-006`).

- `id` (UUID, PK)
- `slug` (Text, unique, e.g. `ai_runs_250`)
- `name` (Text, e.g. "250 AI Runs")
- `credit_type` (Text: `AI_RUNS`, `EMAIL_SENDS`, `CONTACT_SLOTS`, `SOCIAL_POSTS`)
- `credits` (Integer — how many units this pack adds)
- `price_usd` / `price_inr` (Numeric(10, 2), nullable — `NULL` = not purchasable in that
  currency yet; every pack is INR-only today, USD pending Razorpay's international
  payments approval, §8)
- `is_active` (Boolean, default true)
- `created_at` / `updated_at`

### Table 6: `coupon_codes` (new — `DEC-GRX-030` point 6, `GRX-SAAS-012`)

- `id` (UUID, PK)
- `code` (Text, unique, e.g. `WELCOME20`)
- `discount_type` (Text: `PERCENTAGE`, `FIXED_AMOUNT`, `CREDIT_GRANT`)
- `discount_value` (Numeric — percent, or fixed amount in the account's currency, or
  credit quantity, depending on `discount_type`)
- `credit_type` (Text, nullable — only set when `discount_type = CREDIT_GRANT`)
- `applicable_plan_slugs` (JSONB array, nullable — `NULL` = all plans)
- `max_redemptions` (Integer, nullable — `NULL` = unlimited)
- `redemption_count` (Integer, default 0)
- `expires_at` (DateTime, nullable)
- `is_active` (Boolean, default true)
- `created_by_platform_admin_id` (UUID, FK → `platform_admins.id`)
- `created_at` / `updated_at`

### Table 7: `coupon_redemptions` (one row per use — enforces per-account redemption limits, gives real usage analytics)

- `id` (UUID, PK)
- `coupon_code_id` (UUID, FK → `coupon_codes.id`)
- `account_id` (UUID, FK → `accounts.id`)
- `redeemed_at` (DateTime)
- Unique constraint on `(coupon_code_id, account_id)` — a given account can redeem a
  given code once, matching typical SaaS coupon behavior

### 3.4 New-account bootstrap

Every account gets a `Free`-tier `account_subscriptions` row **synchronously at
registration** (`POST /accounts/register`, `GRX-SAAS-003`) — never left absent. The
quota evaluator (§4) assumes exactly one row per account and raises on a missing row
by design (fail loud, not silently permissive); leaving this to a lazy/best-effort
creation elsewhere would make that failure mode reachable in production.

---

## 4. Atomic quota evaluator (`GRX-BILL-005`, shipped)

Single running balance (Table 3) makes the "was the overage covered by credits"
check a single atomic `UPDATE`, with no multi-batch traversal needed. The shape below
is what actually shipped in `billing/services.py` — it corrects one bug an earlier
draft of this section had (the `f"..."` string-formatting trick doesn't actually match
this schema: `"ai_run".upper()` is `"AI_RUN"`, but the real `credit_type` value is
`"AI_RUNS"`; `check_and_consume_quota` uses an explicit per-operation table instead)
and adds one rule the earlier draft never specified: **which subscription statuses get
to use their `plan_id`'s real limits.**

```python
@dataclass(frozen=True)
class _MeteredOperation:
    period_used_attr: str
    plan_limit_attr: str
    credit_type: str


_METERED_OPERATIONS = {
    "email": _MeteredOperation(
        "period_email_used", "max_monthly_emails", "EMAIL_SENDS"
    ),
    "ai_run": _MeteredOperation("period_ai_used", "max_monthly_ai_runs", "AI_RUNS"),
}

# PENDING (checkout not yet confirmed -- plan_id already points at the *target* plan
# per set_pending_subscription, §4a, so it must not be trusted yet) and HALTED (billing
# broken) both fall back to the Free plan's allowance instead of plan_id's. CANCELED
# stays here deliberately: the webhook handler (§5) leaves current_period_end untouched
# on cancellation so the account keeps its plan's features until the period genuinely
# ends -- the cancellation-downgrade ticker (GRX-BILL-006) is what actually rewrites
# plan_id, not this evaluator.
_STATUSES_HONORING_PLAN_LIMITS = frozenset({"ACTIVE", "PAST_DUE", "CANCELED"})


async def check_and_consume_quota(
    session: AsyncSession,
    *,
    account_id: UUID,
    operation: Literal["email", "ai_run"],
    qty: int = 1,
) -> None:
    spec = _METERED_OPERATIONS[operation]

    # 1. Lock the subscription row & read the running monthly counter + plan limit
    subscription, plan = await get_locked_account_subscription_with_plan(
        session, account_id
    )
    limit = (
        getattr(plan, spec.plan_limit_attr)
        if subscription.status in _STATUSES_HONORING_PLAN_LIMITS
        else getattr(await get_plan_by_slug(session, "free"), spec.plan_limit_attr)
    )
    current_used = getattr(subscription, spec.period_used_attr)

    # NULL limit = unlimited (Enterprise, or an admin-overridden plan)
    if limit is None:
        setattr(subscription, spec.period_used_attr, current_used + qty)
        await session.commit()
        return

    # Case A: fully covered by the monthly plan allowance
    if current_used + qty <= limit:
        setattr(subscription, spec.period_used_attr, current_used + qty)
        await session.commit()
        return

    # Case B: plan allowance partially or fully exhausted -- cover the exact overage
    # from the credit balance, not the full qty (fixes the double-charge bug found
    # reviewing an earlier draft of this design).
    already_covered = max(0, limit - current_used)
    needed_extra = qty - already_covered

    result = await session.execute(
        text("""
            UPDATE account_credit_balances
            SET remaining_credits = remaining_credits - :needed, updated_at = NOW()
            WHERE account_id = :account_id
              AND credit_type = :credit_type
              AND remaining_credits >= :needed
            RETURNING remaining_credits
        """),
        {
            "needed": needed_extra,
            "account_id": account_id,
            "credit_type": spec.credit_type,
        },
    )

    if result.first() is not None:
        setattr(subscription, spec.period_used_attr, limit)  # monthly side maxed out
        await session.commit()
        return

    # Case C: neither the plan allowance nor credits cover it -- block
    await session.rollback()
    raise QuotaExceededError(operation)  # the route layer maps this to HTTP 402
```

`with_for_update()` on the subscription row plus the single atomic credit `UPDATE`
closes the race condition an earlier draft had (two concurrent requests both reading
"under the limit" before either wrote back). `check_and_consume_quota` commits its own
transaction on every path (success or `QuotaExceededError`) — callers must call it
before any other uncommitted work they want to survive a block, same as `generate()`
below calling it before the provider call.

**Duplicated on the worker side.** The email path is metered from
`apps/worker/send_campaign.py`, not `apps/api` — the worker has its own thin,
hand-kept-in-sync copy of this logic (`growixa_worker/billing_quota.py`,
`check_and_consume_email_quota`), consistent with how `apps/worker/models.py` already
duplicates the handful of `growixa_api` tables it touches rather than depending on
`growixa_api` as a library (`MODULE_BOUNDARIES.md`). It's called once per recipient,
immediately before the real SMTP send, inside `handle_send_campaign`'s existing loop —
a blocked recipient gets a `FAILED` `MessageDelivery`/`DeliveryAttempt` with an
explanatory `error_message`, and the loop continues to the next recipient rather than
aborting the whole campaign.

### 4.1 AI credit metering only applies when Growixa is paying for the call

Only generations run on the **platform-provided** LLM consume the `AI_RUNS` quota —
generations run on the account's own **bring-your-own** key never do, since Growixa
incurs zero inference cost for those. This is already implied by the pricing table's
"BYO AI Key: ✅ Unlimited" cell (§2); this section makes the mechanism explicit.

`ai/providers/factory.py`'s `get_effective_ai_provider()` (built in `GRX-AI-003`) is
the one place that already knows which path resolved the call — its resolution order
is the account's active `ai_provider_connections` row first, else
`platform_ai_provider_config`, else `AINotConfiguredError`. Its return type,
`ResolvedAIProvider`, currently has no field distinguishing the two paths:

```python
@dataclass
class ResolvedAIProvider:
    provider: AIModelProvider
    provider_name: str
    model: str
```

This needs one addition — a `source` discriminator, set inside
`get_effective_ai_provider()` depending on which branch actually resolved:

```python
@dataclass
class ResolvedAIProvider:
    provider: AIModelProvider
    provider_name: str
    model: str
    source: Literal["ACCOUNT_BYO", "PLATFORM_DEFAULT"]
```

`ai/services.py`'s `generate()` then branches on `resolved.source`:

```python
resolved = await get_effective_ai_provider(session, account_id)
if resolved.source == "PLATFORM_DEFAULT":
    await check_and_consume_quota(
        session, account_id=account_id, operation="ai_run", qty=1
    )
# else: ACCOUNT_BYO -- no quota check, unlimited by design
result = await capability_module.run(
    capability_input, resolved.provider, resolved.model
)
```

Quota is checked **before** the provider call (a flat "1 generation = 1 credit," not
token-metered — matches the pricing table's "10 / 150 / 1,000 AI runs/mo" framing) so
an over-quota account is blocked before Growixa spends real platform LLM budget on a
call that was never going to be allowed. `QuotaExceededError` propagates out of
`generate()` uncaught (no `ai_generations` row is written for a blocked call, same
shape as the pre-existing `AINotConfiguredError` case) — `ai/api.py`'s
`generate_content_route` maps it to `HTTP 402` with the same
`{"error": "QUOTA_EXCEEDED", "message": ..., "upgrade_url": "/dashboard/billing"}` body
shape every other quota-blocked route in this document uses. This is a distinct, new
counter from the `usage_records` row `generate()` already writes on every call — that
one is Sprint 1's raw usage telemetry (what the platform-admin usage dashboard reads);
`period_ai_used` and `account_credit_balances` are the new billing-specific counters
this document adds. Both are written on the same successful call; neither replaces the
other.

### 4b. Point-in-time cap checks (inventory-style resources)

Contacts, social accounts, and user seats aren't period-metered — there's no monthly
counter to reset, just "how many do you have right now vs. your plan's limit." A
second, simpler function handles these:

```python
async def check_plan_limit(
    session: AsyncSession,
    *,
    account_id: UUID,
    limit_attr: str,
    current_count: int,
    resource: str,
) -> None:
    subscription = await get_account_subscription(session, account_id)
    plan = await session.get(SubscriptionPlan, subscription.plan_id)
    limit = (
        getattr(plan, limit_attr)
        if subscription.status in _STATUSES_HONORING_PLAN_LIMITS
        else getattr(await get_plan_by_slug(session, "free"), limit_attr)
    )
    if limit is not None and current_count >= limit:
        raise PlanLimitExceededError(resource)  # the route layer maps this to HTTP 402
```

No row lock here (unlike `check_and_consume_quota`) — there's no counter to
increment-and-commit, and a lock on `account_subscriptions` wouldn't serialize a
`COUNT(*)` against an unrelated table anyway. This is a deliberately best-effort,
not-strictly-serializable check: two simultaneous creates for the same account right at
the boundary could both pass, the same tolerance most soft plan-limit enforcement
accepts. Wired into three creation endpoints, each supplying its own `COUNT(*)`:

- `POST /contacts` (`contacts/services.py`'s `create_or_update_contact`, create branch
  only) — `limit_attr="max_contacts"`, counting `contacts` rows with `status = 'ACTIVE'`.
- `GET /social/oauth/callback` (`social/services.py`'s `complete_oauth_callback`) —
  `limit_attr="max_social_accounts"`, counting `social_connections` rows with
  `is_active = true`, **excluding** the provider being (re)connected right now, so
  refreshing an already-connected platform's token never trips the cap (one active
  connection per provider, `DEC-GRX-025` — a reconnect deactivates-then-recreates, it
  never grows the count).
- `POST /users/invitations/accept` (`users/services.py`'s `accept_invitation` — the
  actual seat-creation point, not `invite_user`, which only creates a pending
  invitation and costs nothing) — `limit_attr="max_user_seats"`, counting `users` rows
  with `status = 'ACTIVE'`.

**Known gap, deliberately out of this pass's scope:** CSV bulk contact import
(`POST /contacts/import`, `contacts/services.py`'s `import_contacts_from_csv`) is not
capped. Wiring it in raises a real product question this task didn't have an answer
for — does one over-cap row abort the whole import, or import up to the cap and mark
the rest `SKIPPED`? — rather than a mechanical repeat of the single-create wiring
above. Follow-up, not silently dropped.

---

## 4a. Customer checkout (`GRX-BILL-004`)

Two authenticated routes, both gated `billing.manage`, both resolving price/plan
server-side from the DB only — never from client input (`THREAT_MODEL.md` T62):

### `POST /billing/subscribe` — subscribe or change plan

1. Looks up `subscription_plans` by `plan_slug` (`starter`/`pro` only — Free needs no
   checkout, Enterprise is contact-sales/admin-only, §2).
2. Reads that plan's `razorpay_plan_id_usd`/`_inr` for the requested currency; `NULL`
   (not yet synced for that currency, e.g. USD before international payments are
   approved, §8) is a `400`, not a crash.
3. Calls Razorpay to create the Subscription (`total_count` set to a large fixed number
   of monthly cycles — Razorpay has no "renews forever" option; a real cancellation
   still works via the webhook regardless of this number).
4. **Immediately** stores the returned `razorpay_subscription_id` on the account's row
   and sets `status = PENDING`, `plan_id` = the target plan. This has to happen before
   the customer even sees Razorpay's checkout widget — the webhook (§5) finds this row
   by `razorpay_subscription_id`, and if that column were still empty when
   `subscription.charged` fires, the webhook would have nothing to update.
5. Returns `{razorpay_subscription_id, razorpay_key_id}` for the frontend's Checkout.js
   widget. Nothing is granted yet — only the webhook flips `PENDING` → `ACTIVE`.

### `POST /billing/topup` — buy a top-up credit pack

1. Looks up `credit_packs` by `pack_slug`; `NULL` price for the requested currency is a
   `400`, same as above.
2. Creates a one-time Razorpay Order (not a Subscription — top-ups are single
   payments), with `notes = {kind: "credit_topup", account_id, credit_type, credits}` —
   this is the exact marker `payment.captured`'s handler (§5) looks for.
3. Returns `{razorpay_order_id, razorpay_key_id, amount_smallest_unit, currency}`.
   **No DB write happens here at all** — unlike subscribing, there's no `PENDING` state
   to worry about, since credits are only ever granted by the webhook once payment is
   actually captured.

Both routes are live-verified against the real Razorpay Test Mode account (INR) —
see `GRX-BILL-004`'s `MASTER_TASK_TRACKER.md` evidence for the full round-trip.

## 4c. Billing read endpoints + customer billing page (`GRX-BILL-007`)

Every route/schema/repository/service function built through `GRX-BILL-006` was
write-side only — nothing existed yet for a page to actually *read* the account's
current plan, usage, or the plan/pack catalogs, so this task added three `billing.view`
read routes alongside the frontend page:

- `GET /billing/subscription` → current plan (nested, full `SubscriptionPlanOut`),
  `status`, `currency`, `current_period_start`/`current_period_end`,
  `period_email_used`/`period_ai_used`, and every `account_credit_balances` row the
  account has (a credit type with no purchase/grant yet simply has no row — the
  frontend defaults it to `0`, not a `404`).
- `GET /billing/plans` → the full `subscription_plans` catalog, ascending by
  `price_usd` (Enterprise's `NULL` price last).
- `GET /billing/credit-packs` → the active `credit_packs` catalog.

All three reuse `billing.view` (not `billing.manage`) — matching RBAC.md's own framing
("View the account's current plan, usage/quota bars, and billing history") and this
codebase's read/write permission split everywhere else in this module. Read-only, no
row lock (unlike `check_and_consume_quota`'s `get_locked_account_subscription_with_plan`)
— `get_account_subscription_with_plan` is the unlocked counterpart used here.

**Frontend**: `/dashboard/billing` (`apps/web/src/app/(dashboard)/dashboard/billing/`)
— current plan card with usage bars and credit balances, a plan comparison grid
(Subscribe/Upgrade, gated `billing.manage`), a credit-pack top-up grid (Buy, gated
`billing.manage`), and a currency toggle (defaults to the account's own
`subscription.currency`). Both actions call their respective `POST` route then open
Razorpay's real Checkout.js widget client-side (`apps/web/src/lib/razorpay.ts`, a thin
typed wrapper, script loaded lazily from Razorpay's CDN — not bundled, matching this
codebase's thin-adapter convention for every other third-party integration). Checkout's
own success callback only means the customer submitted payment details — the actual
plan/credit change still lands via the webhook (§5) asynchronously, so the page does a
best-effort re-fetch of `/billing/subscription` a few seconds later rather than
optimistically updating state itself.

Live-verified against the real Razorpay Test Mode account: `/billing/subscribe` opened
a real Checkout.js session showing the correct plan/price/recurring terms; `/billing/topup`
opened a real order-based session; both correctly flipped the account's real DB state
beforehand (`PENDING`/target plan for subscribe, no DB write for topup, per §4a).

---

## 5. Razorpay Subscriptions webhook + cancellation-downgrade ticker

### Webhook handler (`POST /billing/razorpay`)

Signature-verified before touching any table (mirrors the existing Postmark webhook's
"verify before touching any table" shape, `GRX-EMAIL-005`).

| Razorpay event | Effect |
|---|---|
| `subscription.activated` / `subscription.charged` | `status = ACTIVE`; update `current_period_end`; reset `period_email_used`/`period_ai_used` to 0 |
| `subscription.halted` | `status = HALTED` (payment method failing — Razorpay's own retry state) |
| `subscription.cancelled` | `status = CANCELED`; account **keeps** its current plan's features until `current_period_end` — no immediate downgrade |
| `payment.captured` (top-up order, not a subscription charge) | Atomically increments `account_credit_balances.remaining_credits`; inserts one `account_credit_purchases` receipt row |

### Cancellation-downgrade ticker (`GRX-BILL-006`, shipped)

A `CANCELED` subscription isn't downgraded by the webhook itself — nothing fires again
at `current_period_end`. This codebase's established ticker pattern
(`GRX-SCHED-002`, `GRX-SOCIAL-007`) is **not** a separate `apps/worker` CLI job on a
cron schedule — both existing tickers (campaigns, social) run as an in-process asyncio
loop started from `app.py`'s FastAPI `lifespan`, polling on an interval, alongside the
main API process. `billing/scheduler.py`'s `run_downgrade_loop` follows the exact same
shape, registered as a third background task in `lifespan` next to the other two. The
poll interval is deliberately coarse (`billing_downgrade_poll_interval_seconds`,
default 3600s/hourly) — unlike a scheduled send/post where a few seconds of lateness is
user-visible, a subscription downgrade only ever needs to land sometime within the day
its period actually ends.

```python
async def downgrade_expired_cancellations(session: AsyncSession) -> int:
    free_plan = await get_plan_by_slug(session, "free")
    now = datetime.now(UTC)
    result = await session.execute(
        text("""
            UPDATE account_subscriptions
            SET plan_id = :free_plan_id,
                status = 'ACTIVE',
                current_period_start = :period_start,
                current_period_end = :period_end,
                period_email_used = 0,
                period_ai_used = 0,
                razorpay_subscription_id = NULL,
                set_by_platform_admin_id = NULL,
                updated_at = :now
            WHERE status = 'CANCELED' AND current_period_end <= :now
            RETURNING account_id
        """),
        {
            "free_plan_id": free_plan.id,
            "period_start": now,
            "period_end": now + timedelta(days=FREE_PLAN_PERIOD_DAYS),
            "now": now,
        },
    )
    downgraded_count = len(result.fetchall())
    await session.commit()
    return downgraded_count
```

This corrects two gaps the earlier draft's minimal `SET plan_id, status` pseudocode
had:

- **A downgraded account would otherwise never get a fresh billing period again.** Its
  monthly counters (`period_email_used`/`period_ai_used`) only ever reset via a real
  `subscription.charged` webhook (§5's table above) — but a downgraded-to-Free account
  has no real Razorpay Subscription left to ever send one. The ticker has to do what
  that webhook would have done: reset both counters to `0` and roll
  `current_period_start`/`current_period_end` forward by a fresh
  `FREE_PLAN_PERIOD_DAYS` (30) days, the same period length a brand-new signup gets
  (§3.4).
- **`razorpay_subscription_id` is cleared**, not left pointing at the now-fully-dead
  subscription — closes a low-probability but real edge case where a delayed or
  replayed webhook event for that same id could otherwise flip status back to `ACTIVE`
  on the old paid `plan_id` (the webhook handlers, §5's table, look up purely by
  `razorpay_subscription_id` and trust whatever they find). `razorpay_customer_id` is
  deliberately *not* cleared — that's the person's durable Razorpay identity, reusable
  if they resubscribe later. `set_by_platform_admin_id` is cleared too, since it no
  longer reflects who set the plan the account is actually on once the ticker is what
  changed it.

---

## 6. Platform-admin subscription management (`GRX-SAAS-006`, shipped)

Not new scope — this is exactly what `GRX-SAAS-006`'s tracker row already describes
("View/change plans, trial extensions, usage credits"). `DEC-GRX-030` makes it
concrete. Every action bypasses Razorpay entirely — no payment, no webhook required —
and is gated `platform.billing.manage` (owner + finance only, `RBAC.md`), via
`require_platform_permission` same as every other platform-admin route.

`platform_admin/api.py`/`services.py` never write `billing/`'s tables directly
(`MODULE_BOUNDARIES.md`) — every route below calls into a new `billing/services.py`
`admin_*` function (`admin_override_subscription`, `admin_grant_credits`,
`admin_create_plan`/`admin_update_plan`, `admin_create_credit_pack`/
`admin_update_credit_pack`), which does the actual table write but deliberately does
**not** commit — the platform_admin wrapper adds an audit-log entry
(`account.subscription_overridden`, `account.credits_granted`,
`subscription_plan.created`/`updated`, `credit_pack.created`/`updated`) and commits
both together in one transaction, matching `update_account_status`/`pause_campaign`'s
existing shape exactly.

### 6.1 Manual plan/status override

`GET`/`PATCH /platform/accounts/{account_id}/subscription` — sets `plan_id` (looked up
by slug, no `Literal` restriction unlike `SubscribeIn`) and/or `status` directly,
stamping `set_by_platform_admin_id`. §6.1 and §6.3 from the original draft are
**merged into this one endpoint** — a separate `PATCH /platform/accounts/{id}/status`
already exists for `accounts.status` (`GRX-SAAS-005`), so a same-shaped billing-status
route would have collided on path; one call accepting either field (or both) avoided
the collision and is more ergonomic besides. Used for Enterprise activation (§2),
trial extensions, support-driven upgrades/downgrades, or comping an account.

### 6.2 Manual credit grant

`POST /platform/accounts/{account_id}/credits/grant` — atomically increments
`account_credit_balances` (same table, same shape §4 reads from — no separate code
path for "admin credits" vs "purchased credits"), inserts an
`account_credit_purchases` row with `razorpay_payment_id = NULL` and
`granted_by_platform_admin_id` set, so grants remain distinguishable from real
purchases in the receipt history without needing a different balance mechanism.

### 6.3 Plan catalog: create + edit

`GET`/`POST /platform/subscription-plans`, `PUT /platform/subscription-plans/{id}` —
a genuine *create*, not just edit, per the product owner's explicit request. This
required widening `subscription_plans.slug`'s CHECK constraint (migration
`e3e939e991f4`) from a fixed 4-value whitelist to a plain slug-format check — the old
constraint made "create a new tier" a lie, since any admin-authored slug beyond
free/starter/pro/enterprise would have violated it at insert time. A newly-created
tier is **not** automatically self-serve-checkout-able: `POST /billing/subscribe`'s
`SubscribeIn.plan_slug` (`GRX-BILL-004`) stays a deliberate `Literal["starter", "pro"]`
until wiring a new tier into customer-facing checkout is a real, separate ask (open
item, §8) — an admin can still grant a new plan to any account directly via §6.1 today,
and it shows up in the customer billing page's plan grid (`GRX-BILL-007`) without a
Subscribe button. `slug` is immutable on edit (only settable at creation) — it's
referenced by string literal elsewhere in the codebase (the Free-plan bootstrap
lookup, `SubscribeIn`'s Literal).

### 6.4 Credit pack catalog: create + edit

`GET`/`POST /platform/credit-packs`, `PUT /platform/credit-packs/{id}` — same
create/edit shape as plans. The admin-facing `GET` deliberately does **not** filter to
`is_active` (unlike the customer-facing `GET /billing/credit-packs`, `GRX-BILL-007`) —
an admin managing the catalog needs to see (and reactivate) deactivated packs too.

Editing a plan/pack affects every account on it going forward; it does not
retroactively change `account_subscriptions` rows already past their
`current_period_start`. This is how Enterprise accounts get individually-negotiated
terms in practice: either a dedicated per-account plan row, or a direct
`account_subscriptions` override via §6.1.

---

## 7. Coupon & discount engine (new scope — `DEC-GRX-030` point 6, `GRX-SAAS-012`)

### 7.1 Coupon types

- **Percentage discount** (`WELCOME20` → 20% off) — **top-up (`POST /billing/topup`)
  only**, see the Razorpay constraint below.
- **Fixed-amount discount** (`LAUNCH10` → $10 / ₹800 off, in the account's currency)
  — **top-up only**, same constraint.
- **Free credit grant** (`FREEAI250` → +250 `AI_RUNS` credited directly to
  `account_credit_balances`, redeemed via `POST /billing/redeem-coupon`, no discount
  on any checkout)

**Corrected from this section's original draft**: percentage/fixed-amount coupons
are *not* applied to `POST /billing/subscribe`. Verified against Razorpay's own docs
(`razorpay.com/docs/payments/offers/` and the Checkout.js integration reference) —
Offers/discounts are an Orders-API (one-time payment) feature; Checkout.js documents
no `offer_id`/`discount`/`coupon` parameter for Subscription checkout, and a
Subscription's price is fixed by its Razorpay `Plan`. `SubscribeIn` therefore has no
`coupon_code` field. Percentage/fixed-amount coupons apply cleanly to
`POST /billing/topup` instead, since a top-up is a `Razorpay Order` whose amount is
computed server-side before the order is created — `create_topup_checkout`
(`billing/services.py`) applies the discount to `amount_smallest_unit` before calling
the gateway.

### 7.2 Platform-admin management (`/platform/coupons`)

- `GET /platform/coupons` — list the full catalog (active and inactive), gated
  `platform.billing.manage`.
- `POST /platform/coupons` — create (`code`, `discount_type`, `discount_value`,
  `credit_type` — required and only meaningful for `CREDIT_GRANT`,
  `applicable_plan_slugs`, `max_redemptions`, `expires_at`). Rejects a duplicate
  `code` (`409`) and a `CREDIT_GRANT` coupon missing `credit_type` (`400`).
- `PATCH /platform/coupons/{id}` — toggle `is_active` only; there is no field-editing
  PUT (mirrors "coupons are created right or deactivated," not silently mutated
  mid-campaign). `404` if the id doesn't exist.
- Each write records a `coupon.created`/`coupon.updated` audit-log entry
  (`platform_admin/services.py`, same one-transaction commit pattern as
  `admin_override_subscription`/`admin_create_plan`) and shows `redemption_count`
  directly on `CouponOut` for at-a-glance redemption analytics — same list shape as
  `/platform/subscriptions`.
- Frontend: `/platform/coupons` (sidebar entry under `platform.billing.manage`).

### 7.3 Customer-facing redemption

Two distinct paths, matching the type split in §7.1:

- **`POST /billing/redeem-coupon`** (`{code}`) — `CREDIT_GRANT` coupons only. Credits
  the account immediately via the same `grant_credits` path platform-admin grants use
  (`granted_by_platform_admin_id` is `NULL` for a coupon-driven grant; the
  `coupon_redemptions` row is the real provenance record for that case — see the
  known minor ambiguity noted in §7.4). Never touches Razorpay. A `PERCENTAGE`/
  `FIXED_AMOUNT` code here returns `400` (`CouponWrongTypeForActionError`).
  Frontend: a coupon-code field under "Credit balances" on `/dashboard/billing`.
- **`POST /billing/topup`'s optional `coupon_code`** — `PERCENTAGE`/`FIXED_AMOUNT`
  coupons only (`CREDIT_GRANT` here also returns `400`). Frontend: a coupon-code
  field above the "Top up credits" pack grid, applied to whichever pack is bought.

Both paths run the same validation (`_validate_coupon_for_redemption`,
`billing/services.py`): `is_active`, not expired, `redemption_count <
max_redemptions`, plan eligibility (`applicable_plan_slugs`, when set), and the
`(coupon_code_id, account_id)` uniqueness constraint — one redemption per account per
code, enforced by both an app-level pre-check and `coupon_redemptions`' unique index.
Both routes are also rate-limited (`THREAT_MODEL.md` T65) via the same Redis-backed
fixed-window limiter `auth/api.py` uses for login, keyed on source IP rather than
account_id/email — coupon farming defeats the per-account uniqueness constraint
precisely by using many real accounts, so the limiter needs to key on something an
attacker can't cheaply multiply the way they can spin up accounts.

**Redemption-timing tradeoff**: `record_coupon_redemption` is called *after* the real
Razorpay gateway call succeeds (a failed gateway call never wastes a coupon) but
*before* the customer completes the Checkout.js widget payment. This accepts
"abandoned checkout wastes the coupon" (same class of gap as open item §8.5) in
exchange for closing a worse race: two parallel top-up requests both reading
`redemption_count` before either writes would otherwise let one coupon apply twice.

### 7.4 Known minor ambiguity

A coupon-driven `CREDIT_GRANT` redemption produces the same `NULL
razorpay_payment_id` + `NULL granted_by_platform_admin_id` shape in
`account_credit_purchases` as would any other non-payment, non-admin grant, if one
existed. There isn't a schema column that alone distinguishes "platform-admin grant"
from "coupon redemption" today, both of which are already-possible states —
`coupon_redemptions` is the real provenance source of truth for the coupon case.
Not fixed with a new column here; the two grant paths are already fully
distinguishable by joining `coupon_redemptions`, and no operational need for a
denormalized marker has come up yet.

---

## 8. Open items

Implementation is underway (`GRX-BILL-002`–`007` and `GRX-SAAS-006` are `DONE` as of
this update). Remaining open items:

1. **USD/international payments are not yet enabled on the Razorpay account** — found
   live while running `GRX-BILL-002`'s plan-sync CLI: Razorpay rejects `currency: USD`
   outright ("Currency provided is not supported"). This is an account-level approval
   Razorpay requires beyond basic signup, not something fixable in code. Every plan
   and credit pack today only has an INR price (`price_usd` is `NULL` everywhere) —
   checkout (§4a) correctly returns `400` for a USD request rather than a confusing
   gateway error. USD support is on the product owner to request from Razorpay
   directly; the code path is already built and will work the moment a USD
   `razorpay_plan_id`/price exists.
2. **Final plan quota numbers and Starter/Pro/credit-pack prices** (§2's table, §3
   Table 5) remain a working draft, accepted by the product owner as the starting
   point — changeable anytime via `platform.billing.manage` (`GRX-SAAS-006`, which
   also needs *create*, not just edit, per the product owner's explicit request).
3. **Whether "Bring Your Own AI Key" and self-hosted/Modal-style providers should be
   treated as one of the four existing adapters** (`OpenAI`/`Azure OpenAI`/
   `Anthropic`/`Ollama`, per `DEC-GRX-026`) **or need a fifth adapter** — a
   self-hosted model server (e.g. on Modal) can already work today *if* it exposes an
   OpenAI- or Ollama-compatible endpoint (the same mechanism Krutrim uses via the
   `OpenAIProvider`'s `base_url` override), but that's a specific technical path, not
   an automatic "Modal support" checkbox. Not yet confirmed with the product owner.
4. **Whether multiple named "Brand Voices" per account (as implied by the pricing
   table's "1 / 5 / Unlimited Brand Voices" row) is real scope for this pass.**
   `brand_profiles` today is one row per account, read as a single value in every AI
   generation call (`ai/services.py`) — supporting several *selectable* brand voices
   per account is a schema change (a `brand_voices` table) and an AI-capability UI
   change, not a billing-layer concern. Recommend scoping this out of the billing
   work and treating it as a separate, later `GRX-AI-*` follow-up task if the product
   owner still wants it, rather than blocking billing on it.
5. **Abandoned checkouts leave a row in `PENDING` indefinitely** — if a customer
   starts `POST /billing/subscribe` but never completes Razorpay's Checkout widget,
   nothing currently cleans that row up (it just never receives a
   `subscription.activated`/`charged` webhook). Not a security issue — `PENDING`
   grants nothing — but worth a follow-up ticker or TTL if it becomes an operational
   annoyance (e.g. a stale subscribe attempt blocking a later real one).
6. **CSV bulk contact import isn't capped** (§4b) — only the single-contact-create
   endpoint is. Needs a product decision (abort vs. partial-import-then-skip) before
   it can be wired in, not just a mechanical repeat of the other point-in-time checks.
7. **"Social posts" is not a capped resource, despite `GRX-BILL-005`'s original
   tracker description grouping it with contacts/social-accounts/user-seats.** There's
   no `max_social_posts` column on `subscription_plans`, and §2's pricing table caps
   only email/AI quotas — no plan-level post limit was ever actually decided. Scoped
   out of `GRX-BILL-005` rather than inventing an uncommitted business rule (e.g. would
   it be a lifetime cap or a monthly one?); revisit only if the product owner
   confirms real demand for it.
8. **A platform-admin-created plan tier isn't wired into self-serve checkout** (§6.3)
   — `POST /billing/subscribe`'s `plan_slug` stays `Literal["starter", "pro"]`
   deliberately. An admin can still grant a new tier to any account directly (§6.1),
   and it shows up read-only in the customer billing page's plan grid, but a customer
   can't self-serve-subscribe to it yet. Revisit once the product owner actually wants
   a fifth self-serve tier, rather than guessing at the checkout-eligibility rule now.
