"use client";

import { useState } from "react";
import Link from "next/link";
import { Card3D } from "@/components/card-3d";
import { Floating3DObjects } from "@/components/floating-3d-objects";
import styles from "./marketing.module.css";

export function HeroSection() {
  const [aiPrompt, setAiPrompt] = useState("Write a launch email for our new SaaS product");
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

      {/* Native 3D Interactive Hero Showcase */}
      <div className={styles.heroPreviewWrapper} style={{ position: "relative", zIndex: 2 }}>
        <div className={styles.glowBg} />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1.75rem" }}>
          {/* 3D Glass Card 1: Smart Audience Segmentation */}
          <Card3D depth={16}>
            <div
              style={{
                background:
                  "radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.15), rgba(15, 23, 42, 0.8) 70%)",
                border: "1px solid rgba(56, 189, 248, 0.35)",
                borderRadius: "24px",
                padding: "2.25rem",
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
                    marginBottom: "1.25rem",
                  }}
                >
                  <div style={{ fontSize: "2rem" }}>🎯 👥</div>
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
                    fontSize: "1.4rem",
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
                    fontSize: "0.9375rem",
                    color: "#94a3b8",
                    lineHeight: 1.6,
                    marginBottom: "1.5rem",
                  }}
                >
                  Create laser-focused customer segments based on real-time behavior, dynamic
                  AND-rules, and custom contact attributes.
                </p>
              </div>

              {/* Native Dynamic Rule Widget */}
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "14px",
                  padding: "1.25rem",
                }}
              >
                <div
                  style={{
                    fontSize: "0.8125rem",
                    color: "#64748b",
                    fontWeight: 600,
                    marginBottom: "0.75rem",
                  }}
                >
                  DYNAMIC SEGMENT RULE BUILDER
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    marginBottom: "0.75rem",
                  }}
                >
                  <span
                    style={{
                      background: "rgba(37, 99, 235, 0.2)",
                      color: "#60a5fa",
                      padding: "0.375rem 0.75rem",
                      borderRadius: "6px",
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      border: "1px solid rgba(37, 99, 235, 0.4)",
                    }}
                  >
                    Field: tag
                  </span>
                  <span
                    style={{
                      background: "rgba(124, 58, 237, 0.2)",
                      color: "#c084fc",
                      padding: "0.375rem 0.75rem",
                      borderRadius: "6px",
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      border: "1px solid rgba(124, 58, 237, 0.4)",
                    }}
                  >
                    Operator: equals
                  </span>
                  <span
                    style={{
                      background: "rgba(16, 185, 129, 0.2)",
                      color: "#34d399",
                      padding: "0.375rem 0.75rem",
                      borderRadius: "6px",
                      fontSize: "0.8125rem",
                      fontWeight: 600,
                      border: "1px solid rgba(16, 185, 129, 0.4)",
                    }}
                  >
                    Value: &quot;VIP Buyer&quot;
                  </span>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    paddingTop: "0.5rem",
                    borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                    fontSize: "0.8125rem",
                    color: "#94a3b8",
                  }}
                >
                  <span>
                    Matched Contacts: <strong style={{ color: "#38bdf8" }}>42,850</strong>
                  </span>
                  <span style={{ color: "#34d399", fontWeight: 600 }}>✓ Auto-Updating</span>
                </div>
              </div>
            </div>
          </Card3D>

          {/* 3D Glass Card 2: AI Content Assistant */}
          <Card3D depth={16}>
            <div
              style={{
                background:
                  "radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.15), rgba(15, 23, 42, 0.8) 70%)",
                border: "1px solid rgba(168, 85, 247, 0.35)",
                borderRadius: "24px",
                padding: "2.25rem",
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
                    marginBottom: "1.25rem",
                  }}
                >
                  <div style={{ fontSize: "2rem" }}>🤖 ✨</div>
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
                    EFFICIENCY
                  </span>
                </div>

                <h3
                  style={{
                    fontSize: "1.4rem",
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
                    fontSize: "0.9375rem",
                    color: "#94a3b8",
                    lineHeight: 1.6,
                    marginBottom: "1.5rem",
                  }}
                >
                  Generate compelling copy, email subject lines, social captions, and creative ideas
                  powered by AI.
                </p>
              </div>

              {/* Native Interactive AI Copy Generator Widget */}
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "14px",
                  padding: "1.25rem",
                }}
              >
                <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    style={{
                      flex: 1,
                      background: "rgba(255, 255, 255, 0.06)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      borderRadius: "8px",
                      padding: "0.5rem 0.75rem",
                      color: "#ffffff",
                      fontSize: "0.8125rem",
                      outline: "none",
                    }}
                    placeholder="Enter prompt..."
                  />
                  <button
                    onClick={handleGenerate}
                    disabled={isGenerating}
                    style={{
                      background: "linear-gradient(135deg, #7c3aed, #2563eb)",
                      color: "white",
                      border: "none",
                      borderRadius: "8px",
                      padding: "0.5rem 0.875rem",
                      fontSize: "0.8125rem",
                      fontWeight: 700,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {isGenerating ? "Generating..." : "⚡ Generate"}
                  </button>
                </div>

                <div
                  style={{
                    background: "rgba(0, 0, 0, 0.4)",
                    border: "1px solid rgba(255, 255, 255, 0.08)",
                    borderRadius: "8px",
                    padding: "0.875rem",
                    fontSize: "0.8125rem",
                    color: "#cbd5e1",
                    whiteSpace: "pre-wrap",
                    maxHeight: "100px",
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
