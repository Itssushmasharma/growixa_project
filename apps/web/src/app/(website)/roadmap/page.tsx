"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Rocket, 
  Sparkles, 
  Layers, 
  Clock, 
  CheckCircle2, 
  ArrowRight, 
  MessageSquare, 
  Bot, 
  Zap, 
  ShieldCheck, 
  BarChart3, 
  Smartphone,
  Share2,
  Workflow
} from "lucide-react";
import styles from "./roadmap.module.css";

interface RoadmapTicket {
  id: string;
  title: string;
  desc: string;
  category: string;
  quarter: string;
  icon: React.ReactNode;
  tags: string[];
}

const NOW_TICKETS: RoadmapTicket[] = [
  {
    id: "GRX-RM-01",
    title: "WhatsApp Business V2 & Catalog Sync",
    desc: "Full support for WhatsApp catalog integration, automated cart recovery messages, and interactive multi-media templates.",
    category: "Messaging Engine",
    quarter: "In Active Build",
    icon: <MessageSquare className="w-5 h-5 text-rose-700" />,
    tags: ["WhatsApp API", "Catalog Sync", "Automated Triggers"],
  },
  {
    id: "GRX-RM-02",
    title: "AI Content Generator 2.0 with Brand Voice",
    desc: "Generate highly targeted email sequences and multi-channel social posts based on live CRM audience segments.",
    category: "AI Studio",
    quarter: "In Active Build",
    icon: <Bot className="w-5 h-5 text-rose-700" />,
    tags: ["GPT-4o & Claude", "Brand Guardrails", "Auto-Drafts"],
  },
  {
    id: "GRX-RM-03",
    title: "High-Volume Postmark SMTP Relays",
    desc: "Dedicated SMTP pool rotation with real-time delivery telemetry, bounce management, and open/click webhooks.",
    category: "Email Infrastructure",
    quarter: "In Active Build",
    icon: <Zap className="w-5 h-5 text-rose-700" />,
    tags: ["SMTP Pools", "Bounce Detection", "Real-Time Webhooks"],
  },
];

const NEXT_TICKETS: RoadmapTicket[] = [
  {
    id: "GRX-RM-04",
    title: "Custom Drag & Drop Dashboard Widgets",
    desc: "Allow users to build custom reporting dashboards using a modular drag-and-drop widget library and telemetry gauges.",
    category: "Analytics UI",
    quarter: "Q4 2026",
    icon: <BarChart3 className="w-5 h-5 text-rose-700" />,
    tags: ["Custom Widgets", "Candlestick Telemetry", "Export PDF"],
  },
  {
    id: "GRX-RM-05",
    title: "Shopify & E-commerce Deep Sync",
    desc: "Real-time bi-directional synchronization of products, orders, and customer purchase histories into Growixa CRM.",
    category: "Integrations",
    quarter: "Q4 2026",
    icon: <Workflow className="w-5 h-5 text-rose-700" />,
    tags: ["Shopify SDK", "Order Events", "LTV Tracking"],
  },
  {
    id: "GRX-RM-06",
    title: "Multi-Step Role Approval Workflows",
    desc: "Granular multi-stage approval pipelines for agencies and enterprise teams before publishing campaigns.",
    category: "Governance",
    quarter: "Q4 2026",
    icon: <ShieldCheck className="w-5 h-5 text-rose-700" />,
    tags: ["Manager Signoff", "Audit Logged", "Role Guardrails"],
  },
];

const FUTURE_TICKETS: RoadmapTicket[] = [
  {
    id: "GRX-RM-07",
    title: "TikTok & Shorts Native Video Scheduler",
    desc: "Direct video publishing, automatic clip transcoding, and engagement analytics for TikTok, Shorts, and Reels.",
    category: "Social Media",
    quarter: "Q1 2027",
    icon: <Smartphone className="w-5 h-5 text-rose-700" />,
    tags: ["Reels & TikTok", "Video Transcoder", "Engagement Telemetry"],
  },
  {
    id: "GRX-RM-08",
    title: "Predictive Lead LTV Scoring AI",
    desc: "Machine learning models to predict lifetime revenue potential the moment a new contact enters your CRM.",
    category: "AI & Data",
    quarter: "Q1 2027",
    icon: <Sparkles className="w-5 h-5 text-rose-700" />,
    tags: ["Predictive Models", "Conversion Probability", "Auto Segment"],
  },
  {
    id: "GRX-RM-09",
    title: "Unified Omnichannel Customer Inbox",
    desc: "Single unified inbox combining email replies, social DMs, WhatsApp messages, and Webhook alerts.",
    category: "Communication",
    quarter: "Q1 2027",
    icon: <Share2 className="w-5 h-5 text-rose-700" />,
    tags: ["Unified Inbox", "Cross-Channel", "Instant Response"],
  },
];

