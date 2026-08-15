"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { QuotaGauge } from "@/components/dashboard/quota-gauge";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { PageHeader } from "@/components/page-header/page-header";
import { StatCard } from "@/components/stat-card/stat-card";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./dashboard-page.module.css";
import type { CampaignStatusBreakdown, DashboardOverview } from "./types";

const STATUS_LABEL: Record<keyof CampaignStatusBreakdown, string> = {
  draft: "Draft",
  scheduled: "Scheduled",
  sending: "Sending",
  sent: "Sent",
  cancelled: "Cancelled",
  failed: "Failed",
};

function statusToneClass(status: keyof CampaignStatusBreakdown): string {
  if (status === "sent") return styles.toneSuccess ?? "";
  if (status === "failed") return styles.toneDanger ?? "";
  if (status === "scheduled" || status === "sending") return styles.toneInfo ?? "";
  return styles.toneNeutral ?? "";
}

function formatPct(value: number | null): string {
  return value === null ? "—" : `${value}%`;
}

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<DashboardOverview>("/dashboard/overview");
        setOverview(data);
      } catch (err) {
        setLoadError(
          err instanceof ApiError ? "Could not load your dashboard." : "Something went wrong.",
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

  if (loadError || !overview) {
    return <div className={styles.card}>{loadError ?? "Could not load your dashboard."}</div>;
  }

  const statusEntries = Object.entries(overview.campaign_status_breakdown) as [
    keyof CampaignStatusBreakdown,
    number,
  ][];
  const statusTotal = statusEntries.reduce((sum, [, count]) => sum + count, 0);

  return (
    <div className={styles.page}>
      {/* Page Header */}
      <PageHeader
        icon="📊"
        title="Dashboard Overview"
        description="Welcome back! Track your multi-channel marketing performance and audience growth."
        actions={
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <Link href="/dashboard/ai" className={styles.actionButtonSecondary}>
              ⚡ AI Copilot
            </Link>
            <Link href="/dashboard/campaigns/new" className={styles.actionButton}>
              + Create Campaign
            </Link>
          </div>
        }
      />

      {/* KPI Stats Grid (Real Overview Data) */}
      <section className={styles.metricsGrid} aria-label="Overview KPI metrics">
        <StatCard
          label="Total Contacts"
          value={overview.total_contacts.toLocaleString()}
          subtext="Audience"
        />
        <StatCard
          label="Active Campaigns"
          value={overview.active_campaigns}
          subtext="Live & scheduled"
        />
        <StatCard
          label="Scheduled Posts"
          value={overview.scheduled_social_posts}
          subtext="Social queue"
        />
        <StatCard
          label="Email Open Rate"
          value={formatPct(overview.email_open_rate_pct)}
          subtext="Delivered campaigns"
        />
        <StatCard
          label="Email Click Rate"
          value={formatPct(overview.email_click_rate_pct)}
          subtext="Delivered campaigns"
        />
      </section>

      <div className={styles.card}>
        <div className={styles.chartHeader}>
          <h3 className={styles.cardTitle}>Contact growth — last 6 months</h3>
          <span className={styles.chartTotal}>
            {overview.total_contacts.toLocaleString()} total
          </span>
        </div>
        <TrendChart
          points={overview.contact_growth_6_months.map((point) => ({
            label: point.month.slice(5),
            value: point.contacts,
          }))}
        />
      </div>

      <div className={styles.twoColumn}>
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>Plan &amp; quota — {overview.quota.plan_name}</h3>
          <div className={styles.gauges}>
            <QuotaGauge
              label="Contacts"
              used={overview.quota.contact_usage}
              limit={overview.quota.contact_limit}
            />
            <QuotaGauge
              label="Emails this period"
              used={overview.quota.email_usage}
              limit={overview.quota.email_limit}
            />
            <QuotaGauge
              label="AI runs this period"
              used={overview.quota.ai_usage}
              limit={overview.quota.ai_limit}
            />
          </div>
          <p className={styles.hint}>
            {overview.quota.ai_credits_remaining.toLocaleString()} top-up AI credits remaining.{" "}
            <Link href="/dashboard/billing">Manage billing →</Link>
          </p>
        </div>

        <div className={styles.card}>
          <h3 className={styles.cardTitle}>Campaign status</h3>
          {statusTotal === 0 ? (
            <p className={styles.hint}>No campaigns yet.</p>
          ) : (
            <ul className={styles.statusList}>
              {statusEntries
                .filter(([, count]) => count > 0)
                .map(([status, count]) => (
                  <li key={status} className={styles.statusRow}>
                    <span className={`${styles.statusDot} ${statusToneClass(status)}`} />
                    <span className={styles.statusLabel}>{STATUS_LABEL[status]}</span>
                    <span className={styles.statusCount}>{count}</span>
                  </li>
                ))}
            </ul>
          )}
        </div>
      </div>

      <div className={styles.card}>
        <h3 className={styles.cardTitle}>Recent campaigns</h3>
        {overview.recent_campaigns.length === 0 ? (
          <p className={styles.hint}>
            No campaigns yet. <Link href="/dashboard/campaigns/new">Create one →</Link>
          </p>
        ) : (
          <table className={styles.table}>
            <tbody>
              {overview.recent_campaigns.map((campaign) => (
                <tr key={campaign.id}>
                  <td>
                    <Link href={`/dashboard/campaigns/${campaign.id}`}>{campaign.name}</Link>
                  </td>
                  <td className={styles.tableStatus}>{campaign.status}</td>
                  <td className={styles.tableNumeric}>
                    {campaign.sent_count.toLocaleString()} sent
                  </td>
                  <td className={styles.tableNumeric}>{formatPct(campaign.open_rate_pct)} open</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
