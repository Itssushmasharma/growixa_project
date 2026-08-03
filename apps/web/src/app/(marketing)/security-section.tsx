import styles from "./marketing.module.css";

const securityFeatures = [
  {
    title: "SOC2 Ready Architecture",
    desc: "Built adhering to strict B2B security and operational compliance controls.",
  },
  {
    title: "GDPR & Opt-Out Handling",
    desc: "Automated consent tracking, single-click unsubscribes, and instant suppression enforcement.",
  },
  {
    title: "Fernet Encrypted Credentials",
    desc: "SMTP, API keys, and access tokens encrypted at rest using AES-128 Fernet cryptography.",
  },
  {
    title: "Insert-Only Audit Logging",
    desc: "Complete append-only audit trail tracking every system action and user permission check.",
  },
  {
    title: "Granular RBAC Controls",
    desc: "Role-based access separating Super Admin, Admin, Manager, Creator, and Viewer roles.",
  },
  {
    title: "99.99% SLA Uptime",
    desc: "High-availability background job worker queues powered by Redis and RabbitMQ.",
  },
];

export function SecuritySection() {
  return (
    <section className={styles.section} style={{ background: "#f8fafc" }}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Enterprise Reliability</div>
        <h2 className={styles.sectionTitle}>Built with Bank-Grade Security</h2>
        <p className={styles.sectionSub}>
          Protect your customer data and ensure delivery compliance with end-to-end encryption and
          audit logging.
        </p>
      </div>

      <div className={styles.cardsGrid}>
        {securityFeatures.map((sec, idx) => (
          <div key={idx} className={styles.card}>
            <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>🛡️</div>
            <h3 className={styles.cardTitle}>{sec.title}</h3>
            <p className={styles.cardDesc}>{sec.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
