"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import styles from "./auth.module.css";

interface AuthTabsProps {
  activeTab: "login" | "register";
}

export function AuthTabs({ activeTab }: AuthTabsProps) {
  const searchParams = useSearchParams();
  const next = searchParams.get("next");
  const query = next ? `?next=${encodeURIComponent(next)}` : "";

  return (
    <div className={styles.tabContainer} role="tablist" aria-label="Authentication mode">
      <Link
        href={`/login${query}`}
        role="tab"
        aria-selected={activeTab === "login"}
        className={`${styles.tab} ${activeTab === "login" ? styles.tabActive : ""}`}
      >
        <span>Login</span>
        {activeTab === "login" && <span className={styles.tabIndicator} />}
      </Link>
      <Link
        href={`/register${query}`}
        role="tab"
        aria-selected={activeTab === "register"}
        className={`${styles.tab} ${activeTab === "register" ? styles.tabActive : ""}`}
      >
        <span>Sign up</span>
        {activeTab === "register" && <span className={styles.tabIndicator} />}
      </Link>
    </div>
  );
}
