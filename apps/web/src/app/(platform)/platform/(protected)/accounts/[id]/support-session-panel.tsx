"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { SupportSession, SupportSessionAccessLevel } from "../types";
import styles from "./support-session-panel.module.css";

const WRITE_PERMISSION = "platform.support_session.write";

function isActive(session: SupportSession): boolean {
  return session.ended_at === null && new Date(session.expires_at) > new Date();
}

export function SupportSessionPanel({ accountId }: { accountId: string }) {
  const router = useRouter();
  const { showToast } = useToast();
  const [sessions, setSessions] = useState<SupportSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [canWrite, setCanWrite] = useState(false);
  const [reason, setReason] = useState("");
  const [ticketNumber, setTicketNumber] = useState("");
  const [accessLevel, setAccessLevel] = useState<SupportSessionAccessLevel>("READ");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [history, me] = await Promise.all([
          apiFetch<SupportSession[]>(`/platform/accounts/${accountId}/support-sessions`),
          apiFetch<{ permissions: string[] }>("/platform/auth/me"),
        ]);
        setSessions(history);
        setCanWrite(me.permissions.includes(WRITE_PERMISSION));
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [accountId]);

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStarting(true);
    try {
      const session = await apiFetch<SupportSession>(
        `/platform/accounts/${accountId}/support-sessions`,
        {
          method: "POST",
          body: JSON.stringify({
            reason,
            ticket_number: ticketNumber,
            access_level: accessLevel,
          }),
        },
      );
      router.push(`/platform/support-sessions/${session.id}`);
    } catch {
      showToast("error", "Could not start a support session.");
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className={styles.card}>
      <h3 className={styles.sectionTitle}>Support sessions</h3>

      <form onSubmit={handleStart} className={styles.form}>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="support-session-reason">
            Reason
          </label>
          <input
            id="support-session-reason"
            className={styles.input}
            required
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="e.g. Investigating a delivery issue reported by the customer"
          />
        </div>
        <div className={styles.field}>
          <label className={styles.label} htmlFor="support-session-ticket">
            Ticket number
          </label>
          <input
            id="support-session-ticket"
            className={styles.input}
            required
            value={ticketNumber}
            onChange={(event) => setTicketNumber(event.target.value)}
            placeholder="e.g. SUP-1234"
          />
        </div>
        <div className={styles.field}>
          <span className={styles.label}>Access</span>
          <div className={styles.radioGroup}>
            <label className={styles.radioLabel}>
              <input
                type="radio"
                name="access-level"
                checked={accessLevel === "READ"}
                onChange={() => setAccessLevel("READ")}
              />
              Read-only
            </label>
            {canWrite && (
              <label className={styles.radioLabel}>
                <input
                  type="radio"
                  name="access-level"
                  checked={accessLevel === "WRITE"}
                  onChange={() => setAccessLevel("WRITE")}
                />
                Read &amp; write
              </label>
            )}
          </div>
        </div>
        <button type="submit" className={styles.submitButton} disabled={starting}>
          {starting ? "Starting…" : "Start support session"}
        </button>
      </form>

      <div className={styles.history}>
        {loading && <div className={styles.empty}>Loading…</div>}
        {!loading && sessions.length === 0 && (
          <div className={styles.empty}>No support sessions yet.</div>
        )}
        {!loading &&
          sessions.map((session) => {
            const active = isActive(session);
            const row = (
              <div className={styles.historyRow}>
                <div className={styles.historyMain}>
                  <span className={styles.historyReason}>{session.reason}</span>
                  <span className={styles.historyTicket}>#{session.ticket_number}</span>
                </div>
                <span
                  className={`${styles.accessBadge} ${
                    session.access_level === "WRITE" ? styles.accessWrite : styles.accessRead
                  }`}
                >
                  {session.access_level}
                </span>
                <span className={styles.historyStatus}>
                  {active ? "Active" : session.ended_at ? "Ended" : "Expired"}
                </span>
              </div>
            );
            return active ? (
              <Link
                key={session.id}
                href={`/platform/support-sessions/${session.id}`}
                className={styles.historyLink}
              >
                {row}
              </Link>
            ) : (
              <div key={session.id}>{row}</div>
            );
          })}
      </div>
    </div>
  );
}
