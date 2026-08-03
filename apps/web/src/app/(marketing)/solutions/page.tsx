import Link from "next/link";
import styles from "../marketing.module.css";

export const metadata = {
  title: "Solutions by Industry — Growixa AI Growth Engine",
  description:
    "Tailored AI growth solutions for Marketers, Agencies, SaaS Startups, and E-Commerce stores.",
};

const solutions = [
  {
    tag: "For Growth Marketers",
    title: "Automate Campaigns & Scale Personalization",
    desc: "Run targeted email sequences and social posts without manually drafting copy for every audience segment.",
  },
  {
    tag: "For Agencies & Consultants",
    title: "Manage Multiple Brands from One Workspace",
    desc: "Streamline client campaign creation, approval workflows, and deliverability reports with RBAC access.",
  },
  {
    tag: "For SaaS Startups",
    title: "Convert Trial Users into Long-Term Customers",
    desc: "Trigger AI-driven onboarding emails based on product usage events and in-app behavior.",
  },
  {
    tag: "For E-Commerce",
    title: "Boost Repeat Purchases & LTV",
    desc: "Automatically segment buyers, send re-engagement offers, and publish seasonal promotions.",
  },
];

export default function SolutionsPage() {
  return (
    <div className={styles.container}>
      <section className={styles.hero}>
        <div className={styles.pillBadge}>Industry Solutions</div>
        <h1 className={styles.heroTitle}>
          Built to Scale <span className={styles.gradientText}>Your Business</span>
        </h1>
        <p className={styles.heroSub}>
          Discover how Growixa&apos;s AI Growth Engine powers campaigns for growth teams, agencies,
          and online businesses.
        </p>
      </section>

      <section className={styles.section}>
        <div className={styles.cardsGrid} style={{ gridTemplateColumns: "repeat(2, 1fr)" }}>
          {solutions.map((sol, idx) => (
            <div key={idx} className={styles.card}>
              <div
                style={{
                  color: "#2563eb",
                  fontWeight: 700,
                  fontSize: "0.875rem",
                  marginBottom: "0.5rem",
                }}
              >
                {sol.tag}
              </div>
              <h2 className={styles.cardTitle}>{sol.title}</h2>
              <p className={styles.cardDesc} style={{ marginBottom: "1.5rem" }}>
                {sol.desc}
              </p>
              <Link href="/login" className={styles.primaryBtn} style={{ display: "inline-block" }}>
                Explore {sol.tag} →
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
