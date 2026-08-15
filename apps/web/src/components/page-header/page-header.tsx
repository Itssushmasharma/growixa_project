import type { ReactNode } from "react";
import styles from "./page-header.module.css";

export interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: string | ReactNode;
  badge?: string;
  actions?: ReactNode;
}

export function PageHeader({
  title,
  description,
  icon,
  badge,
  actions,
}: PageHeaderProps) {
  return (
    <div className={styles.pageHeader}>
      <div className={styles.titleArea}>
        <div className={styles.titleRow}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <h1 className={styles.title}>{title}</h1>
          {badge && <span className={styles.badge}>{badge}</span>}
        </div>
        {description && <p className={styles.description}>{description}</p>}
      </div>
      {actions && <div className={styles.actionsArea}>{actions}</div>}
    </div>
  );
}
