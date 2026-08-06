"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

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

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<ListFormState>(EMPTY_FORM);
  const [creating, setCreating] = useState(false);

  const [selectedList, setSelectedList] = useState<ContactList | null>(null);
  const [listMembers, setListMembers] = useState<Contact[]>([]);
  const [listMembersLoading, setListMembersLoading] = useState(false);
  const [addContactId, setAddContactId] = useState("");
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

  const metrics = useMemo(() => {
    const totalLists = lists.length;
    const totalMemberships = lists.reduce((acc, l) => acc + l.member_count, 0);
    const avgMembers = totalLists > 0 ? Math.round(totalMemberships / totalLists) : 0;
    return { totalLists, totalMemberships, avgMembers };
  }, [lists]);

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
      setShowCreateModal(false);
      setCreateForm(EMPTY_FORM);
      showToast("success", "List created.");
    } catch {
      showToast("error", "Could not create the list.");
    } finally {
      setCreating(false);
    }
  }

  async function openManageModal(list: ContactList) {
    setSelectedList(list);
    setAddContactId("");
    setListMembersLoading(true);
    try {
      const members = await apiFetch<Contact[]>(`/contacts/lists/${list.id}/members`);
      setListMembers(members);
    } catch {
      setListMembers([]);
    } finally {
      setListMembersLoading(false);
    }
  }

  function closeManageModal() {
    setSelectedList(null);
    setListMembers([]);
  }

  async function handleAddMember(listId: string) {
    if (!addContactId) return;
    setMemberActionPending(true);

    try {
      const updatedList = await apiFetch<ContactList>(`/contacts/lists/${listId}/members`, {
        method: "POST",
        body: JSON.stringify({ contact_id: addContactId }),
      });
      setLists((current) => current.map((l) => (l.id === listId ? updatedList : l)));
      setSelectedList(updatedList);
      const updatedMembers = await apiFetch<Contact[]>(`/contacts/lists/${listId}/members`);
      setListMembers(updatedMembers);
      setAddContactId("");
      showToast("success", "Contact added to list.");
    } catch {
      showToast("error", "Could not add contact to list.");
    } finally {
      setMemberActionPending(false);
    }
  }

  async function handleRemoveMember(listId: string, contactId: string) {
    setMemberActionPending(true);

    try {
      const updatedList = await apiFetch<ContactList>(
        `/contacts/lists/${listId}/members/${contactId}`,
        {
          method: "DELETE",
        },
      );
      setLists((current) => current.map((l) => (l.id === listId ? updatedList : l)));
      setSelectedList(updatedList);
      setListMembers((current) => current.filter((c) => c.id !== contactId));
      showToast("success", "Contact removed from list.");
    } catch {
      showToast("error", "Could not remove contact from list.");
    } finally {
      setMemberActionPending(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading lists…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view lists.</div>;
  }

  return (
    <div>
      {/* Metric Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Lists</div>
          <div className={styles.metricValue}>{metrics.totalLists}</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Memberships</div>
          <div className={styles.metricValue} style={{ color: "var(--color-primary)" }}>
            {metrics.totalMemberships}
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Avg Members / List</div>
          <div className={styles.metricValue} style={{ color: "var(--color-slate)" }}>
            {metrics.avgMembers}
          </div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>
            Lists <span className={styles.headerCount}>· {lists.length}</span>
          </h2>
          {canManage && (
            <button
              type="button"
              className={styles.addButton}
              onClick={() => setShowCreateModal(true)}
            >
              + Add list
            </button>
          )}
        </div>

        {lists.length === 0 ? (
          <div className={styles.emptyState}>No lists yet.</div>
        ) : (
          <div>
            {/* Table Header Row */}
            <div className={styles.tableHeader}>
              <div>Name</div>
              <div>Description</div>
              <div>Members</div>
              <div style={{ textAlign: "right" }}>Actions</div>
            </div>

            {lists.map((list) => {
              return (
                <div key={list.id} className={styles.contactBlock}>
                  <div className={styles.row}>
                    <div className={styles.name}>{list.name}</div>
                    <div className={styles.description}>{list.description || "—"}</div>
                    <div>
                      <span className={styles.countBadge}>{list.member_count} members</span>
                    </div>
                    <div className={styles.rowActions}>
                      <button
                        type="button"
                        className={styles.viewButton}
                        onClick={() => openManageModal(list)}
                      >
                        Manage
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create List Modal */}
      {showCreateModal && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowCreateModal(false);
          }}
        >
          <div className={styles.modalContent} style={{ maxWidth: 520 }}>
            <div className={styles.modalHeader}>
              <h3 className={styles.name} style={{ fontSize: 18, margin: 0 }}>
                Create New List
              </h3>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={() => setShowCreateModal(false)}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>
            <form className={styles.modalForm} onSubmit={handleCreateSubmit}>
              <div className={styles.createField} style={{ marginBottom: 16 }}>
                <label className={styles.label} htmlFor="create-list-name">
                  Name
                </label>
                <input
                  id="create-list-name"
                  type="text"
                  required
                  className={styles.input}
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                />
              </div>
              <div className={styles.createField} style={{ marginBottom: 20 }}>
                <label className={styles.label} htmlFor="create-list-description">
                  Description
                </label>
                <input
                  id="create-list-description"
                  type="text"
                  className={styles.input}
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                />
              </div>
              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className={styles.modalCloseButton}
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" disabled={creating} className={styles.submit}>
                  {creating ? "Creating..." : "Create list"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage List Members Modal */}
      {selectedList && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeManageModal();
          }}
        >
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <div>
                <h3 className={styles.name} style={{ fontSize: 18, margin: "0 0 4px" }}>
                  {selectedList.name}
                </h3>
                <div className={styles.description}>
                  {selectedList.description || "No description provided."}
                </div>
              </div>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={closeManageModal}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>

            {!canManage && (
              <p className={styles.readOnlyNote} style={{ marginBottom: 12 }}>
                You have view-only access to lists.
              </p>
            )}

            <div className={styles.detailMeta}>
              <span>Members: {selectedList.member_count}</span>
              <span>Created {new Date(selectedList.created_at).toLocaleDateString()}</span>
            </div>

            {canManage && (
              <div className={styles.manageRow} style={{ marginBottom: 20 }}>
                <select
                  value={addContactId}
                  onChange={(e) => setAddContactId(e.target.value)}
                  className={styles.select}
                  aria-label="Contact to add"
                  style={{ flex: 1 }}
                >
                  <option value="">Select a contact to add…</option>
                  {contacts
                    .filter((c) => !listMembers.some((m) => m.id === c.id))
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.email} (
                        {c.first_name || c.last_name
                          ? [c.first_name, c.last_name].filter(Boolean).join(" ")
                          : "No name"}
                        )
                      </option>
                    ))}
                </select>
                <button
                  type="button"
                  disabled={!addContactId || memberActionPending}
                  className={styles.submit}
                  onClick={() => handleAddMember(selectedList.id)}
                >
                  Add to list
                </button>
              </div>
            )}

            <h4 style={{ fontSize: 14, fontWeight: 700, margin: "0 0 10px" }}>Current Members</h4>
            {listMembersLoading ? (
              <div className={styles.description}>Loading list members…</div>
            ) : listMembers.length === 0 ? (
              <div className={styles.description}>No members in this list yet.</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {listMembers.map((member) => (
                  <div
                    key={member.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "8px 12px",
                      background: "#f8fafc",
                      borderRadius: 10,
                    }}
                  >
                    <div>
                      <div className={styles.name} style={{ fontSize: 13 }}>
                        {[member.first_name, member.last_name].filter(Boolean).join(" ") ||
                          "No name"}
                      </div>
                      <div className={styles.email}>{member.email}</div>
                    </div>
                    {canManage && (
                      <button
                        type="button"
                        disabled={memberActionPending}
                        className={styles.viewButton}
                        onClick={() => handleRemoveMember(selectedList.id, member.id)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
