"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./accounts-page.module.css";
import type { AccountListItem } from "./types";

function statusBadgeClass(status: AccountListItem["status"]): string {
  if (status === "ACTIVE") return styles.statusActive ?? "";
  if (status === "SUSPENDED") return styles.statusSuspended ?? "";
  return styles.statusClosed ?? "";
}

export function AccountsPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<AccountListItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const list = await apiFetch<AccountListItem[]>("/platform/accounts");
        setAccounts(list);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to manage accounts.");
        } else {
          setLoadError("Could not load accounts.");
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
      <h2 className={styles.headerTitle}>
        Accounts <span className={styles.headerCount}>· {accounts.length} total</span>
      </h2>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Plan</th>
            <th>Users</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((account) => (
            <tr key={account.id}>
              <td>
                <Link href={`/platform/accounts/${account.id}`} className={styles.nameLink}>
                  {account.name}
                </Link>
              </td>
              <td>
                <span className={`${styles.statusBadge} ${statusBadgeClass(account.status)}`}>
                  {account.status}
                </span>
              </td>
              <td className={styles.planCell}>{account.selected_plan_slug ?? "—"}</td>
              <td>{account.user_count}</td>
              <td>{new Date(account.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
