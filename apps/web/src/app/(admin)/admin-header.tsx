"use client";

import Link from "next/link";
import { LogoutButton } from "../(dashboard)/dashboard/logout-button";
import styles from "./admin-header.module.css";

export function AdminHeader({ fullName }: { fullName: string }) {
  return (
    <header className={styles.header}>
      <div className={styles.brandArea}>
        <div className={styles.brand}>
          <span>Growixa</span>
          <span className={styles.badge}>Admin</span>
        </div>
        <Link href="/dashboard" className={styles.backLink}>
          &larr; Back to Dashboard
        </Link>
      </div>
      <div className={styles.userArea}>
        <span className={styles.userName}>{fullName}</span>
        <LogoutButton />
      </div>
    </header>
  );
}
