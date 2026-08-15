"use client";

import { useState } from "react";
import Link from "next/link";
import { Card3D } from "@/components/card-3d";
import styles from "./marketing.module.css";

type Currency = "USD" | "INR";

interface Plan {
  slug: string;
  name: string;
  priceUsd: string;
  priceInr: string;
  period: string;
  desc: string;
  features: string[];
  buttonText: string;
  href: string;
  featured: boolean;
}

const plans: Plan[] = [
  {
    slug: "free",
    name: "Free",
    priceUsd: "$0",
    priceInr: "₹0",
    period: "Free forever",
    desc: "For small teams & startups exploring AI-powered growth.",
    features: [
      "250 Total Contacts",
      "1,000 Emails / mo",
      "10 AI Generations / mo",
      "1 User Seat",
      "7 Days Audit Log Retention",
    ],
    buttonText: "Start Free",
    href: "/register?plan=free",
    featured: false,
  },
  {
    slug: "starter",
    name: "Starter",
    priceUsd: "$19",
    priceInr: "₹1,499",
    period: "/ month",
    desc: "For growing businesses automating email & social campaigns.",
    features: [
      "2,500 Total Contacts",
      "15,000 Emails / mo",
      "150 AI Generations / mo",
      "3 User Seats",
      "Custom SMTP Integration",
      "30 Days Audit Log Retention",
    ],
    buttonText: "Start 14-Day Free Trial",
    href: "/register?plan=starter",
    featured: false,
  },
  {
    slug: "pro",
    name: "Pro",
    priceUsd: "$49",
    priceInr: "₹3,999",
    period: "/ month",
    desc: "For scaling brands requiring BYO AI keys & full RBAC.",
    features: [
      "15,000 Total Contacts",
      "100,000 Emails / mo",
      "1,000 AI Generations / mo",
      "Bring Your Own AI Key (BYO OpenAI / Anthropic)",
      "10 User Seats with Full RBAC (6 Roles)",
      "Postmark + Custom SMTP Relays",
      "90 Days Audit Log Retention",
    ],
    buttonText: "Get Started Pro",
    href: "/register?plan=pro",
    featured: true,
  },
  {
    slug: "enterprise",
    name: "Enterprise",
    priceUsd: "Custom",
    priceInr: "Custom",
    period: "Tailored to scale",
    desc: "For agencies & large brands needing unlimited scale & dedicated IPs.",
    features: [
      "100,000+ Total Contacts",
      "Unlimited Monthly Emails",
      "Unlimited AI Generations",
      "Unlimited User Seats & Custom Roles",
      "Dedicated IP Relays & Custom Workspaces",
      "365 Days Audit Log Retention",
      "Dedicated Support Session SLA",
    ],
    buttonText: "Contact Sales",
    href: "/login",
    featured: false,
  },
];

interface CreditPack {
  icon: string;
  name: string;
  priceInr: string;
  approxUsd: string;
  desc: string;
}

const creditPacks: CreditPack[] = [
  {
    icon: "🤖",
    name: "250 AI Runs",
    priceInr: "₹400",
    approxUsd: "~$5",
    desc: "+250 AI generations (never expires)",
  },
  {
    icon: "⚡",
    name: "1,000 AI Runs",
    priceInr: "₹1,200",
    approxUsd: "~$15",
    desc: "+1,000 AI generations (bulk discount)",
  },
  {
    icon: "📧",
    name: "10,000 Email Sends",
    priceInr: "₹800",
    approxUsd: "~$10",
    desc: "+10,000 extra email delivery credits",
  },
  {
    icon: "👥",
    name: "2,500 Contact Slots",
    priceInr: "₹800",
    approxUsd: "~$10",
    desc: "+2,500 extra audience capacity",
  },
  {
    icon: "📱",
    name: "50 Social Posts",
    priceInr: "₹400",
    approxUsd: "~$5",
    desc: "+50 scheduled or published social posts",
  },
];

