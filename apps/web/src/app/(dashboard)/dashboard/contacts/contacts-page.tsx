"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./shared.module.css";
import type { ConsentRecord, Contact, MeResponse, Tag } from "./types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

interface ContactFormState {
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  source: string;
}

const EMPTY_FORM: ContactFormState = {
  email: "",
  first_name: "",
  last_name: "",
  phone: "",
  source: "",
};

interface ConsentFormState {
  channel: "EMAIL" | "SMS";
  status: "GRANTED" | "WITHDRAWN" | "UNKNOWN";
  source: string;
}

const EMPTY_CONSENT_FORM: ConsentFormState = {
  channel: "EMAIL",
  status: "GRANTED",
  source: "",
};

function displayName(contact: Contact): string {
  const name = [contact.first_name, contact.last_name].filter(Boolean).join(" ");
  return name || "—";
}

function initialsFor(contact: Contact): string {
  const source = displayName(contact) !== "—" ? displayName(contact) : contact.email;
  return source
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function capitalize(value: string): string {
  return value ? value.charAt(0).toUpperCase() + value.slice(1).toLowerCase() : "";
}

function getTagInfo(tag: Tag | string): { id: string; name: string } {
  if (typeof tag === "object" && tag !== null) {
    return { id: tag.id, name: tag.name };
  }
  return { id: String(tag), name: String(tag) };
}

function resolveTagId(tagItem: Tag | string, tagList: Tag[]): string {
  if (typeof tagItem === "object" && tagItem !== null) {
    return tagItem.id;
  }
  const match = tagList.find((t) => t.name === tagItem || t.id === tagItem);
  return match ? match.id : String(tagItem);
}

export function ContactsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<ContactFormState>(EMPTY_FORM);
  const [creating, setCreating] = useState(false);

  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [editForm, setEditForm] = useState<ContactFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [statusPendingId, setStatusPendingId] = useState<string | null>(null);

  const [attachTagId, setAttachTagId] = useState("");
  const [newTagName, setNewTagName] = useState("");
  const [tagActionPending, setTagActionPending] = useState(false);

  const [consentHistory, setConsentHistory] = useState<ConsentRecord[]>([]);
  const [consentLoading, setConsentLoading] = useState(false);
  const [consentForm, setConsentForm] = useState<ConsentFormState>(EMPTY_CONSENT_FORM);
  const [consentSubmitting, setConsentSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [me, contactList, tagList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<Contact[]>("/contacts"),
          apiFetch<Tag[]>("/contacts/tags"),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setContacts(contactList);
        setTags(tagList);
      } catch {
        setLoadError("Could not load contacts.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, statusFilter, pageSize]);

  const visibleContacts = useMemo(() => {
    const query = search.trim().toLowerCase();
    return contacts.filter((c) => {
      const matchesSearch =
        !query ||
        c.email.toLowerCase().includes(query) ||
        (c.first_name && c.first_name.toLowerCase().includes(query)) ||
        (c.last_name && c.last_name.toLowerCase().includes(query)) ||
        (c.source && c.source.toLowerCase().includes(query));
      const matchesStatus = statusFilter === "ALL" || c.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [contacts, search, statusFilter]);

  const totalPages = Math.ceil(visibleContacts.length / pageSize) || 1;
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, visibleContacts.length);
  const paginatedContacts = useMemo(() => {
    return visibleContacts.slice(startIndex, endIndex);
  }, [visibleContacts, startIndex, endIndex]);

  const metrics = useMemo(() => {
    return {
      total: contacts.length,
      active: contacts.filter((c) => c.status === "ACTIVE").length,
      suppressed: contacts.filter((c) => c.is_suppressed).length,
      archived: contacts.filter((c) => c.status === "ARCHIVED").length,
    };
  }, [contacts]);

  function handleExportCsv() {
    if (visibleContacts.length === 0) {
      showToast("error", "No contacts available to export.");
      return;
    }
    const csvHeaders = [
      "ID",
      "Email",
      "First Name",
      "Last Name",
      "Phone",
      "Status",
      "Source",
      "Created At",
    ];
    const csvRows = visibleContacts.map((c) => [
      c.id,
      `"${c.email.replace(/"/g, '""')}"`,
      `"${(c.first_name || "").replace(/"/g, '""')}"`,
      `"${(c.last_name || "").replace(/"/g, '""')}"`,
      `"${(c.phone || "").replace(/"/g, '""')}"`,
      c.status,
      `"${(c.source || "").replace(/"/g, '""')}"`,
      `"${new Date(c.created_at).toLocaleString()}"`,
    ]);
    const csvContent = [csvHeaders.join(","), ...csvRows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `growixa_contacts_export_${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("success", `Exported ${visibleContacts.length} contacts to CSV.`);
  }

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);

    try {
      const created = await apiFetch<Contact>("/contacts", {
        method: "POST",
        body: JSON.stringify({
          email: createForm.email,
          first_name: createForm.first_name || null,
          last_name: createForm.last_name || null,
          phone: createForm.phone || null,
          source: createForm.source || null,
        }),
      });
      setContacts((current) => [created, ...current]);
      setShowCreateForm(false);
      setCreateForm(EMPTY_FORM);
      showToast("success", "Contact created.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        showToast("error", "A contact with this email already exists.");
      } else {
        showToast("error", "Could not create the contact.");
      }
    } finally {
      setCreating(false);
    }
  }

  async function openContactModal(contact: Contact) {
    setSelectedContact(contact);
    setEditForm({
      email: contact.email,
      first_name: contact.first_name ?? "",
      last_name: contact.last_name ?? "",
      phone: contact.phone ?? "",
      source: contact.source ?? "",
    });
    setAttachTagId("");
    setNewTagName("");
    setConsentForm(EMPTY_CONSENT_FORM);

    setConsentLoading(true);
    try {
      const history = await apiFetch<ConsentRecord[]>(`/contacts/${contact.id}/consent`);
      setConsentHistory(history);
    } catch {
      setConsentHistory([]);
    } finally {
      setConsentLoading(false);
    }
  }

  function closeContactModal() {
    setSelectedContact(null);
  }

  async function handleSaveEdit(event: FormEvent<HTMLFormElement>, contactId: string) {
    event.preventDefault();
    setSaving(true);
    try {
      const updated = await apiFetch<Contact>(`/contacts/${contactId}`, {
        method: "PATCH",
        body: JSON.stringify({
          email: editForm.email,
          first_name: editForm.first_name || null,
          last_name: editForm.last_name || null,
          phone: editForm.phone || null,
          source: editForm.source || null,
        }),
      });
      setContacts((current) => current.map((c) => (c.id === contactId ? updated : c)));
      setSelectedContact(updated);
      showToast("success", "Contact updated.");
    } catch {
      showToast("error", "Could not update contact.");
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(contactId: string, nextStatus: "ACTIVE" | "ARCHIVED") {
    setStatusPendingId(contactId);
    try {
      const updated = await apiFetch<Contact>(`/contacts/${contactId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setContacts((current) => current.map((c) => (c.id === contactId ? updated : c)));
      setSelectedContact(updated);
      showToast("success", `Status changed to ${nextStatus}.`);
    } catch {
      showToast("error", "Could not change status.");
    } finally {
      setStatusPendingId(null);
    }
  }

  async function handleAttachExistingTag(contactId: string) {
    if (!attachTagId) return;
    setTagActionPending(true);
    try {
      const updated = await apiFetch<Contact>(`/contacts/${contactId}/tags`, {
        method: "POST",
        body: JSON.stringify({ tag_id: attachTagId }),
      });
      setContacts((current) => current.map((c) => (c.id === contactId ? updated : c)));
      setSelectedContact(updated);
      setAttachTagId("");
      showToast("success", "Tag attached.");
    } catch {
      showToast("error", "Could not attach tag.");
    } finally {
      setTagActionPending(false);
    }
  }

  async function handleCreateAndAttachTag(contactId: string) {
    if (!newTagName.trim()) return;
    setTagActionPending(true);
    try {
      const newTag = await apiFetch<Tag>("/contacts/tags", {
        method: "POST",
        body: JSON.stringify({ name: newTagName.trim() }),
      });
      setTags((current) => [...current, newTag]);
      const updated = await apiFetch<Contact>(`/contacts/${contactId}/tags`, {
        method: "POST",
        body: JSON.stringify({ tag_id: newTag.id }),
      });
      setContacts((current) => current.map((c) => (c.id === contactId ? updated : c)));
      setSelectedContact(updated);
      setNewTagName("");
      showToast("success", "Tag created and attached.");
    } catch {
      showToast("error", "Could not create tag.");
    } finally {
      setTagActionPending(false);
    }
  }

  async function handleDetachTag(contactId: string, tagItem: Tag | string) {
    const targetTagId = resolveTagId(tagItem, tags);
    setTagActionPending(true);
    try {
      const updated = await apiFetch<Contact>(`/contacts/${contactId}/tags/${targetTagId}`, {
        method: "DELETE",
      });
      setContacts((current) => current.map((c) => (c.id === contactId ? updated : c)));
      setSelectedContact(updated);
      showToast("success", "Tag removed.");
    } catch {
      showToast("error", "Could not remove tag.");
    } finally {
      setTagActionPending(false);
    }
  }

  async function handleRecordConsent(event: FormEvent<HTMLFormElement>, contactId: string) {
    event.preventDefault();
    setConsentSubmitting(true);
    try {
      const record = await apiFetch<ConsentRecord>(`/contacts/${contactId}/consent`, {
        method: "POST",
        body: JSON.stringify({
          channel: consentForm.channel,
          status: consentForm.status,
          source: consentForm.source || null,
        }),
      });
      setConsentHistory((current) => [record, ...current]);
      setConsentForm(EMPTY_CONSENT_FORM);
      showToast("success", "Consent recorded.");
    } catch {
      showToast("error", "Could not record consent.");
    } finally {
      setConsentSubmitting(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading contacts…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view contacts.</div>;
  }

  return (
    <div>
      {/* Metric Summary Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Contacts</div>
          <div className={styles.metricValue}>{metrics.total}</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Active Contacts</div>
          <div className={styles.metricValue} style={{ color: "var(--color-success)" }}>
            {metrics.active}
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Suppressed Contacts</div>
          <div className={styles.metricValue} style={{ color: "var(--color-error)" }}>
            {metrics.suppressed}
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Archived Contacts</div>
          <div className={styles.metricValue} style={{ color: "var(--color-slate)" }}>
            {metrics.archived}
          </div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>
            Contacts <span className={styles.headerCount}>· {visibleContacts.length}</span>
          </h2>
          {canManage && (
            <button
              type="button"
              className={styles.addButton}
              onClick={() => setShowCreateForm(!showCreateForm)}
            >
              {showCreateForm ? "Cancel" : "+ Add contact"}
            </button>
          )}
        </div>

        {/* Search & Filter Toolbar */}
        <div className={styles.toolbar}>
          <div className={styles.searchGroup}>
            <input
              type="text"
              placeholder="Search by name, email, or source..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className={styles.searchInput}
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className={styles.select}
              aria-label="Filter by status"
            >
              <option value="ALL">All Statuses</option>
              <option value="ACTIVE">Active Contacts</option>
              <option value="ARCHIVED">Archived Contacts</option>
            </select>
          </div>
          <div className={styles.actionGroup}>
            <button type="button" className={styles.exportButton} onClick={handleExportCsv}>
              📥 Export CSV
            </button>
          </div>
        </div>

        {showCreateForm && canManage && (
          <form className={styles.createForm} onSubmit={handleCreateSubmit}>
            <div className={styles.createField}>
              <label className={styles.label} htmlFor="create-email">
                Email
              </label>
              <input
                id="create-email"
                type="email"
                required
                className={styles.input}
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
              />
            </div>
            <div className={styles.createField}>
              <label className={styles.label} htmlFor="create-first-name">
                First name
              </label>
              <input
                id="create-first-name"
                type="text"
                className={styles.input}
                value={createForm.first_name}
                onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
              />
            </div>
            <div className={styles.createField}>
              <label className={styles.label} htmlFor="create-last-name">
                Last name
              </label>
              <input
                id="create-last-name"
                type="text"
                className={styles.input}
                value={createForm.last_name}
                onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
              />
            </div>
            <div className={styles.createField}>
              <label className={styles.label} htmlFor="create-phone">
                Phone
              </label>
              <input
                id="create-phone"
                type="text"
                className={styles.input}
                value={createForm.phone}
                onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
              />
            </div>
            <div className={styles.createField}>
              <label className={styles.label} htmlFor="create-source">
                Source
              </label>
              <input
                id="create-source"
                type="text"
                className={styles.input}
                value={createForm.source}
                onChange={(e) => setCreateForm({ ...createForm, source: e.target.value })}
              />
            </div>
            <button type="submit" disabled={creating} className={styles.submit}>
              {creating ? "Saving..." : "Create contact"}
            </button>
          </form>
        )}

        {contacts.length === 0 ? (
          <div className={styles.emptyState}>No contacts yet.</div>
        ) : visibleContacts.length === 0 ? (
          <div className={styles.emptyState}>No contacts match your criteria.</div>
        ) : (
          <div>
            <div className={styles.tableScrollContainer}>
              {/* Table Header Row */}
              <div className={styles.tableHeader}>
                <div>Contact</div>
                <div>Status</div>
                <div>Source</div>
                <div>Created</div>
                <div style={{ textAlign: "right" }}>Actions</div>
              </div>

              {paginatedContacts.map((contact) => {
                return (
                  <div key={contact.id} className={styles.contactBlock}>
                    <div className={styles.row}>
                      <div className={styles.identity}>
                        <div className={styles.avatar}>{initialsFor(contact)}</div>
                        <div>
                          <div className={styles.name}>{displayName(contact)}</div>
                          <div className={styles.email}>{contact.email}</div>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        <span
                          className={`${styles.statusBadge} ${
                            contact.status === "ACTIVE"
                              ? styles.statusActive
                              : styles.statusArchived
                          }`}
                        >
                          {capitalize(contact.status)}
                        </span>
                        {contact.is_suppressed && (
                          <span className={styles.suppressedBadge}>Suppressed</span>
                        )}
                      </div>
                      <div className={styles.description}>{contact.source || "—"}</div>
                      <div className={styles.description}>
                        {new Date(contact.created_at).toLocaleDateString()}
                      </div>
                      <div className={styles.rowActions}>
                        <button
                          type="button"
                          className={styles.viewButton}
                          onClick={() => openContactModal(contact)}
                        >
                          View
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Pagination Controls Bar */}
            {visibleContacts.length > 0 && (
              <div className={styles.paginationBar}>
                <div className={styles.paginationInfo}>
                  Showing <strong>{visibleContacts.length > 0 ? startIndex + 1 : 0}</strong>–
                  <strong>{endIndex}</strong> of{" "}
                  <strong>{visibleContacts.length.toLocaleString()}</strong> contacts
                </div>

                <div className={styles.paginationControls}>
                  <label
                    htmlFor="contacts-page-size"
                    className={styles.paginationInfo}
                    style={{ marginRight: 4 }}
                  >
                    Per page:
                  </label>
                  <select
                    id="contacts-page-size"
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    className={styles.pageSizeSelect}
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>

                  <button
                    type="button"
                    disabled={safeCurrentPage <= 1}
                    onClick={() => setCurrentPage(1)}
                    className={styles.paginationButton}
                    title="First page"
                  >
                    ⏮
                  </button>

                  <button
                    type="button"
                    disabled={safeCurrentPage <= 1}
                    onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                    className={styles.paginationButton}
                  >
                    ◀ Prev
                  </button>

                  <span className={styles.paginationInfo} style={{ margin: "0 6px" }}>
                    Page <strong>{safeCurrentPage}</strong> of <strong>{totalPages}</strong>
                  </span>

                  <button
                    type="button"
                    disabled={safeCurrentPage >= totalPages}
                    onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                    className={styles.paginationButton}
                  >
                    Next ▶
                  </button>

                  <button
                    type="button"
                    disabled={safeCurrentPage >= totalPages}
                    onClick={() => setCurrentPage(totalPages)}
                    className={styles.paginationButton}
                    title="Last page"
                  >
                    ⏭
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Contact Details & Edit Modal Overlay */}
      {selectedContact && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeContactModal();
          }}
        >
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <div className={styles.identity}>
                <div className={styles.avatar} style={{ width: 44, height: 44, fontSize: 16 }}>
                  {initialsFor(selectedContact)}
                </div>
                <div>
                  <h3 className={styles.name} style={{ fontSize: 18 }}>
                    {displayName(selectedContact)}
                  </h3>
                  <div className={styles.email} style={{ fontSize: 14 }}>
                    {selectedContact.email}
                  </div>
                </div>
              </div>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={closeContactModal}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>

            <div
              className={styles.detailPanel}
              style={{ margin: 0, padding: 0, background: "transparent" }}
            >
              {!canManage && (
                <p className={styles.readOnlyNote} style={{ marginBottom: 12 }}>
                  You have view-only access to contacts.
                </p>
              )}

              <div className={styles.detailMeta}>
                <span>Created {new Date(selectedContact.created_at).toLocaleString()}</span>
                <span>Updated {new Date(selectedContact.updated_at).toLocaleString()}</span>
              </div>

              {/* Tag management */}
              <div className={styles.tagList}>
                {selectedContact.tags.map((tagItem) => {
                  const tag = getTagInfo(tagItem);
                  return (
                    <span key={tag.id} className={styles.tagChip}>
                      <span>{tag.name}</span>
                      {canManage && (
                        <button
                          type="button"
                          disabled={tagActionPending}
                          className={styles.tagRemoveButton}
                          onClick={() => handleDetachTag(selectedContact.id, tagItem)}
                          aria-label={`Remove tag ${tag.name}`}
                        >
                          ×
                        </button>
                      )}
                    </span>
                  );
                })}
              </div>

              {canManage && (
                <div className={styles.attachTagRow}>
                  <select
                    value={attachTagId}
                    onChange={(e) => setAttachTagId(e.target.value)}
                    className={styles.select}
                    aria-label="Attach an existing tag"
                  >
                    <option value="">Attach a tag...</option>
                    {tags
                      .filter(
                        (t) =>
                          !selectedContact.tags.some((ct) => {
                            const info = getTagInfo(ct);
                            return info.id === t.id || info.name === t.name;
                          }),
                      )
                      .map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name}
                        </option>
                      ))}
                  </select>
                  <button
                    type="button"
                    disabled={!attachTagId || tagActionPending}
                    className={styles.viewButton}
                    onClick={() => handleAttachExistingTag(selectedContact.id)}
                  >
                    Attach
                  </button>

                  <div className={styles.newTagForm}>
                    <input
                      type="text"
                      placeholder="New tag name"
                      value={newTagName}
                      onChange={(e) => setNewTagName(e.target.value)}
                      className={styles.input}
                      style={{ width: 160 }}
                      aria-label="New tag name"
                    />
                    <button
                      type="button"
                      disabled={!newTagName.trim() || tagActionPending}
                      className={styles.viewButton}
                      onClick={() => handleCreateAndAttachTag(selectedContact.id)}
                    >
                      + New tag
                    </button>
                  </div>
                </div>
              )}

              {/* Consent section */}
              <div style={{ margin: "20px 0" }}>
                <h4
                  style={{
                    fontSize: 14,
                    fontWeight: 700,
                    margin: "0 0 10px",
                    color: "var(--color-dark-text)",
                  }}
                >
                  Consent history
                </h4>
                {consentLoading ? (
                  <div className={styles.description}>Loading consent history…</div>
                ) : consentHistory.length === 0 ? (
                  <div className={styles.description}>No consent recorded yet.</div>
                ) : (
                  <ul style={{ paddingLeft: 18, margin: "0 0 14px", fontSize: 13 }}>
                    {consentHistory.map((rec) => (
                      <li key={rec.id}>
                        {rec.channel}: {rec.status} ({rec.source ?? "n/a"}) at{" "}
                        {new Date(rec.recorded_at).toLocaleString()}
                      </li>
                    ))}
                  </ul>
                )}

                {canManage && (
                  <form
                    onSubmit={(e) => handleRecordConsent(e, selectedContact.id)}
                    style={{
                      display: "flex",
                      gap: 8,
                      flexWrap: "wrap",
                      alignItems: "center",
                    }}
                  >
                    <select
                      value={consentForm.channel}
                      onChange={(e) =>
                        setConsentForm({
                          ...consentForm,
                          channel: e.target.value as "EMAIL" | "SMS",
                        })
                      }
                      className={styles.select}
                      aria-label="Consent channel"
                    >
                      <option value="EMAIL">Email</option>
                      <option value="SMS">SMS</option>
                    </select>

                    <select
                      value={consentForm.status}
                      onChange={(e) =>
                        setConsentForm({
                          ...consentForm,
                          status: e.target.value as "GRANTED" | "WITHDRAWN" | "UNKNOWN",
                        })
                      }
                      className={styles.select}
                      aria-label="Consent status"
                    >
                      <option value="GRANTED">Granted</option>
                      <option value="WITHDRAWN">Withdrawn</option>
                      <option value="UNKNOWN">Unknown</option>
                    </select>

                    <input
                      type="text"
                      placeholder="Source (optional)"
                      value={consentForm.source}
                      onChange={(e) => setConsentForm({ ...consentForm, source: e.target.value })}
                      className={styles.input}
                      style={{ width: 180 }}
                      aria-label="Consent source"
                    />

                    <button
                      type="submit"
                      disabled={consentSubmitting}
                      className={styles.viewButton}
                    >
                      Record consent
                    </button>
                  </form>
                )}
              </div>

              {/* Edit contact form */}
              {canManage && (
                <form
                  className={styles.editForm}
                  onSubmit={(e) => handleSaveEdit(e, selectedContact.id)}
                  style={{ marginTop: 20 }}
                >
                  <div className={styles.createField}>
                    <label className={styles.label} htmlFor={`edit-email-${selectedContact.id}`}>
                      Email
                    </label>
                    <input
                      id={`edit-email-${selectedContact.id}`}
                      type="email"
                      required
                      className={styles.input}
                      value={editForm.email}
                      onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                    />
                  </div>

                  <div className={styles.createField}>
                    <label
                      className={styles.label}
                      htmlFor={`edit-first-name-${selectedContact.id}`}
                    >
                      First name
                    </label>
                    <input
                      id={`edit-first-name-${selectedContact.id}`}
                      type="text"
                      className={styles.input}
                      value={editForm.first_name}
                      onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                    />
                  </div>

                  <div className={styles.createField}>
                    <label
                      className={styles.label}
                      htmlFor={`edit-last-name-${selectedContact.id}`}
                    >
                      Last name
                    </label>
                    <input
                      id={`edit-last-name-${selectedContact.id}`}
                      type="text"
                      className={styles.input}
                      value={editForm.last_name}
                      onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                    />
                  </div>

                  <div className={styles.createField}>
                    <label className={styles.label} htmlFor={`edit-phone-${selectedContact.id}`}>
                      Phone
                    </label>
                    <input
                      id={`edit-phone-${selectedContact.id}`}
                      type="text"
                      className={styles.input}
                      value={editForm.phone}
                      onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                    />
                  </div>

                  <button type="submit" disabled={saving} className={styles.submit}>
                    {saving ? "Saving..." : "Save changes"}
                  </button>

                  {selectedContact.status === "ACTIVE" ? (
                    <button
                      type="button"
                      disabled={statusPendingId === selectedContact.id}
                      className={styles.cancel}
                      onClick={() => setStatus(selectedContact.id, "ARCHIVED")}
                    >
                      Archive
                    </button>
                  ) : (
                    <button
                      type="button"
                      disabled={statusPendingId === selectedContact.id}
                      className={styles.viewButton}
                      onClick={() => setStatus(selectedContact.id, "ACTIVE")}
                    >
                      Unarchive
                    </button>
                  )}
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
