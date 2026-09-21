"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Check, X, Star } from "lucide-react";
import styles from "./pricing.module.css";

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(true);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>PREMIUM PRICING</span>
        <h1 className={styles.title}>Plans that start free and grow with you</h1>
        <p className={styles.subtitle}>
          Transparent pricing designed for founders, scaling growth teams, and enterprise operations.
        </p>
      </header>

      {/* Monthly / Annually Toggle Switch */}
      <div className={styles.toggleContainer}>
        <span
          className={`${styles.toggleLabel} ${!isAnnual ? styles.active : ""}`}
          onClick={() => setIsAnnual(false)}
        >
          Monthly
        </span>
        <div
          className={`${styles.toggleSwitch} ${isAnnual ? styles.active : ""}`}
          onClick={() => setIsAnnual(!isAnnual)}
          role="button"
          tabIndex={0}
          aria-label="Toggle Annual Billing"
        >
          <div className={styles.toggleKnob}></div>
        </div>
        <span
          className={`${styles.toggleLabel} ${isAnnual ? styles.active : ""}`}
          onClick={() => setIsAnnual(true)}
        >
          Annually
        </span>
        <span className={styles.discountBadge}>Save 20%</span>
      </div>

      {/* 4-Column Comparison Table (Matching Reference Image 5 Layout) */}
      <div className={styles.pricingGrid}>
        {/* Standard / Free Plan */}
        <div className={styles.pricingCard}>
          <h2 className={styles.planTitle}>Standard</h2>
          <p className={styles.planDesc}>
            Ideal for low-volume testing where basic social publishing & email relays are needed.
          </p>

          <div className={styles.priceRow}>
            <span className={styles.priceVal}>$0</span>
            <span className={styles.pricePeriod}>/ per month</span>
          </div>

          <Link href="/register?plan=standard" className={styles.cardBtnOutline}>
            Test 30 days for free
          </Link>

          <div className={styles.featureDivider} />

          <ul className={styles.featureList}>
            <li className={styles.featureRow}>
              <span>Limit of contacts &amp; emails</span>
              <strong className={styles.limitVal}>1,000 / mo</strong>
            </li>
            <li className={styles.featureRow}>
              <span>Advanced campaign configuration</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Insightful analytics &amp; reporting</span>
              <X className={styles.xIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Sending domain certificates</span>
              <X className={styles.xIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Additional user accounts &amp; collaboration</span>
              <X className={styles.xIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Customization &amp; premium support</span>
              <X className={styles.xIcon} />
            </li>
          </ul>
        </div>

        {/* Pro Plan (Highlighted Recommended Card) */}
        <div className={`${styles.pricingCard} ${styles.recommendedCard}`}>
          <div className={styles.recommendedTag}>
            <Star className="w-3.5 h-3.5 fill-current" /> Recommended
          </div>

          <h2 className={styles.planTitle}>Pro</h2>
          <p className={styles.planDesc}>
            Fits most use cases with active social posting, automated sequences, and AI copy.
          </p>

          <div className={styles.priceRow}>
            <span className={styles.priceVal}>${isAnnual ? "49" : "59"}</span>
            <span className={styles.pricePeriod}>/ per month</span>
          </div>

          <Link href="/register?plan=pro" className={styles.cardBtnPrimary}>
            Start Pro for free
          </Link>

          <div className={styles.featureDivider} />

          <ul className={styles.featureList}>
            <li className={styles.featureRow}>
              <span>Limit of contacts &amp; emails</span>
              <strong className={styles.limitVal}>25,000 / mo</strong>
            </li>
            <li className={styles.featureRow}>
              <span>Advanced campaign configuration</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Insightful analytics &amp; reporting</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Sending domain certificates</span>
              <X className={styles.xIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Additional user accounts &amp; collaboration</span>
              <X className={styles.xIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Customization &amp; premium support</span>
              <X className={styles.xIcon} />
            </li>
          </ul>
        </div>

        {/* Max Plan */}
        <div className={styles.pricingCard}>
          <h2 className={styles.planTitle}>Max</h2>
          <p className={styles.planDesc}>
            High-volume campaigns, unlimited AI assistant generation, and chart telemetry.
          </p>

          <div className={styles.priceRow}>
            <span className={styles.priceVal}>${isAnnual ? "119" : "149"}</span>
            <span className={styles.pricePeriod}>/ per month</span>
          </div>

          <Link href="/register?plan=max" className={styles.cardBtnOutline}>
            Test 30 days for free
          </Link>

          <div className={styles.featureDivider} />

          <ul className={styles.featureList}>
            <li className={styles.featureRow}>
              <span>Limit of contacts &amp; emails</span>
              <strong className={styles.limitVal}>Unlimited</strong>
            </li>
            <li className={styles.featureRow}>
              <span>Advanced campaign configuration</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Insightful analytics &amp; reporting</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Sending domain certificates</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Additional user accounts &amp; collaboration</span>
              <X className={styles.xIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Customization &amp; premium support</span>
              <X className={styles.xIcon} />
            </li>
          </ul>
        </div>

        {/* Max Enterprise Plan */}
        <div className={styles.pricingCard}>
          <h2 className={styles.planTitle}>Max Enterprise</h2>
          <p className={styles.planDesc}>
            Full multi-tenant team collaboration, dedicated IP pools, custom SLAs, and custom limits.
          </p>

          <div className={styles.priceRow}>
            <span className={styles.priceValQuote}>Custom quote</span>
          </div>

          <Link href="/contact" className={styles.cardBtnOutline}>
            Contact Us
          </Link>

          <div className={styles.featureDivider} />

          <ul className={styles.featureList}>
            <li className={styles.featureRow}>
              <span>Limit of contacts &amp; emails</span>
              <strong className={styles.limitVal}>Unlimited</strong>
            </li>
            <li className={styles.featureRow}>
              <span>Advanced campaign configuration</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Insightful analytics &amp; reporting</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Sending domain certificates</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Additional user accounts &amp; collaboration</span>
              <Check className={styles.checkIcon} />
            </li>
            <li className={styles.featureRow}>
              <span>Customization &amp; premium support</span>
              <Check className={styles.checkIcon} />
            </li>
          </ul>
        </div>
      </div>

      {/* Bottom CTA Button */}
      <div className={styles.bottomCtaBox}>
        <Link href="/register" className={styles.tryFreeBtn}>
          Try it out for free
        </Link>
      </div>
    </main>
  );
}
