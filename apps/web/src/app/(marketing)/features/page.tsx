import { AiTeamSection } from "../ai-team-section";
import { WorkflowShowcase } from "../workflow-showcase";
import styles from "../marketing.module.css";

export const metadata = {
  title: "Platform & Features — Growixa AI Growth Engine",
  description:
    "Explore Growixa's Email Campaigns, AI Marketing Assistants, Audience Segmentation, and Social Scheduling features.",
};

export default function FeaturesPage() {
  return (
    <div className={styles.container}>
      <section className={styles.hero} style={{ paddingBottom: "2rem" }}>
        <div className={styles.pillBadge}>Platform Deep Dive</div>
        <h1 className={styles.heroTitle}>
          Every Growth Capability in <span className={styles.gradientText}>One Platform</span>
        </h1>
        <p className={styles.heroSub}>
          Eliminate disconnected SaaS subscriptions. Growixa combines high-deliverability email
          relays, AI content generation, dynamic contact segmentation, and social scheduling.
        </p>
      </section>

      <AiTeamSection />
      <WorkflowShowcase />
    </div>
  );
}
