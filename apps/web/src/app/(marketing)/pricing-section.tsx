"use client";

import { useState } from "react";
import Link from "next/link";
import { Card3D } from "@/components/card-3d";
import styles from "./marketing.module.css";

type Currency = "USD" | "INR";
type BillingPeriod = "MONTHLY" | "ANNUAL";

const plans = [
  {
    slug: "free",
    name: "Free",
    priceUsd: "$0",
    priceInr: "₹0",
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
    priceUsdMonthly: "$19",
    priceUsdAnnual: "$15",
    priceInrMonthly: "₹1,499",
    priceInrAnnual: "₹1,199",
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
    priceUsdMonthly: "$49",
    priceUsdAnnual: "$39",
    priceInrMonthly: "₹3,999",
    priceInrAnnual: "₹3,199",
    desc: "For scaling brands requiring BYO AI keys & full RBAC.",
    features: [
      "15,000 Total Contacts",
      "100,000 Emails / mo",
      "1,000 AI Generations / mo",
      "Bring Your Own AI Key (BYO OpenAI/Anthropic/Modal)",
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
    priceUsdMonthly: "$149",
    priceUsdAnnual: "$119",
    priceInrMonthly: "₹11,999",
    priceInrAnnual: "₹9,599",
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

const addOnPacks = [
  {
    name: "🤖 AI Generation Pack",
    priceUsd: "+$5",
    priceInr: "+₹399",
    desc: "+250 Extra AI Runs (Never expires)",
  },
  {
    name: "📧 Email Send Pack",
    priceUsd: "+$10",
    priceInr: "+₹799",
    desc: "+10,000 Extra Email Credits",
  },
  {
    name: "👥 Extra Contacts Pack",
    priceUsd: "+$10",
    priceInr: "+₹799",
    desc: "+2,500 Extra Contact Slots",
  },
  {
    name: "📸 Social Account Add-on",
    priceUsd: "+$5 /mo",
    priceInr: "+₹399 /mo",
    desc: "+3 Connected Social Accounts",
  },
];

export function PricingSection() {
  const [currency, setCurrency] = useState<Currency>("USD");
  const [period, setPeriod] = useState<BillingPeriod>("MONTHLY");

  const getPriceDisplay = (plan: typeof plans[0]) => {
    if (plan.slug === "free") {
      return currency === "USD" ? "$0" : "₹0";
    }
    if (currency === "USD") {
      return period === "MONTHLY" ? plan.priceUsdMonthly : plan.priceUsdAnnual;
    }
    return period === "MONTHLY" ? plan.priceInrMonthly : plan.priceInrAnnual;
  };

  return (
    <section className={styles.section} id="pricing">
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Flexible & Transparent Pricing</div>
        <h2 className={styles.sectionTitle}>Simple Plans That Scale With Your Growth</h2>
        <p className={styles.sectionSub}>
          Start free with no credit card required. Upgrade or buy one-time credit packs anytime.
        </p>

        {/* Currency & Billing Frequency Toggle Controls */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "1.5rem",
            marginTop: "1.5rem",
            flexWrap: "wrap",
          }}
        >
          {/* Currency Switcher */}
          <div
            style={{
              background: "rgba(15, 23, 42, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: "9999px",
              padding: "4px",
              display: "inline-flex",
            }}
          >
            <button
              onClick={() => setCurrency("USD")}
              style={{
                background: currency === "USD" ? "linear-gradient(135deg, #38bdf8, #a855f7)" : "transparent",
                color: currency === "USD" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: "9999px",
                padding: "6px 16px",
                fontSize: "0.875rem",
                fontWeight: 700,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              $ USD
            </button>
            <button
              onClick={() => setCurrency("INR")}
              style={{
                background: currency === "INR" ? "linear-gradient(135deg, #38bdf8, #a855f7)" : "transparent",
                color: currency === "INR" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: "9999px",
                padding: "6px 16px",
                fontSize: "0.875rem",
                fontWeight: 700,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
            >
              ₹ INR
            </button>
          </div>

          {/* Billing Period Toggle */}
          <div
            style={{
              background: "rgba(15, 23, 42, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              borderRadius: "9999px",
              padding: "4px",
              display: "inline-flex",
              alignItems: "center",
            }}
          >
            <button
              onClick={() => setPeriod("MONTHLY")}
              style={{
                background: period === "MONTHLY" ? "rgba(255, 255, 255, 0.12)" : "transparent",
                color: period === "MONTHLY" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: "9999px",
                padding: "6px 16px",
                fontSize: "0.875rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Monthly
            </button>
            <button
              onClick={() => setPeriod("ANNUAL")}
              style={{
                background: period === "ANNUAL" ? "linear-gradient(135deg, #10b981, #059669)" : "transparent",
                color: "#ffffff",
                border: "none",
                borderRadius: "9999px",
                padding: "6px 16px",
                fontSize: "0.875rem",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              Annual <span style={{ fontSize: "0.75rem", marginLeft: "4px" }}>(Save 20%)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Pricing Grid */}
      <div
        className={styles.pricingGrid}
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1.5rem" }}
      >
        {plans.map((plan) => (
          <Card3D key={plan.slug} depth={12}>
            <div className={plan.featured ? styles.featuredPriceCard : styles.priceCard}>
              <div>
                <div className={styles.priceHeader}>
                  {plan.featured && (
                    <span
                      style={{
                        background: "linear-gradient(135deg, #38bdf8 0%, #a855f7 100%)",
                        color: "white",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        padding: "0.25rem 0.625rem",
                        borderRadius: "9999px",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                        display: "inline-block",
                        marginBottom: "0.75rem",
                      }}
                    >
                      Most Popular
                    </span>
                  )}
                  <div className={styles.planName}>{plan.name}</div>
                  <div>
                    <span className={styles.priceValue}>{getPriceDisplay(plan)}</span>
                    <span className={styles.pricePeriod}>/month</span>
                  </div>
                  <div style={{ fontSize: "0.875rem", color: "#94a3b8", marginTop: "0.5rem" }}>
                    {plan.desc}
                  </div>
                </div>

                <ul className={styles.featureList}>
                  {plan.features.map((feat, fidx) => (
                    <li key={fidx} className={styles.featureItem}>
                      <span className={styles.checkMark}>✓</span>
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href={plan.href}
                className={plan.featured ? styles.primaryBtn : styles.secondaryBtn}
                style={{ textAlign: "center", display: "block" }}
              >
                {plan.buttonText}
              </Link>
            </div>
          </Card3D>
        ))}
      </div>

      {/* Add-On Credit Packs Widget */}
      <div
        style={{
          marginTop: "3.5rem",
          background: "radial-gradient(circle at 50% 0%, rgba(56, 189, 248, 0.12), rgba(15, 23, 42, 0.9) 70%)",
          border: "1px solid rgba(56, 189, 248, 0.3)",
          borderRadius: "24px",
          padding: "2.25rem",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <h3 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#ffffff", marginBottom: "0.5rem" }}>
            💳 Pay-As-You-Go Add-On Credit Packs
          </h3>
          <p style={{ fontSize: "0.9375rem", color: "#94a3b8" }}>
            Ran out of AI credits or email sends? Buy one-time credit top-ups without changing your monthly plan.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem" }}>
          {addOnPacks.map((pack, idx) => (
            <div
              key={idx}
              style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "16px",
                padding: "1.25rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ fontSize: "1rem", fontWeight: 700, color: "#ffffff", marginBottom: "0.25rem" }}>
                  {pack.name}
                </div>
                <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#38bdf8", marginBottom: "0.5rem" }}>
                  {currency === "USD" ? pack.priceUsd : pack.priceInr}
                </div>
                <div style={{ fontSize: "0.8125rem", color: "#94a3b8" }}>{pack.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

