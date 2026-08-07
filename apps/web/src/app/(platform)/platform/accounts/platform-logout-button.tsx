"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiFetch } from "@/lib/api-client";

import styles from "./platform-shell.module.css";

export function PlatformLogoutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleLogout() {
    setLoading(true);
    try {
      await apiFetch("/platform/auth/logout", { method: "POST" });
    } finally {
      router.push("/platform/login");
      router.refresh();
    }
  }

  return (
    <button type="button" className={styles.logoutButton} onClick={handleLogout} disabled={loading}>
      Log out
    </button>
  );
}
