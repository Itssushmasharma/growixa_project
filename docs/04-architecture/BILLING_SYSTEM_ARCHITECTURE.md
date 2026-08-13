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
- `status` (Text: `ACTIVE`, `PAST_DUE`, `CANCELED`, `HALTED`)
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

### Table 5: `coupon_codes` (new — `DEC-GRX-030` point 6, `GRX-SAAS-012`)

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

### Table 6: `coupon_redemptions` (one row per use — enforces per-account redemption limits, gives real usage analytics)

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

## 4. Atomic quota evaluator

Single running balance (Table 3) makes the "was the overage covered by credits"
check a single atomic `UPDATE`, with no multi-batch traversal needed:

```python
async def check_and_consume_quota(
    session: AsyncSession, account_id: UUID, operation: str, qty: int = 1
) -> bool:
    # 1. Lock the subscription row & read the running monthly counter + plan limit
    sub = await session.execute(
        select(AccountSubscription, SubscriptionPlan)
        .join(SubscriptionPlan)
        .where(AccountSubscription.account_id == account_id)
        .with_for_update()
    )
    sub_row, plan = sub.one()  # raises if the bootstrap in §3.4 was ever skipped

    current_used = getattr(sub_row, f"period_{operation}_used")
    plan_limit = getattr(plan, f"max_monthly_{operation}s")

    # NULL plan_limit = unlimited (Enterprise, or an admin-overridden plan)
    if plan_limit is None:
        setattr(sub_row, f"period_{operation}_used", current_used + qty)
        return True

    # Case A: fully covered by the monthly plan allowance
    if current_used + qty <= plan_limit:
        setattr(sub_row, f"period_{operation}_used", current_used + qty)
        return True

    # Case B: plan allowance partially or fully exhausted -- cover the exact overage
    # from the credit balance, not the full qty (fixes the double-charge bug found
    # reviewing an earlier draft of this design).
    already_covered = max(0, plan_limit - current_used)
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
        {"needed": needed_extra, "account_id": account_id, "credit_type": operation.upper()},
    )

    if result.rowcount > 0:
        setattr(sub_row, f"period_{operation}_used", plan_limit)  # monthly side maxed out
        return True

    # Case C: neither the plan allowance nor credits cover it -- block
    raise HTTPException(
        status_code=402,
        detail={
            "error": "QUOTA_EXCEEDED",
            "message": f"You have reached your limit for {operation}.",
            "upgrade_url": "/dashboard/billing",
        },
    )
```

`with_for_update()` on the subscription row plus the single atomic credit `UPDATE`
closes the race condition an earlier draft had (two concurrent requests both reading
"under the limit" before either wrote back).

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
    await check_and_consume_quota(session, account_id, operation="ai_run", qty=1)
# else: ACCOUNT_BYO -- no quota check, unlimited by design
result = await capability_module.run(capability_input, resolved.provider, resolved.model)
```

Quota is checked **before** the provider call (a flat "1 generation = 1 credit," not
token-metered — matches the pricing table's "10 / 150 / 1,000 AI runs/mo" framing) so
an over-quota account is blocked before Growixa spends real platform LLM budget on a
call that was never going to be allowed. This is a distinct, new counter from the
`usage_records` row `generate()` already writes on every call — that one is Sprint 1's
raw usage telemetry (what the platform-admin usage dashboard reads); `period_ai_used`
and `account_credit_balances` are the new billing-specific counters this document
adds. Both are written on the same successful call; neither replaces the other.

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

### Cancellation-downgrade ticker (`apps/worker`)

A `CANCELED` subscription isn't downgraded by the webhook itself — nothing fires again
at `current_period_end`. Following this codebase's established ticker pattern
(`GRX-SCHED-002`, `GRX-SOCIAL-007`), a daily worker job performs the actual downgrade:

```python
# python -m growixa_worker.jobs.subscription_downgrade_ticker (daily, 00:30 UTC)
async def process_expired_cancellation_downgrades(session: AsyncSession) -> None:
    free_plan_id = await get_free_plan_id(session)
    await session.execute(
        text("""
            UPDATE account_subscriptions
            SET plan_id = :free_plan_id, status = 'ACTIVE'
            WHERE status = 'CANCELED' AND current_period_end <= NOW()
        """),
        {"free_plan_id": free_plan_id},
    )
    await session.commit()
