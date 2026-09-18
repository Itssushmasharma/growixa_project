"use client";

import { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from "recharts";
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

  const trafficSources = [
    { name: "Social Media", value: 45 },
    { name: "Organic Search", value: 30 },
    { name: "Direct", value: 15 },
    { name: "Paid Ads", value: 10 },
  ];
  const COLORS = ["#4F46E5", "#10B981", "#F59E0B", "#EC4899"];

  const conversionFunnel = [
    { name: "Page Views", count: 12500 },
    { name: "Signups", count: 3200 },
    { name: "Activated", count: 1800 },
    { name: "Customers", count: 450 },
  ];

  return (
    <div className={styles.page}>
      <PageHeader
        icon="📈"
        title="Analytics & Reports"
        description="Unified analytics across all your connected channels and campaigns."
        actions={
          <button
            type="button"
            className={styles.primaryButton}
            onClick={() => { window.location.href = "/dashboard/analytics/insights"; }}
            style={{ display: "flex", gap: "8px", alignItems: "center" }}
          >
            <span>✨</span> Generate AI Insights
          </button>
        }
      />

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

      <div className={styles.grid} style={{ marginTop: "24px" }}>
        {/* Traffic Sources Donut Chart */}
        <div className={styles.card} style={{ gridColumn: "span 1" }}>
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>Traffic Sources</h3>
            <p className={styles.headerSubtitle}>Where your visitors are coming from</p>
          </div>
          <div style={{ height: "300px", width: "100%", marginTop: "16px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={trafficSources}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {trafficSources.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  formatter={(value: unknown) => [`${value}%`, 'Traffic']}
                />
                <Legend iconType="circle" verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Conversion Funnel Bar Chart */}
        <div className={styles.card} style={{ gridColumn: "span 2" }}>
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>Conversion Funnel</h3>
            <p className={styles.headerSubtitle}>User drop-off at each stage</p>
          </div>
          <div style={{ height: "300px", width: "100%", marginTop: "16px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={conversionFunnel}
                layout="vertical"
                margin={{ top: 20, right: 30, left: 40, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#E5E7EB" />
                <XAxis type="number" axisLine={false} tickLine={false} tick={{fill: '#6B7280', fontSize: 12}} />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{fill: '#374151', fontSize: 13, fontWeight: 500}} width={100} />
                <Tooltip 
                  cursor={{fill: '#F3F4F6'}}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
                  formatter={(value: unknown) => [Number(value).toLocaleString(), 'Users']}
                />
                <Bar dataKey="count" fill="#4F46E5" radius={[0, 6, 6, 0]} barSize={32}>
                  {conversionFunnel.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={`hsl(243, 75%, ${59 - index * 8}%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
