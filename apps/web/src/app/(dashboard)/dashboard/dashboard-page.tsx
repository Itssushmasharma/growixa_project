"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "@/lib/api-client";
import styles from "./dashboard-page.module.css";
import type { DashboardOverview } from "./types";

interface GrowthInsightsOut {
  insights: string[];
  recommendations: string[];
  topics: string[];
}

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [timeTab, setTimeTab] = useState<"daily" | "weekly" | "monthly" | "yearly">("monthly");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    apiFetch<DashboardOverview>("/dashboard/overview")
      .then(setOverview)
      .catch((err) =>
        setLoadError(
          err instanceof ApiError ? "Could not load your workspace." : "Something went wrong.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className={styles.loading}>
        <span />
        Initializing Growixa Dashboard...
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

  return (
    <main className={styles.page}>
      {/* 1. TOP TITLE & TIME FILTER BAR */}
      <div className={styles.topBar}>
        <div className={styles.topBarTitle}>
          <h1>Growixa Command OS — Dashboard</h1>
          <p>Overview of Latest Month Performance & Unified Agency Telemetry</p>
        </div>
        <div className={styles.timeTabs}>
          {(["daily", "weekly", "monthly", "yearly"] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              className={`${styles.timeTab} ${timeTab === tab ? styles.timeTabActive : ""}`}
              onClick={() => setTimeTab(tab)}
            >
              {tab.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* 2. HERO DUAL ANALYTICS ROW (EARNINGS + SPLINE CHART + TRAFFIC DONUT) */}
      <div className={styles.heroRow}>
        {/* Left: Earnings Overview */}
        <div className={styles.earningsCard}>
          <div>
            <span className={styles.cardLabel}>Current Month Earnings</span>
            <div className={styles.earningsAmount}>$3,468.96</div>
            <div className={styles.earningsSub}>Updated 12 mins ago</div>

            <div className={styles.salesCount}>82</div>
            <div className={styles.salesSub}>Current Month Conversions</div>
          </div>

          <button type="button" className={styles.summaryBtn}>
            Last Month Summary →
          </button>

          <div className={styles.statPillsGrid}>
            <div className={styles.statPill}>
              <div className={styles.pillIconPink}>👛</div>
              <div className={styles.pillInfo}>
                <span>Wallet Balance</span>
                <strong>$4,567.53</strong>
              </div>
            </div>
            <div className={styles.statPill}>
              <div className={styles.pillIconPurple}>💜</div>
              <div className={styles.pillInfo}>
                <span>Referral Earning</span>
                <strong>$1,689.53</strong>
              </div>
            </div>
            <div className={styles.statPill}>
              <div className={styles.pillIconBlue}>💙</div>
              <div className={styles.pillInfo}>
                <span>Estimate Sales</span>
                <strong>$2,851.53</strong>
              </div>
            </div>
            <div className={styles.statPill}>
              <div className={styles.pillIconYellow}>💛</div>
              <div className={styles.pillInfo}>
                <span>Earning</span>
                <strong>$52,567.53</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Wave Spline Revenue/Reach Chart */}
        <div className={styles.splineCard}>
          <div className={styles.chartHeader}>
            <div>
              <span className={styles.cardLabel}>Audience & Growth Curve</span>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 800, margin: "2px 0 0 0" }}>
                Revenue & Engagement Wave
              </h2>
            </div>
            <div className={styles.chartLegend}>
              <span className={styles.legendItem}>
                <span className={styles.dotBlue} /> Online Store
              </span>
              <span className={styles.legendItem}>
                <span className={styles.dotCherry} /> Meta & WhatsApp Ads
              </span>
            </div>
          </div>

          <div className={styles.svgSplineContainer}>
            <svg
              viewBox="0 0 500 200"
              className="w-full h-full"
              preserveAspectRatio="none"
              style={{ overflow: "visible" }}
            >
              <defs>
                <linearGradient id="splineGradCherry" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6D0626" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#6D0626" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="splineGradBlue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0284c7" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#0284c7" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="0" y1="40" x2="500" y2="40" stroke="#f1f5f9" strokeDasharray="4 4" />
              <line x1="0" y1="80" x2="500" y2="80" stroke="#f1f5f9" strokeDasharray="4 4" />
              <line x1="0" y1="120" x2="500" y2="120" stroke="#f1f5f9" strokeDasharray="4 4" />
              <line x1="0" y1="160" x2="500" y2="160" stroke="#f1f5f9" strokeDasharray="4 4" />

              {/* Spline Area 1 (Blue) */}
              <path
                d="M 0,140 Q 60,110 120,130 T 240,110 T 360,120 T 500,60 L 500,190 L 0,190 Z"
                fill="url(#splineGradBlue)"
              />
              <path
                d="M 0,140 Q 60,110 120,130 T 240,110 T 360,120 T 500,60"
                fill="none"
                stroke="#0284c7"
                strokeWidth="3"
              />

              {/* Spline Area 2 (Cherry) */}
              <path
                d="M 0,160 Q 70,120 140,140 T 280,100 T 420,50 T 500,70 L 500,190 L 0,190 Z"
                fill="url(#splineGradCherry)"
              />
              <path
                d="M 0,160 Q 70,120 140,140 T 280,100 T 420,50 T 500,70"
                fill="none"
                stroke="#6D0626"
                strokeWidth="3"
              />

              {/* Highlight Nodes */}
              <circle cx="280" cy="100" r="5" fill="#6D0626" stroke="white" strokeWidth="2" />
              <circle cx="420" cy="50" r="5" fill="#db2777" stroke="white" strokeWidth="2" />

              {/* X Axis Labels */}
              <text x="10" y="195" fontSize="10" fill="#94a3b8">Jan</text>
              <text x="100" y="195" fontSize="10" fill="#94a3b8">Feb</text>
              <text x="190" y="195" fontSize="10" fill="#94a3b8">Mar</text>
              <text x="280" y="195" fontSize="10" fill="#94a3b8">Apr</text>
              <text x="370" y="195" fontSize="10" fill="#94a3b8">May</text>
              <text x="460" y="195" fontSize="10" fill="#94a3b8">Jun</text>
            </svg>
          </div>
        </div>

        {/* Right: Traffic Donut Chart */}
        <div className={styles.donutCard}>
          <div className={styles.chartHeader}>
            <span className={styles.cardLabel}>Traffic Sources</span>
          </div>

          <div className={styles.donutSvgWrap}>
            <svg width="150" height="150" viewBox="0 0 100 100">
              {/* Donut Background Circle */}
              <circle cx="50" cy="50" r="38" fill="none" stroke="#f1f5f9" strokeWidth="14" />

              {/* Segment 1: Facebook / Meta (55% -> Magenta) */}
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="none"
                stroke="#6D0626"
                strokeWidth="14"
                strokeDasharray="131 238"
                strokeDashoffset="0"
                transform="rotate(-90 50 50)"
              />
              {/* Segment 2: WhatsApp / Social (33% -> Purple) */}
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="none"
                stroke="#9333ea"
                strokeWidth="14"
                strokeDasharray="78 238"
                strokeDashoffset="-131"
                transform="rotate(-90 50 50)"
              />
              {/* Segment 3: Direct Search (12% -> Yellow) */}
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="none"
                stroke="#d97706"
                strokeWidth="14"
                strokeDasharray="29 238"
                strokeDashoffset="-209"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div className={styles.donutCenterText}>
              <strong>100%</strong>
              <span>Channels</span>
            </div>
          </div>

          <div className={styles.donutLegendGrid}>
            <div>
              <strong>33%</strong>
              <span>Meta Ads</span>
            </div>
            <div>
              <strong>55%</strong>
              <span>WhatsApp</span>
            </div>
            <div>
              <strong>12%</strong>
              <span>Direct</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. SECOND ROW: 4 VIBRANT METRIC SPARKLINE CARDS */}
      <div className={styles.vibrantMetricsGrid}>
        {/* Card 1: Revenue Status (Cherry Gradient) */}
        <div className={`${styles.gradientCard} ${styles.cardCherry}`}>
          <div className={styles.cardLeftInfo}>
            <h4>Revenue Status</h4>
            <strong>$432</strong>
            <span>Jan 01 - Jan 10</span>
          </div>
          <div className={styles.cardSparkline}>
            <svg viewBox="0 0 80 48" width="80" height="48">
              <path d="M 0,38 L 15,20 L 30,30 L 45,10 L 60,25 L 75,5" fill="none" stroke="white" strokeWidth="2.5" />
              <rect x="10" y="32" width="6" height="12" fill="white" opacity="0.4" />
              <rect x="25" y="24" width="6" height="20" fill="white" opacity="0.6" />
              <rect x="40" y="14" width="6" height="30" fill="white" opacity="0.8" />
              <rect x="55" y="28" width="6" height="16" fill="white" opacity="0.4" />
              <rect x="70" y="8" width="6" height="36" fill="white" opacity="1" />
            </svg>
          </div>
        </div>

        {/* Card 2: Page Views (Purple Gradient) */}
        <div className={`${styles.gradientCard} ${styles.cardPurple}`}>
          <div className={styles.cardLeftInfo}>
            <h4>Page Views</h4>
            <strong>12,432</strong>
            <span>Active Visitors</span>
          </div>
          <div className={styles.cardSparkline}>
            <svg viewBox="0 0 80 48" width="80" height="48">
              <path d="M 0,35 Q 20,10 40,30 T 80,15 L 80,48 L 0,48 Z" fill="rgba(255,255,255,0.2)" />
              <path d="M 0,35 Q 20,10 40,30 T 80,15" fill="none" stroke="white" strokeWidth="2.5" />
            </svg>
          </div>
        </div>

        {/* Card 3: Bounce Rate / CTR (Cyan Gradient) */}
        <div className={`${styles.gradientCard} ${styles.cardCyan}`}>
          <div className={styles.cardLeftInfo}>
            <h4>Bounce Rate</h4>
            <strong>2.4%</strong>
            <span>Monthly Avg</span>
          </div>
          <div className={styles.cardSparkline}>
            <svg viewBox="0 0 80 48" width="80" height="48">
              <path d="M 0,25 L 20,35 L 40,15 L 60,30 L 80,10" fill="none" stroke="white" strokeWidth="2.5" />
              <circle cx="40" cy="15" r="4" fill="white" />
              <circle cx="80" cy="10" r="4" fill="white" />
            </svg>
          </div>
        </div>

        {/* Card 4: Total Leads (Orange Gradient) */}
        <div className={`${styles.gradientCard} ${styles.cardOrange}`}>
          <div className={styles.cardLeftInfo}>
            <h4>Total Leads</h4>
            <strong>842</strong>
            <span>Qualified Growth</span>
          </div>
          <div className={styles.cardSparkline}>
            <svg viewBox="0 0 80 48" width="80" height="48">
              <rect x="5" y="28" width="10" height="20" rx="2" fill="white" opacity="0.6" />
              <rect x="23" y="18" width="10" height="30" rx="2" fill="white" opacity="0.8" />
              <rect x="41" y="24" width="10" height="24" rx="2" fill="white" opacity="0.6" />
              <rect x="59" y="8" width="10" height="40" rx="2" fill="white" opacity="1" />
            </svg>
          </div>
        </div>
      </div>

      {/* 4. BOTTOM GRID (RECENT ACTIVITIES + ORDER STATUS/LEAD MANAGEMENT DATA TABLE) */}
      <div className={styles.bottomGrid}>
        {/* Left: Recent Activities */}
        <div className={styles.activityPanel}>
          <div className={styles.panelHeader}>Recent Activities</div>

          <div className={styles.timelineList}>
            <div className={styles.timelineItem}>
              <span className={styles.timelineTime}>42 Mins Ago</span>
              <div className={styles.timelineBadgePink}>📋</div>
              <div className={styles.timelineContent}>
                <strong>Task Updated</strong>
                <p>Nikolai Updated a Task in Creative Studio</p>
              </div>
            </div>

            <div className={styles.timelineItem}>
              <span className={styles.timelineTime}>1 day Ago</span>
              <div className={styles.timelineBadgePurple}>💼</div>
              <div className={styles.timelineContent}>
                <strong>Deal Added</strong>
                <p>Panshi Updated a Task in CRM Pipeline</p>
              </div>
            </div>

            <div className={styles.timelineItem}>
              <span className={styles.timelineTime}>42 Mins Ago</span>
              <div className={styles.timelineBadgeCyan}>📝</div>
              <div className={styles.timelineContent}>
                <strong>Published Article</strong>
                <p>Rasel Published an Article to Landing Page</p>
              </div>
            </div>

            <div className={styles.timelineItem}>
              <span className={styles.timelineTime}>1 day Ago</span>
              <div className={styles.timelineBadgeOrange}>⚡</div>
              <div className={styles.timelineContent}>
                <strong>Dock Updated</strong>
                <p>Reshmi Updated a Dock in Automations</p>
              </div>
            </div>

            <div className={styles.timelineItem}>
              <span className={styles.timelineTime}>1 day Ago</span>
              <div className={styles.timelineBadgeGreen}>💬</div>
              <div className={styles.timelineContent}>
                <strong>Replied Comment</strong>
                <p>Jenathon Added a Comment in WhatsApp Broadcast</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Order Status & Lead Data Table */}
        <div className={styles.tablePanel}>
          <div>
            <div className={styles.tableTopRow}>
              <div>
                <span className={styles.cardLabel}>Overview of Latest Month</span>
                <h2 style={{ fontSize: "1.1rem", fontWeight: 800, margin: "2px 0 0 0" }}>
                  Order Status & Lead Stream
                </h2>
              </div>

              <div className={styles.tableActions}>
                <button type="button" className={styles.addBtn}>
                  + Add
                </button>
                <button type="button" className={styles.iconBtn} title="Print">
                  🖨️
                </button>
                <button type="button" className={styles.iconBtn} title="Delete">
                  🗑️
                </button>
                <button type="button" className={styles.iconBtn} title="Lock">
                  🔒
                </button>
                <input
                  type="text"
                  placeholder="Search..."
                  className={styles.searchInput}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            <table className={styles.dataTable}>
              <thead>
                <tr>
                  <th>INVOICE</th>
                  <th>CUSTOMERS</th>
                  <th>FROM</th>
                  <th>PRICE</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>#12386</td>
                  <td>Charly Dues</td>
                  <td>Brazil</td>
                  <td>$299</td>
                  <td>
                    <span className={styles.badgeProcess}>Process</span>
                  </td>
                </tr>
                <tr>
                  <td>#12387</td>
                  <td>Marko</td>
                  <td>Italy</td>
                  <td>$2,642</td>
                  <td>
                    <span className={styles.badgeOpen}>Open</span>
                  </td>
                </tr>
                <tr>
                  <td>#12388</td>
                  <td>Deniyel Onak</td>
                  <td>Russia</td>
                  <td>$981</td>
                  <td>
                    <span className={styles.badgeOnHold}>On Hold</span>
                  </td>
                </tr>
                <tr>
                  <td>#12389</td>
                  <td>Belgiri Bastana</td>
                  <td>Korea</td>
                  <td>$369</td>
                  <td>
                    <span className={styles.badgeProcess}>Process</span>
                  </td>
                </tr>
                <tr>
                  <td>#12390</td>
                  <td>Sarti Unona</td>
                  <td>Japan</td>
                  <td>$1,240</td>
                  <td>
                    <span className={styles.badgeDone}>Open</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className={styles.tableFooter}>
            <span>Showing 1 to 20 of 20 entries</span>
            <div className={styles.pagination}>
              <div className={`${styles.pageItem} ${styles.pageActive}`}>1</div>
              <div className={styles.pageItem}>2</div>
              <div className={styles.pageItem}>3</div>
              <div className={styles.pageItem}>4</div>
              <div className={styles.pageItem}>5</div>
              <div className={styles.pageItem}>6</div>
              <div className={styles.pageItem}>&gt;</div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. QUICK MODULE ACCESS STRIP FOR ALL BUILT PAGES */}
      <div className={styles.moduleStrip}>
        <div className={styles.moduleStripTitle}>
          🚀 Growixa Built Pages & Agency Modules Quick Launcher
        </div>
        <div className={styles.moduleGrid}>
          <Link href="/dashboard/creative-studio" className={styles.moduleLink}>
            🎨 Creative Studio
          </Link>
          <Link href="/dashboard/ads-hub" className={styles.moduleLink}>
            📊 PPC Ads Hub
          </Link>
          <Link href="/dashboard/lead-gen" className={styles.moduleLink}>
            🧲 Lead Gen & CRM
          </Link>
          <Link href="/dashboard/communications" className={styles.moduleLink}>
            💬 WhatsApp & SMS
          </Link>
          <Link href="/dashboard/planner" className={styles.moduleLink}>
            🧠 AI Strategy Planner
          </Link>
          <Link href="/dashboard/business-presence" className={styles.moduleLink}>
            🌐 Website Presence
          </Link>
          <Link href="/dashboard/seo" className={styles.moduleLink}>
            🔍 SEO Audit
          </Link>
          <Link href="/dashboard/campaigns" className={styles.moduleLink}>
            🎯 Campaigns
          </Link>
          <Link href="/dashboard/social" className={styles.moduleLink}>
            📱 Social Publisher
          </Link>
          <Link href="/dashboard/inbox" className={styles.moduleLink}>
            📥 Unified Inbox
          </Link>
          <Link href="/dashboard/analytics" className={styles.moduleLink}>
            📈 Telemetry
          </Link>
          <Link href="/dashboard/billing" className={styles.moduleLink}>
            💳 Billing Quotas
          </Link>
        </div>
      </div>
    </main>
  );
}
