"use client";

import Link from "next/link";
import { Card3D } from "@/components/card-3d";
import styles from "./marketing.module.css";

const plans = [
  {
    name: "Starter",
    price: "$0",
    period: "/month",
    desc: "For startups and small teams exploring AI growth.",
    features: [
      "Up to 2,500 Contacts",
      "10,000 Emails / mo",
      "50 AI Copy Generations / mo",
      "1 User Account",
      "Basic Audience Segmentation",
    ],
    buttonText: "Start Free",
    featured: false,
  },
  {
    name: "Growth",
    price: "$29",
    period: "/month",
    desc: "For growing businesses scaling multi-channel marketing.",
    features: [
      "Up to 25,000 Contacts",
      "100,000 Emails / mo",
      "1,000 AI Copy Generations / mo",
      "5 User Accounts (RBAC)",
      "Dynamic AND-Rule Segmentation",
      "Social Media Scheduler",
      "Postmark SMTP Integration",
    ],
    buttonText: "Start 14-Day Free Trial",
    featured: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "For agencies and large brands needing dedicated infrastructure.",
    features: [
      "Unlimited Contacts & Emails",
      "Unlimited AI Generations",
      "Dedicated IP & SMTP Relay",
      "Custom Workspaces & SSO",
      "24/7 Priority SLA & Audit Logs",
      "Dedicated Growth Manager",
    ],
    buttonText: "Contact Sales",
    featured: false,
  },
];

export function PricingSection() {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Transparent Pricing</div>
        <h2 className={styles.sectionTitle}>Simple Plans for Every Stage</h2>
        <p className={styles.sectionSub}>
          Start free with no credit card required. Upgrade as your contact list and campaigns grow.
        </p>
      </div>

      <div className={styles.pricingGrid}>
        {plans.map((plan, idx) => (
          <Card3D key={idx} depth={12}>
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
                    <span className={styles.priceValue}>{plan.price}</span>
                    <span className={styles.pricePeriod}>{plan.period}</span>
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
                href="/login"
                className={plan.featured ? styles.primaryBtn : styles.secondaryBtn}
                style={{ textAlign: "center", display: "block" }}
              >
                {plan.buttonText}
              </Link>
            </div>
          </Card3D>
        ))}
      </div>
    </section>
  );
}
