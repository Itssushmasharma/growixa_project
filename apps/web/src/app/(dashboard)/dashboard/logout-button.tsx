"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiFetch } from "@/lib/api-client";

import styles from "./topbar.module.css";

export function LogoutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleLogout() {
    setLoading(true);
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } finally {
      router.push("/login");
      router.refresh();
    }
  }

  return (
    <button type="button" className={styles.logoutButton} onClick={handleLogout} disabled={loading}>
      Log out
    </button>
  );
}
