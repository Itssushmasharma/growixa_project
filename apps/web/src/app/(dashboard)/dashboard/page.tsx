import styles from "./page.module.css";

export default function DashboardPage() {
  return (
    <div className={styles.emptyState}>
      <h2 className={styles.heading}>Welcome to Growixa</h2>
      <p className={styles.body}>
        There&apos;s nothing here yet. Once you add contacts and campaigns, your growth metrics will
        show up on this dashboard.
      </p>
    </div>
  );
}
