import styles from "./marketing.module.css";

const logos = [
  "Postmark",
  "OpenAI",
  "Claude AI",
  "Stripe",
  "Razorpay",
  "Google Workspace",
  "Meta Ads",
  "LinkedIn",
  "Slack",
  "Zapier",
];

export function IntegrationsSection() {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Ecosystem</div>
        <h2 className={styles.sectionTitle}>Connects With Your Tech Stack</h2>
        <p className={styles.sectionSub}>
          Native integrations with leading email relays, payment gateways, LLMs, and social
          platforms.
        </p>
      </div>

      <div className={styles.logosGrid}>
        {logos.map((name, idx) => (
          <div key={idx} className={styles.logoBox}>
            {name}
          </div>
        ))}
      </div>
    </section>
  );
}