export function PricingSection() {
  const [currency, setCurrency] = useState<Currency>("USD");

  const getPriceDisplay = (plan: Plan) => {
    if (plan.slug === "enterprise") return "Custom";
    return currency === "USD" ? plan.priceUsd : plan.priceInr;
  };

  return (
    <section className={styles.section} id="pricing">
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Flexible & Transparent Pricing</div>
        <h2 className={styles.sectionTitle}>Simple Plans That Scale With Your Growth</h2>
        <p className={styles.sectionSub}>
          Start free with no credit card required. Upgrade or top-up with one-time credit packs
          anytime.
        </p>

        {/* Currency Switcher Controls */}
        <div className={styles.pricingControls}>
          <div className={styles.currencyToggle} role="group" aria-label="Select billing currency">
            <button
              type="button"
              onClick={() => setCurrency("USD")}
              className={`${styles.currencyBtn} ${currency === "USD" ? styles.currencyBtnActive : ""}`}
              aria-pressed={currency === "USD"}
            >
              $ USD
            </button>
            <button
              type="button"
              onClick={() => setCurrency("INR")}
              className={`${styles.currencyBtn} ${currency === "INR" ? styles.currencyBtnActive : ""}`}
              aria-pressed={currency === "INR"}
            >
              ₹ INR
            </button>
          </div>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div className={styles.pricingGrid}>
        {plans.map((plan) => {
          const isFeatured = plan.featured;
          return (
            <Card3D key={plan.slug} depth={15}>
              <div className={isFeatured ? styles.featuredPriceCard : styles.priceCard}>
                {isFeatured && <div className={styles.featuredBadge}>MOST POPULAR</div>}
                <div className={styles.priceHeader}>
                  <h3 className={styles.planName}>{plan.name}</h3>
                  <div className={styles.priceContainer}>
                    <span className={styles.priceValue}>{getPriceDisplay(plan)}</span>
                    <span className={styles.pricePeriod}>{plan.period}</span>
                  </div>
                  <p className={styles.planDesc}>{plan.desc}</p>
                </div>

                <ul className={styles.featureList} aria-label={`${plan.name} plan features`}>
                  {plan.features.map((feat) => (
                    <li key={feat} className={styles.featureItem}>
                      <span className={styles.checkMark} aria-hidden="true">
                        ✓
                      </span>
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={isFeatured ? styles.featuredPriceBtn : styles.priceBtn}
                >
                  {plan.buttonText}
                </Link>
              </div>
            </Card3D>
          );
        })}
      </div>

      {/* Pay-As-You-Go Credit Packs Section */}
      <div className={styles.creditPacksSection}>
        <div className={styles.creditPacksHeader}>
          <div className={styles.creditPacksBadge}>No Lock-In Add-Ons</div>
          <h3 className={styles.creditPacksTitle}>Pay-As-You-Go Top-Up Credit Packs</h3>
          <p className={styles.creditPacksSub}>
            Need extra AI generations, email volume, or contact slots without upgrading your monthly
            plan? Purchase top-up packs directly from your dashboard anytime — credits never expire.
          </p>
        </div>

        <div className={styles.creditPacksGrid}>
          {creditPacks.map((pack) => (
            <div key={pack.name} className={styles.creditPackCard}>
              <div className={styles.creditPackTop}>
                <span className={styles.creditPackIcon} aria-hidden="true">
                  {pack.icon}
                </span>
                <span className={styles.creditPackPrice}>
                  {currency === "INR" ? pack.priceInr : `${pack.priceInr} (${pack.approxUsd})`}
                </span>
              </div>
              <h4 className={styles.creditPackName}>{pack.name}</h4>
              <p className={styles.creditPackDesc}>{pack.desc}</p>
            </div>
          ))}
        </div>

        <p className={styles.creditPacksNote}>
          * Top-up credit packs are billed one-time via Razorpay and remain in your account until
          used.
        </p>
      </div>
    </section>
  );
}
