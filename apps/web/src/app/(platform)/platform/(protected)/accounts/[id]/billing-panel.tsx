"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import type {
  AccountBillingOverview,
  BillingCreditType,
  BillingSubscriptionPlan,
  BillingSubscriptionStatus,
} from "../types";
import styles from "./billing-panel.module.css";

const STATUS_OPTIONS: BillingSubscriptionStatus[] = ["ACTIVE", "PAST_DUE", "HALTED", "CANCELED"];

const CREDIT_TYPE_OPTIONS: BillingCreditType[] = [
  "AI_RUNS",
  "EMAIL_SENDS",
  "CONTACT_SLOTS",
  "SOCIAL_POSTS",
];

function errorDetail(error: unknown, fallback: string): string {
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

export function BillingPanel({ accountId }: { accountId: string }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [overview, setOverview] = useState<AccountBillingOverview | null>(null);
  const [plans, setPlans] = useState<BillingSubscriptionPlan[]>([]);

  const [overridePlanSlug, setOverridePlanSlug] = useState("");
  const [overrideStatus, setOverrideStatus] = useState("");
  const [overriding, setOverriding] = useState(false);

  const [grantCreditType, setGrantCreditType] = useState<BillingCreditType>("AI_RUNS");
  const [grantCredits, setGrantCredits] = useState("");
  const [granting, setGranting] = useState(false);

  async function refresh() {
    const current = await apiFetch<AccountBillingOverview>(
      `/platform/accounts/${accountId}/subscription`,
    );
    setOverview(current);
  }

  useEffect(() => {
    async function load() {
      try {
        const [current, planList] = await Promise.all([
          apiFetch<AccountBillingOverview>(`/platform/accounts/${accountId}/subscription`),
          apiFetch<BillingSubscriptionPlan[]>("/platform/subscription-plans"),
        ]);
        setOverview(current);
        setPlans(planList);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to manage this account's billing.");
        } else {
          setLoadError("Could not load billing information.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [accountId]);

  async function handleOverride(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOverriding(true);
    try {
      await apiFetch(`/platform/accounts/${accountId}/subscription`, {
        method: "PATCH",
        body: JSON.stringify({
          plan_slug: overridePlanSlug || null,
          status: overrideStatus || null,
        }),
      });
      await refresh();
      setOverridePlanSlug("");
      setOverrideStatus("");
      showToast("success", "Subscription updated.");
    } catch (err) {
      showToast("error", errorDetail(err, "Could not update the subscription."));
    } finally {
      setOverriding(false);
    }
  }

  async function handleGrant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGranting(true);
    try {
      await apiFetch(`/platform/accounts/${accountId}/credits/grant`, {
        method: "POST",
        body: JSON.stringify({ credit_type: grantCreditType, credits: Number(grantCredits) }),
      });
      await refresh();
      setGrantCredits("");
      showToast("success", "Credits granted.");
    } catch (err) {
      showToast("error", errorDetail(err, "Could not grant credits."));
    } finally {
      setGranting(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading billing…</div>;
  }

  if (loadError || !overview) {
    return <div className={styles.card}>{loadError ?? "Could not load billing information."}</div>;
  }

  const balanceByType = new Map(
    overview.credit_balances.map((balance) => [balance.credit_type, balance.remaining_credits]),
  );

  return (
    <div className={styles.card}>
      <h3 className={styles.sectionTitle}>Billing</h3>

      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Plan</span>
        <span>{overview.plan.name}</span>
      </div>
      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Status</span>
        <span>{overview.status}</span>
      </div>
      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Currency</span>
        <span>{overview.currency}</span>
      </div>
      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Period</span>
        <span>
          {new Date(overview.current_period_start).toLocaleDateString()} –{" "}
          {new Date(overview.current_period_end).toLocaleDateString()}
        </span>
      </div>
      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Usage this period</span>
        <span>
          {overview.period_email_used.toLocaleString()} emails ·{" "}
          {overview.period_ai_used.toLocaleString()} AI runs
        </span>
      </div>
      <div className={styles.creditsRow}>
        {CREDIT_TYPE_OPTIONS.map((type) => (
          <span className={styles.creditPill} key={type}>
            {type}: {(balanceByType.get(type) ?? 0).toLocaleString()}
          </span>
        ))}
      </div>

      <form onSubmit={handleOverride} className={styles.form}>
        <div className={styles.formHeading}>Override plan / status</div>
        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="override-plan">
              Plan
            </label>
            <select
              id="override-plan"
              className={styles.select}
              value={overridePlanSlug}
              onChange={(event) => setOverridePlanSlug(event.target.value)}
            >
              <option value="">No change</option>
              {plans.map((plan) => (
                <option key={plan.id} value={plan.slug}>
                  {plan.name}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="override-status">
              Status
            </label>
            <select
              id="override-status"
              className={styles.select}
              value={overrideStatus}
              onChange={(event) => setOverrideStatus(event.target.value)}
            >
              <option value="">No change</option>
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          type="submit"
          className={styles.actionButton}
          disabled={overriding || (!overridePlanSlug && !overrideStatus)}
        >
          {overriding ? "Saving…" : "Apply override"}
        </button>
      </form>

      <form onSubmit={handleGrant} className={styles.form}>
        <div className={styles.formHeading}>Grant free credits</div>
        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="grant-credit-type">
              Credit type
            </label>
            <select
              id="grant-credit-type"
              className={styles.select}
              value={grantCreditType}
              onChange={(event) => setGrantCreditType(event.target.value as BillingCreditType)}
            >
              {CREDIT_TYPE_OPTIONS.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="grant-credits">
              Credits
            </label>
            <input
              id="grant-credits"
              className={styles.input}
              type="number"
              min={1}
              required
              value={grantCredits}
              onChange={(event) => setGrantCredits(event.target.value)}
            />
          </div>
        </div>
        <button type="submit" className={styles.actionButton} disabled={granting || !grantCredits}>
          {granting ? "Granting…" : "Grant credits"}
        </button>
      </form>
    </div>
  );
}
