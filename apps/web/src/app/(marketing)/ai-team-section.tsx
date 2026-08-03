import styles from "./marketing.module.css";

const aiTeamMembers = [
  {
    icon: "✍️",
    title: "AI Copywriter",
    desc: "Generate high-converting email copy, subject lines, and ad text tailored to your brand voice in seconds.",
  },
  {
    icon: "📧",
    title: "Email Optimizer",
    desc: "Real-time spam checks, deliverability scoring, and subject line performance predictions before sending.",
  },
  {
    icon: "📈",
    title: "Campaign Planner",
    desc: "Automated multi-channel sequence planning that adapts based on user behavior and engagement signals.",
  },
  {
    icon: "🎯",
    title: "Audience Builder",
    desc: "Dynamic AND-rule segmentation that groups leads automatically based on real-time activity and custom fields.",
  },
  {
    icon: "💬",
    title: "Social Creator",
    desc: "Craft, schedule, and publish platform-optimized posts across LinkedIn, Twitter, Meta, and Instagram.",
  },
  {
    icon: "📊",
    title: "Marketing Analyst",
    desc: "Instant revenue attribution insights, open/click heatmaps, and actionable growth recommendations.",
  },
];

export function AiTeamSection() {
  return (
    <section className={styles.section}>
      <div className={styles.sectionHeader}>
        <div className={styles.sectionTag}>Autonomous Capabilities</div>
        <h2 className={styles.sectionTitle}>Meet Your AI Marketing Team</h2>
        <p className={styles.sectionSub}>
          Replace fragmented tools with AI agents designed to handle campaign drafting, audience
          targeting, and analytics.
        </p>
      </div>

      <div className={styles.cardsGrid}>
        {aiTeamMembers.map((member, idx) => (
          <div key={idx} className={styles.card}>
            <div className={styles.cardIcon}>{member.icon}</div>
            <h3 className={styles.cardTitle}>{member.title}</h3>
            <p className={styles.cardDesc}>{member.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
