import { SecuritySection } from "../security-section";
import styles from "../marketing.module.css";

export const metadata = {
  title: "Security & Compliance — Growixa AI Growth Engine",
  description:
    "Learn about Growixa's SOC2 compliance, Fernet encryption, insert-only audit logs, and data protection standards.",
};

export default function SecurityPage() {
  return (
    <div className={styles.container}>
      <SecuritySection />
    </div>
  );
}
