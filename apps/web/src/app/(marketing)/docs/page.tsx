import Link from "next/link";
import styles from "../marketing.module.css";

export const metadata = {
  title: "API & Developer Documentation — Growixa",
  description:
    "REST API references, SDK guides, Webhook event specs, and authentication documentation.",
};

const docTopics = [
  {
    title: "Authentication",
    desc: "Bearer token authentication, session cookies, and API key permissions.",
  },
  {
    title: "Contacts & Audience API",
    desc: "Create, update, tag, segment, and suppress contact records programmatically.",
  },
  {
    title: "Email Campaign API",
    desc: "Trigger synchronous test sends and enqueue async worker campaign dispatch.",
  },
  {
    title: "Webhook Events",
    desc: "Listen for real-time email delivery events, bounces, complaints, and unsubscribes.",
  },
  {
    title: "Audit Log Trail",
    desc: "Query insert-only audit logs for security, compliance, and user action tracking.",
  },
  {
    title: "OpenAPI Specification",
    desc: "Download raw OpenAPI 3.0 JSON schema for SDK generation.",
  },
];

export default function DocsPage() {
  return (
    <div className={styles.container}>
      <section className={styles.hero}>
        <div className={styles.pillBadge}>Developer Hub</div>
        <h1 className={styles.heroTitle}>
          API & Developer <span className={styles.gradientText}>Documentation</span>
        </h1>
        <p className={styles.heroSub}>
          Integrate Growixa&apos;s AI Growth Engine directly into your web applications, webhooks,
          and automation tools.
        </p>
      </section>

      <section className={styles.section}>
        <div className={styles.cardsGrid}>
          {docTopics.map((topic, idx) => (
            <div key={idx} className={styles.card}>
              <div
                style={{
                  color: "#7c3aed",
                  fontWeight: 700,
                  fontSize: "0.875rem",
                  marginBottom: "0.5rem",
                }}
              >
                API Reference
              </div>
              <h2 className={styles.cardTitle}>{topic.title}</h2>
              <p className={styles.cardDesc} style={{ marginBottom: "1rem" }}>
                {topic.desc}
              </p>
              <Link
                href="/login"
                style={{ color: "#2563eb", fontWeight: 600, textDecoration: "none" }}
              >
                View Guide →
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
