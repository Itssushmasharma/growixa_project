import Link from "next/link";
import styles from "./marketing.module.css";

export function HeroSection() {
  return (
    <section className={styles.hero}>
      <div className={styles.pillBadge}>
        <span>✨ The AI Growth Platform for Modern Businesses</span>
      </div>

      <h1 className={styles.heroTitle}>
        Grow Faster. Market Smarter. <br />
        <span className={styles.gradientText}>Powered by AI.</span>
      </h1>

      <p className={styles.heroSub}>
        One platform to automate email campaigns, generate AI content, manage audience segments, and
        schedule social posts with real-time growth analytics.
      </p>

      <div className={styles.heroCtas}>
        <Link href="/login" className={styles.primaryBtn}>
          Start Free — No credit card required
        </Link>
        <Link href="/login" className={styles.secondaryBtn}>
          Book Demo →
        </Link>
      </div>

      {/* 3D Dashboard Card Preview */}
      <div className={styles.heroPreviewWrapper}>
        <div className={styles.glowBg} />
        <div className={styles.dashboardCard}>
          <div className={styles.dashboardHeader}>
            <div className={styles.windowControls}>
              <span className={`${styles.dot} ${styles.dotRed}`} />
              <span className={`${styles.dot} ${styles.dotYellow}`} />
              <span className={`${styles.dot} ${styles.dotGreen}`} />
            </div>
            <span style={{ fontSize: "0.8125rem", color: "#64748b", fontWeight: 600 }}>
              Growixa Live Growth Overview
            </span>
          </div>

          <div className={styles.statsGrid}>
            <div className={styles.statItem}>
              <div className={styles.statLabel}>Active Campaigns</div>
              <div className={styles.statValue}>24</div>
              <div className={styles.statBadge}>↑ 12% this week</div>
            </div>
            <div className={styles.statItem}>
              <div className={styles.statLabel}>Emails Delivered</div>
              <div className={styles.statValue}>1,284,900</div>
              <div className={styles.statBadge}>↑ 99.98% rate</div>
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

          {/* Simulated Growth Chart Bar */}
          <div
            style={{
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "10px",
              padding: "1.25rem",
              display: "flex",
              alignItems: "flex-end",
              gap: "0.75rem",
              height: "120px",
            }}
          >
            {[40, 55, 35, 70, 65, 85, 95, 110, 105, 125, 140, 160].map((val, idx) => (
              <div
                key={idx}
                style={{
                  flex: 1,
                  height: `${(val / 160) * 100}%`,
                  background:
                    idx >= 8
                      ? "linear-gradient(180deg, #2563eb 0%, #7c3aed 100%)"
                      : "rgba(37, 99, 235, 0.2)",
                  borderRadius: "4px 4px 0 0",
                  transition: "height 0.3s ease",
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
