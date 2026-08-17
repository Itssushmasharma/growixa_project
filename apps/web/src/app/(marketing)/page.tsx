import { HeroSection } from "./hero-section";
import { TrustBar } from "./trust-bar";
import { AiTeamSection } from "./ai-team-section";
import { WorkflowShowcase } from "./workflow-showcase";
import { IntegrationsSection } from "./integrations-section";
import { SecuritySection } from "./security-section";
import { PricingSection } from "./pricing-section";
import { FaqSection } from "./faq-section";
import styles from "./marketing.module.css";

export const metadata = {
  title: "Growixa — The AI Growth Platform",
  description:
    "One platform to automate marketing, generate AI content, manage contacts, schedule social posts, and scale your business.",
};

export default function LandingPage() {
  return (
    <div className={styles.container}>
      <HeroSection />
      <TrustBar />
      <AiTeamSection />
      <WorkflowShowcase />
      <IntegrationsSection />
      <SecuritySection />
      <PricingSection />
      <FaqSection />
    </div>
  );
}
