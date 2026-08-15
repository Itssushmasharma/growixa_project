"use client";

import { useEffect, useState } from "react";

import { MetricCard } from "@/components/dashboard/metric-card";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./finance-page.module.css";
import type { FinancialMetrics } from "./types";

function formatMoney(amount: number, currency: "$" | "₹"): string {
  return `${currency}${Math.round(amount).toLocaleString()}`;
}

export function FinancePage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<FinancialMetrics | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<FinancialMetrics>("/platform/monitoring/financials");
        setMetrics(data);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to view the financial dashboard.");
        } else {
          setLoadError("Could not load financial metrics.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError || !metrics) {
    return <div className={styles.card}>{loadError ?? "Could not load financial metrics."}</div>;
  }

  return (
    <div className={styles.page}>
      <div className={styles.metricsGrid}>
        <MetricCard label="MRR (USD)" value={formatMoney(metrics.mrr_by_currency.USD ?? 0, "$")} />
        <MetricCard label="MRR (INR)" value={formatMoney(metrics.mrr_by_currency.INR ?? 0, "₹")} />
        <MetricCard label="ARR (USD)" value={formatMoney(metrics.arr_by_currency.USD ?? 0, "$")} />
        <MetricCard label="ARR (INR)" value={formatMoney(metrics.arr_by_currency.INR ?? 0, "₹")} />
        <MetricCard
          label="Active subscriptions"
          value={metrics.active_subscription_count.toLocaleString()}
        />
        <MetricCard
          label="Churn (30d)"
          value={`${metrics.churn_rate_percent}%`}
          hint={`${metrics.churned_last_30_days} cancellation${
            metrics.churned_last_30_days === 1 ? "" : "s"
          } in the last 30 days`}
          deltaTone={metrics.churn_rate_percent > 0 ? "negative" : "neutral"}
        />
      </div>
      <div className={styles.card}>
        <p className={styles.hint}>
          MRR/ARR count only ACTIVE subscriptions, same definition shown on the platform overview
          page. Top-up/credit-pack revenue isn&apos;t included yet — the purchase record
          doesn&apos;t capture amount or currency paid.
        </p>
      </div>
    </div>
  );
}
