"use client";

import { useEffect, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./monitoring-page.module.css";
import type { QueueDepths } from "./types";

export function MonitoringPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [queues, setQueues] = useState<Record<string, number | string>>({});

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<QueueDepths>("/platform/monitoring/queues");
        setQueues(data.queues);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to view infra monitoring.");
        } else {
          setLoadError("Could not load queue depths.");
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

  const entries = Object.entries(queues);

  return (
    <div className={styles.card}>
      <h2 className={styles.headerTitle}>RabbitMQ queue depths</h2>
      {entries.length === 0 && <div className={styles.empty}>No queues to report.</div>}
      {entries.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Queue</th>
              <th>Depth</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, depth]) => {
              const isDlq = name.endsWith(".dlq");
              const isNumeric = typeof depth === "number";
              const isBacklogged = isNumeric && depth > 0;
              return (
                <tr key={name}>
                  <td className={styles.queueCell}>
                    {name}
                    {isDlq && <span className={styles.dlqPill}>DLQ</span>}
                  </td>
                  <td
                    className={
                      isBacklogged ? (isDlq ? styles.depthDlqAlert : styles.depthAlert) : undefined
                    }
                  >
                    {isNumeric ? depth : <span className={styles.notDeclared}>{depth}</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
