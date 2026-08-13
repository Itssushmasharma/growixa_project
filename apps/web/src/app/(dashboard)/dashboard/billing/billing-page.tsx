"use client";

import { useCallback, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";
import { openRazorpayCheckout } from "@/lib/razorpay";

import styles from "./billing-page.module.css";
import {
  type AccountSubscription,
  type BillingCurrency,
  CREDIT_TYPE_LABEL,
  type CreditPack,
  type MeResponse,
  STATUS_LABEL,
  type SubscribablePlanSlug,
  type SubscribeResponse,
  type SubscriptionPlan,
  type TopUpResponse,
} from "./types";

const VIEW_PERMISSION = "billing.view";
const MANAGE_PERMISSION = "billing.manage";

// Post-payment crediting happens asynchronously via the Razorpay webhook (GRX-BILL-003),
// not in Checkout.js's own success callback -- this is just a courtesy re-fetch so the
// page usually reflects the new state without a manual reload, not a guarantee.
const REFRESH_DELAY_AFTER_PAYMENT_MS = 3000;

function apiErrorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string | { message?: string } };
      if (typeof parsed.detail === "string") return parsed.detail;
      if (parsed.detail?.message) return parsed.detail.message;
    } catch {
      // Not JSON
    }
  }
  return fallback;
}

function formatMoney(amount: number, currency: BillingCurrency): string {
  const symbol = currency === "USD" ? "$" : "₹";
  return `${symbol}${amount.toLocaleString()}`;
}

function planPrice(plan: SubscriptionPlan, currency: BillingCurrency): number | null {
  return currency === "USD" ? plan.price_usd : plan.price_inr;
}