export default function RoadmapPage() {
  const [activeTab, setActiveTab] = useState<"all" | "now" | "next" | "future">("all");

  return (
    <main className={styles.page}>
      {/* Background Giant Brand Watermark Text */}
      <div className={styles.watermarkText} aria-hidden="true">
        GROWIXA
      </div>

      {/* Page Header */}
      <header className={styles.header}>
        <div className={styles.eyebrow}>
          <Rocket className="w-4 h-4 text-rose-700" /> Growixa Product Roadmap
        </div>
        <h1 className={styles.title}>
          Building the Future of <span>Growth Automation</span>
        </h1>
        <p className={styles.subtitle}>
          Explore our product vision, see what&apos;s currently in active build, and help shape the next features in our ecosystem.
        </p>
      </header>

      {/* Infographic Connected Stack Architecture Diagram (Reference Image Layout) */}
      <section className={styles.architectureDiagram} aria-label="Roadmap Core OS Diagram">
        <div className={styles.diagTitleRow}>
          <span className={styles.diagTag}>Ecosystem Roadmap Architecture</span>
          <h2>Connect Your Tech Stack &amp; Automate Growth</h2>
        </div>

        <div className={styles.diagGrid}>
          {/* Left Node: Active Integrations */}
          <div className={styles.diagNodeCard}>
            <div className={styles.nodeBadge}>CONNECTED STACK</div>
            <div className={styles.iconGrid}>
              <span className={styles.iconPill}>Mail</span>
              <span className={styles.iconPill}>AI</span>
              <span className={styles.iconPill}>Stripe</span>
              <span className={styles.iconPill}>Social</span>
              <span className={styles.iconPill}>Zapier</span>
              <span className={styles.iconPill}>Slack</span>
            </div>
            <p className={styles.nodeDesc}>Unified connectors syncing audience &amp; execution events</p>
          </div>

          {/* Central Connector Node: Growixa Business OS */}
          <div className={styles.centerOsCard}>
            <div className={styles.centerPulseGlow} aria-hidden="true" />
            <div className={styles.osIconBox}>
              <Layers className="w-10 h-10 text-white" />
            </div>
            <h3 className={styles.osTitle}>Growixa Core OS</h3>
            <span className={styles.osSub}>Automate. Publish. Convert.</span>
          </div>

          {/* Right Node: Real-time Telemetry */}
          <div className={styles.diagNodeCard}>
            <div className={styles.nodeBadge}>TELEMETRY DASHBOARD</div>
            <div className={styles.statList}>
              <div className={styles.statItem}>
                <span>Campaign Delivery</span>
                <strong>99.8%</strong>
              </div>
              <div className={styles.statItem}>
                <span>AI Approvals</span>
                <strong>Instant</strong>
              </div>
              <div className={styles.statItem}>
                <span>Active Workflows</span>
                <strong>1,240+</strong>
              </div>
            </div>
            <p className={styles.nodeDesc}>Real-time performance telemetry &amp; conversion tracking</p>
          </div>
        </div>

        {/* 4 Benefit Pillars Strip below Diagram */}
        <div className={styles.pillarStrip}>
          <div className={styles.pillarItem}>
            <CheckCircle2 className="w-5 h-5 text-rose-700" />
            <div>
              <strong>Fewer Tools</strong>
              <small>Lower cost &amp; zero clutter</small>
            </div>
          </div>
          <div className={styles.pillarItem}>
            <Workflow className="w-5 h-5 text-rose-700" />
            <div>
              <strong>Better Flow</strong>
              <small>Automate campaign handoffs</small>
            </div>
          </div>
          <div className={styles.pillarItem}>
            <BarChart3 className="w-5 h-5 text-rose-700" />
            <div>
              <strong>Real-Time Telemetry</strong>
              <small>Act faster with live data</small>
            </div>
          </div>
          <div className={styles.pillarItem}>
            <ShieldCheck className="w-5 h-5 text-rose-700" />
            <div>
              <strong>Built to Scale</strong>
              <small>Bank-grade SOC2 &amp; GDPR</small>
            </div>
          </div>
        </div>
      </section>

      {/* Filter Tabs for Kanban View */}
      <div className={styles.filterRow}>
        <button
          className={`${styles.filterBtn} ${activeTab === "all" ? styles.filterActive : ""}`}
          onClick={() => setActiveTab("all")}
        >
          All Stages
        </button>
        <button
          className={`${styles.filterBtn} ${activeTab === "now" ? styles.filterActive : ""}`}
          onClick={() => setActiveTab("now")}
        >
          🔥 In Active Build
        </button>
        <button
          className={`${styles.filterBtn} ${activeTab === "next" ? styles.filterActive : ""}`}
          onClick={() => setActiveTab("next")}
        >
          🚀 Q4 2026
        </button>
        <button
          className={`${styles.filterBtn} ${activeTab === "future" ? styles.filterActive : ""}`}
          onClick={() => setActiveTab("future")}
        >
          🔮 Future Vision
        </button>
      </div>

      {/* Kanban Stages Grid */}
      <div className={styles.kanbanBoard}>
        {/* Column 1: NOW */}
        {(activeTab === "all" || activeTab === "now") && (
          <div className={styles.kanbanCol}>
            <div className={styles.colHeader}>
              <div className={styles.colHeaderLeft}>
                <Clock className="w-5 h-5 text-rose-700" />
                <h3 className={styles.colTitle}>NOW</h3>
              </div>
              <span className={`${styles.colBadge} ${styles.badgeNow}`}>In Active Build</span>
            </div>

            <div className={styles.ticketList}>
              {NOW_TICKETS.map((t) => (
                <div key={t.id} className={styles.ticketCard}>
                  <div className={styles.ticketTop}>
                    <div className={styles.ticketIcon}>{t.icon}</div>
                    <span className={styles.ticketCategory}>{t.category}</span>
                  </div>
                  <h4 className={styles.ticketTitle}>{t.title}</h4>
                  <p className={styles.ticketDesc}>{t.desc}</p>
                  <div className={styles.tagWrap}>
                    {t.tags.map((tag) => (
                      <span key={tag} className={styles.tagPill}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Column 2: NEXT */}
        {(activeTab === "all" || activeTab === "next") && (
          <div className={styles.kanbanCol}>
            <div className={styles.colHeader}>
              <div className={styles.colHeaderLeft}>
                <Rocket className="w-5 h-5 text-rose-700" />
                <h3 className={styles.colTitle}>NEXT</h3>
              </div>
              <span className={`${styles.colBadge} ${styles.badgeNext}`}>Up Next · Q4 2026</span>
            </div>

            <div className={styles.ticketList}>
              {NEXT_TICKETS.map((t) => (
                <div key={t.id} className={styles.ticketCard}>
                  <div className={styles.ticketTop}>
                    <div className={styles.ticketIcon}>{t.icon}</div>
                    <span className={styles.ticketCategory}>{t.category}</span>
                  </div>
                  <h4 className={styles.ticketTitle}>{t.title}</h4>
                  <p className={styles.ticketDesc}>{t.desc}</p>
                  <div className={styles.tagWrap}>
                    {t.tags.map((tag) => (
                      <span key={tag} className={styles.tagPill}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Column 3: FUTURE */}
        {(activeTab === "all" || activeTab === "future") && (
          <div className={styles.kanbanCol}>
            <div className={styles.colHeader}>
              <div className={styles.colHeaderLeft}>
                <Sparkles className="w-5 h-5 text-rose-700" />
                <h3 className={styles.colTitle}>FUTURE</h3>
              </div>
              <span className={`${styles.colBadge} ${styles.badgeFuture}`}>Exploring Vision</span>
            </div>

            <div className={styles.ticketList}>
              {FUTURE_TICKETS.map((t) => (
                <div key={t.id} className={styles.ticketCard}>
                  <div className={styles.ticketTop}>
                    <div className={styles.ticketIcon}>{t.icon}</div>
                    <span className={styles.ticketCategory}>{t.category}</span>
                  </div>
                  <h4 className={styles.ticketTitle}>{t.title}</h4>
                  <p className={styles.ticketDesc}>{t.desc}</p>
                  <div className={styles.tagWrap}>
                    {t.tags.map((tag) => (
                      <span key={tag} className={styles.tagPill}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Submit Feature Request Banner */}
      <section className={styles.submitSection}>
        <div className={styles.submitCard}>
          <div className={styles.submitLeft}>
            <div className={styles.submitIconBox}>
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className={styles.submitTitle}>Have a feature request or integration idea?</h2>
              <p className={styles.submitDesc}>
                We build Growixa directly for your team&apos;s growth goals. Submit your feedback to shape our upcoming release cycles.
              </p>
            </div>
          </div>
          <Link href="/contact" className={styles.submitBtn}>
            Submit an Idea <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>
      </section>
    </main>
  );
}
