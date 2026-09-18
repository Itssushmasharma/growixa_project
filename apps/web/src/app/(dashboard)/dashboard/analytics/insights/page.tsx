"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/page-header/page-header";
import { apiFetch } from "@/lib/api-client";
import styles from "../../dashboard-page.module.css";
import Link from "next/link";

interface GrowthInsightsOut {
  insights: string[];
  recommendations: string[];
  topics: string[];
}

export default function InsightsPage() {
  const [data, setData] = useState<GrowthInsightsOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const response = await apiFetch<GrowthInsightsOut>("/analytics/insights");
        setData(response);
      } catch (err) {
        console.error("Failed to load insights", err);
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  if (loading || !data) {
    return (
      <div className={styles.page}>
        <PageHeader title="AI Growth Intelligence" description="Analyzing 30 days of performance data to generate custom insights..." />
        <div className={styles.grid}>
          <div className={styles.card} style={{ gridColumn: "1 / -1", textAlign: "center", padding: "48px" }}>
            <div style={{ fontSize: "32px", animation: "pulse 1.5s infinite" }}>✨</div>
            <h3 style={{ marginTop: "16px", fontWeight: 600 }}>Synthesizing Data...</h3>
            <p style={{ color: "#6b7280" }}>Our AI is looking for patterns in your reach and engagement.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        icon="✨"
        title="AI Growth Intelligence"
        description="Your automated marketing strategist. Actionable insights derived from your recent performance."
      >
        <Link href="/dashboard/analytics" className={styles.secondaryButton} style={{ textDecoration: "none" }}>
          Back to Analytics
        </Link>
      </PageHeader>

      <div className={styles.grid}>
        {/* Key Insights */}
        <div className={styles.card} style={{ gridColumn: "span 2" }}>
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>📊 Key Insights</h3>
          </div>
          <ul style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "12px", listStyle: "none", padding: 0 }}>
            {data.insights.map((insight, idx) => (
              <li key={idx} style={{ padding: "12px", backgroundColor: "#f9fafb", borderRadius: "8px", borderLeft: "4px solid #4f46e5" }}>
                {insight}
              </li>
            ))}
          </ul>
        </div>

        {/* Content Topics */}
        <div className={styles.card} style={{ gridColumn: "span 1" }}>
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>💡 Trending Topics</h3>
            <p className={styles.headerSubtitle}>Ideas that resonate right now.</p>
          </div>
          <ul style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "12px", listStyle: "none", padding: 0 }}>
            {data.topics.map((topic, idx) => (
              <li key={idx} style={{ padding: "12px", backgroundColor: "#fdf4ff", color: "#86198f", borderRadius: "8px", fontWeight: 500 }}>
                # {topic}
              </li>
            ))}
          </ul>
        </div>

        {/* Recommendations */}
        <div className={styles.card} style={{ gridColumn: "1 / -1" }}>
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>🚀 Optimization Recommendations</h3>
          </div>
          <div style={{ marginTop: "24px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
            {data.recommendations.map((rec, idx) => (
              <div key={idx} style={{ padding: "20px", border: "1px solid #e5e7eb", borderRadius: "12px", boxShadow: "0 1px 2px rgba(0,0,0,0.05)" }}>
                <span style={{ fontSize: "20px", marginBottom: "8px", display: "block" }}>⚡</span>
                <p style={{ color: "#374151", lineHeight: 1.5 }}>{rec}</p>
                <button className={styles.primaryButton} style={{ marginTop: "16px", width: "100%" }}>
                  Apply to Next Campaign
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