function packPrice(pack: CreditPack, currency: BillingCurrency): number | null {
  return currency === "USD" ? pack.price_usd : pack.price_inr;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function statusBadgeClass(status: AccountSubscription["status"]): string | undefined {
  if (status === "ACTIVE") return styles.statusActive;
  if (status === "PENDING") return styles.statusPending;
  return styles.statusAtRisk;
}

interface UsageBarProps {
  label: string;
  used: number;
  limit: number | null;
}

function UsageBar({ label, used, limit }: UsageBarProps) {
  const pct = limit === null || limit === 0 ? 0 : Math.min(100, Math.round((used / limit) * 100));
  return (
    <div className={styles.usageRow}>
      <div className={styles.usageLabelRow}>
        <span className={styles.usageLabel}>{label}</span>
        <span className={styles.usageValue}>
          {used.toLocaleString()} / {limit === null ? "Unlimited" : limit.toLocaleString()}
        </span>
      </div>
      {limit !== null && (
        <div className={styles.usageBar}>
          <div
            className={pct >= 100 ? styles.usageBarFillFull : styles.usageBarFill}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}

export function BillingPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);

  const [subscription, setSubscription] = useState<AccountSubscription | null>(null);
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [creditPacks, setCreditPacks] = useState<CreditPack[]>([]);
  const [currency, setCurrency] = useState<BillingCurrency>("INR");

  const [subscribingSlug, setSubscribingSlug] = useState<string | null>(null);
  const [buyingPackSlug, setBuyingPackSlug] = useState<string | null>(null);

  const refreshSubscription = useCallback(async () => {
    try {
      const sub = await apiFetch<AccountSubscription>("/billing/subscription");
      setSubscription(sub);
    } catch {
      // A courtesy refresh -- the page just keeps showing what it already had.
    }
  }, []);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        if (hasView) {
          const [sub, planList, packList] = await Promise.all([
            apiFetch<AccountSubscription>("/billing/subscription"),
            apiFetch<SubscriptionPlan[]>("/billing/plans"),
            apiFetch<CreditPack[]>("/billing/credit-packs"),
          ]);
          setSubscription(sub);
          setPlans(planList);
          setCreditPacks(packList);
          setCurrency(sub.currency);
        }
      } catch {
        setLoadError("Could not load billing information.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleSubscribe(plan: SubscriptionPlan) {
    if (!canManage) return;
    setSubscribingSlug(plan.slug);
    try {
      const result = await apiFetch<SubscribeResponse>("/billing/subscribe", {
        method: "POST",
        body: JSON.stringify({
          plan_slug: plan.slug as SubscribablePlanSlug,
          currency,
        }),
      });
      await openRazorpayCheckout({
        key: result.razorpay_key_id,
        subscription_id: result.razorpay_subscription_id,
        name: "Growixa",
        description: `Subscribe to ${plan.name}`,
        theme: { color: "#1457e6" },
        handler: () => {
          showToast("success", "Payment submitted — your plan will update shortly.");
          window.setTimeout(() => void refreshSubscription(), REFRESH_DELAY_AFTER_PAYMENT_MS);
        },
      });
    } catch (error) {
      showToast("error", apiErrorDetail(error, "Could not start checkout."));
    } finally {
      setSubscribingSlug(null);
    }
  }

  async function handleTopUp(pack: CreditPack) {
    if (!canManage) return;
    setBuyingPackSlug(pack.slug);
    try {
      const result = await apiFetch<TopUpResponse>("/billing/topup", {
        method: "POST",
        body: JSON.stringify({ pack_slug: pack.slug, currency }),
      });
      await openRazorpayCheckout({
        key: result.razorpay_key_id,
        order_id: result.razorpay_order_id,
        amount: result.amount_smallest_unit,
        currency: result.currency,
        name: "Growixa",
        description: `${pack.name} top-up`,
        theme: { color: "#1457e6" },
        handler: () => {
          showToast("success", "Payment submitted — your credits will appear shortly.");
          window.setTimeout(() => void refreshSubscription(), REFRESH_DELAY_AFTER_PAYMENT_MS);
        },
      });
    } catch (error) {
      showToast("error", apiErrorDetail(error, "Could not start checkout."));
    } finally {
      setBuyingPackSlug(null);
    }
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>Loading…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>{loadError}</div>
      </div>
    );
  }

  if (!canView || !subscription) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to billing.</div>
      </div>
    );
  }

  const balanceByType = new Map(
    subscription.credit_balances.map((balance) => [balance.credit_type, balance.remaining_credits]),
  );

  return (
    <div className={styles.page}>
      <div className={styles.currencyToggle} role="group" aria-label="Currency">
        <button
          type="button"
          className={currency === "INR" ? styles.currencyPillActive : styles.currencyPill}
          onClick={() => setCurrency("INR")}
        >
          ₹ INR
        </button>
        <button
          type="button"
          className={currency === "USD" ? styles.currencyPillActive : styles.currencyPill}
          onClick={() => setCurrency("USD")}
        >
          $ USD
        </button>
      </div>

      <div className={styles.card}>
        <div className={styles.currentPlanHeader}>
          <div>
            <h2 className={styles.heading}>{subscription.plan.name} plan</h2>
            <p className={styles.hint}>
              {formatDate(subscription.current_period_start)} –{" "}
              {formatDate(subscription.current_period_end)}
            </p>
          </div>
          <span className={statusBadgeClass(subscription.status)}>
            {STATUS_LABEL[subscription.status]}
          </span>
        </div>

        <div className={styles.usageSection}>
          <UsageBar
            label="Email sends this period"
            used={subscription.period_email_used}
            limit={subscription.plan.max_monthly_emails}
          />
          <UsageBar
            label="AI runs this period"
            used={subscription.period_ai_used}
            limit={subscription.plan.max_monthly_ai_runs}
          />
        </div>

        <div className={styles.creditsSection}>
          <h3 className={styles.subheading}>Credit balances</h3>
          <div className={styles.creditsList}>
            {(["AI_RUNS", "EMAIL_SENDS", "CONTACT_SLOTS", "SOCIAL_POSTS"] as const).map((type) => (
              <div className={styles.creditRow} key={type}>
                <span>{CREDIT_TYPE_LABEL[type]}</span>
                <span className={styles.creditValue}>
                  {(balanceByType.get(type) ?? 0).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h3 className={styles.sectionHeading}>Plans</h3>
        <div className={styles.plansGrid}>
          {plans.map((plan) => {
            const isCurrent = plan.slug === subscription.plan.slug;
            const price = planPrice(plan, currency);
            const isSelfServe = plan.slug === "starter" || plan.slug === "pro";
            return (
              <div className={styles.planCard} key={plan.id}>
                <div className={styles.planCardHeader}>
                  <span className={styles.planName}>{plan.name}</span>
                  {isCurrent && <span className={styles.currentBadge}>Current plan</span>}
                </div>
                <p className={styles.planPrice}>
                  {price !== null ? `${formatMoney(price, currency)}/mo` : "Contact sales"}
                </p>
                <ul className={styles.planFeatures}>
                  <li>
                    {plan.max_contacts === null
                      ? "Unlimited contacts"
                      : `${plan.max_contacts.toLocaleString()} contacts`}
                  </li>
                  <li>
                    {plan.max_monthly_emails === null
                      ? "Unlimited emails/mo"
                      : `${plan.max_monthly_emails.toLocaleString()} emails/mo`}
                  </li>
                  <li>
                    {plan.max_monthly_ai_runs === null
                      ? "Unlimited AI runs/mo"
                      : `${plan.max_monthly_ai_runs.toLocaleString()} AI runs/mo`}
                  </li>
                  <li>{plan.allow_byo_ai_key ? "Bring your own AI key" : "Platform AI only"}</li>
                </ul>
                {canManage && isSelfServe && (
                  <button
                    type="button"
                    className={styles.actionButton}
                    disabled={isCurrent || price === null || subscribingSlug === plan.slug}
                    onClick={() => void handleSubscribe(plan)}
                  >
                    {subscribingSlug === plan.slug
                      ? "Starting checkout…"
                      : isCurrent
                        ? "Current plan"
                        : price === null
                          ? `Not available in ${currency}`
                          : "Subscribe"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <h3 className={styles.sectionHeading}>Top up credits</h3>
        <div className={styles.plansGrid}>
          {creditPacks.map((pack) => {
            const price = packPrice(pack, currency);
            return (
              <div className={styles.planCard} key={pack.id}>
                <div className={styles.planCardHeader}>
                  <span className={styles.planName}>{pack.name}</span>
                </div>
                <p className={styles.planPrice}>
                  {price !== null ? formatMoney(price, currency) : "Contact sales"}
                </p>
                <p className={styles.hint}>{CREDIT_TYPE_LABEL[pack.credit_type]}, never expires</p>
                {canManage && (
                  <button
                    type="button"
                    className={styles.secondaryButton}
                    disabled={price === null || buyingPackSlug === pack.slug}
                    onClick={() => void handleTopUp(pack)}
                  >
                    {buyingPackSlug === pack.slug
                      ? "Starting checkout…"
                      : price === null
                        ? `Not available in ${currency}`
                        : "Buy"}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
