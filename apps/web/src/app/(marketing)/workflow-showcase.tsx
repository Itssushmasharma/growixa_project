import styles from "./marketing.module.css";

const steps = [
  { icon: "📝", title: "Lead Fills Form", sub: "Form or Landing Page" },
  { icon: "🧠", title: "AI Scores Lead", sub: "Intent & Fit Rating" },
  { icon: "📧", title: "Email Sequence", sub: "Personalized Outreach" },
  { icon: "💬", title: "WhatsApp / SMS", sub: "Instant Multi-Channel" },
  { icon: "🔔", title: "Sales Notified", sub: "Slack & CRM Alert" },
];

export function WorkflowShowcase() {
  return (
    <section className={styles.section} style={{ background: "#fafafa" }}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Visual Automation</div>
        <h2 className={styles.sectionTitle}>Automate Entire Marketing Pipelines</h2>
        <p className={styles.sectionSub}>
          Connect trigger events to AI decisions and automated actions across email, messaging, and
          sales alerts.
        </p>
      </div>

      <div className={styles.workflowPipeline}>
        {steps.map((step, idx) => (
          <div key={idx} style={{ display: "flex", alignItems: "center", gap: "1rem", flex: 1 }}>
            <div className={styles.workflowStep}>
              <div className={styles.stepIcon}>{step.icon}</div>
              <div className={styles.stepTitle}>{step.title}</div>
              <div className={styles.stepSub}>{step.sub}</div>
            </div>
            {idx < steps.length - 1 && <span className={styles.arrow}>→</span>}
          </div>
        ))}
      </div>
    </section>
  );
}
