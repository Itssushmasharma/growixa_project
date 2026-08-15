import styles from "./quota-gauge.module.css";

export interface QuotaGaugeProps {
  label: string;
  used: number;
  limit: number | null;
}

export function QuotaGauge({ label, used, limit }: QuotaGaugeProps) {
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const tone = limit === null ? "unlimited" : pct >= 90 ? "danger" : pct >= 70 ? "warning" : "ok";

  return (
    <div className={styles.gauge}>
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        <span className={styles.usage}>
          {limit === null
            ? `${used.toLocaleString()} (unlimited)`
            : `${used.toLocaleString()} / ${limit.toLocaleString()}`}
        </span>
      </div>
      <div className={styles.track}>
        <div
          className={`${styles.fill} ${styles[tone]}`}
          style={{ width: limit === null ? "100%" : `${pct}%` }}
        />
      </div>
    </div>
  );
}
