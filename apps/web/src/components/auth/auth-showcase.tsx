"use client";

import Image from "next/image";
import Link from "next/link";
import { Zap, Users, LineChart } from "lucide-react";
import styles from "./auth.module.css";

// ---------- Inline SVG for the bottom ribbon wave ----------
function RibbonWave() {
  return (
    <svg
      className={styles.ribbonSvg}
      viewBox="0 0 1440 420"
      preserveAspectRatio="none"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="waveGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00d2ff" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#7c3aed" stopOpacity="0.55" />
        </linearGradient>
        <linearGradient id="waveGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#6366f1" stopOpacity="0.35" />
        </linearGradient>
        <linearGradient id="waveGrad3" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.12" />
        </linearGradient>
        <filter id="glow1" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="8" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Back ribbon — wide gentle sweep */}
      <path
        d="M-60 380 C200 260 520 180 800 240 C1080 300 1280 220 1500 260 L1500 430 L-60 430 Z"
        fill="url(#waveGrad3)"
      />

      {/* Mid ribbon */}
      <path
        d="M-60 400 C130 310 380 260 680 300 C940 340 1160 270 1500 320 L1500 430 L-60 430 Z"
        fill="url(#waveGrad2)"
        filter="url(#glow1)"
      />

      {/* Front ribbon — vivid cyan-to-purple */}
      <path
        d="M-60 415 C100 370 260 325 480 345 C710 365 900 310 1120 330 C1290 345 1400 380 1500 400 L1500 430 L-60 430 Z"
        fill="url(#waveGrad1)"
        filter="url(#glow1)"
      />
    </svg>
  );
}

