"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./account-detail-page.module.css";
import { BillingPanel } from "./billing-panel";
import { SupportSessionPanel } from "./support-session-panel";
import type { AccountDetail, AccountStatus } from "../types";

const STATUS_LABELS: Record<AccountStatus, string> = {
  ACTIVE: "Activate",
  SUSPENDED: "Suspend",
  CLOSED: "Close",
};

function statusBadgeClass(status: AccountStatus): string {
  if (status === "ACTIVE") return styles.statusActive ?? "";
  if (status === "SUSPENDED") return styles.statusSuspended ?? "";
  return styles.statusClosed ?? "";
}

export function AccountDetailPage({ accountId }: { accountId: string }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [account, setAccount] = useState<AccountDetail | null>(null);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const detail = await apiFetch<AccountDetail>(`/platform/accounts/${accountId}`);
        setAccount(detail);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to manage accounts.");
        } else if (err instanceof ApiError && err.status === 404) {
          setLoadError("Account not found.");
        } else {
          setLoadError("Could not load this account.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [accountId]);

  async function handleStatusChange(status: AccountStatus) {
    setUpdating(true);
    try {
      await apiFetch(`/platform/accounts/${accountId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      const detail = await apiFetch<AccountDetail>(`/platform/accounts/${accountId}`);
      setAccount(detail);
      showToast("success", `Account ${status.toLowerCase()}.`);
    } catch {
      showToast("error", "Could not change this account's status.");
    } finally {
      setUpdating(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError || !account) {
    return <div className={styles.card}>{loadError ?? "Could not load this account."}</div>;
  }

  return (
    <>
      <Link href="/platform/accounts" className={styles.backLink}>
        ← All accounts
      </Link>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>{account.name}</h2>
          <div className={styles.statusActions}>
            {(["ACTIVE", "SUSPENDED", "CLOSED"] as const).map((status) => (
              <button
                key={status}
                type="button"
                className={styles.statusButton}
                disabled={updating || account.status === status}
                onClick={() => handleStatusChange(status)}
              >
                {STATUS_LABELS[status]}
              </button>
            ))}
          </div>
        </div>
        <div className={styles.meta}>
          <span className={`${styles.statusBadge} ${statusBadgeClass(account.status)}`}>
            {account.status}
          </span>
          {" · "}
          {account.selected_plan_slug ?? "no plan"} · created{" "}
          {new Date(account.created_at).toLocaleDateString()}
        </div>
      </div>

      <div className={styles.card}>
        <h3 className={styles.sectionTitle}>Users · {account.users.length}</h3>
        {account.users.length === 0 && <div className={styles.empty}>No users yet.</div>}
        {account.users.map((user) => (
          <div className={styles.row} key={user.id}>
            <div className={styles.identity}>
              <div className={styles.name}>{user.full_name}</div>
              <div className={styles.email}>{user.email}</div>
            </div>
            <span
              className={`${styles.statusBadge} ${
                user.status === "ACTIVE" ? styles.statusActive : styles.statusClosed
              }`}
            >
              {user.status}
            </span>
          </div>
        ))}
      </div>

      <div className={styles.card}>
        <h3 className={styles.sectionTitle}>
          Login &amp; security activity · {account.security_activity.length}
        </h3>
        {account.security_activity.length === 0 && (
          <div className={styles.empty}>No activity recorded yet.</div>
        )}
        {account.security_activity.map((event) => (
          <div className={styles.activityRow} key={event.id}>
            <span className={styles.activityAction}>{event.action}</span>
            <span className={styles.activityTime}>
              {new Date(event.created_at).toLocaleString()}
            </span>
          </div>
        ))}
      </div>

      <BillingPanel accountId={accountId} />

      <SupportSessionPanel accountId={accountId} />
    </>
  );
}
