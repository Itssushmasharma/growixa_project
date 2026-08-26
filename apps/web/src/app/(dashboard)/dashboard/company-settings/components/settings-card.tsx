import type { ReactNode } from "react";

import styles from "./components.module.css";

interface SettingsCardProps {
  icon: string;
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function SettingsCard({ icon, title, subtitle, children }: SettingsCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.cardHeaderIcon} aria-hidden="true">
          {icon}
        </span>
        <div>
          <h3 className={styles.cardHeaderTitle}>{title}</h3>
          <p className={styles.cardHeaderSubtitle}>{subtitle}</p>
        </div>
      </div>
      {children}
    </div>
  );
}
