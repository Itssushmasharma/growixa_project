"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
import type { Contact, ContactList, MeResponse } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

export interface Theme {
  icon: string;
  bg: string;
  color: string;
  bar: string;
}

export function getAudienceTheme(name: string): Theme {
  const n = name.toLowerCase();
  if (n.includes("vip") || n.includes("enterprise") || n.includes("star")) {
    return { icon: "⭐", bg: "rgba(139, 92, 246, 0.12)", color: "#7c3aed", bar: "#8b5cf6" };
  }
  if (n.includes("news") || n.includes("newsletter") || n.includes("update")) {
    return { icon: "📰", bg: "rgba(16, 185, 129, 0.12)", color: "#059669", bar: "#10b981" };
  }
  if (
    n.includes("webinar") ||
    n.includes("lead") ||
    n.includes("intent") ||
    n.includes("event") ||
    n.includes("attendee")
  ) {
    return { icon: "🎯", bg: "rgba(236, 72, 153, 0.12)", color: "#db2777", bar: "#ec4899" };
  }
  if (n.includes("fresh") || n.includes("new")) {
    return { icon: "🌱", bg: "rgba(34, 197, 94, 0.12)", color: "#16a34a", bar: "#22c55e" };
  }
  if (n.includes("inactive") || n.includes("old") || n.includes("idle") || n.includes("60d")) {
    return { icon: "⏳", bg: "rgba(245, 158, 11, 0.12)", color: "#d97706", bar: "#f59e0b" };
  }
  if (n.includes("churn") || n.includes("risk") || n.includes("warn") || n.includes("bounce")) {
    return { icon: "⚠️", bg: "rgba(239, 68, 68, 0.12)", color: "#dc2626", bar: "#ef4444" };
  }
  if (n.includes("all") || n.includes("subscriber") || n.includes("customer")) {
    return { icon: "👥", bg: "rgba(59, 130, 246, 0.12)", color: "#2563eb", bar: "#3b82f6" };
  }
  return { icon: "📋", bg: "rgba(99, 102, 241, 0.12)", color: "#4f46e5", bar: "#6366f1" };
}

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
  const [memberSearch, setMemberSearch] = useState("");
  const [addContactId, setAddContactId] = useState("");
  const [memberActionPending, setMemberActionPending] = useState(false);

  const filteredMembers = useMemo(() => {
    if (!memberSearch.trim()) return listMembers;
    const q = memberSearch.trim().toLowerCase();
    return listMembers.filter((c) => {
      const fullName = [c.first_name, c.last_name].filter(Boolean).join(" ").toLowerCase();
      const email = (c.email || "").toLowerCase();
      const phone = (c.phone || "").toLowerCase();
      return fullName.includes(q) || email.includes(q) || phone.includes(q);
    });
  }, [listMembers, memberSearch]);

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

  const maxMembers = useMemo(() => {
    if (lists.length === 0) return 1;
    return Math.max(1, ...lists.map((l) => l.member_count));
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
    setMemberSearch("");
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
    setMemberSearch("");
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
      const added = contacts.find((c) => c.id === addContactId);
      if (added && !listMembers.some((m) => m.id === added.id)) {
        setListMembers((prev) => [...prev, added]);
      }
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
          <div className={styles.segmentGrid}>
            {lists.map((list) => {
              const theme = getAudienceTheme(list.name);
              const percentage = Math.min(100, Math.round((list.member_count / maxMembers) * 100));

              return (
                <div
                  key={list.id}
                  className={styles.segmentCard}
                  onClick={() => openManageModal(list)}
                >
                  <div className={styles.segmentCardTop}>
                    <div
                      className={styles.segmentIconBadge}
                      style={{ background: theme.bg, color: theme.color }}
                    >
                      {theme.icon}
                    </div>
                    <span
                      className={styles.percentageBadge}
                      style={{ background: theme.bg, color: theme.color }}
                    >
                      {percentage}% of max
                    </span>
                  </div>

                  <div>
                    <h3 className={styles.segmentCardTitle}>{list.name}</h3>
                    <div className={styles.segmentCardCount}>
                      {list.member_count.toLocaleString()}
                    </div>
                  </div>

                  <div>
                    <div className={styles.progressTrack}>
                      <div
                        className={styles.progressFill}
                        style={{ width: `${Math.max(5, percentage)}%`, background: theme.bar }}
                      />
                    </div>
                    <div className={styles.segmentCardFooter}>
                      <span className={styles.countBadge}>{list.member_count} members</span>
                      <span className={styles.segmentCardMetaText} title={list.description || ""}>
                        {list.description || "No description"}
                      </span>
                      <button
                        type="button"
                        className={styles.viewButton}
                        onClick={(e) => {
                          e.stopPropagation();
                          void openManageModal(list);
                        }}
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

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                margin: "0 0 12px",
                gap: 12,
                flexWrap: "wrap",
              }}
            >
              <h4 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
                Current Members ({filteredMembers.length}
                {memberSearch.trim() ? ` of ${listMembers.length}` : ""})
              </h4>
              <input
                type="text"
                placeholder="🔍 Search name, email, phone…"
                value={memberSearch}
                onChange={(e) => setMemberSearch(e.target.value)}
                className={styles.input}
                style={{ maxWidth: 240, padding: "6px 12px", fontSize: 12 }}
                aria-label="Search current members"
              />
            </div>

            {listMembersLoading ? (
              <div className={styles.description}>Loading list members…</div>
            ) : listMembers.length === 0 ? (
              <div className={styles.description}>No members in this list yet.</div>
            ) : filteredMembers.length === 0 ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: "24px 16px",
                  background: "#f8fafc",
                  borderRadius: 10,
                  gap: 8,
                }}
              >
                <div className={styles.description}>
                  No members match &ldquo;{memberSearch}&rdquo;
                </div>
                <button
                  type="button"
                  className={styles.viewButton}
                  onClick={() => setMemberSearch("")}
                  style={{ fontSize: 12 }}
                >
                  Clear search
                </button>
              </div>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                  maxHeight: 340,
                  overflowY: "auto",
                }}
              >
                {filteredMembers.map((member) => (
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
                      <div className={styles.email}>
                        {member.email}
                        {member.phone ? ` · ${member.phone}` : ""}
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span
                        className={styles.statusActive}
                        style={{
                          padding: "2px 8px",
                          borderRadius: 999,
                          fontSize: 11,
                          fontWeight: 700,
                        }}
                      >
                        {member.status}
                      </span>
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
