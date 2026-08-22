"use client";

import Image from "next/image";
import Link from "next/link";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import {
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
      {/* Background Glowing 3D Vector Wave Ribbon & Particle Sparkles */}
      <div className={styles.waveCanvas} aria-hidden="true">
        {/* Subtle dot matrix grid */}
        <div className={styles.dotMatrixGrid} />

        {/* Ambient Glowing Orbs */}
        <div className={styles.waveGlow1} />
        <div className={styles.waveGlow2} />
        <div className={styles.waveGlow3} />

        {/* Multi-layered flowing ribbon SVG curves */}
        <svg
          className={styles.ribbonSvg}
          viewBox="0 0 1000 800"
          preserveAspectRatio="xMidYMid slice"
          fill="none"
        >
          <defs>
            <linearGradient id="waveGrad1" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00d2ff" stopOpacity="0.85" />
              <stop offset="40%" stopColor="#06b6d4" stopOpacity="0.7" />
              <stop offset="70%" stopColor="#6366f1" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#a855f7" stopOpacity="0.4" />
            </linearGradient>
            <linearGradient id="waveGrad2" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.6" />
              <stop offset="50%" stopColor="#818cf8" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#c084fc" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="waveGrad3" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.9" />
              <stop offset="60%" stopColor="#a855f7" stopOpacity="0.75" />
              <stop offset="100%" stopColor="#ec4899" stopOpacity="0.4" />
            </linearGradient>
            <linearGradient id="waveMesh" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00d2ff" stopOpacity="0.25" />
              <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.15" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
            </linearGradient>
            <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Ribbon Waves */}
          <path
            d="M-50,750 C150,780 200,620 400,650 C600,680 700,500 900,420 C1000,380 1100,360 1150,340 L1150,850 L-50,850 Z"
            fill="url(#waveMesh)"
          />

          {/* Glowing flowing ribbon line 1 */}
          <path
            d="M-50,740 C120,770 220,640 420,660 C620,680 720,490 920,410 C1020,370 1080,340 1150,320"
            stroke="url(#waveGrad1)"
            strokeWidth="3.5"
            strokeLinecap="round"
            filter="url(#glowFilter)"
          />

          {/* Glowing flowing ribbon line 2 */}
          <path
            d="M-50,720 C100,750 240,630 440,650 C640,670 740,470 940,390 C1040,350 1100,320 1150,300"
            stroke="url(#waveGrad2)"
            strokeWidth="2"
            strokeDasharray="4 8"
            strokeLinecap="round"
          />

          {/* Glowing flowing ribbon line 3 (Main vibrant crest) */}
          <path
            d="M-50,700 C150,730 260,610 460,630 C660,650 760,450 960,370 C1060,330 1110,300 1150,280"
            stroke="url(#waveGrad3)"
            strokeWidth="3"
            strokeLinecap="round"
          />

          {/* Dotted particle lines */}
          <path
            d="M-50,680 C180,710 280,590 480,610 C680,630 780,430 980,350 C1080,310 1120,280 1150,260"
            stroke="url(#waveGrad1)"
            strokeWidth="1.5"
            strokeDasharray="2 10"
            strokeLinecap="round"
          />

          <path
            d="M-50,660 C200,690 300,570 500,590 C700,610 800,410 1000,330 C1100,290 1130,260 1150,240"
            stroke="url(#waveGrad2)"
            strokeWidth="1"
            strokeDasharray="3 14"
            strokeLinecap="round"
          />

          {/* Connecting faint curved line to top paperplane */}
          <path
            d="M500,590 C650,450 750,300 830,140"
            stroke="url(#waveGrad2)"
            strokeWidth="1.5"
            strokeDasharray="4 8"
            strokeLinecap="round"
            opacity="0.65"
          />

          {/* Sparkling particle stars along the crest */}
          <circle cx="280" cy="620" r="3.5" fill="#00d2ff" filter="url(#glowFilter)" />
          <circle cx="480" cy="615" r="4.5" fill="#38bdf8" filter="url(#glowFilter)" />
          <circle cx="680" cy="520" r="3" fill="#a855f7" filter="url(#glowFilter)" />
          <circle cx="780" cy="440" r="4" fill="#c084fc" filter="url(#glowFilter)" />
          <circle cx="900" cy="380" r="3" fill="#ec4899" filter="url(#glowFilter)" />
          <circle cx="85" cy="710" r="2.5" fill="#00d2ff" />
          <circle cx="560" cy="580" r="2" fill="#818cf8" />
          <circle cx="980" cy="340" r="2.5" fill="#f43f5e" />
        </svg>
      </div>

      {/* Brand Header */}
      <div className={styles.showcaseHeader}>
        <Link href="/" className={styles.showcaseBrand} aria-label="Growixa Home">
          <Image src={iconMark} alt="" width={32} height={32} className={styles.showcaseLogo} />
          <span className={styles.showcaseBrandName}>Growixa</span>
        </Link>
      </div>

      {/* Main Canvas Area */}
      <div className={styles.showcaseMainGrid}>
        {/* Left Column: Hero Title & Feature Pills */}
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

        {/* Right Showcase Area: Distributed Floating 3D Metric Cards */}
        <div className={styles.showcaseCardsArea} aria-hidden="true">
          {/* Floating Cyan Paperplane Badge at Top Right */}
          <div className={styles.floatingPaperplaneOrb}>
            <SendIcon width={16} height={16} />
          </div>

          {/* Floating Purple Sparkle Badge at Middle Right */}
          <div className={styles.floatingSparkleOrb}>
            <SparklesIcon width={18} height={18} />
          </div>

          {/* Card 1: Campaign Performance 4.82x Growth with Green Sparkline */}
          <div className={`${styles.floatingCard} ${styles.performanceCard}`}>
            <div className={styles.cardHeaderRow}>
              <span className={styles.cardHeaderLabel}>Campaign Performance</span>
              <span className={styles.growthBadge}>
                <span className={styles.diagonalArrow}>↗</span>
              </span>
            </div>
            <div className={styles.growthValue}>4.82x</div>
            <div className={styles.cardSublabel}>Growth</div>
            <div className={styles.sparklineContainer}>
              <svg viewBox="0 0 160 50" className={styles.sparklineSvg}>
                <path
                  d="M 5 45 C 35 44, 45 32, 70 34 C 95 36, 105 20, 125 24 C 140 26, 145 10, 155 6"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>

          {/* Card 2: 99.4% Circular Gauge */}
          <div className={`${styles.floatingCard} ${styles.gaugeCard}`}>
            <div className={styles.gaugeContent}>
              <svg viewBox="0 0 90 90" className={styles.gaugeSvg}>
                <circle
                  cx="45"
                  cy="45"
                  r="36"
                  fill="none"
                  stroke="rgba(226, 232, 240, 0.7)"
                  strokeWidth="7"
                />
                <circle
                  cx="45"
                  cy="45"
                  r="36"
                  fill="none"
                  stroke="url(#gaugeGradient)"
                  strokeWidth="7"
                  strokeDasharray="226"
                  strokeDashoffset="24"
                  strokeLinecap="round"
                  transform="rotate(-90 45 45)"
                  className={styles.gaugeFill}
                />
                <defs>
                  <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#00d2ff" />
                    <stop offset="60%" stopColor="#3b82f6" />
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
            <div className={styles.audienceTag}>High Value</div>
            <div className={styles.audienceSegment}>Segment</div>
            <div className={styles.avatarStack}>
              <div className={`${styles.avatarCircle} ${styles.avatarPhoto1}`}>
                <span>👩🏻</span>
              </div>
              <div className={`${styles.avatarCircle} ${styles.avatarPhoto2}`}>
                <span>👨🏽</span>
              </div>
              <div className={`${styles.avatarCircle} ${styles.avatarPhoto3}`}>
                <span>👩🏼</span>
              </div>
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
              <div className={styles.brightscaleLogoIcon}>
                <span className={styles.brightscaleG}>G</span>
              </div>
              <span className={styles.brightscaleText}>BrightScale</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
