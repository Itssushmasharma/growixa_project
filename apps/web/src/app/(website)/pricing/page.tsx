"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import styles from "./pricing.module.css";

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(true);

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <span className={styles.eyebrow}>Pricing</span>
        <h1 className={styles.title}>Simple Plans That Scale With Your Growth</h1>
        <p className={styles.subtitle}>
          Start free with no credit card required. Upgrade or top-up with one-time credit packs anytime.
        </p>
      </header>

      <div className={styles.toggleContainer}>
        <span className={`${styles.toggleLabel} ${!isAnnual ? styles.active : ""}`} onClick={() => setIsAnnual(false)}>
          Monthly
        </span>
        <div className={`${styles.toggleSwitch} ${isAnnual ? styles.active : ""}`} onClick={() => setIsAnnual(!isAnnual)}>
          <div className={styles.toggleKnob}></div>
        </div>
        <span className={`${styles.toggleLabel} ${isAnnual ? styles.active : ""}`} onClick={() => setIsAnnual(true)}>
          Annually
        </span>
        <span className={styles.badge}>Save 20%</span>
      </div>

      <div className={styles.grid}>
        {/* Free Plan */}
        <div className={styles.card}>
          <h2 className={styles.planName}>Free</h2>
          <p className={styles.planDesc}>Perfect for exploring the platform and testing tools.</p>
          <div className={styles.priceBlock}>
            <span className={styles.price}>$0</span>
            <span className={styles.period}>/mo</span>
          </div>
          <Link href="/register?plan=free" className={`${styles.btn} ${styles.secondaryBtn}`}>
            Start Free
          </Link>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> 1 Team Member</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> 2 Social Accounts</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Community Support</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Basic Templates</li>
          </ul>
        </div>

        {/* Starter Plan */}
        <div className={styles.card}>
          <h2 className={styles.planName}>Starter</h2>
          <p className={styles.planDesc}>Perfect for small teams and early-stage startups.</p>
          <div className={styles.priceBlock}>
            <span className={styles.price}>${isAnnual ? "49" : "59"}</span>
            <span className={styles.period}>/mo</span>
          </div>
          <Link href="/register?plan=starter" className={`${styles.btn} ${styles.secondaryBtn}`}>
            Get Started
          </Link>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> 2 Team Members</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> 5 Social Accounts</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Unified Inbox (Basic)</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Basic Analytics</li>
          </ul>
        </div>

        {/* Professional Plan */}
        <div className={`${styles.card} ${styles.popularCard}`}>
          <div className={styles.popularBadge}>Most Popular</div>
          <h2 className={styles.planName}>Professional</h2>
          <p className={styles.planDesc}>Everything you need to run scaling marketing operations.</p>
          <div className={styles.priceBlock}>
            <span className={styles.price}>${isAnnual ? "99" : "119"}</span>
            <span className={styles.period}>/mo</span>
          </div>
          <Link href="/register?plan=pro" className={`${styles.btn} ${styles.primaryBtn}`}>
            Start Free Trial
          </Link>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Unlimited Team Members</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> 15 Social Accounts</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Advanced AI Automations</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> CRM & Audience Segmentation</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Predictive Analytics</li>
          </ul>
        </div>

        {/* Enterprise Plan */}
        <div className={styles.card}>
          <h2 className={styles.planName}>Enterprise</h2>
          <p className={styles.planDesc}>Custom setups, dedicated support, and SLA guarantees.</p>
          <div className={styles.priceBlock}>
            <span className={styles.price}>$299</span>
            <span className={styles.period}>/mo</span>
          </div>
          <Link href="/contact" className={`${styles.btn} ${styles.secondaryBtn}`}>
            Contact Sales
          </Link>
          <ul className={styles.featuresList}>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Unlimited Everything</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Dedicated Success Manager</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> Custom API & Integrations</li>
            <li className={styles.featureItem}><Check size={20} className={styles.featureIcon} /> SLA & Priority Support</li>
          </ul>
        </div>
      </div>

      <section className={styles.faqSection}>
        <h2 className={styles.faqTitle}>Frequently Asked Questions</h2>
        <div className={styles.faqGrid}>
          <div className={styles.faqItem}>
            <h3 className={styles.faqQ}>Can I change my plan later?</h3>
            <p className={styles.faqA}>Yes, you can upgrade or downgrade your plan at any time. Prorated charges or credits will automatically be applied to your account.</p>
          </div>
          <div className={styles.faqItem}>
            <h3 className={styles.faqQ}>What payment methods do you accept?</h3>
            <p className={styles.faqA}>We accept all major credit cards including Visa, Mastercard, and American Express. For Enterprise plans, we also support invoicing and wire transfers.</p>
          </div>
          <div className={styles.faqItem}>
            <h3 className={styles.faqQ}>Is there a free trial?</h3>
            <p className={styles.faqA}>Yes! Our Professional plan comes with a 14-day free trial. No credit card required to start.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
