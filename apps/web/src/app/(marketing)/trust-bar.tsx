import styles from "./marketing.module.css";

export function TrustBar() {
  return (
    <section className={styles.trustBar}>
      <div className={styles.trustGrid}>
        <div>
          <div className={styles.trustNumber}>1,000+</div>
          <div className={styles.trustLabel}>Businesses Growing</div>
        </div>
        <div>
          <div className={styles.trustNumber}>50M+</div>
          <div className={styles.trustLabel}>Emails Delivered</div>
        </div>
        <div>
          <div className={styles.trustNumber}>12M+</div>
          <div className={styles.trustLabel}>AI Copy Generations</div>
        </div>
        <div>
          <div className={styles.trustNumber}>99.99%</div>
          <div className={styles.trustLabel}>Guaranteed Uptime</div>
        </div>
      </div>
    </section>
  );
}
