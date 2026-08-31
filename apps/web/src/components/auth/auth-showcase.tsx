"use client";

import Link from "next/link";
import styles from "./auth.module.css";

export function AuthShowcase() {
  return (
    <section className={styles.showcase} aria-label="Product showcase">
      <div className={styles.showcaseTop}>
        {/* Brand header & Back Link */}
        <header className={styles.showcaseHeader}>
          <Link href="/" className={styles.showcaseBrand}>
            <div className={styles.brandMark} aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span>Growixa</span>
          </Link>

          <Link href="/" className={styles.backPill}>
            <span>&larr;</span>
            <span>Back to website</span>
          </Link>
        </header>

        {/* Hero Display Text */}
        <div className={styles.showcaseHero}>
          <h1 className={styles.showcaseTitle}>
            <span className={styles.showcaseGradientTitle}>AI-Powered Growth</span>
            Working while you sleep.
          </h1>
          <p className={styles.showcaseSubtitle}>
            Reach the right audience with intelligent segmentation, automated multi-channel
            campaigns, and real-time analytics &mdash; all in one platform.
          </p>
        </div>

        {/* Live Run Telemetry Card */}
        <div className={styles.telemetryCard} aria-label="Live engine run metrics">
          <div className={styles.telemetryHeader}>
            <span>Last Night&apos;s Engine Run</span>
            <span className={styles.liveBadge}>
              <span className={styles.pulseDot} aria-hidden="true" />
              <span>All Systems Go</span>
            </span>
          </div>

          <div className={styles.telemetryGrid}>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryValue}>3,410</span>
              <span className={styles.telemetryLabel}>Sourced &amp; verified</span>
            </div>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryValue}>4.82x</span>
              <span className={styles.telemetryLabel}>Campaign ROI</span>
            </div>
            <div className={styles.telemetryItem}>
              <span className={styles.telemetryValue}>99.4%</span>
              <span className={styles.telemetryLabel}>Inbox deliverability</span>
            </div>
          </div>
        </div>

        {/* Proof Badges */}
        <div className={styles.proofRow}>
          <div className={styles.proofBadge}>
            <span className={styles.proofDot} style={{ background: "var(--create)" }} />
            <span>5-stage autonomous GTM</span>
          </div>
          <div className={styles.proofBadge}>
            <span className={styles.proofDot} style={{ background: "var(--manage)" }} />
            <span>Unlimited team seats</span>
          </div>
          <div className={styles.proofBadge}>
            <span className={styles.proofDot} style={{ background: "var(--find)" }} />
            <span>One-click export</span>
          </div>
        </div>
      </div>

      {/* Showcase Footer */}
      <footer className={styles.showcaseFooter}>
        <span>&copy; {new Date().getFullYear()} Growixa Inc.</span>
        <span>256-bit encryption &bull; GDPR &amp; CAN-SPAM compliant</span>
      </footer>
    </section>
  );
}
