import React from "react";
import styles from "./how-it-works-bento.module.css";
import { Layers, Rocket, Sparkles } from "lucide-react";

export function HowItWorksBentoSection() {
  return (
    <section className={styles.section} id="how-it-works">
      <div className={styles.header}>
        <div className={styles.eyebrow}>
          <Layers className="w-4 h-4" /> Simple 3-Step Setup
        </div>
        <h2 className={styles.title}>
          How It Works — <span>Automate Growth in Minutes</span>
        </h2>
        <p className={styles.subtitle}>
          Connect your existing tech stack, configure AI brand guardrails, and let Growixa handle execution.
        </p>
      </div>

      <div className={styles.stepGrid}>
        {/* Step 1 */}
        <div className={styles.stepCard}>
          <div>
            <span className={styles.stepBadge}>Step 1</span>
            <h3 className={styles.stepTitle}>Connect Your Tech Stack</h3>
            <p className={styles.stepDesc}>
              Plug in Postmark SMTP, Razorpay payments, and AI keys (OpenAI / Anthropic / Ollama) via zero-code integrations.
            </p>
          </div>
          <div className={styles.mockWindow}>
            <div className={styles.mockHeader}>
              <span className={`${styles.dot} ${styles.dotRed}`} />
              <span className={`${styles.dot} ${styles.dotYellow}`} />
              <span className={`${styles.dot} ${styles.dotGreen}`} />
            </div>
            <div className={styles.mockContent}>
              <div className={styles.codeLine}>
                <span className={styles.codeKeyword}>import</span> Growixa <span className={styles.codeKeyword}>from</span> <span className={styles.codeString}>&quot;growixa&quot;</span>
              </div>
              <div className={styles.codeLine}>
                <span className={styles.codeKeyword}>const</span> app = <span className={styles.codeKeyword}>new</span> Growixa({`{`}
              </div>
              <div style={{ paddingLeft: "12px" }}>
                provider: <span className={styles.codeString}>&quot;postmark&quot;</span>,
              </div>
              <div style={{ paddingLeft: "12px" }}>
                aiModel: <span className={styles.codeString}>&quot;gpt-4o&quot;</span>,
              </div>
              <div>{`});`}</div>
            </div>
          </div>
        </div>

        {/* Step 2 */}
        <div className={styles.stepCard}>
          <div>
            <span className={styles.stepBadge}>Step 2</span>
            <h3 className={styles.stepTitle}>Orchestrate Campaigns with AI</h3>
            <p className={styles.stepDesc}>
              Use the AI Assistant to generate high-converting email sequences and Instagram/LinkedIn posts with brand voice rules.
            </p>
          </div>
          <div className={styles.mockWindow}>
            <div className={styles.mockHeader}>
              <span className={`${styles.dot} ${styles.dotRed}`} />
              <span className={`${styles.dot} ${styles.dotYellow}`} />
              <span className={`${styles.dot} ${styles.dotGreen}`} />
            </div>
            <div className={styles.mockContent}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--brand-gold)" }}>
                <Sparkles className="w-4 h-4" /> AI Generation Guardrails
              </div>
              <div style={{ color: "#34d399", fontSize: "0.75rem" }}>
                ✓ Persona: High-Growth B2B
              </div>
              <div style={{ color: "#34d399", fontSize: "0.75rem" }}>
                ✓ Tone: Authoritative & Direct
              </div>
              <div style={{ color: "#34d399", fontSize: "0.75rem" }}>
                ✓ Output: 3-Part Email Campaign
              </div>
            </div>
          </div>
        </div>

        {/* Step 3 */}
        <div className={styles.stepCard}>
          <div>
            <span className={styles.stepBadge}>Step 3</span>
            <h3 className={styles.stepTitle}>Publish, Track & Scale</h3>
            <p className={styles.stepDesc}>
              Schedule campaign dispatches, track real-time open/click webhook telemetry, and monitor credit quotas.
            </p>
          </div>
          <div className={styles.mockWindow}>
            <div className={styles.mockHeader}>
              <span className={`${styles.dot} ${styles.dotRed}`} />
              <span className={`${styles.dot} ${styles.dotYellow}`} />
              <span className={`${styles.dot} ${styles.dotGreen}`} />
            </div>
            <div className={styles.mockContent}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#10b981" }}>
                <Rocket className="w-4 h-4" /> Dispatch Pipeline Active
              </div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                Delivered: 12,450 emails • 99.8% inbox rate
              </div>
              <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                Social: 14 posts published to Instagram
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dark Institutional Banner (Image 2 style) */}
      <div className={styles.darkStatsBanner}>
        <div className={styles.statItem}>
          <div className={styles.statValue}>10M+</div>
          <div className={styles.statLabel}>Messages Delivered</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statValue}>99.9%</div>
          <div className={styles.statLabel}>Delivery & Uptime</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statValue}>10+</div>
          <div className={styles.statLabel}>Native Integrations</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statValue}>100%</div>
          <div className={styles.statLabel}>GDPR & SOC2 Ready</div>
        </div>
      </div>
    </section>
  );
}