// ---------- Sparkline miniature chart ----------
function SparklineSvg() {
  const points = [
    [0, 36],
    [18, 28],
    [36, 32],
    [54, 18],
    [72, 22],
    [90, 10],
    [108, 16],
    [126, 8],
    [144, 14],
    [160, 4],
  ];

  const pathD = "M" + points.map((p) => p.join(",")).join(" L");

  const lastPoint = points[points.length - 1] ?? [160, 4];
  const areaD = pathD + ` L${lastPoint[0]},44 L0,44 Z`;

  return (
    <svg
      className={styles.sparklineSvg}
      viewBox="0 0 160 44"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="sparkGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#00c8ff" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
        <linearGradient id="sparkArea" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#00c8ff" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#7c3aed" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaD} fill="url(#sparkArea)" />
      <path
        d={pathD}
        fill="none"
        stroke="url(#sparkGrad)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ---------- Main Showcase ----------
export function AuthShowcase() {
  return (
    <section className={styles.showcase} aria-label="Product showcase">
      {/* Bottom wave ribbon layer */}
      <div className={styles.waveCanvas} aria-hidden="true">
        <RibbonWave />
      </div>

      {/* Brand header */}
      <header className={styles.showcaseHeader}>
        <Link href="/" className={styles.showcaseBrand}>
          <Image
            src="/assets/logo-horizontal.png"
            alt="Growixa"
            width={160}
            height={44}
            priority
            className={styles.showcaseLogo}
          />
        </Link>
      </header>

      {/* Hero text — left portion of showcase */}
      <div className={styles.showcaseHero}>
        <h1 className={styles.showcaseTitle}>
          <span className={styles.showcaseGradientTitle}>AI-Powered Growth</span>
          Built for Modern&nbsp;Marketers
        </h1>
        <p className={styles.showcaseSubtitle}>
          Reach the right audience with intelligent segmentation, automated campaigns, and real-time
          analytics — all in one platform.
        </p>

        <ul className={styles.featureList} aria-label="Platform features">
          <li className={styles.featurePill}>
            <span className={`${styles.featureIconBox} ${styles.featureIconGreen}`}>
              <Zap size={17} aria-hidden="true" />
            </span>
            <div>
              <div className={styles.featureName}>Smart Campaign Automation</div>
              <div className={styles.featureDesc}>Trigger workflows based on real behaviour</div>
            </div>
          </li>
          <li className={styles.featurePill}>
            <span className={`${styles.featureIconBox} ${styles.featureIconBlue}`}>
              <Users size={17} aria-hidden="true" />
            </span>
            <div>
              <div className={styles.featureName}>AI Audience Segmentation</div>
              <div className={styles.featureDesc}>Precision targeting, zero guesswork</div>
            </div>
          </li>
          <li className={styles.featurePill}>
            <span className={`${styles.featureIconBox} ${styles.featureIconPurple}`}>
              <LineChart size={17} aria-hidden="true" />
            </span>
            <div>
              <div className={styles.featureName}>Real-Time Analytics</div>
              <div className={styles.featureDesc}>Live dashboards and instant insights</div>
            </div>
          </li>
        </ul>
      </div>

      {/* ---- Floating cards area (absolute, right half of showcase) ---- */}
      <div className={styles.showcaseCardsArea} aria-hidden="true">
        {/* Cyan paper-plane orb — top right */}
        <div className={styles.floatingPaperplaneOrb}>
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M22 2L11 13" />
            <path d="M22 2L15 22 11 13 2 9l20-7z" />
          </svg>
        </div>

        {/* Sparkle orb — mid right */}
        <div className={styles.floatingSparkleOrb}>
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 2 L13.5 9 L20 9 L14.7 13.5 L16.9 20.5 L12 16.5 L7.1 20.5 L9.3 13.5 L4 9 L10.5 9 Z" />
          </svg>
        </div>

        {/* Card 1: Campaign Performance — top-left of cards area */}
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
            <SparklineSvg />
          </div>
        </div>

        {/* Card 2: 99.4% Gauge — overlapping right, below Card 1 */}
        <div className={`${styles.floatingCard} ${styles.gaugeCard}`}>
          <div className={styles.gaugeContent}>
            <svg className={styles.gaugeSvg} viewBox="0 0 96 96">
              {/* track */}
              <circle cx="48" cy="48" r="38" fill="none" stroke="#f0f4f8" strokeWidth="8" />
              {/* fill — 99.4% of 238.76 = 237.4 */}
              <circle
                cx="48"
                cy="48"
                r="38"
                fill="none"
                stroke="url(#gaugeGrad)"
                strokeWidth="8"
                strokeDasharray="238.76"
                strokeDashoffset="1.4"
                strokeLinecap="round"
                transform="rotate(-90 48 48)"
                className={styles.gaugeFill}
              />
              <defs>
                <linearGradient
                  id="gaugeGrad"
                  x1="0"
                  y1="0"
                  x2="96"
                  y2="96"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop stopColor="#00c8ff" />
                  <stop offset="1" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
            </svg>
            <div className={styles.gaugeTextCenter}>
              <span className={styles.gaugeValue}>99.4%</span>
              <span className={styles.gaugeLabel}>Delivered</span>
            </div>
          </div>
        </div>

        {/* Card 3: AI Audience Score — mid-left of cards area */}
        <div className={`${styles.floatingCard} ${styles.audienceCard}`}>
          <div className={styles.audienceHeader}>AI Audience Score</div>
          <div className={styles.audienceTag}>High Intent</div>
          <div className={styles.audienceSegment}>B2B SaaS · Segment A</div>
          <div className={styles.avatarStack}>
            {["🧑🏽", "👩🏻", "🧑🏿"].map((emoji, i) => (
              <div
                key={i}
                className={`${styles.avatarCircle} ${
                  i === 0
                    ? styles.avatarPhoto1
                    : i === 1
                      ? styles.avatarPhoto2
                      : styles.avatarPhoto3
                }`}
              >
                <span role="img" aria-label="user avatar">
                  {emoji}
                </span>
              </div>
            ))}
            <div
              className={styles.avatarCircle}
              style={{ background: "#f0f4f8", fontSize: 11, fontWeight: 700, color: "#475569" }}
            >
              +9k
            </div>
          </div>
        </div>

        {/* Card 4: Testimonial — bottom center */}
        <div className={`${styles.floatingCard} ${styles.testimonialCard}`}>
          {/* 5 stars */}
          <div className={styles.ratingStars} aria-label="5 out of 5 stars">
            {Array.from({ length: 5 }).map((_, i) => (
              <svg key={i} width="14" height="14" viewBox="0 0 24 24" aria-hidden="true">
                <path
                  d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                  fill="#f59e0b"
                  stroke="none"
                />
              </svg>
            ))}
          </div>
          <p className={styles.testimonialQuote}>
            &ldquo;Growixa cut our campaign setup time by 70%. Our email open rates have never
            looked better.&rdquo;
          </p>
          <div className={styles.testimonialAuthor}>
            <div className={styles.brightscaleLogoIcon}>
              <span className={styles.brightscaleG}>G</span>
            </div>
            <span className={styles.brightscaleText}>Brightscale Media</span>
          </div>
        </div>
      </div>
    </section>
  );
}
