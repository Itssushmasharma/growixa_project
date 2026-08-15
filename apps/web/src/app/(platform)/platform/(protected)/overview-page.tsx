"use client";

import { useEffect, useState } from "react";

import { MetricCard } from "@/components/dashboard/metric-card";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./overview-page.module.css";
import type { PlatformDashboardSummary } from "./types";

function formatMoney(amount: number, currency: "$" | "₹"): string {
  return `${currency}${Math.round(amount).toLocaleString()}`;
}

export function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [summary, setSummary] = useState<PlatformDashboardSummary | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<PlatformDashboardSummary>("/platform/dashboard/summary");
        setSummary(data);
      } catch (err) {
        setLoadError(
          err instanceof ApiError
            ? "Could not load the platform overview."
            : "Something went wrong.",
        );
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError || !summary) {
    return (
      <div className={styles.card}>{loadError ?? "Could not load the platform overview."}</div>
    );
  }

  const maxAccountCount = Math.max(...summary.plan_distribution.map((p) => p.account_count), 1);

  return (
    <div className={styles.page}>
      <div className={styles.metricsGrid}>
        <MetricCard
          label="Active accounts"
          value={summary.total_active_accounts.toLocaleString()}
        />
        <MetricCard label="MRR (USD)" value={formatMoney(summary.total_mrr_usd, "$")} />
        <MetricCard label="MRR (INR)" value={formatMoney(summary.total_mrr_inr, "₹")} />
        <MetricCard
          label="Emails this period"
          value={summary.period_emails_used.toLocaleString()}
        />
        <MetricCard
          label="AI runs this period"
          value={summary.period_ai_runs_used.toLocaleString()}
        />
      </div>

      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Plan distribution</h3>
        {summary.plan_distribution.length === 0 ? (
          <p className={styles.hint}>No active subscriptions yet.</p>
        ) : (
          <ul className={styles.planList}>
            {summary.plan_distribution.map((plan) => (
              <li key={plan.plan_slug} className={styles.planRow}>
                <span className={styles.planName}>{plan.plan_name}</span>
                <div className={styles.planBarTrack}>
                  <div
                    className={styles.planBarFill}
                    style={{ width: `${(plan.account_count / maxAccountCount) * 100}%` }}
                  />
                </div>
                <span className={styles.planCount}>{plan.account_count.toLocaleString()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
