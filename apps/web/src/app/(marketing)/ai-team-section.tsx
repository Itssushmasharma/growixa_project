"use client";

import { Card3D } from "@/components/card-3d";
import styles from "./marketing.module.css";

const aiTeamMembers = [
  {
    icon: "🌐",
    title: "Website Growth Agent",
    desc: "Automated site crawling, lead capture popups, and AI Search Optimization (SEO / AEO / GEO) to scale organic traffic.",
  },
  {
    icon: "✍️",
    title: "AI Copywriter",
    desc: "Generate high-converting email copy, subject lines, and ad text tailored to your brand voice in seconds.",
  },
  {
    icon: "📧",
    title: "Email Optimizer",
    desc: "Real-time spam checks, deliverability scoring, and subject line performance predictions before sending.",
  },
  {
    icon: "📈",
    title: "Campaign Planner",
    desc: "Automated multi-channel sequence planning that adapts based on user behavior and engagement signals.",
  },
  {
    icon: "🎯",
    title: "Audience Builder",
    desc: "Dynamic AND-rule segmentation that groups leads automatically based on real-time activity and custom fields.",
  },
  {
    icon: "💬",
    title: "Social Creator",
    desc: "Craft, schedule, and publish platform-optimized posts across LinkedIn, Twitter, Meta, and Instagram.",
  },
];

const pillars = [
  {
    badge: "WEBSITE GROWTH",
    title: "Site Intelligence & Lead Capture",
    desc: "Smart exit-intent popups, automated website crawling, lead forms, and AI Search Engine Optimization (SEO / AEO / GEO).",
    accent: "rgba(16, 185, 129, 0.4)",
    badgeColor: "#34d399",
  },
  {
    badge: "DELIVERABILITY",
    title: "Email Marketing Engine",
    desc: "High-deliverability SMTP relay, Postmark integration, instant webhooks, and automated unsubscribe handling.",
    accent: "rgba(56, 189, 248, 0.4)",
    badgeColor: "#38bdf8",
  },
  {
    badge: "MULTI-CHANNEL",
    title: "Social Scheduler",
    desc: "Visual content calendar, multi-platform publishing, custom hashtags, and post performance analytics.",
    accent: "rgba(168, 85, 247, 0.4)",
    badgeColor: "#c084fc",
  },
  {
    badge: "EFFICIENCY",
    title: "AI Content Assistant",
    desc: "Brand voice tone injection, human-in-the-loop approval controls, token cost metering, and LLM prompt optimization.",
    accent: "rgba(244, 63, 94, 0.4)",
    badgeColor: "#fb7185",
  },
];

export function AiTeamSection() {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Autonomous Capabilities</div>
        <h2 className={styles.sectionTitle}>Meet Your AI Marketing Team</h2>
        <p className={styles.sectionSub}>
          Replace fragmented tools with AI agents designed to handle website growth, email
          campaigns, audience targeting, and analytics.
        </p>
      </div>

      <div className={styles.cardsGrid} style={{ marginBottom: "4rem" }}>
        {aiTeamMembers.map((member, idx) => (
          <Card3D key={idx} depth={10}>
            <div className={styles.card}>
              <div className={styles.cardIcon}>{member.icon}</div>
              <h3 className={styles.cardTitle}>{member.title}</h3>
              <p className={styles.cardDesc}>{member.desc}</p>
            </div>
          </Card3D>
        ))}
      </div>

      {/* Native 3D Pillars Feature Showcase Grid */}
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Core Pillars</div>
        <h2 className={styles.sectionTitle}>The 4 Foundations of Growixa</h2>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "2rem" }}>
        {pillars.map((pil, idx) => (
          <Card3D key={idx} depth={14}>
            <div
              style={{
                background: "rgba(15, 23, 42, 0.7)",
                border: `1px solid ${pil.accent}`,
                borderRadius: "20px",
                padding: "2.25rem",
                textAlign: "left",
                backdropFilter: "blur(20px)",
                boxShadow: `0 15px 40px rgba(0, 0, 0, 0.4), 0 0 25px ${pil.accent}`,
              }}
            >
              <span
                style={{
                  background: "rgba(255, 255, 255, 0.08)",
                  border: `1px solid ${pil.accent}`,
                  color: pil.badgeColor,
                  fontSize: "0.75rem",
                  fontWeight: 800,
                  padding: "0.25rem 0.625rem",
                  borderRadius: "9999px",
                  letterSpacing: "0.08em",
                  display: "inline-block",
                  marginBottom: "1rem",
                }}
              >
                {pil.badge}
              </span>
              <h3
                style={{
                  fontSize: "1.4rem",
                  fontWeight: 800,
                  color: "#ffffff",
                  marginBottom: "0.625rem",
                }}
              >
                {pil.title}
              </h3>
              <p style={{ fontSize: "0.9375rem", color: "#94a3b8", lineHeight: 1.65, margin: 0 }}>
                {pil.desc}
              </p>
            </div>
          </Card3D>
        ))}
      </div>
    </section>
  );
}
