"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LiveActivityStream } from "@/components/dashboard/live-activity-stream";
import { QuotaGauge } from "@/components/dashboard/quota-gauge";
import { TrendChart } from "@/components/dashboard/trend-chart";
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

const QUICK_ACTIONS = [
  {
    eyebrow: "PLAN",
    title: "Create a campaign",
    description: "Start with your goal, audience and message.",
    href: "/dashboard/campaigns/new",
    icon: "↗",
    tone: "violet",
  },
  {
    eyebrow: "CREATE",
    title: "Build email content",
    description: "Use a responsive template or create your own.",
    href: "/dashboard/templates/new",
    icon: "✦",
    tone: "blue",
  },
  {
    eyebrow: "AUDIENCE",
    title: "Add contacts",
    description: "Import, organize and segment your audience.",
    href: "/dashboard/contacts/imports",
    icon: "+",
    tone: "cyan",
  },
  {
    eyebrow: "SCHEDULE",
    title: "Plan social content",
    description: "Create a post and place it on your calendar.",
    href: "/dashboard/social",
    icon: "◎",
    tone: "green",
  },
] as const;

function formatPct(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : `${value}%`;
}

function recommendationFor(overview: DashboardOverview) {
  if (overview.campaign_status_breakdown.failed > 0)
    return {
      label: "Needs attention",
      title: `${overview.campaign_status_breakdown.failed} campaign failure${overview.campaign_status_breakdown.failed === 1 ? "" : "s"}`,
      description: "Review the failure before scheduling another send. Your campaign data is safe.",
      href: "/dashboard/campaigns?status=failed",
      action: "Review campaigns",
      tone: "danger",
    };
  if (overview.total_contacts === 0)
    return {
      label: "Best next step",
      title: "Build your first audience",
      description: "Import contacts, map consent correctly, then create a focused segment.",
      href: "/dashboard/contacts/imports",
      action: "Import contacts",
      tone: "info",
    };
  if (overview.active_campaigns === 0)
    return {
      label: "Growth opportunity",
      title: "Turn your audience into a campaign",
      description: `You have ${overview.total_contacts.toLocaleString()} contacts and no active campaign. Start with one clear business goal.`,
      href: "/dashboard/campaigns/new",
      action: "Create campaign",
      tone: "growth",
    };
  return {
    label: "Keep momentum",
    title: "Review live campaign performance",
    description: "Use clicks and recipient activity to decide what to improve next.",
    href: "/dashboard/campaigns",
    action: "View campaigns",
    tone: "growth",
  };
}

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);

  useEffect(() => {
    apiFetch<DashboardOverview>("/dashboard/overview")
      .then(setOverview)
      .catch((err) =>
        setLoadError(
          err instanceof ApiError ? "Could not load your command center." : "Something went wrong.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className={styles.loading} role="status">
        <span />
        Preparing your growth command center…
      </div>
    );
  if (loadError || !overview)
    return (
      <div className={styles.errorState} role="alert">
        <strong>Growixa could not load this workspace.</strong>
        <span>{loadError ?? "Could not load your command center."}</span>
        <button type="button" onClick={() => window.location.reload()}>
          Try again
        </button>
      </div>
    );

  const statusEntries = Object.entries(overview.campaign_status_breakdown) as [
    keyof CampaignStatusBreakdown,
    number,
  ][];
  const recommendation = recommendationFor(overview);
  const statusTotal = statusEntries.reduce((sum, [, count]) => sum + count, 0);

  return (
    <main className={styles.page}>
      <section className={styles.hero} aria-labelledby="command-center-heading">
        <div className={styles.heroContent}>
          <span className={styles.eyebrow}>GROWTH COMMAND CENTER</span>
          <h1 id="command-center-heading">What do you want to grow today?</h1>
          <p>Turn a business goal into an audience, campaign and measurable next action.</p>
          <div className={styles.heroActions}>
            <Link href="/dashboard/ai" className={styles.primaryAction}>
              ✦ Ask Growixa
            </Link>
            <Link href="/dashboard/campaigns/new" className={styles.secondaryAction}>
              Create campaign
            </Link>
          </div>
        </div>
        <div className={styles.heroSignal} aria-label="Current workspace signal">
          <span className={styles.signalLabel}>LIVE WORKSPACE</span>
          <strong>{overview.active_campaigns}</strong>
          <span>active campaigns</span>
          <div />
          <small>{overview.scheduled_social_posts} social posts scheduled</small>
        </div>
      </section>

      <section aria-labelledby="quick-actions-heading">
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>START HERE</span>
            <h2 id="quick-actions-heading">Quick actions</h2>
          </div>
          <span>Every action opens a working Growixa flow</span>
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
              <span className={styles.quickIcon} aria-hidden="true">
                {action.icon}
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section aria-labelledby="growth-pulse-heading">
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionKicker}>REAL WORKSPACE DATA</span>
            <h2 id="growth-pulse-heading">Growth pulse</h2>
          </div>
          <Link href="/dashboard/campaigns">View campaign details →</Link>
        </div>
        <div className={styles.pulseGrid}>
          <article className={styles.pulseCard}>
            <div className={styles.pulseHeaderRow}>
              <span>Audience</span>
              <span className="tactileBadge tactileBadgeCyan">UI</span>
            </div>
            <strong>{overview.total_contacts.toLocaleString()}</strong>
            <small>Total contacts</small>
          </article>
          <article className={styles.pulseCard}>
            <div className={styles.pulseHeaderRow}>
              <span>Campaigns</span>
              <span className="tactileBadge tactileBadgePurple">UX</span>
            </div>
            <strong>{overview.active_campaigns}</strong>
            <small>Live &amp; scheduled</small>
          </article>
          <article className={`${styles.pulseCard} ${styles.featuredPulse}`}>
            <div className={styles.pulseHeaderRow}>
              <span>Email clicks</span>
              <span className="tactileBadge tactileBadgeAmber">Growth</span>
            </div>
            <strong>{formatPct(overview.email_click_rate_pct)}</strong>
            <div className="tactileTrack" style={{ marginTop: "4px" }}>
              <div className="tactileProgress" style={{ width: `${Math.min((overview.email_click_rate_pct || 0) * 8, 100)}%` }} />
            </div>
            <small>Delivered campaigns</small>
          </article>
          <article className={styles.pulseCard}>
            <div className={styles.pulseHeaderRow}>
              <span>Click-to-open</span>
              <span className="tactileBadge tactileBadgePink">Audience</span>
            </div>
            <strong>{formatPct(overview.email_ctor_pct)}</strong>
            <small>Unique CTOR</small>
          </article>
          <article className={styles.pulseCard}>
            <div className={styles.pulseHeaderRow}>
              <span>Email opens</span>
              <span className="tactileBadge tactileBadgeEmerald">Delivery</span>
            </div>
            <strong>{formatPct(overview.email_open_rate_pct)}</strong>
            <small>Directional signal</small>
          </article>
        </div>
      </section>

      <section className={styles.insightCard} aria-labelledby="recommendation-heading">
        <div className={`${styles.insightIcon} ${styles[recommendation.tone]}`} aria-hidden="true">
          ✦
        </div>
        <div className={styles.insightCopy}>
          <span>{recommendation.label}</span>
          <h2 id="recommendation-heading">{recommendation.title}</h2>
          <p>{recommendation.description}</p>
        </div>
        <Link href={recommendation.href}>{recommendation.action} →</Link>
      </section>

      <div className={styles.analyticsGrid}>
        <section className={styles.card} aria-labelledby="audience-growth-heading">
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.sectionKicker}>AUDIENCE</span>
              <h2 id="audience-growth-heading">Contact growth</h2>
            </div>
            <strong>{overview.total_contacts.toLocaleString()} total</strong>
          </div>
          <TrendChart
            points={overview.contact_growth_6_months.map((point) => ({
              label: point.month.slice(5),
              value: point.contacts,
            }))}
          />
        </section>
        <section className={styles.card} aria-labelledby="campaign-health-heading">
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.sectionKicker}>EXECUTION</span>
              <h2 id="campaign-health-heading">Campaign health</h2>
            </div>
          </div>
          {statusTotal === 0 ? (
            <EmptyCampaign />
          ) : (
            <ul className={styles.statusList}>
              {statusEntries
                .filter(([, count]) => count > 0)
                .map(([status, count]) => (
                  <li key={status}>
                    <div>
                      <span className={`${styles.statusDot} ${styles[`status_${status}`]}`} />
                      <span>{STATUS_LABEL[status]}</span>
                    </div>
                    <strong>{count}</strong>
                  </li>
                ))}
            </ul>
          )}
        </section>
      </div>

      <div className={styles.activityGrid}>
        <LiveActivityStream items={overview.recent_activity ?? []} />
        <section className={styles.card} aria-labelledby="quota-heading">
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.sectionKicker}>CAPACITY</span>
              <h2 id="quota-heading">{overview.quota.plan_name} plan usage</h2>
            </div>
          </div>
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
          <p className={styles.quotaHint}>
            {overview.quota.ai_credits_remaining.toLocaleString()} top-up AI credits remaining.{" "}
            <Link href="/dashboard/billing">Manage plan →</Link>
          </p>
        </section>
      </div>

      <section className={styles.card} aria-labelledby="recent-campaigns-heading">
        <div className={styles.cardHeader}>
          <div>
            <span className={styles.sectionKicker}>RECENT WORK</span>
            <h2 id="recent-campaigns-heading">Recent campaigns</h2>
          </div>
          <Link href="/dashboard/campaigns">View all →</Link>
        </div>
        {overview.recent_campaigns.length === 0 ? (
          <EmptyCampaign />
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Campaign</th>
                  <th>Status</th>
                  <th>Sent</th>
                  <th>Open signal</th>
                  <th>
                    <span className={styles.srOnly}>Action</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {overview.recent_campaigns.map((campaign) => (
                  <tr key={campaign.id}>
                    <td>
                      <Link href={`/dashboard/campaigns/${campaign.id}`}>{campaign.name}</Link>
                    </td>
                    <td>
                      <span className={styles.statusBadge}>{campaign.status}</span>
                    </td>
                    <td>{campaign.sent_count.toLocaleString()}</td>
                    <td>{formatPct(campaign.open_rate_pct)}</td>
                    <td>
                      <Link
                        href={`/dashboard/campaigns/${campaign.id}`}
                        aria-label={`View ${campaign.name}`}
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

function EmptyCampaign() {
  return (
    <div className={styles.emptyState}>
      <strong>Your campaign workspace is ready</strong>
      <span>
        Start with a goal and Growixa will guide you through audience, content, review and
        scheduling.
      </span>
      <Link href="/dashboard/campaigns/new">Create campaign</Link>
    </div>
  );
}
