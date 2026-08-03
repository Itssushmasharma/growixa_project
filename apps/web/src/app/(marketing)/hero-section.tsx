"use client";

import { useState } from "react";
import Image from "next/image";
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

      {/* Interactive 3D Hero Perspective Frame */}
      <div className={styles.heroPreviewWrapper} style={{ position: "relative", zIndex: 2 }}>
        <div className={styles.glowBg} />

        <Card3D depth={14}>
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
                      background:
                        activeTab === tab.id
                          ? "linear-gradient(135deg, #2563eb, #7c3aed)"
                          : "rgba(255, 255, 255, 0.06)",
                      color: activeTab === tab.id ? "#ffffff" : "#94a3b8",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: "6px",
                      padding: "0.4rem 0.85rem",
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

            {/* 3D Visual Concept Image Display */}
            <Image
              src="/assets/hero-3d-concept.png"
              alt="Growixa 3D Perspective Dashboard Preview"
              width={1200}
              height={675}
              className={styles.heroImage3D}
              priority
            />

            {/* Interactive Metric Overlay Badges */}
            <div className={styles.statsGridOverlay}>
              <div className={styles.statItem}>
                <div className={styles.statLabel}>Active Campaigns</div>
                <div className={styles.statValue}>
                  {activeTab === "email" && "24 Active"}
                  {activeTab === "ai" && "18 AI Drafted"}
                  {activeTab === "segments" && "12 Dynamic Rules"}
                  {activeTab === "analytics" && "99.99% Uptime"}
                </div>
                <div className={styles.statBadge}>↑ 12% this week</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statLabel}>Emails Delivered</div>
                <div className={styles.statValue}>1,284,900</div>
                <div className={styles.statBadge}>↑ 99.98% delivery rate</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statLabel}>AI Generations</div>
                <div className={styles.statValue}>84,210</div>
                <div className={styles.statBadge}>⚡ Instant speed</div>
              </div>
              <div className={styles.statItem}>
                <div className={styles.statLabel}>Audience Reach</div>
                <div className={styles.statValue}>450,000</div>
                <div className={styles.statBadge}>↑ 18% growth</div>
              </div>
            </div>
          </div>
        </Card3D>
      </div>
    </section>
  );
}
