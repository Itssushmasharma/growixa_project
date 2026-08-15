import type { ReactNode } from "react";
import styles from "./stat-card.module.css";

export interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: "up" | "down" | "neutral";
  subtext?: string;
  icon?: ReactNode;
}

export function StatCard({
  label,
  value,
  trend,
  trendDirection = "up",
  subtext = "vs last month",
}: StatCardProps) {
  const trendClass =
    trendDirection === "up"
      ? styles.trendPositive
      : trendDirection === "down"
        ? styles.trendNegative
        : styles.trendNeutral;

  return (
    <div className={styles.statCard}>
      <span className={styles.label}>{label}</span>
      <div className={styles.valueRow}>
        <span className={styles.value}>{value}</span>
        {trend && (
          <span className={`${styles.trend} ${trendClass}`}>
            {trendDirection === "up" && "↑"}
            {trendDirection === "down" && "↓"}
            {trend}
          </span>
        )}
      </div>
      {subtext && <span className={styles.subtext}>{subtext}</span>}
    </div>
  );
}
