# Sprint 08 — Billing

- Document ID: DOC-SPRINT-08
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-08-13
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DEVELOPMENT_READINESS](../00-project-control/DEVELOPMENT_READINESS.md), [DECISIONS §DEC-GRX-029/030](../00-project-control/DECISIONS.md), [BILLING_SYSTEM_ARCHITECTURE](../04-architecture/BILLING_SYSTEM_ARCHITECTURE.md)

This is the 8th sprint *file* chronologically, and it implements product **Slice 7**
(Billing) — the first slice that moves real money. Razorpay Subscriptions API,
dual-currency (USD/INR) plan tiers, atomic usage-quota metering with non-expiring
top-up credits, a platform-admin override path that bypasses payment entirely, and a
coupon/discount engine.

## Included

Per [BILLING_SYSTEM_ARCHITECTURE.md](../04-architecture/BILLING_SYSTEM_ARCHITECTURE.md)
(`DEC-GRX-029`/`030`):

1. Razorpay Subscriptions API integration (not self-managed Orders), dual-currency —
   an account subscribes in USD or INR and stays on that currency
2. `subscription_plans` / `account_subscriptions` / `account_credit_balances` /
   `account_credit_purchases` schema; every account gets a `Free`-tier
   `account_subscriptions` row automatically at registration
3. Authenticated Razorpay webhook receiver (`POST /billing/razorpay`,
   signature-verified before touching any table) + a daily cancellation-downgrade
   ticker worker job, following the existing `GRX-SCHED-*`/`GRX-SOCIAL-007` ticker
   pattern
