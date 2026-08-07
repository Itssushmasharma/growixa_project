"use client";

import Link from "next/link";
import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./support-session-detail-page.module.css";
import type { SupportSessionContact, SupportSessionOverview } from "../types";

interface ContactEditState {
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
}

function toEditState(contact: SupportSessionContact): ContactEditState {
  return {
    email: contact.email,
    first_name: contact.first_name ?? "",
    last_name: contact.last_name ?? "",
    phone: contact.phone ?? "",
  };
}

export function SupportSessionDetailPage({ supportSessionId }: { supportSessionId: string }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [overview, setOverview] = useState<SupportSessionOverview | null>(null);
  const [ending, setEnding] = useState(false);
  const [editingContactId, setEditingContactId] = useState<string | null>(null);
  const [editState, setEditState] = useState<ContactEditState | null>(null);
  const [savingContact, setSavingContact] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<SupportSessionOverview>(
          `/platform/support-sessions/${supportSessionId}/overview`,
        );
        setOverview(data);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setLoadError("Support session not found.");
        } else if (err instanceof ApiError && err.status === 410) {
          setLoadError("This support session has ended or expired.");
        } else {
          setLoadError("Could not load this support session.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [supportSessionId]);

  async function handleEnd() {
    setEnding(true);
    try {
      await apiFetch(`/platform/support-sessions/${supportSessionId}/end`, { method: "POST" });
      showToast("success", "Support session ended.");
      setOverview((current) =>
        current
          ? { ...current, session: { ...current.session, ended_at: new Date().toISOString() } }
          : current,
      );
    } catch {
      showToast("error", "Could not end this support session.");
    } finally {
      setEnding(false);
    }
  }

  function startEditing(contact: SupportSessionContact) {
    setEditingContactId(contact.id);
    setEditState(toEditState(contact));
  }

  async function handleSaveContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingContactId || !editState) return;

    setSavingContact(true);
    try {
      const updated = await apiFetch<SupportSessionContact>(
        `/platform/support-sessions/${supportSessionId}/contacts/${editingContactId}`,
        { method: "PATCH", body: JSON.stringify(editState) },
      );
      setOverview((current) =>
        current
          ? {
              ...current,
              contacts: current.contacts.map((contact) =>
                contact.id === editingContactId ? updated : contact,
              ),
            }
          : current,
      );
      showToast("success", "Contact updated.");
      setEditingContactId(null);
      setEditState(null);
    } catch {
      showToast("error", "Could not update this contact.");
    } finally {
      setSavingContact(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError || !overview) {
    return <div className={styles.card}>{loadError ?? "Could not load this support session."}</div>;
  }

  const { session, company, contacts, audit_events: auditEvents } = overview;
  const isActive = session.ended_at === null && new Date(session.expires_at) > new Date();
  const canWrite = session.access_level === "WRITE";

  return (
    <>
      <Link href={`/platform/accounts/${session.account_id}`} className={styles.backLink}>
        ← Back to account
      </Link>

      <div className={styles.card}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.headerTitle}>{session.reason}</h2>
            <div className={styles.meta}>
              Ticket #{session.ticket_number} ·{" "}
              <span
                className={`${styles.accessBadge} ${
                  canWrite ? styles.accessWrite : styles.accessRead
                }`}
              >
                {session.access_level}
              </span>{" "}
              · {isActive ? `Expires ${new Date(session.expires_at).toLocaleString()}` : "Inactive"}
            </div>
          </div>
          {isActive && (
            <button
              type="button"
              className={styles.endButton}
              disabled={ending}
              onClick={handleEnd}
            >
              {ending ? "Ending…" : "End session"}
            </button>
          )}
        </div>
      </div>

      <div className={styles.card}>
        <h3 className={styles.sectionTitle}>Company</h3>
        {company ? (
          <div className={styles.meta}>
            {company.name}
            {company.website ? ` · ${company.website}` : ""}
            {company.industry ? ` · ${company.industry}` : ""}
          </div>
        ) : (
          <div className={styles.empty}>No company profile on file.</div>
        )}
      </div>

      <div className={styles.card}>
        <h3 className={styles.sectionTitle}>Contacts · {contacts.length}</h3>
        {contacts.length === 0 && <div className={styles.empty}>No contacts yet.</div>}
        {contacts.map((contact) => (
          <div className={styles.row} key={contact.id}>
            {editingContactId === contact.id && editState ? (
              <form onSubmit={handleSaveContact} className={styles.editForm}>
                <input
                  className={styles.editInput}
                  value={editState.first_name}
                  onChange={(event) =>
                    setEditState({ ...editState, first_name: event.target.value })
                  }
                  placeholder="First name"
                />
                <input
                  className={styles.editInput}
                  value={editState.last_name}
                  onChange={(event) =>
                    setEditState({ ...editState, last_name: event.target.value })
                  }
                  placeholder="Last name"
                />
                <input
                  className={styles.editInput}
                  value={editState.phone}
                  onChange={(event) => setEditState({ ...editState, phone: event.target.value })}
                  placeholder="Phone"
                />
                <button type="submit" className={styles.saveButton} disabled={savingContact}>
                  {savingContact ? "Saving…" : "Save"}
                </button>
                <button
                  type="button"
                  className={styles.cancelButton}
                  onClick={() => {
                    setEditingContactId(null);
                    setEditState(null);
                  }}
                >
                  Cancel
                </button>
              </form>
            ) : (
              <>
                <div className={styles.identity}>
                  <div className={styles.name}>
                    {[contact.first_name, contact.last_name].filter(Boolean).join(" ") ||
                      "(no name)"}
                  </div>
                  <div className={styles.email}>{contact.email}</div>
                </div>
                {isActive && canWrite && (
                  <button
                    type="button"
                    className={styles.editButton}
                    onClick={() => startEditing(contact)}
                  >
                    Edit
                  </button>
                )}
              </>
            )}
          </div>
        ))}
      </div>

      <div className={styles.card}>
        <h3 className={styles.sectionTitle}>Audit trail · {auditEvents.length}</h3>
        {auditEvents.length === 0 && <div className={styles.empty}>No activity recorded yet.</div>}
        {auditEvents.map((event) => (
          <div className={styles.activityRow} key={event.id}>
            <span className={styles.activityAction}>{event.action}</span>
            <span className={styles.activityTime}>
              {new Date(event.created_at).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}
