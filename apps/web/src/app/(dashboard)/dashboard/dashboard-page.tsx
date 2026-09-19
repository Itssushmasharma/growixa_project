"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { QuotaGauge } from "@/components/dashboard/quota-gauge";
import { TrendChart } from "@/components/dashboard/trend-chart";
import { ActivityFeed } from "@/components/global/ActivityFeed";
import { ApiError, apiFetch } from "@/lib/api-client";
import styles from "./dashboard-page.module.css";
import type { DashboardOverview } from "./types";

interface GrowthInsightsOut {
  insights: string[];
  recommendations: string[];
  topics: string[];
}


const QUICK_ACTIONS = [
  {
    eyebrow: "PLAN",
    title: "Create Campaign",
    description: "Start with your goal, audience and message.",
    href: "/dashboard/campaigns/new",
    icon: "🚀",
    tone: "violet",
  },
  {
    eyebrow: "CREATE",
    title: "Email Templates",
    description: "Use a responsive template or create your own.",
    href: "/dashboard/templates/new",
    icon: "✨",
    tone: "blue",
  },
  {
    eyebrow: "AUDIENCE",
    title: "Import Contacts",
    description: "Import, organize and segment your audience.",
    href: "/dashboard/contacts/imports",
    icon: "👥",
    tone: "cyan",
  },
  {
    eyebrow: "SCHEDULE",
    title: "Social Publisher",
    description: "Create a post and place it on your calendar.",
    href: "/dashboard/social",
    icon: "📅",
    tone: "green",
  },
] as const;

function formatPct(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : `${value}%`;
}

