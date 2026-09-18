"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { PageHeader } from "@/components/page-header/page-header";
import { apiFetch } from "@/lib/api-client";
import styles from "../dashboard-page.module.css";

interface TimeSeriesPoint {
  name: string;
  followers: number;
  engagement: number;
  reach: number;
}

interface AnalyticsDashboardOut {
  total_followers: number;
  followers_change: number;
  total_engagement: number;
  engagement_change: number;
  total_reach: number;
  reach_change: number;
  chart_data: TimeSeriesPoint[];
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsDashboardOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const response = await apiFetch<AnalyticsDashboardOut>("/analytics/dashboard");
        setData(response);
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  if (loading || !data) {
    return (
      <div className={styles.page}>
        <PageHeader title="Analytics & Reports" description="Loading metrics..." />
        <div className={styles.grid}>
          <div className={styles.card}>Loading...</div>
        </div>
      </div>
    );
  }

  function formatNumber(num: number) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  function formatChange(change: number) {
    const isPos = change >= 0;
    const color = isPos ? "#15803d" : "#b91c1c";
    const arrow = isPos ? "↑" : "↓";
    return (
      <span style={{ color, fontSize: "14px", fontWeight: 500, marginTop: "8px", display: "block" }}>
        {arrow} {Math.abs(change)}% from last week
      </span>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        icon="📈"
        title="Analytics & Reports"
        description="Unified analytics across all your connected channels and campaigns."
      >
        <button
          type="button"
          className={styles.primaryButton}
          onClick={() => { window.location.href = "/dashboard/analytics/insights"; }}
          style={{ display: "flex", gap: "8px", alignItems: "center" }}
        >
          <span>✨</span> Generate AI Insights
        </button>
      </PageHeader>

      <div className={styles.grid}>
        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>👥</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Total Followers</span>
            <span className={styles.metricValue}>{formatNumber(data.total_followers)}</span>
            {formatChange(data.followers_change)}
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>❤️</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Total Engagement</span>
            <span className={styles.metricValue}>{formatNumber(data.total_engagement)}</span>
            {formatChange(data.engagement_change)}
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>👁️</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Total Reach</span>
            <span className={styles.metricValue}>{formatNumber(data.total_reach)}</span>
            {formatChange(data.reach_change)}
          </div>
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.card} style={{ gridColumn: "1 / -1" }}>
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>Audience Growth & Engagement</h3>
          </div>
          <div style={{ height: "400px", width: "100%", marginTop: "24px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.chart_data}>
                <defs>
                  <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#4F46E5" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorEngagement" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} dy={10} />
                <YAxis yAxisId="left" axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} />
                <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                />
                <Area yAxisId="left" type="monotone" dataKey="followers" stroke="#4F46E5" fillOpacity={1} fill="url(#colorFollowers)" strokeWidth={2} name="Followers" />
                <Area yAxisId="right" type="monotone" dataKey="engagement" stroke="#10B981" fillOpacity={1} fill="url(#colorEngagement)" strokeWidth={2} name="Engagement" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