```

---

## 6. Platform-admin subscription management (`GRX-SAAS-006`)

Not new scope — this is exactly what `GRX-SAAS-006`'s tracker row already describes
("View/change plans, trial extensions, usage credits"). `DEC-GRX-030` makes it
concrete. All four actions bypass Razorpay entirely — no payment, no webhook required
— and are gated the same way `GRX-SAAS-005`/`006` already gate platform-admin routes
(`require_platform_permission`, `platform.finance`/`platform.admin` roles per that
row's own acceptance criterion).

### 6.1 Manual plan override

`PATCH /platform/accounts/{id}/subscription` — sets `plan_id` (and optionally
`status`) directly, stamping `set_by_platform_admin_id`. Used for Enterprise
activation (§2), trial extensions, support-driven upgrades/downgrades, or comping an
account.

### 6.2 Manual credit grant

`POST /platform/accounts/{id}/credits/grant` — atomically increments
`account_credit_balances` (same table, same shape §4 reads from — no separate code
path for "admin credits" vs "purchased credits"), inserts an
`account_credit_purchases` row with `razorpay_payment_id = NULL` and
`granted_by_platform_admin_id` set, so grants remain distinguishable from real
purchases in the receipt history without needing a different balance mechanism.

### 6.3 Subscription status control

`PATCH /platform/accounts/{id}/status` (billing-specific status, distinct from
`accounts.status` which `GRX-SAAS-005` already controls) — sets `ACTIVE`/`PAST_DUE`/
`HALTED`/`CANCELED` directly, for support cases where Razorpay's own state needs a
manual override (e.g. a payment dispute resolved outside Razorpay).

### 6.4 Plan-wide quota/price editing

`PUT /platform/subscription-plans/{id}` — edits a plan's quotas and prices platform-
wide (affects every account on that plan going forward; does not retroactively change
`account_subscriptions` rows already past their `current_period_start`). This is how
Enterprise accounts get individually-negotiated terms in practice: either a dedicated
per-account plan row, or a direct `account_subscriptions` override via §6.1.

---

## 7. Coupon & discount engine (new scope — `DEC-GRX-030` point 6, `GRX-SAAS-012`)

### 7.1 Coupon types

- **Percentage discount** (`WELCOME20` → 20% off the first charge)
- **Fixed-amount discount** (`LAUNCH10` → $10 / ₹800 off, in the account's currency)
- **Free credit grant** (`FREEAI250` → +250 `AI_RUNS` credited directly to
  `account_credit_balances`, no discount on the subscription price itself)

### 7.2 Platform-admin management (`/platform/coupons`)

Create (code, discount type/value, expiry, `max_redemptions`,
`applicable_plan_slugs`), toggle `is_active`, and view redemption analytics
(`coupon_redemptions` count vs. `max_redemptions`) — same list/detail shape as the
existing `/platform/accounts` pages.

### 7.3 Customer-facing redemption (`/dashboard/billing`)

A code entered at checkout/upgrade is validated (`is_active`, not expired,
`redemption_count < max_redemptions`, plan eligibility, and the
`(coupon_code_id, account_id)` uniqueness constraint — one redemption per account per
code) before being applied. Percentage/fixed-amount coupons are passed to Razorpay's
checkout as a discount on the subscription's first invoice; credit-grant coupons
never touch Razorpay at all — they call the same crediting path as §6.2.

---

## 8. Open items before `GRX-SAAS-004` can move from `BLOCKED` to `READY`

Per `DEC-GRX-030`, everything in this document is architecturally decided **except**:

1. **Final plan quota numbers and Starter/Pro prices** (§2's table is a working
   draft).
2. **Whether "Bring Your Own AI Key" and self-hosted/Modal-style providers should be
   treated as one of the four existing adapters** (`OpenAI`/`Azure OpenAI`/
   `Anthropic`/`Ollama`, per `DEC-GRX-026`) **or need a fifth adapter** — a
   self-hosted model server (e.g. on Modal) can already work today *if* it exposes an
   OpenAI- or Ollama-compatible endpoint (the same mechanism Krutrim uses via the
   `OpenAIProvider`'s `base_url` override), but that's a specific technical path, not
   an automatic "Modal support" checkbox. Not yet confirmed with the product owner.
3. **Whether multiple named "Brand Voices" per account (as implied by the pricing
   table's "1 / 5 / Unlimited Brand Voices" row) is real scope for this pass.**
   `brand_profiles` today is one row per account, read as a single value in every AI
   generation call (`ai/services.py`) — supporting several *selectable* brand voices
   per account is a schema change (a `brand_voices` table) and an AI-capability UI
   change, not a billing-layer concern. Recommend scoping this out of the billing
   work and treating it as a separate, later `GRX-AI-*` follow-up task if the product
   owner still wants it, rather than blocking billing on it.

Once (1) is confirmed, `GRX-SAAS-004` can move to `READY` and implementation
(schema migration, Razorpay webhook receiver, quota-evaluator middleware, the
`/dashboard/billing` page) can begin.