function recommendationFor(overview: DashboardOverview) {
  if (overview.campaign_status_breakdown.failed > 0)
    return {
      label: "Action Required",
      title: `${overview.campaign_status_breakdown.failed} Campaign Failure${overview.campaign_status_breakdown.failed === 1 ? "" : "s"}`,
      description: "Review the failure before scheduling another send. Your campaign data is safe.",
      href: "/dashboard/campaigns?status=failed",
      action: "Review campaigns",
      tone: "danger",
    };
  if (overview.total_contacts === 0)
    return {
      label: "Next Step",
      title: "Build Your Audience",
      description: "Import contacts, map consent correctly, then create a focused segment.",
      href: "/dashboard/contacts/imports",
      action: "Import contacts",
      tone: "info",
    };
  if (overview.active_campaigns === 0)
    return {
      label: "Growth Engine",
      title: "Launch a Campaign",
      description: `You have ${overview.total_contacts.toLocaleString()} contacts ready. Start engaging them today.`,
      href: "/dashboard/campaigns/new",
      action: "Create campaign",
      tone: "growth",
    };
  return {
    label: "Momentum",
    title: "Monitor Performance",
    description: "Use analytics to optimize your next automated workflow.",
    href: "/dashboard/campaigns",
    action: "View campaigns",
    tone: "growth",
  };
}

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);

  const [aiInsights, setAiInsights] = useState<GrowthInsightsOut | null>(null);
  const [aiLoading, setAiLoading] = useState(true);

  useEffect(() => {
    apiFetch<DashboardOverview>("/dashboard/overview")
      .then(setOverview)
      .catch((err) =>
        setLoadError(
          err instanceof ApiError ? "Could not load your workspace." : "Something went wrong.",
        ),
      )
      .finally(() => setLoading(false));
      
    // Fetch AI Phase 9 Insights
    apiFetch<GrowthInsightsOut>("/analytics/insights")
      .then(setAiInsights)
      .catch(() => console.error("Failed to load AI insights"))
      .finally(() => setAiLoading(false));
  }, []);

  if (loading)
    return (
      <div className={styles.loading}>
        <span />
        Initializing Workspace...
      </div>
    );
  if (loadError || !overview)
    return (
      <div className={styles.errorState}>
        <strong>System Offline</strong>
        <span>{loadError ?? "Could not connect to the backend."}</span>
        <button type="button" onClick={() => window.location.reload()}>
          Retry Connection
        </button>
      </div>
    );


  const recommendation = recommendationFor(overview);

  return (
    <main className={styles.page}>
      
      {/* 1. HERO COMMAND CENTER */}
      <section className={styles.hero}>
        <div className={styles.heroContent}>
          <span className={styles.eyebrow}>WORKSPACE DASHBOARD</span>
          <h1>Welcome to Growixa OS.</h1>
          <p>Your central hub for marketing automation, audience management, and AI generation.</p>
          <div className={styles.heroActions}>
            <Link href="/dashboard/ai" className={styles.primaryAction}>
              Ask AI Assistant
            </Link>
            <Link href="/dashboard/campaigns/new" className={styles.secondaryAction}>
              Launch Campaign
            </Link>
          </div>
        </div>
        <div className={styles.heroSignal}>
          <span className={styles.signalLabel}>ACTIVE CAMPAIGNS</span>
          <strong>{overview.active_campaigns}</strong>
          <span>currently running</span>
          <div />
          <small>{overview.scheduled_social_posts} social posts queued</small>
        </div>
      </section>

      {/* 2. BENTO QUICK ACTIONS */}
      <section>
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>WORKFLOWS</span>
            <h2>Quick Actions</h2>
          </div>
        </div>
        <div className={styles.quickGrid}>
          {QUICK_ACTIONS.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className={`${styles.quickCard} ${styles[action.tone]}`}
            >
              <div>
                <span className={styles.quickEyebrow}>{action.eyebrow}</span>
                <h3>{action.title}</h3>
                <p>{action.description}</p>
              </div>
              <span className={styles.quickIcon}>{action.icon}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* 3. GROWTH PULSE (KPIs) */}
      <section>
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>ANALYTICS</span>
            <h2>System Pulse</h2>
          </div>
        </div>
        
        <div className={styles.pulseGrid}>
          <article className={styles.pulseCard}>
            <div className={styles.pulseHeaderRow}>
              <span>Total Contacts</span>
            </div>
            <strong>{overview.total_contacts.toLocaleString()}</strong>
            <small>Active Audience Size</small>
          </article>
          
          <article className={styles.pulseCard}>
            <div className={styles.pulseHeaderRow}>
              <span>Live Campaigns</span>
            </div>
            <strong>{overview.active_campaigns}</strong>
            <small>Scheduled & Sending</small>
          </article>

          <article className={`${styles.pulseCard} ${styles.featuredPulse}`}>
            <div className={styles.pulseHeaderRow}>
              <span>Email CTR</span>
            </div>
            <strong>{formatPct(overview.email_click_rate_pct)}</strong>
            <small>Aggregate Engagement</small>
          </article>
        </div>
      </section>

      {/* 4. SMART INSIGHT (AI RECOMMENDATION) */}
      <section className={styles.insightCard}>
        <div className={`${styles.insightIcon} ${styles[recommendation.tone]}`}>
          {recommendation.tone === 'danger' ? '⚠️' : '💡'}
        </div>
        <div className={styles.insightCopy}>
          <span>{recommendation.label}</span>
          <h2>{recommendation.title}</h2>
          <p>{recommendation.description}</p>
        </div>
        <Link href={recommendation.href}>{recommendation.action}</Link>
      </section>

      {/* 4.5 AI GROWTH INTELLIGENCE (Phase 9) */}
      <section>
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>AI STRATEGIST</span>
            <h2>AI Growth Intelligence</h2>
          </div>
          <Link href="/dashboard/analytics/insights" className={styles.secondaryButton} style={{ textDecoration: 'none', padding: '8px 16px', borderRadius: '8px', border: '1px solid #e5e7eb', fontSize: '14px', fontWeight: 500, color: '#374151' }}>
            View Full Report
          </Link>
        </div>
        
        {aiLoading ? (
          <div className={styles.card} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '24px' }}>
            <span style={{ animation: "pulse 1.5s infinite", fontSize: '24px' }}>✨</span>
            <span style={{ color: '#6b7280' }}>AI is analyzing your 30-day performance data...</span>
          </div>
        ) : aiInsights ? (
          <div className={styles.pulseGrid} style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
            <article className={styles.card} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>📊</span>
                <strong style={{ fontSize: '16px' }}>Key Insight</strong>
              </div>
              <p style={{ color: '#4b5563', lineHeight: 1.5, margin: 0 }}>
                {aiInsights.insights?.[0] || "Trend analysis complete."}
              </p>
            </article>

            <article className={styles.card} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px', background: 'linear-gradient(to right bottom, #eef2ff, #faf5ff)', border: '1px solid #e0e7ff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>🚀</span>
                <strong style={{ fontSize: '16px', color: '#4338ca' }}>Top Recommendation</strong>
              </div>
              <p style={{ color: '#374151', lineHeight: 1.5, margin: 0, fontWeight: 500 }}>
                {aiInsights.recommendations?.[0] || "Keep posting consistently."}
              </p>
            </article>

            <article className={styles.card} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>💡</span>
                <strong style={{ fontSize: '16px' }}>Trending Topic</strong>
              </div>
              <p style={{ color: '#86198f', lineHeight: 1.5, margin: 0, fontWeight: 600, display: 'inline-block', backgroundColor: '#fdf4ff', padding: '4px 12px', borderRadius: '16px', width: 'fit-content' }}>
                # {aiInsights.topics?.[0] || "Industry News"}
              </p>
            </article>
          </div>
        ) : null}
      </section>

      {/* 5. CHARTS & METRICS */}
      <div className={styles.analyticsGrid}>
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.sectionKicker}>TRENDS</span>
              <h2>Audience Growth</h2>
            </div>
            <strong>{overview.total_contacts.toLocaleString()}</strong>
          </div>
          <TrendChart
            points={overview.contact_growth_6_months.map((point) => ({
              label: point.month.slice(5),
              value: point.contacts,
            }))}
          />
        </section>

        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.sectionKicker}>LIMITS</span>
              <h2>Plan Usage</h2>
            </div>
          </div>
          <div className={styles.gauges}>
            <QuotaGauge label="Contacts" used={overview.quota.contact_usage} limit={overview.quota.contact_limit} />
            <QuotaGauge label="Emails" used={overview.quota.email_usage} limit={overview.quota.email_limit} />
          </div>
          <p className={styles.quotaHint}>
            <Link href="/dashboard/billing">Manage Subscription</Link>
          </p>
        </section>
      </div>

      {/* 6. GLOBAL ACTIVITY FEED (TRANSPARENCY) */}
      <section style={{ marginTop: '2rem' }}>
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>TRANSPARENCY</span>
            <h2>Command Center Activity</h2>
          </div>
        </div>
        <ActivityFeed />
      </section>

    </main>
  );
}
