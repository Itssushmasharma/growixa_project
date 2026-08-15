"use client";

import { type ChangeEvent, type FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";
import { getApiUrl } from "@/lib/env";

import styles from "../shared.module.css";
import type { Contact, MeResponse, SuppressionEntry, SuppressionImportResult } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

interface SuppressionFormState {
  email: string;
  reason: "UNSUBSCRIBED" | "BOUNCED" | "COMPLAINED" | "MANUAL";
  contact_id: string;
}

const EMPTY_FORM: SuppressionFormState = {
  email: "",
  reason: "UNSUBSCRIBED",
  contact_id: "",
};

export function SuppressionPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [entries, setEntries] = useState<SuppressionEntry[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState<SuppressionFormState>(EMPTY_FORM);
  const [adding, setAdding] = useState(false);

  const [showDomainModal, setShowDomainModal] = useState(false);
  const [domainInput, setDomainInput] = useState("");
  const [blockingDomain, setBlockingDomain] = useState(false);

  const [removePendingId, setRemovePendingId] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const visibleEntries = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return entries;
    return entries.filter((e) => (e.email ?? e.domain ?? "").toLowerCase().includes(q));
  }, [entries, search]);

  const metrics = useMemo(() => {
    const total = entries.length;
    const unsubscribed = entries.filter((e) => e.reason === "UNSUBSCRIBED").length;
    const bounced = entries.filter((e) => e.reason === "BOUNCED").length;
    const complained = entries.filter((e) => e.reason === "COMPLAINED").length;
    return { total, unsubscribed, bounced, complained };
  }, [entries]);

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
      setShowAddModal(false);
      setAddForm(EMPTY_FORM);
      showToast("success", "Email suppressed.");
    } catch {
      showToast("error", "Could not suppress email.");
    } finally {
      setAdding(false);
    }
  }

  async function handleBlockDomainSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBlockingDomain(true);

    try {
      const entry = await apiFetch<SuppressionEntry>("/contacts/suppression/domains", {
        method: "POST",
        body: JSON.stringify({ domain: domainInput }),
      });
      setEntries((current) => [entry, ...current.filter((e) => e.id !== entry.id)]);
      setShowDomainModal(false);
      setDomainInput("");
      showToast("success", `Domain "${entry.domain}" blocked.`);
    } catch {
      showToast("error", "Could not block domain.");
    } finally {
      setBlockingDomain(false);
    }
  }

  async function handleRemove(id: string) {
    setRemovePendingId(id);
    try {
      await apiFetch(`/contacts/suppression/${id}`, { method: "DELETE" });
      setEntries((current) => current.filter((e) => e.id !== id));
      showToast("success", "Suppression removed.");
    } catch {
      showToast("error", "Could not remove suppression.");
    } finally {
      setRemovePendingId(null);
    }
  }

  async function handleImportFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setImporting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await apiFetch<SuppressionImportResult>("/contacts/suppression/import", {
        method: "POST",
        body: formData,
      });
      const refreshed = await apiFetch<SuppressionEntry[]>("/contacts/suppression");
      setEntries(refreshed);
      showToast(
        "success",
        `Imported ${result.created} new suppression${result.created === 1 ? "" : "s"} (${result.skipped} already suppressed, ${result.total_rows} rows read).`,
      );
    } catch {
      showToast("error", 'Could not import CSV — check it has an "email" column.');
    } finally {
      setImporting(false);
    }
  }

  async function handleExport() {
    setExporting(true);
    try {
      const response = await fetch(`${getApiUrl()}/contacts/suppression/export`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("export failed");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "suppression-list.csv";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      showToast("error", "Could not export suppression list.");
    } finally {
      setExporting(false);
    }
  }

  function getMatchingContactName(contactId: string | null): string {
    if (!contactId) return "No matching contact";
    const contact = contacts.find((c) => c.id === contactId);
    if (!contact) return "No matching contact";
    const name = [contact.first_name, contact.last_name].filter(Boolean).join(" ");
    return name ? `${name} (${contact.email})` : contact.email;
  }

  if (loading) {
    return <div className={styles.card}>Loading suppression list…</div>;
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
    <div>
      {/* Metric Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Suppressed</div>
          <div className={styles.metricValue}>{metrics.total}</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Unsubscribed</div>
          <div className={styles.metricValue} style={{ color: "#d97706" }}>
            {metrics.unsubscribed}
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Bounced</div>
          <div className={styles.metricValue} style={{ color: "var(--color-error)" }}>
            {metrics.bounced}
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Complained</div>
          <div className={styles.metricValue} style={{ color: "var(--color-purple)" }}>
            {metrics.complained}
          </div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>
            Suppression list <span className={styles.headerCount}>· {visibleEntries.length}</span>
          </h2>
          {canManage && (
            <div style={{ display: "flex", gap: 8 }}>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                style={{ display: "none" }}
                onChange={handleImportFile}
              />
              <button
                type="button"
                className={styles.viewButton}
                disabled={importing}
                onClick={() => fileInputRef.current?.click()}
              >
                {importing ? "Importing…" : "Import CSV"}
              </button>
              <button
                type="button"
                className={styles.viewButton}
                disabled={exporting || entries.length === 0}
                onClick={handleExport}
              >
                {exporting ? "Exporting…" : "Export CSV"}
              </button>
              <button
                type="button"
                className={styles.viewButton}
                onClick={() => setShowDomainModal(true)}
              >
                + Block a domain
              </button>
              <button
                type="button"
                className={styles.addButton}
                onClick={() => setShowAddModal(true)}
              >
                + Suppress an email
              </button>
            </div>
          )}
        </div>

        {/* Search Toolbar */}
        <div className={styles.toolbar}>
          <div className={styles.searchGroup}>
            <input
              type="text"
              placeholder="Search suppressed email or domain..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={styles.searchInput}
            />
          </div>
        </div>

        {entries.length === 0 ? (
          <div className={styles.emptyState}>No suppressed emails yet.</div>
        ) : visibleEntries.length === 0 ? (
          <div className={styles.emptyState}>No suppressed emails match your search.</div>
        ) : (
          <div>
            {/* Table Header Row */}
            <div className={styles.tableHeader}>
              <div>Email / Domain</div>
              <div>Reason</div>
              <div>Matching Contact</div>
              <div>Suppressed At</div>
              <div style={{ textAlign: "right" }}>Actions</div>
            </div>

            {visibleEntries.map((entry) => {
              const isDomain = entry.email === null;
              return (
                <div key={entry.id} className={styles.contactBlock}>
                  <div className={styles.row}>
                    <div className={styles.name}>
                      {isDomain ? `*@${entry.domain}` : entry.email}
                    </div>
                    <div>
                      <span
                        className={`${styles.statusBadge} ${
                          entry.reason === "UNSUBSCRIBED"
                            ? styles.statusUnsubscribed
                            : styles.statusBounced
                        }`}
                      >
                        {isDomain ? "DOMAIN BLOCK" : entry.reason}
                      </span>
                    </div>
                    <div className={styles.description}>
                      {isDomain ? "—" : getMatchingContactName(entry.contact_id)}
                    </div>
                    <div className={styles.description}>
                      {new Date(entry.suppressed_at).toLocaleString()}
                    </div>
                    <div className={styles.rowActions}>
                      {canManage && (
                        <button
                          type="button"
                          disabled={removePendingId === entry.id}
                          className={styles.viewButton}
                          onClick={() => handleRemove(entry.id)}
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Suppress Email Modal */}
      {showAddModal && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowAddModal(false);
          }}
        >
          <div className={styles.modalContent} style={{ maxWidth: 540 }}>
            <div className={styles.modalHeader}>
              <h3 className={styles.name} style={{ fontSize: 18, margin: 0 }}>
                Suppress Email Address
              </h3>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={() => setShowAddModal(false)}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>
            <form onSubmit={handleAddSubmit}>
              <div className={styles.createField} style={{ marginBottom: 16 }}>
                <label className={styles.label} htmlFor="suppress-email">
                  Email
                </label>
                <input
                  id="suppress-email"
                  type="email"
                  required
                  className={styles.input}
                  value={addForm.email}
                  onChange={(e) => setAddForm({ ...addForm, email: e.target.value })}
                />
              </div>

              <div className={styles.createField} style={{ marginBottom: 16 }}>
                <label className={styles.label} htmlFor="suppress-reason">
                  Reason
                </label>
                <select
                  id="suppress-reason"
                  className={styles.select}
                  style={{ width: "100%" }}
                  value={addForm.reason}
                  onChange={(e) =>
                    setAddForm({
                      ...addForm,
                      reason: e.target.value as SuppressionFormState["reason"],
                    })
                  }
                >
                  <option value="UNSUBSCRIBED">Unsubscribed</option>
                  <option value="BOUNCED">Bounced</option>
                  <option value="COMPLAINED">Complained</option>
                  <option value="MANUAL">Manual</option>
                </select>
              </div>

              <div className={styles.createField} style={{ marginBottom: 24 }}>
                <label className={styles.label} htmlFor="suppress-contact">
                  Matching Contact (optional)
                </label>
                <select
                  id="suppress-contact"
                  className={styles.select}
                  style={{ width: "100%" }}
                  value={addForm.contact_id}
                  onChange={(e) => setAddForm({ ...addForm, contact_id: e.target.value })}
                >
                  <option value="">No matching contact</option>
                  {contacts.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.email}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className={styles.modalCloseButton}
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" disabled={adding} className={styles.submit}>
                  {adding ? "Suppressing..." : "Suppress email"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Block Domain Modal */}
      {showDomainModal && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowDomainModal(false);
          }}
        >
          <div className={styles.modalContent} style={{ maxWidth: 480 }}>
            <div className={styles.modalHeader}>
              <h3 className={styles.name} style={{ fontSize: 18, margin: 0 }}>
                Block a Domain
              </h3>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={() => setShowDomainModal(false)}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>
            <form onSubmit={handleBlockDomainSubmit}>
              <div className={styles.createField} style={{ marginBottom: 24 }}>
                <label className={styles.label} htmlFor="block-domain">
                  Domain
                </label>
                <input
                  id="block-domain"
                  type="text"
                  required
                  placeholder="competitor.com"
                  className={styles.input}
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                />
                <p style={{ fontSize: 12.5, color: "var(--color-slate)", marginTop: 6 }}>
                  Blocks every address at this domain from future sends — e.g. entering{" "}
                  <code>competitor.com</code> blocks anyone@competitor.com.
                </p>
              </div>

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className={styles.modalCloseButton}
                  onClick={() => setShowDomainModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" disabled={blockingDomain} className={styles.submit}>
                  {blockingDomain ? "Blocking..." : "Block domain"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
