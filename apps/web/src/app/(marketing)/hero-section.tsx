"use client";

import { useState } from "react";
import Link from "next/link";
import { Card3D } from "@/components/card-3d";
import { Floating3DObjects } from "@/components/floating-3d-objects";
import styles from "./marketing.module.css";

const tabs = [
  { id: "email", label: "📧 Email Campaigns" },
  { id: "ai", label: "🤖 AI Assistant" },
  { id: "segments", label: "🎯 Audience Segments" },
  { id: "analytics", label: "📈 Growth Analytics" },
];

export function HeroSection() {
  const [activeTab, setActiveTab] = useState("email");

  return (
    <section className={styles.hero}>
      <Floating3DObjects />

      <div style={{ position: "relative", zIndex: 2 }}>
        <div className={styles.pillBadge}>
          <span>✨ The AI Growth Platform for Modern Businesses</span>
        </div>

        <h1 className={styles.heroTitle}>
          Grow Faster. Market Smarter. <br />
          <span className={styles.gradientText}>Powered by AI.</span>
        </h1>

        <p className={styles.heroSub}>
          One platform to automate email campaigns, generate AI content, manage audience segments,
          and schedule social posts with real-time growth analytics.
        </p>

        <div className={styles.heroCtas}>
          <Link href="/login" className={styles.primaryBtn}>
            Start Free — No credit card required
          </Link>
          <Link href="/login" className={styles.secondaryBtn}>
            Book Demo →
          </Link>
        </div>
      </div>

      {/* Interactive 3D Card Dashboard Preview */}
      <div className={styles.heroPreviewWrapper} style={{ position: "relative", zIndex: 2 }}>
        <div className={styles.glowBg} />

        <Card3D depth={12}>
          <div className={styles.dashboard3dContainer}>
            {/* Interactive Tab Switcher */}
            <div className={styles.dashboardHeader}>
              <div className={styles.windowControls}>
                <span className={`${styles.dot} ${styles.dotRed}`} />
                <span className={`${styles.dot} ${styles.dotYellow}`} />
                <span className={`${styles.dot} ${styles.dotGreen}`} />
              </div>

              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      background: activeTab === tab.id ? "#2563eb" : "rgba(255, 255, 255, 0.06)",
                      color: activeTab === tab.id ? "#ffffff" : "#94a3b8",
                      border: "1px solid rgba(255, 255, 255, 0.12)",
                      borderRadius: "6px",
                      padding: "0.375rem 0.75rem",
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                    }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Live Interactive Preview Content */}
            <div style={{ padding: "1rem" }}>
              {activeTab === "email" && (
                <div style={{ textAlign: "left" }}>
                  <div className={styles.statsGridOverlay}>
                    <div className={styles.statItem}>
                      <div className={styles.statLabel}>Campaign Name</div>
                      <div className={styles.statValue} style={{ fontSize: "1.125rem" }}>
                        Q3 Product Launch
                      </div>
                      <div className={styles.statBadge}>Status: Active (Postmark Relay)</div>
                    </div>
                    <div className={styles.statItem}>
                      <div className={styles.statLabel}>Total Sent</div>
                      <div className={styles.statValue}>1,284,900</div>
                      <div className={styles.statBadge}>↑ 99.98% delivery rate</div>
                    </div>
                    <div className={styles.statItem}>
                      <div className={styles.statLabel}>Open Rate</div>
                      <div className={styles.statValue}>48.2%</div>
                      <div className={styles.statBadge}>↑ 2.4x industry avg</div>
                    </div>
                    <div className={styles.statItem}>
                      <div className={styles.statLabel}>Click Rate</div>
                      <div className={styles.statValue}>14.8%</div>
                      <div className={styles.statBadge}>⚡ High Engagement</div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "ai" && (
                <div
                  style={{
                    textAlign: "left",
                    background: "rgba(30, 41, 59, 0.6)",
                    border: "1px solid rgba(168, 85, 247, 0.3)",
                    borderRadius: "12px",
                    padding: "1.25rem",
                  }}
                >
                  <div
                    style={{
                      color: "#c084fc",
                      fontWeight: 700,
                      fontSize: "0.875rem",
                      marginBottom: "0.5rem",
                    }}
                  >
                    🤖 AI Copy Generator (Anthropic Claude 3.5 Sonnet)
                  </div>
                  <p
                    style={{ color: "#e2e8f0", fontSize: "0.9375rem", lineHeight: 1.6, margin: 0 }}
                  >
                    &ldquo;Scale your marketing pipeline seamlessly with Growixa. Automated email
                    campaigns, dynamic lead scoring, and instant social scheduler in one unified
                    platform.&rdquo;
                  </p>
                </div>
              )}

              {activeTab === "segments" && (
                <div style={{ textAlign: "left" }}>
                  <div className={styles.statsGridOverlay}>
                    <div className={styles.statItem}>
                      <div className={styles.statLabel}>Segment Rule</div>
                      <div className={styles.statValue} style={{ fontSize: "1.125rem" }}>
                        VIP Buyers AND Tag == &quot;Engaged&quot;
                      </div>
                      <div className={styles.statBadge}>Real-time Dynamic AND-Rule</div>
                    </div>
                    <div className={styles.statItem}>
                      <div className={styles.statLabel}>Matched Contacts</div>
                      <div className={styles.statValue}>42,850</div>
                      <div className={styles.statBadge}>Auto-updated</div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "analytics" && (
                <div style={{ textAlign: "left" }}>
                  <div
                    style={{
                      background: "rgba(15, 23, 42, 0.6)",
                      border: "1px solid rgba(56, 189, 248, 0.2)",
                      borderRadius: "10px",
                      padding: "1.25rem",
                      display: "flex",
                      alignItems: "flex-end",
                      gap: "0.75rem",
                      height: "140px",
                    }}
                  >
                    {[35, 50, 45, 75, 80, 110, 125, 140, 160, 185, 210, 240].map((val, idx) => (
                      <div
                        key={idx}
                        style={{
                          flex: 1,
                          height: `${(val / 240) * 100}%`,
                          background:
                            idx >= 8
                              ? "linear-gradient(180deg, #38bdf8 0%, #a855f7 100%)"
                              : "rgba(56, 189, 248, 0.25)",
                          borderRadius: "4px 4px 0 0",
                          transition: "height 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </Card3D>
      </div>
    </section>
  );
}
