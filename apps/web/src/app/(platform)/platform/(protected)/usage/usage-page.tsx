"use client";

import { useEffect, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./usage-page.module.css";
import type { UsageSummaryItem } from "./types";

export function UsagePage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [items, setItems] = useState<UsageSummaryItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const list = await apiFetch<UsageSummaryItem[]>("/platform/usage");
        setItems(list);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to view usage.");
        } else {
          setLoadError("Could not load usage data.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.headerTitle}>Usage by account</h2>
      {items.length === 0 && <div className={styles.empty}>No usage recorded yet.</div>}
      {items.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Account</th>
              <th>Operation</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={`${item.account_id}:${item.operation_type}`}>
                <td className={styles.accountCell}>{item.account_name}</td>
                <td className={styles.operationCell}>{item.operation_type}</td>
                <td>
                  {item.total_quantity} {item.unit}
                  {item.total_quantity === 1 ? "" : "s"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
