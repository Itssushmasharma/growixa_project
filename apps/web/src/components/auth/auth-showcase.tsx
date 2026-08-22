"use client";

import Image from "next/image";
import Link from "next/link";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import {
  CheckIcon,
  MailIcon,
  SendIcon,
  SparklesIcon,
  StarIcon,
  TrendingUpIcon,
  UsersIcon,
} from "./auth-icons";
import styles from "./auth.module.css";

export function AuthShowcase() {
  return (
    <aside className={styles.showcase} aria-label="Growixa Platform Highlights">
      {/* Background Glowing Wave Ribbon & Orbs */}
      <div className={styles.waveCanvas} aria-hidden="true">
        <div className={styles.waveGlow1} />
        <div className={styles.waveGlow2} />
        <div className={styles.waveRibbon} />
      </div>

      {/* Floating Accent Orbs */}
      <div className={styles.floatingOrb1} aria-hidden="true">
        <SendIcon width={16} height={16} />
      </div>
      <div className={styles.floatingOrb2} aria-hidden="true">
        <SparklesIcon width={16} height={16} />
      </div>

      {/* Brand Header */}
      <div className={styles.showcaseHeader}>
        <Link href="/" className={styles.showcaseBrand} aria-label="Growixa Home">
          <Image src={iconMark} alt="" width={32} height={32} className={styles.showcaseLogo} />
          <span className={styles.showcaseBrandName}>Growixa</span>
        </Link>
      </div>

      {/* Main Showcase Hero */}
      <div className={styles.showcaseHero}>
        <h1 className={styles.showcaseTitle}>
          <span className={styles.showcaseGradientTitle}>AI-Powered Growth</span>
          <br />
          Built for Modern Marketers
        </h1>
        <p className={styles.showcaseSubtitle}>
          Automate smarter campaigns, reach the right audience, and scale your business with AI.
        </p>

        {/* Feature Highlight Pills */}
        <div className={styles.featureList}>
          <div className={styles.featurePill}>
            <div className={`${styles.featureIconBox} ${styles.featureIconGreen}`}>
              <TrendingUpIcon />
            </div>
            <div>
              <div className={styles.featureName}>AI Multichannel Campaigns</div>
              <div className={styles.featureDesc}>Reach more people, automatically</div>
            </div>
          </div>

          <div className={styles.featurePill}>
            <div className={`${styles.featureIconBox} ${styles.featureIconBlue}`}>
              <MailIcon />
            </div>
            <div>
              <div className={styles.featureName}>Smart Deliverability</div>
              <div className={styles.featureDesc}>99.4% inbox placement</div>
            </div>
          </div>

          <div className={styles.featurePill}>
            <div className={`${styles.featureIconBox} ${styles.featureIconPurple}`}>
              <UsersIcon />
            </div>
            <div>
              <div className={styles.featureName}>Real-time Audience Insights</div>
              <div className={styles.featureDesc}>Understand. Optimize. Grow.</div>
            </div>
          </div>
        </div>
      </div>

      {/* Floating 3D Analytics Metric Cards */}
      <div className={styles.metricsContainer} aria-hidden="true">
        {/* Card 1: Campaign Performance */}
        <div className={`${styles.floatingCard} ${styles.performanceCard}`}>
          <div className={styles.cardHeaderRow}>
            <span className={styles.cardHeaderLabel}>Campaign Performance</span>
            <span className={styles.growthBadge}>
              <TrendingUpIcon width={12} height={12} />
            </span>
          </div>
          <div className={styles.growthValue}>4.82x</div>
          <div className={styles.cardSublabel}>Growth</div>
          <div className={styles.sparklineContainer}>
            <svg viewBox="0 0 160 40" className={styles.sparklineSvg}>
              <path
                d="M 0 32 Q 25 35, 45 20 T 90 22 T 130 8 T 160 4"
                fill="none"
                stroke="url(#sparklineGrad)"
                strokeWidth="3.5"
                strokeLinecap="round"
              />
              <defs>
                <linearGradient id="sparklineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#34d399" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        {/* Card 2: 99.4% Deliverability Radial Gauge */}
        <div className={`${styles.floatingCard} ${styles.gaugeCard}`}>
          <div className={styles.gaugeContent}>
            <svg viewBox="0 0 80 80" className={styles.gaugeSvg}>
              <circle
                cx="40"
                cy="40"
                r="32"
                fill="none"
                stroke="rgba(15, 42, 86, 0.08)"
                strokeWidth="6"
              />
              <circle
                cx="40"
                cy="40"
                r="32"
                fill="none"
                stroke="url(#gaugeGrad)"
                strokeWidth="6"
                strokeDasharray="201"
                strokeDashoffset="10"
                strokeLinecap="round"
                transform="rotate(-90 40 40)"
                className={styles.gaugeFill}
              />
              <defs>
                <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
            <div className={styles.gaugeTextCenter}>
              <div className={styles.gaugeValue}>99.4%</div>
              <div className={styles.gaugeLabel}>Inbox Rate ↗</div>
            </div>
          </div>
        </div>

        {/* Card 3: AI Audience Score */}
        <div className={`${styles.floatingCard} ${styles.audienceCard}`}>
          <div className={styles.audienceHeader}>AI Audience Score</div>
          <div className={styles.audienceTag}>High Value Segment</div>
          <div className={styles.avatarStack}>
            <span className={`${styles.avatarCircle} ${styles.avatar1}`}>AJ</span>
            <span className={`${styles.avatarCircle} ${styles.avatar2}`}>SK</span>
            <span className={`${styles.avatarCircle} ${styles.avatar3}`}>MR</span>
          </div>
        </div>

        {/* Card 4: Customer Testimonial */}
        <div className={`${styles.floatingCard} ${styles.testimonialCard}`}>
          <div className={styles.ratingStars}>
            <StarIcon className={styles.starActive} />
            <StarIcon className={styles.starActive} />
            <StarIcon className={styles.starActive} />
            <StarIcon className={styles.starActive} />
            <StarIcon className={styles.starActive} />
          </div>
          <p className={styles.testimonialQuote}>
            &ldquo;Growixa helped us 4x our pipeline with AI-driven automation.&rdquo;
          </p>
          <div className={styles.testimonialAuthor}>
            <span className={styles.authorBadge}>
              <CheckIcon width={10} height={10} />
            </span>
            <span>BrightScale</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
