"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./contacts-page.module.css";
import type { Contact, MeResponse } from "./types";

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

export function ContactsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<ContactFormState>(EMPTY_FORM);
  const [creating, setCreating] = useState(false);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<ContactFormState>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [statusPendingId, setStatusPendingId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [me, contactList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<Contact[]>("/contacts"),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setContacts(contactList);
      } catch {
        setLoadError("Could not load contacts.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

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

  function toggleExpand(contact: Contact) {
    if (expandedId === contact.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(contact.id);
    setEditForm({
      email: contact.email,
      first_name: contact.first_name ?? "",
      last_name: contact.last_name ?? "",
      phone: contact.phone ?? "",
      source: contact.source ?? "",
    });
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>, contactId: string) {
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
        }),
      });
      setContacts((current) => current.map((c) => (c.id === contactId ? updated : c)));
      showToast("success", "Contact updated.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        showToast("error", "Another contact already uses this email.");
      } else {
        showToast("error", "Could not update the contact.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleStatus(contact: Contact) {
    const nextStatus = contact.status === "ACTIVE" ? "ARCHIVED" : "ACTIVE";
    setStatusPendingId(contact.id);

    try {
      const updated = await apiFetch<Contact>(`/contacts/${contact.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setContacts((current) => current.map((c) => (c.id === contact.id ? updated : c)));
      showToast("success", nextStatus === "ARCHIVED" ? "Contact archived." : "Contact activated.");
    } catch {
      showToast("error", "Could not change that contact's status.");
    } finally {
      setStatusPendingId(null);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view contacts.</div>;
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Contacts <span className={styles.headerCount}>· {contacts.length}</span>
        </h2>
        {canManage && !showCreateForm && (
          <button
            type="button"
            className={styles.addButton}
            onClick={() => setShowCreateForm(true)}
          >
            + Add contact
          </button>
        )}
      </div>

      {showCreateForm && (
        <form className={styles.createForm} onSubmit={handleCreateSubmit}>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="contact-email">
              Email
            </label>
            <input
              id="contact-email"
              type="email"
              required
              className={styles.input}
              value={createForm.email}
              onChange={(event) => setCreateForm({ ...createForm, email: event.target.value })}
            />
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="contact-first-name">
              First name
            </label>
            <input
              id="contact-first-name"
              className={styles.input}
              value={createForm.first_name}
              onChange={(event) => setCreateForm({ ...createForm, first_name: event.target.value })}
            />
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="contact-last-name">
              Last name
            </label>
            <input
              id="contact-last-name"
              className={styles.input}
              value={createForm.last_name}
              onChange={(event) => setCreateForm({ ...createForm, last_name: event.target.value })}
            />
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="contact-phone">
              Phone
            </label>
            <input
              id="contact-phone"
              className={styles.input}
              value={createForm.phone}
              onChange={(event) => setCreateForm({ ...createForm, phone: event.target.value })}
            />
          </div>
          <button type="submit" className={styles.submit} disabled={creating}>
            {creating ? "Creating…" : "Create contact"}
          </button>
          <button type="button" className={styles.cancel} onClick={() => setShowCreateForm(false)}>
            Cancel
          </button>
        </form>
      )}

      {contacts.length === 0 && <p className={styles.emptyState}>No contacts yet.</p>}

      {contacts.map((contact) => {
        const isExpanded = expandedId === contact.id;
        const isStatusPending = statusPendingId === contact.id;
        return (
          <div className={styles.contactBlock} key={contact.id}>
            <div className={styles.row}>
              <div className={styles.avatar}>{initialsFor(contact)}</div>
              <div className={styles.identity}>
                <div className={styles.name}>{displayName(contact)}</div>
                <div className={styles.email}>{contact.email}</div>
              </div>
              <div className={styles.rowActions}>
                {contact.is_suppressed && (
                  <span className={styles.suppressedBadge}>Suppressed</span>
                )}
                <span
                  className={`${styles.statusBadge} ${
                    contact.status === "ACTIVE" ? styles.statusActive : styles.statusArchived
                  }`}
                >
                  {contact.status === "ACTIVE" ? "Active" : "Archived"}
                </span>
                <button
                  type="button"
                  className={styles.viewButton}
                  onClick={() => toggleExpand(contact)}
                >
                  {isExpanded ? "Close" : "View"}
                </button>
              </div>
            </div>

            {isExpanded && (
              <div className={styles.detailPanel}>
                <div className={styles.detailMeta}>
                  <span>Created {new Date(contact.created_at).toLocaleString()}</span>
                  <span>Updated {new Date(contact.updated_at).toLocaleString()}</span>
                </div>

                {contact.tags.length > 0 && (
                  <div className={styles.tagList}>
                    {contact.tags.map((tag) => (
                      <span className={styles.tagChip} key={tag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {Object.keys(contact.custom_fields).length > 0 && (
                  <dl className={styles.customFields}>
                    {Object.entries(contact.custom_fields).map(([key, value]) => (
                      <div className={styles.customFieldRow} key={key}>
                        <dt>{key}</dt>
                        <dd>{value}</dd>
                      </div>
                    ))}
                  </dl>
                )}

                {canManage ? (
                  <form
                    className={styles.editForm}
                    onSubmit={(event) => handleEditSubmit(event, contact.id)}
                  >
                    <div className={styles.createField}>
                      <label className={styles.label} htmlFor={`edit-email-${contact.id}`}>
                        Email
                      </label>
                      <input
                        id={`edit-email-${contact.id}`}
                        type="email"
                        required
                        className={styles.input}
                        value={editForm.email}
                        onChange={(event) =>
                          setEditForm({ ...editForm, email: event.target.value })
                        }
                      />
                    </div>
                    <div className={styles.createField}>
                      <label className={styles.label} htmlFor={`edit-first-name-${contact.id}`}>
                        First name
                      </label>
                      <input
                        id={`edit-first-name-${contact.id}`}
                        className={styles.input}
                        value={editForm.first_name}
                        onChange={(event) =>
                          setEditForm({ ...editForm, first_name: event.target.value })
                        }
                      />
                    </div>
                    <div className={styles.createField}>
                      <label className={styles.label} htmlFor={`edit-last-name-${contact.id}`}>
                        Last name
                      </label>
                      <input
                        id={`edit-last-name-${contact.id}`}
                        className={styles.input}
                        value={editForm.last_name}
                        onChange={(event) =>
                          setEditForm({ ...editForm, last_name: event.target.value })
                        }
                      />
                    </div>
                    <div className={styles.createField}>
                      <label className={styles.label} htmlFor={`edit-phone-${contact.id}`}>
                        Phone
                      </label>
                      <input
                        id={`edit-phone-${contact.id}`}
                        className={styles.input}
                        value={editForm.phone}
                        onChange={(event) =>
                          setEditForm({ ...editForm, phone: event.target.value })
                        }
                      />
                    </div>
                    <button type="submit" className={styles.submit} disabled={saving}>
                      {saving ? "Saving…" : "Save changes"}
                    </button>
                    <button
                      type="button"
                      className={styles.toggleButton}
                      disabled={isStatusPending}
                      onClick={() => handleToggleStatus(contact)}
                    >
                      {contact.status === "ACTIVE" ? "Archive" : "Activate"}
                    </button>
                  </form>
                ) : (
                  <p className={styles.readOnlyNote}>You have view-only access to contacts.</p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
