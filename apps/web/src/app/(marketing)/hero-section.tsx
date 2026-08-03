import Image from "next/image";
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

      {/* 3D Dashboard Perspective Container */}
      <div className={styles.heroPreviewWrapper}>
        <div className={styles.glowBg} />
        <div className={styles.dashboard3dContainer}>
          <Image
            src="/assets/hero-3d-concept.png"
            alt="Growixa 3D Perspective Dashboard Preview"
            width={1200}
            height={675}
            className={styles.heroImage3D}
            priority
          />

          <div className={styles.statsGridOverlay}>
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
        </div>
      </div>
    </section>
  );
}
