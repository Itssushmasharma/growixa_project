"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
import type { Contact, ContactList, MeResponse } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

interface ListFormState {
  name: string;
  description: string;
}

const EMPTY_FORM: ListFormState = { name: "", description: "" };

export function ListsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [lists, setLists] = useState<ContactList[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<ListFormState>(EMPTY_FORM);
  const [creating, setCreating] = useState(false);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [addContactId, setAddContactId] = useState("");
  const [removeContactId, setRemoveContactId] = useState("");
  const [memberActionPending, setMemberActionPending] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [me, listResponse, contactResponse] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<ContactList[]>("/contacts/lists"),
          apiFetch<Contact[]>("/contacts"),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setLists(listResponse);
        setContacts(contactResponse);
      } catch {
        setLoadError("Could not load lists.");
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
      const created = await apiFetch<ContactList>("/contacts/lists", {
        method: "POST",
        body: JSON.stringify({
          name: createForm.name,
          description: createForm.description || null,
        }),
      });
      setLists((current) => [created, ...current]);
      setShowCreateForm(false);
      setCreateForm(EMPTY_FORM);
      showToast("success", "List created.");
    } catch {
      showToast("error", "Could not create the list.");
    } finally {
      setCreating(false);
    }
  }

  function toggleExpand(list: ContactList) {
    setExpandedId((current) => (current === list.id ? null : list.id));
    setAddContactId("");
    setRemoveContactId("");
  }

  async function handleAddMember(listId: string) {
    if (!addContactId) return;
    setMemberActionPending(true);

    try {
      const updated = await apiFetch<ContactList>(`/contacts/lists/${listId}/members`, {
        method: "POST",
        body: JSON.stringify({ contact_id: addContactId }),
      });
      setLists((current) => current.map((l) => (l.id === listId ? updated : l)));
      setAddContactId("");
      showToast("success", "Contact added to the list.");
    } catch {
      showToast("error", "Could not add that contact to the list.");
    } finally {
      setMemberActionPending(false);
    }
  }

  async function handleRemoveMember(listId: string) {
    if (!removeContactId) return;
    setMemberActionPending(true);

    try {
      const updated = await apiFetch<ContactList>(
        `/contacts/lists/${listId}/members/${removeContactId}`,
        { method: "DELETE" },
      );
      setLists((current) => current.map((l) => (l.id === listId ? updated : l)));
      setRemoveContactId("");
      showToast("success", "Contact removed from the list.");
    } catch {
      showToast("error", "Could not remove that contact from the list.");
    } finally {
      setMemberActionPending(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view lists.</div>;
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Lists <span className={styles.headerCount}>· {lists.length}</span>
        </h2>
        {canManage && !showCreateForm && (
          <button
            type="button"
            className={styles.addButton}
            onClick={() => setShowCreateForm(true)}
          >
            + Add list
          </button>
        )}
      </div>

      {showCreateForm && (
        <form className={styles.createForm} onSubmit={handleCreateSubmit}>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="list-name">
              Name
            </label>
            <input
              id="list-name"
              required
              className={styles.input}
              value={createForm.name}
              onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })}
            />
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="list-description">
              Description
            </label>
            <input
              id="list-description"
              className={styles.input}
              value={createForm.description}
              onChange={(event) =>
                setCreateForm({ ...createForm, description: event.target.value })
              }
            />
          </div>
          <button type="submit" className={styles.submit} disabled={creating}>
            {creating ? "Creating…" : "Create list"}
          </button>
          <button type="button" className={styles.cancel} onClick={() => setShowCreateForm(false)}>
            Cancel
          </button>
        </form>
      )}

      {lists.length === 0 && <p className={styles.emptyState}>No lists yet.</p>}

      {lists.map((list) => {
        const isExpanded = expandedId === list.id;
        return (
          <div className={styles.contactBlock} key={list.id}>
            <div className={styles.row}>
              <div className={styles.identity}>
                <div className={styles.name}>{list.name}</div>
                {list.description && <div className={styles.description}>{list.description}</div>}
              </div>
              <div className={styles.rowActions}>
                <span className={styles.countBadge}>{list.member_count} members</span>
                <button
                  type="button"
                  className={styles.viewButton}
                  onClick={() => toggleExpand(list)}
                >
                  {isExpanded ? "Close" : "Manage"}
                </button>
              </div>
            </div>

            {isExpanded && (
              <div className={styles.detailPanel}>
                {canManage ? (
                  <>
                    <div className={styles.manageRow}>
                      <select
                        className={styles.select}
                        value={addContactId}
                        disabled={memberActionPending}
                        onChange={(event) => setAddContactId(event.target.value)}
                        aria-label="Contact to add"
                      >
                        <option value="">Select a contact to add…</option>
                        {contacts.map((contact) => (
                          <option key={contact.id} value={contact.id}>
                            {contact.email}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className={styles.toggleButton}
                        disabled={memberActionPending || !addContactId}
                        onClick={() => handleAddMember(list.id)}
                      >
                        Add to list
                      </button>
                    </div>
                    <div className={styles.manageRow}>
                      <select
                        className={styles.select}
                        value={removeContactId}
                        disabled={memberActionPending}
                        onChange={(event) => setRemoveContactId(event.target.value)}
                        aria-label="Contact to remove"
                      >
                        <option value="">Select a contact to remove…</option>
                        {contacts.map((contact) => (
                          <option key={contact.id} value={contact.id}>
                            {contact.email}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className={styles.toggleButton}
                        disabled={memberActionPending || !removeContactId}
                        onClick={() => handleRemoveMember(list.id)}
                      >
                        Remove from list
                      </button>
                    </div>
                  </>
                ) : (
                  <p className={styles.readOnlyNote}>You have view-only access to lists.</p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
