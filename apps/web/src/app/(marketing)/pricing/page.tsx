import { PricingSection } from "../pricing-section";
import styles from "../marketing.module.css";

export const metadata = {
  title: "Pricing Plans — Growixa AI Growth Engine",
  description:
    "Simple, transparent pricing plans for startups, growing businesses, and enterprises.",
};

export default function PricingPage() {
  return (
    <div className={styles.container}>
      <PricingSection />
    </div>
  );
}
