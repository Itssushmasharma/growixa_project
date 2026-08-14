import styles from "./metric-card.module.css";

export interface MetricCardProps {
  label: string;
  value: string | number;
  delta?: string;
  deltaTone?: "positive" | "negative" | "neutral";
  hint?: string;
}

export function MetricCard({ label, value, delta, deltaTone = "neutral", hint }: MetricCardProps) {
  return (
    <div className={styles.card}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{value}</div>
      {delta && <div className={`${styles.delta} ${styles[deltaTone]}`}>{delta}</div>}
      {hint && <div className={styles.hint}>{hint}</div>}
    </div>
  );
}
