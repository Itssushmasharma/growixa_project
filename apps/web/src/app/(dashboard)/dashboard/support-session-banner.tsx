"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import styles from "./support-session-banner.module.css";

interface SupportSessionStatus {
  active: boolean;
  started_at: string | null;
  reason: string | null;
}

const POLL_INTERVAL_MS = 30_000;

export function SupportSessionBanner() {
  const [status, setStatus] = useState<SupportSessionStatus | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const data = await apiFetch<SupportSessionStatus>("/accounts/support-session-status");
        if (!cancelled) setStatus(data);
      } catch {
        // Transient errors don't clear an already-shown banner -- a brief network
        // hiccup shouldn't make an active support session appear to vanish.
      }
    }

    void poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (!status?.active) return null;

  return (
    <div className={styles.banner} role="status">
      <span className={styles.icon} aria-hidden="true">
        🛟
      </span>
      Growixa support currently has view access to this account
      {status.reason ? `: ${status.reason}` : "."}
    </div>
  );
}
