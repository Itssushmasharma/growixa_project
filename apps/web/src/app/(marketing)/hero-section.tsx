"use client";

import { useState } from "react";
import Link from "next/link";
import { Card3D } from "@/components/card-3d";
import { Floating3DObjects } from "@/components/floating-3d-objects";
import styles from "./marketing.module.css";

export function HeroSection() {
  const [aiPrompt, setAiPrompt] = useState("Write a product launch email for our new platform");
  const [aiOutput, setAiOutput] = useState(
    "Subject: 🚀 Introducing the AI Growth Platform for Modern Teams\n\nHi {{first_name}},\nScale your marketing pipeline seamlessly with Growixa. Automated email campaigns, dynamic lead scoring, and instant social scheduler in one unified platform.",
  );
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setAiOutput(
        `Subject: ✨ ${aiPrompt.slice(0, 30)}...\n\nHi {{first_name}},\nDiscover how Growixa's AI engine automates your campaign drafting, targets high-intent audience segments, and boosts deliverability to 99.98%.`,
      );
      setIsGenerating(false);
    }, 600);
  };

  return (
    <section className={styles.hero}>
      <Floating3DObjects />

      <div style={{ position: "relative", zIndex: 2 }}>
        <div className={styles.pillBadge}>
          <span>✨ The AI Growth Platform — Built for Modern Businesses</span>
        </div>

        <h1 className={styles.heroTitle}>
          AI growth infrastructure <br />
          <span className={styles.gradientText}>to scale your revenue.</span>
        </h1>

        <p className={styles.heroSub}>
          Automate email campaigns, capture high-intent website leads, optimize AI search rankings
          (SEO & AEO), and schedule multi-channel social posts — from your first lead to your
          millionth.
        </p>

        <div className={styles.heroCtas}>
          <Link href="/login" className={styles.primaryBtn}>
            Start Free — Instant setup
          </Link>
          <Link href="/login" className={styles.secondaryBtn}>
            Book Demo →
          </Link>
        </div>
      </div>

      {/* Stripe Bento Grid Interactive Showcase */}
      <div className={styles.heroPreviewWrapper} style={{ position: "relative", zIndex: 2 }}>
        <div className={styles.glowBg} />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1.5rem" }}>
          {/* Bento Card 1: Smart Audience Segmentation */}
          <Card3D depth={16}>
            <div
              style={{
                background:
                  "radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.15), rgba(15, 23, 42, 0.85) 70%)",
                border: "1px solid rgba(56, 189, 248, 0.35)",
                borderRadius: "20px",
                padding: "1.75rem",
                textAlign: "left",
                boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(56, 189, 248, 0.25)",
                backdropFilter: "blur(20px)",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "1rem",
                  }}
                >
                  <div style={{ fontSize: "1.75rem" }}>🎯 👥</div>
                  <span
                    style={{
                      background: "rgba(56, 189, 248, 0.15)",
                      border: "1px solid rgba(56, 189, 248, 0.4)",
                      color: "#38bdf8",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      padding: "0.25rem 0.625rem",
                      borderRadius: "9999px",
                      letterSpacing: "0.08em",
                    }}
                  >
                    TARGETING
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: "1.2rem",
                    fontWeight: 800,
                    color: "#ffffff",
                    marginBottom: "0.5rem",
                    letterSpacing: "-0.02em",
                  }}
                >
                  SMART AUDIENCE SEGMENTATION
                </h3>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "#94a3b8",
                    lineHeight: 1.6,
                    marginBottom: "1.25rem",
                  }}
                >
                  Create laser-focused customer segments based on real-time behavior, dynamic
                  AND-rules, and custom contact attributes.
                </p>
              </div>

              {/* Dynamic Rule Widget */}
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "12px",
                  padding: "1rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#64748b",
                    fontWeight: 600,
                    marginBottom: "0.5rem",
                  }}
                >
                  DYNAMIC RULE BUILDER
                </div>
                <div
                  style={{
                    fontSize: "0.8125rem",
                    color: "#38bdf8",
                    fontWeight: 700,
                    marginBottom: "0.25rem",
                  }}
                >
                  tag == &quot;VIP Buyer&quot; AND visits &gt; 3
                </div>
                <div style={{ fontSize: "0.75rem", color: "#34d399" }}>
                  ✓ 42,850 Matched Contacts
                </div>
              </div>
            </div>
          </Card3D>

          {/* Bento Card 2: Website Growth & Intelligence */}
          <Card3D depth={16}>
            <div
              style={{
                background:
                  "radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.15), rgba(15, 23, 42, 0.85) 70%)",
                border: "1px solid rgba(16, 185, 129, 0.35)",
                borderRadius: "20px",
                padding: "1.75rem",
                textAlign: "left",
                boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(16, 185, 129, 0.25)",
                backdropFilter: "blur(20px)",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "1rem",
                  }}
                >
                  <div style={{ fontSize: "1.75rem" }}>🌐 📈</div>
                  <span
                    style={{
                      background: "rgba(16, 185, 129, 0.15)",
                      border: "1px solid rgba(16, 185, 129, 0.4)",
                      color: "#34d399",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      padding: "0.25rem 0.625rem",
                      borderRadius: "9999px",
                      letterSpacing: "0.08em",
                    }}
                  >
                    WEBSITE GROWTH
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: "1.2rem",
                    fontWeight: 800,
                    color: "#ffffff",
                    marginBottom: "0.5rem",
                    letterSpacing: "-0.02em",
                  }}
                >
                  WEBSITE GROWTH & INTELLIGENCE
                </h3>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "#94a3b8",
                    lineHeight: 1.6,
                    marginBottom: "1.25rem",
                  }}
                >
                  Smart lead capture popups, automated website crawling, and AI Search Optimization
                  (SEO / AEO / GEO) to scale traffic.
                </p>
              </div>

              {/* Site Intelligence Widget */}
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "12px",
                  padding: "1rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#64748b",
                    fontWeight: 600,
                    marginBottom: "0.5rem",
                  }}
                >
                  SITE INTELLIGENCE SCORE
                </div>
                <div
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
                >
                  <span style={{ fontSize: "1.25rem", fontWeight: 800, color: "#34d399" }}>
                    98 / 100
                  </span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      color: "#60a5fa",
                      background: "rgba(37, 99, 235, 0.2)",
                      padding: "0.25rem 0.5rem",
                      borderRadius: "4px",
                    }}
                  >
                    SEO + AEO Ready
                  </span>
                </div>
              </div>
            </div>
          </Card3D>

          {/* Bento Card 3: AI Content Assistant */}
          <Card3D depth={16}>
            <div
              style={{
                background:
                  "radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.15), rgba(15, 23, 42, 0.85) 70%)",
                border: "1px solid rgba(168, 85, 247, 0.35)",
                borderRadius: "20px",
                padding: "1.75rem",
                textAlign: "left",
                boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5), 0 0 30px rgba(168, 85, 247, 0.25)",
                backdropFilter: "blur(20px)",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "1rem",
                  }}
                >
                  <div style={{ fontSize: "1.75rem" }}>🤖 ✨</div>
                  <span
                    style={{
                      background: "rgba(244, 63, 94, 0.15)",
                      border: "1px solid rgba(244, 63, 94, 0.4)",
                      color: "#fb7185",
                      fontSize: "0.75rem",
                      fontWeight: 800,
                      padding: "0.25rem 0.625rem",
                      borderRadius: "9999px",
                      letterSpacing: "0.08em",
                    }}
                  >
                    EFFICIENCY
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: "1.2rem",
                    fontWeight: 800,
                    color: "#ffffff",
                    marginBottom: "0.5rem",
                    letterSpacing: "-0.02em",
                  }}
                >
                  AI CONTENT ASSISTANT
                </h3>
                <p
                  style={{
                    fontSize: "0.875rem",
                    color: "#94a3b8",
                    lineHeight: 1.6,
                    marginBottom: "1.25rem",
                  }}
                >
                  Generate compelling email copy, subject lines, captions, and blog drafts tailored
                  to your brand voice.
                </p>
              </div>

              {/* Interactive AI Copy Generator Widget */}
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "12px",
                  padding: "0.875rem",
                }}
              >
                <div style={{ display: "flex", gap: "0.375rem", marginBottom: "0.5rem" }}>
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    style={{
                      flex: 1,
                      background: "rgba(255, 255, 255, 0.06)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: "6px",
                      padding: "0.375rem 0.5rem",
                      color: "#ffffff",
                      fontSize: "0.75rem",
                      outline: "none",
                    }}
                  />
                  <button
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    style={{
                      background: "linear-gradient(135deg, #7c3aed, #2563eb)",
                      color: "white",
                      border: "none",
                      borderRadius: "6px",
                      padding: "0.375rem 0.625rem",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {isGenerating ? "..." : "⚡ AI"}
                  </button>
                </div>
                <div
                  style={{
                    background: "rgba(0, 0, 0, 0.4)",
                    borderRadius: "6px",
                    padding: "0.5rem",
                    fontSize: "0.75rem",
                    color: "#cbd5e1",
                    maxHeight: "55px",
                    overflowY: "auto",
                    fontFamily: "monospace",
                  }}
                >
                  {aiOutput}
                </div>
              </div>
            </div>
          </Card3D>
        </div>
      </div>
    </section>
  );
}