4. Atomic, race-free quota evaluator for the two period-resetting metered dimensions
   (monthly email sends, monthly AI runs — the two credit-purchasable quotas): checks
   the plan's monthly allowance first, then the non-expiring credit balance, then
   blocks with `HTTP 402`. Only *platform-provided* AI generations are metered — an
   account's own bring-your-own AI key is never metered (`BILLING_SYSTEM_ARCHITECTURE.md
   §4.1`), requiring a new `source` field on `ai/providers/factory.py`'s
   `ResolvedAIProvider`
5. Simpler point-in-time cap checks (current count vs. plan limit, no period reset) for
   the non-metered plan dimensions: total contacts, connected social accounts, pending
   scheduled social posts, team user seats — enforced at each resource's own
   creation endpoint, not the period-counter mechanism above
6. Non-expiring top-up credit packs (AI runs, email sends, contacts, social posts),
   purchased via a Razorpay one-time order, added to the same running balance the
   quota evaluator reads
7. Platform-admin override UI/API (`GRX-SAAS-006`): manual plan assignment (incl.
   Enterprise activation — contact-sales, not self-serve), manual credit grants,
   billing-status override, plan-wide quota/price editing — all bypass Razorpay
   entirely, gated `platform.billing.manage` (`platform.owner`/`platform.finance` only)
8. Coupon/discount engine (`GRX-SAAS-012`): percentage, fixed-amount, and
   free-credit-grant coupon types; platform-admin create/toggle/redemption-analytics;
   one redemption per account per code
9. Customer-facing `/dashboard/billing` page: current plan, live quota usage bars,
   upgrade/downgrade, top-up purchase buttons, coupon redemption field — gated
   `billing.manage`/`billing.view`
10. Audit log access tiering (export/API access by plan) — **not** retention/deletion;
    audit logs stay permanent for every tier, per `DEC-GRX-030`

Full data model, RBAC, and threat model:
[BILLING_SYSTEM_ARCHITECTURE.md](../04-architecture/BILLING_SYSTEM_ARCHITECTURE.md),
[RBAC.md §Slice 7](../08-security/RBAC.md#slice-7-billing-permission-codes),
[THREAT_MODEL.md §Slice 7](../08-security/THREAT_MODEL.md#slice-7-billing-scope).

Full task breakdown with dependencies: [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md)
(`GRX-BILL-*`, plus `GRX-SAAS-004`/`006`/`009`/`012` as the umbrella/admin/coupon rows).

## Explicitly excluded from Sprint 8

- **Self-managed Orders as the billing primitive** — `DEC-GRX-030` chose the Subscriptions
  API; Razorpay owns the recurring charge, Growixa reacts to webhooks.
- **Expiring top-up credits / multi-batch FIFO consumption** — credits never expire, one
  running balance per `(account_id, credit_type)`, per the product owner's explicit
  choice.
- **Tiered audit-log retention or any audit-log deletion** — audit logs are permanent
  for every plan tier; tiering applies to export/API *access*, not retention length.
- **Self-serve Enterprise checkout** — Enterprise is contact-sales, platform-admin
  activated; no fixed self-serve price, no automatic Razorpay subscription object
  required.
- **A fifth AI provider adapter for Modal.com or other self-hosted endpoints** — still
  an open item (`BILLING_SYSTEM_ARCHITECTURE.md §8`), not resolved or built this
  sprint. Today's four adapters (OpenAI/Azure OpenAI/Anthropic/Ollama) are unaffected;
  a self-hosted model already works if it exposes an OpenAI- or Ollama-compatible
  endpoint (same mechanism Krutrim uses), which is a `base_url` configuration, not new
  code.
- **Multiple named "Brand Voices" per account** — `brand_profiles` stays one row per
  account; the pricing table's "1/5/Unlimited Brand Voices" row is aspirational until a
  separate `GRX-AI-*` follow-up task builds real multi-voice support. Not blocking this
  sprint.
- **Refunds/chargebacks UI** — handled manually via the Razorpay dashboard itself, not
  a Growixa feature this sprint.
- **Proactive fraud/velocity detection on coupon redemption** — `max_redemptions` +
  one-per-account is the only anti-abuse control this sprint (`THREAT_MODEL.md` T65).
- **A dedicated alert/paging mechanism for a failed cancellation-downgrade ticker run**
  — relies on existing worker-job monitoring (`THREAT_MODEL.md` T68).

If implementing a Sprint 8 task seems to require touching any of the above, stop and
flag it — it means the task is scoped wrong, not that a shortcut through excluded
territory is warranted.

## Sprint 8 acceptance criteria

- A new account gets a `Free`-tier `account_subscriptions` row automatically at
  registration — no account is ever left without one.
- An account with `billing.manage` can subscribe to Starter/Pro in either currency via
  Razorpay Checkout; the resulting `subscription.charged` webhook activates the
  subscription and resets the period counters.
- A platform-provided AI generation or an email send beyond the plan's monthly
  allowance is blocked with `HTTP 402` unless covered by a non-expiring top-up credit
  balance; an account's own bring-your-own AI key generation is never blocked by this
  quota (negative + positive test pair).
- Two concurrent metered requests that would together exceed the quota — only one
  succeeds, not both (race-condition test against the atomic evaluator).
- A platform admin with `platform.billing.manage` can assign any account to any plan
  (including Enterprise) without a Razorpay charge, grant free credits, override
  billing status, and edit a plan's quotas/prices; a `platform.support`/`platform.
  operations` admin gets 403 on all four (negative test).
- A forged/unsigned webhook payload to `/billing/razorpay` is rejected before touching
  any table; a replayed (already-processed) event ID is a no-op, not a second credit
  grant (both negative tests).
- A coupon code respects `max_redemptions`, plan eligibility, expiry, and the
  one-redemption-per-account constraint (four negative tests plus one success case).
- A `CANCELED` subscription past `current_period_end` is downgraded to Free by the
  ticker job (test drives the ticker directly, not a real 30-day wait).
- A cross-account attempt to read or act on another account's subscription/credit/
  coupon-redemption row 404s, added to `test_cross_tenant_isolation.py`.
- Automated backend and frontend tests pass; CI passes.

## Definition of done for this sprint

[DEFINITION_OF_DONE.md](../00-project-control/DEFINITION_OF_DONE.md) applies to every
task in this sprint individually — the sprint itself is done only when every task in
[MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md) tagged
`GRX-BILL-*` (plus `GRX-SAAS-006`/`009`/`012`) is `DONE`, not merely attempted. Per
[DEC-GRX-011](../00-project-control/DECISIONS.md), no task is marked `DONE` on
mocked-provider evidence — a real Razorpay Test Mode subscription/payment/webhook
round-trip is required before the checkout and webhook-receiver tasks are marked
`DONE`; if Test Mode credentials aren't available during a given work session, that is
explicitly flagged as an evidence gap rather than silently assumed, same convention
Slice 5/6 used for their own external-credential gaps.
