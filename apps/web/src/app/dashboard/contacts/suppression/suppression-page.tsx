"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
import type { Contact, MeResponse, SuppressionEntry } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

const REASON_OPTIONS = [
  { value: "UNSUBSCRIBED", label: "Unsubscribed" },
  { value: "BOUNCED", label: "Bounced" },
  { value: "COMPLAINED", label: "Complained" },
  { value: "MANUAL", label: "Manual" },
];

interface AddFormState {
  email: string;
  reason: string;
  contact_id: string;
}

const EMPTY_FORM: AddFormState = { email: "", reason: "UNSUBSCRIBED", contact_id: "" };

export function SuppressionPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [entries, setEntries] = useState<SuppressionEntry[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState<AddFormState>(EMPTY_FORM);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [me, entryList, contactList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<SuppressionEntry[]>("/contacts/suppression"),
          apiFetch<Contact[]>("/contacts"),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setEntries(entryList);
        setContacts(contactList);
      } catch {
        setLoadError("Could not load the suppression list.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleAddSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAdding(true);

    try {
      const entry = await apiFetch<SuppressionEntry>("/contacts/suppression", {
        method: "POST",
        body: JSON.stringify({
          email: addForm.email,
          reason: addForm.reason,
          contact_id: addForm.contact_id || null,
        }),
      });
      setEntries((current) => {
        const existingIndex = current.findIndex((e) => e.id === entry.id);
        if (existingIndex >= 0) {
          const updated = [...current];
          updated[existingIndex] = entry;
          return updated;
        }
        return [entry, ...current];
      });
      setShowAddForm(false);
      setAddForm(EMPTY_FORM);
      showToast("success", "Email suppressed.");
    } catch {
      showToast("error", "Could not suppress that email.");
    } finally {
      setAdding(false);
    }
  }

  function contactEmailFor(contactId: string | null): string {
    if (!contactId) return "No matching contact";
    return contacts.find((c) => c.id === contactId)?.email ?? contactId;
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return (
      <div className={styles.card}>You don&apos;t have access to view the suppression list.</div>
    );
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Suppression list <span className={styles.headerCount}>· {entries.length}</span>
        </h2>
        {canManage && !showAddForm && (
          <button type="button" className={styles.addButton} onClick={() => setShowAddForm(true)}>
            + Suppress an email
          </button>
        )}
      </div>

      {showAddForm && (
        <form className={styles.createForm} onSubmit={handleAddSubmit}>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="suppress-email">
              Email
            </label>
            <input
              id="suppress-email"
              type="email"
              required
              className={styles.input}
              value={addForm.email}
              onChange={(event) => setAddForm({ ...addForm, email: event.target.value })}
            />
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="suppress-reason">
              Reason
            </label>
            <select
              id="suppress-reason"
              className={styles.select}
              value={addForm.reason}
              onChange={(event) => setAddForm({ ...addForm, reason: event.target.value })}
            >
              {REASON_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="suppress-contact">
              Matching contact (optional)
            </label>
            <select
              id="suppress-contact"
              className={styles.select}
              value={addForm.contact_id}
              onChange={(event) => setAddForm({ ...addForm, contact_id: event.target.value })}
            >
              <option value="">No matching contact</option>
              {contacts.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.email}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className={styles.submit} disabled={adding}>
            {adding ? "Suppressing…" : "Suppress email"}
          </button>
          <button type="button" className={styles.cancel} onClick={() => setShowAddForm(false)}>
            Cancel
          </button>
        </form>
      )}

      {entries.length === 0 && <p className={styles.emptyState}>No suppressed emails yet.</p>}

      {entries.map((entry) => (
        <div className={styles.row} key={entry.id}>
          <div className={styles.identity}>
            <div className={styles.name}>{entry.email}</div>
            <div className={styles.description}>
              {contactEmailFor(entry.contact_id)} · {new Date(entry.suppressed_at).toLocaleString()}
            </div>
          </div>
          <div className={styles.rowActions}>
            <span className={styles.typeBadge}>{entry.reason}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
