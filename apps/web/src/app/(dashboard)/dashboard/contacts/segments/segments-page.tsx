"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
import {
  type Contact,
  type CustomField,
  type MeResponse,
  type Segment,
  SEGMENT_RULE_FIELDS,
  SEGMENT_RULE_OPERATORS,
} from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

const FIELD_LABELS: Record<string, string> = {
  [SEGMENT_RULE_FIELDS.STATUS]: "Status",
  [SEGMENT_RULE_FIELDS.SOURCE]: "Source",
  [SEGMENT_RULE_FIELDS.TAG]: "Tag",
  [SEGMENT_RULE_FIELDS.EMAIL]: "Email",
  [SEGMENT_RULE_FIELDS.FIRST_NAME]: "First name",
  [SEGMENT_RULE_FIELDS.LAST_NAME]: "Last name",
  [SEGMENT_RULE_FIELDS.PHONE]: "Phone",
  [SEGMENT_RULE_FIELDS.CREATED_AT]: "Created date",
};

const ALLOWED_OPERATORS: Record<string, { label: string; value: string }[]> = {
  [SEGMENT_RULE_FIELDS.STATUS]: [{ label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS }],
  [SEGMENT_RULE_FIELDS.SOURCE]: [{ label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS }],
  [SEGMENT_RULE_FIELDS.CREATED_AT]: [
    { label: "before", value: SEGMENT_RULE_OPERATORS.BEFORE },
    { label: "after", value: SEGMENT_RULE_OPERATORS.AFTER },
  ],
  [SEGMENT_RULE_FIELDS.TAG]: [
    { label: "equals (exact name)", value: SEGMENT_RULE_OPERATORS.EQUALS },
    { label: "contains (sub-text)", value: SEGMENT_RULE_OPERATORS.CONTAINS },
  ],
  [SEGMENT_RULE_FIELDS.EMAIL]: [
    { label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS },
    { label: "contains", value: SEGMENT_RULE_OPERATORS.CONTAINS },
  ],
  [SEGMENT_RULE_FIELDS.FIRST_NAME]: [
    { label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS },
    { label: "contains", value: SEGMENT_RULE_OPERATORS.CONTAINS },
  ],
  [SEGMENT_RULE_FIELDS.LAST_NAME]: [
    { label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS },
    { label: "contains", value: SEGMENT_RULE_OPERATORS.CONTAINS },
  ],
  [SEGMENT_RULE_FIELDS.PHONE]: [
    { label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS },
    { label: "contains", value: SEGMENT_RULE_OPERATORS.CONTAINS },
  ],
  default: [
    { label: "equals", value: SEGMENT_RULE_OPERATORS.EQUALS },
    { label: "contains", value: SEGMENT_RULE_OPERATORS.CONTAINS },
  ],
};

function getOperatorsForField(field: string): { label: string; value: string }[] {
  if (field.startsWith("custom_field:")) {
    return ALLOWED_OPERATORS.default ?? [];
  }
  return ALLOWED_OPERATORS[field] ?? ALLOWED_OPERATORS.default ?? [];
}

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

export interface SegmentRuleInput {
  field: string;
  operator: string;
  value: string;
}

interface SegmentFormState {
  name: string;
  type: "DYNAMIC" | "SAVED";
  rules: SegmentRuleInput[];
}

function emptyRule(): SegmentRuleInput {
  return { field: "status", operator: "equals", value: "" };
}

function emptyForm(): SegmentFormState {
  return { name: "", type: "DYNAMIC", rules: [emptyRule()] };
}

function ruleSummary(
  field: string,
  operator: string,
  value: string,
  customFields: CustomField[] = [],
): string {
  let label = FIELD_LABELS[field] ?? field;
  if (field.startsWith("custom_field:")) {
    const key = field.split(":", 2)[1] ?? "";
    const match = customFields.find((cf) => cf.key === key);
    label = match
      ? match.label
      : key
        ? key.replace(/_/g, " ").replace(/^./, (s) => s.toUpperCase())
        : field;
  }
  return `${label} ${operator} "${value}"`;
}

export function SegmentsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [customFields, setCustomFields] = useState<CustomField[]>([]);

  // Create Segment State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<SegmentFormState>(emptyForm());
  const [creating, setCreating] = useState(false);

  // Edit Segment State
  const [editingSegment, setEditingSegment] = useState<Segment | null>(null);
  const [editForm, setEditForm] = useState<SegmentFormState>(emptyForm());
  const [updating, setUpdating] = useState(false);

  // Delete Segment State
  const [deletingSegment, setDeletingSegment] = useState<Segment | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // View Members Modal State
  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [members, setMembers] = useState<Contact[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [memberSearch, setMemberSearch] = useState("");

  const filteredMembers = useMemo(() => {
    if (!memberSearch.trim()) return members;
    const q = memberSearch.trim().toLowerCase();
    return members.filter((c) => {
      const fullName = [c.first_name, c.last_name].filter(Boolean).join(" ").toLowerCase();
      const email = (c.email || "").toLowerCase();
      const phone = (c.phone || "").toLowerCase();
      return fullName.includes(q) || email.includes(q) || phone.includes(q);
    });
  }, [members, memberSearch]);

  useEffect(() => {
    async function load() {
      try {
        const [me, segmentList, customFieldList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<Segment[]>("/contacts/segments"),
          apiFetch<CustomField[]>("/contacts/custom-fields").catch(() => []),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setSegments(segmentList);
        setCustomFields(customFieldList);
      } catch {
        setLoadError("Could not load segments.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const metrics = useMemo(() => {
    const totalSegments = segments.length;
    const dynamicSegments = segments.filter((s) => s.type === "DYNAMIC").length;
    const totalRules = segments.reduce((acc, s) => acc + s.rules.length, 0);
    return { totalSegments, dynamicSegments, totalRules };
  }, [segments]);

  const maxMembers = useMemo(() => {
    if (segments.length === 0) return 1;
    return Math.max(1, ...segments.map((s) => s.member_count));
  }, [segments]);

  // Create rule handler
  function handleCreateRuleChange(index: number, key: keyof SegmentRuleInput, value: string) {
    setCreateForm((current) => {
      const updatedRules = [...current.rules];
      const existing = updatedRules[index] ?? emptyRule();
      const updated = { ...existing, [key]: value };

      if (key === "field") {
        const allowed = getOperatorsForField(value);
        if (!allowed.some((op) => op.value === updated.operator)) {
          updated.operator = allowed[0]?.value ?? "equals";
        }
      }

      updatedRules[index] = updated;
      return { ...current, rules: updatedRules };
    });
  }

  function handleAddCreateRule() {
    setCreateForm((current) => ({
      ...current,
      rules: [...current.rules, emptyRule()],
    }));
  }

  function handleRemoveCreateRule(index: number) {
    setCreateForm((current) => ({
      ...current,
      rules: current.rules.filter((_, i) => i !== index),
    }));
  }

  // Edit rule handler
  function handleEditRuleChange(index: number, key: keyof SegmentRuleInput, value: string) {
    setEditForm((current) => {
      const updatedRules = [...current.rules];
      const existing = updatedRules[index] ?? emptyRule();
      const updated = { ...existing, [key]: value };

      if (key === "field") {
        const allowed = getOperatorsForField(value);
        if (!allowed.some((op) => op.value === updated.operator)) {
          updated.operator = allowed[0]?.value ?? "equals";
        }
      }

      updatedRules[index] = updated;
      return { ...current, rules: updatedRules };
    });
  }

  function handleAddEditRule() {
    setEditForm((current) => ({
      ...current,
      rules: [...current.rules, emptyRule()],
    }));
  }

  function handleRemoveEditRule(index: number) {
    setEditForm((current) => ({
      ...current,
      rules: current.rules.filter((_, i) => i !== index),
    }));
  }

  function openEditModal(segment: Segment) {
    setEditingSegment(segment);
    setEditForm({
      name: segment.name,
      type: segment.type as "DYNAMIC" | "SAVED",
      rules:
        segment.rules.length > 0
          ? segment.rules.map((r) => ({ field: r.field, operator: r.operator, value: r.value }))
          : [emptyRule()],
    });
  }

  function openDeleteModal(segment: Segment) {
    setDeletingSegment(segment);
    setDeleteError(null);
  }

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);

    try {
      const created = await apiFetch<Segment>("/contacts/segments", {
        method: "POST",
        body: JSON.stringify({
          name: createForm.name,
          type: createForm.type,
          rules: createForm.rules.filter((r) => r.value.trim() !== ""),
        }),
      });
      setSegments((current) => [created, ...current]);
      setShowCreateModal(false);
      setCreateForm(emptyForm());
      showToast("success", "Segment created successfully.");
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Could not create segment.";
      showToast("error", msg);
    } finally {
      setCreating(false);
    }
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingSegment) return;
    setUpdating(true);

    try {
      const updated = await apiFetch<Segment>(`/contacts/segments/${editingSegment.id}`, {
        method: "PUT",
        body: JSON.stringify({
          name: editForm.name,
          type: editForm.type,
          rules: editForm.rules.filter((r) => r.value.trim() !== ""),
        }),
      });
      setSegments((current) => current.map((s) => (s.id === updated.id ? updated : s)));
      setEditingSegment(null);
      showToast("success", "Segment updated successfully.");
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Could not update segment.";
      showToast("error", msg);
    } finally {
      setUpdating(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!deletingSegment) return;
    setDeleting(true);
    setDeleteError(null);

    try {
      await apiFetch(`/contacts/segments/${deletingSegment.id}`, {
        method: "DELETE",
      });
      setSegments((current) => current.filter((s) => s.id !== deletingSegment.id));
      setDeletingSegment(null);
      showToast("success", "Segment deleted.");
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.message : "Could not delete segment.";
      setDeleteError(msg);
      showToast("error", msg);
    } finally {
      setDeleting(false);
    }
  }

  async function openMemberModal(segment: Segment) {
    setSelectedSegment(segment);
    setMemberSearch("");
    setMembersLoading(true);
    try {
      const result = await apiFetch<Contact[]>(`/contacts/segments/${segment.id}/members`);
      setMembers(result);
    } catch {
      setMembers([]);
    } finally {
      setMembersLoading(false);
    }
  }

  function closeMemberModal() {
    setSelectedSegment(null);
    setMemberSearch("");
    setMembers([]);
  }

  if (loading) {
    return <div className={styles.card}>Loading segments…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view segments.</div>;
  }

  return (
    <div>
      {/* Metric Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Total Segments</div>
          <div className={styles.metricValue}>{metrics.totalSegments}</div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Dynamic Segments</div>
          <div className={styles.metricValue} style={{ color: "var(--color-success)" }}>
            {metrics.dynamicSegments}
          </div>
        </div>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Rules Configured</div>
          <div className={styles.metricValue} style={{ color: "var(--color-slate)" }}>
            {metrics.totalRules}
          </div>
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>
            Segments <span className={styles.headerCount}>· {segments.length}</span>
          </h2>
          {canManage && (
            <button
              type="button"
              className={styles.addButton}
              onClick={() => setShowCreateModal(true)}
            >
              + Add segment
            </button>
          )}
        </div>

        {segments.length === 0 ? (
          <div className={styles.emptyState}>No segments yet.</div>
        ) : (
          <div className={styles.segmentGrid}>
            {segments.map((segment) => {
              const theme = getAudienceTheme(segment.name);
              const percentage = Math.min(
                100,
                Math.round((segment.member_count / maxMembers) * 100),
              );

              return (
                <div
                  key={segment.id}
                  className={styles.segmentCard}
                  onClick={() => openMemberModal(segment)}
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
                    <h3 className={styles.segmentCardTitle}>{segment.name}</h3>
                    <div className={styles.segmentCardCount}>
                      {segment.member_count.toLocaleString()}
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
                      <div className={styles.segmentCardBadges}>
                        <span className={styles.typeBadge}>
                          {segment.type === "DYNAMIC" ? "Dynamic" : "Saved"}
                        </span>
                        <span className={styles.countBadge}>{segment.member_count} members</span>
                        <span className={styles.segmentCardMetaText}>
                          {segment.rules.length > 0
                            ? ruleSummary(
                                segment.rules[0]!.field,
                                segment.rules[0]!.operator,
                                segment.rules[0]!.value,
                                customFields,
                              )
                            : "No filter"}
                        </span>
                      </div>
                      <div className={styles.segmentCardActions}>
                        <button
                          type="button"
                          className={styles.viewButton}
                          onClick={(e) => {
                            e.stopPropagation();
                            void openMemberModal(segment);
                          }}
                        >
                          View members
                        </button>
                        {canManage && (
                          <>
                            <button
                              type="button"
                              className={styles.viewButton}
                              onClick={(e) => {
                                e.stopPropagation();
                                openEditModal(segment);
                              }}
                              title="Edit segment rules and name"
                            >
                              ✏️ Edit
                            </button>
                            <button
                              type="button"
                              className={styles.viewButton}
                              style={{ color: "#ef4444", borderColor: "rgba(239, 68, 68, 0.3)" }}
                              onClick={(e) => {
                                e.stopPropagation();
                                openDeleteModal(segment);
                              }}
                              title="Delete segment"
                            >
                              🗑️ Delete
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Segment Modal */}
      {showCreateModal && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowCreateModal(false);
          }}
        >
          <div className={styles.modalContent} style={{ maxWidth: 640 }}>
            <div className={styles.modalHeader}>
              <h3 className={styles.name} style={{ fontSize: 18, margin: 0 }}>
                Create Segment
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
            <form onSubmit={handleCreateSubmit}>
              <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <div style={{ flex: 1 }}>
                  <label className={styles.label} htmlFor="segment-name">
                    Name
                  </label>
                  <input
                    id="segment-name"
                    type="text"
                    required
                    className={styles.input}
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  />
                </div>
                <div style={{ width: 160 }}>
                  <label className={styles.label} htmlFor="segment-type">
                    Type
                  </label>
                  <select
                    id="segment-type"
                    className={styles.select}
                    style={{ width: "100%" }}
                    value={createForm.type}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        type: e.target.value as "DYNAMIC" | "SAVED",
                      })
                    }
                  >
                    <option value="DYNAMIC">Dynamic (live)</option>
                    <option value="SAVED">Saved (snapshot)</option>
                  </select>
                </div>
              </div>

              <h4 style={{ fontSize: 13, fontWeight: 700, margin: "16px 0 8px" }}>Segment Rules</h4>
              {createForm.rules.map((rule, idx) => {
                const operators = getOperatorsForField(rule.field);

                return (
                  <div key={idx} className={styles.ruleRow} style={{ marginBottom: 10 }}>
                    <select
                      value={rule.field}
                      onChange={(e) => handleCreateRuleChange(idx, "field", e.target.value)}
                      className={styles.select}
                      aria-label={`Rule ${idx + 1} field`}
                    >
                      <option value="status">Status</option>
                      <option value="source">Source</option>
                      <option value="tag">Tag</option>
                      <option value="email">Email</option>
                      <option value="first_name">First name</option>
                      <option value="last_name">Last name</option>
                      <option value="phone">Phone</option>
                      <option value="created_at">Created date</option>
                      {customFields.length > 0 && (
                        <optgroup label="Custom Fields">
                          {customFields.map((cf) => (
                            <option key={cf.key} value={`custom_field:${cf.key}`}>
                              {cf.label}
                            </option>
                          ))}
                        </optgroup>
                      )}
                    </select>

                    <select
                      value={rule.operator}
                      onChange={(e) => handleCreateRuleChange(idx, "operator", e.target.value)}
                      className={styles.select}
                      aria-label={`Rule ${idx + 1} operator`}
                    >
                      {operators.map((op) => (
                        <option key={op.value} value={op.value}>
                          {op.label}
                        </option>
                      ))}
                    </select>

                    <input
                      type="text"
                      placeholder="Value"
                      value={rule.value}
                      onChange={(e) => handleCreateRuleChange(idx, "value", e.target.value)}
                      className={styles.input}
                      style={{ flex: 1 }}
                      aria-label={`Rule ${idx + 1} value`}
                    />

                    {createForm.rules.length > 1 && (
                      <button
                        type="button"
                        className={styles.viewButton}
                        onClick={() => handleRemoveCreateRule(idx)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                );
              })}

              <button
                type="button"
                className={styles.viewButton}
                onClick={handleAddCreateRule}
                style={{ marginTop: 4, marginBottom: 20 }}
              >
                + Add rule
              </button>

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className={styles.modalCloseButton}
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" disabled={creating} className={styles.submit}>
                  {creating ? "Creating..." : "Create segment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Segment Modal */}
      {editingSegment && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) setEditingSegment(null);
          }}
        >
          <div className={styles.modalContent} style={{ maxWidth: 640 }}>
            <div className={styles.modalHeader}>
              <h3 className={styles.name} style={{ fontSize: 18, margin: 0 }}>
                Edit Segment
              </h3>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={() => setEditingSegment(null)}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>
            <form onSubmit={handleEditSubmit}>
              <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <div style={{ flex: 1 }}>
                  <label className={styles.label} htmlFor="edit-segment-name">
                    Name
                  </label>
                  <input
                    id="edit-segment-name"
                    type="text"
                    required
                    className={styles.input}
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  />
                </div>
                <div style={{ width: 160 }}>
                  <label className={styles.label} htmlFor="edit-segment-type">
                    Type
                  </label>
                  <select
                    id="edit-segment-type"
                    className={styles.select}
                    style={{ width: "100%" }}
                    value={editForm.type}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        type: e.target.value as "DYNAMIC" | "SAVED",
                      })
                    }
                  >
                    <option value="DYNAMIC">Dynamic (live)</option>
                    <option value="SAVED">Saved (snapshot)</option>
                  </select>
                </div>
              </div>

              <h4 style={{ fontSize: 13, fontWeight: 700, margin: "16px 0 8px" }}>Segment Rules</h4>
              {editForm.rules.map((rule, idx) => {
                const operators = getOperatorsForField(rule.field);

                return (
                  <div key={idx} className={styles.ruleRow} style={{ marginBottom: 10 }}>
                    <select
                      value={rule.field}
                      onChange={(e) => handleEditRuleChange(idx, "field", e.target.value)}
                      className={styles.select}
                      aria-label={`Rule ${idx + 1} field`}
                    >
                      <option value="status">Status</option>
                      <option value="source">Source</option>
                      <option value="tag">Tag</option>
                      <option value="email">Email</option>
                      <option value="first_name">First name</option>
                      <option value="last_name">Last name</option>
                      <option value="phone">Phone</option>
                      <option value="created_at">Created date</option>
                      {customFields.length > 0 && (
                        <optgroup label="Custom Fields">
                          {customFields.map((cf) => (
                            <option key={cf.key} value={`custom_field:${cf.key}`}>
                              {cf.label}
                            </option>
                          ))}
                        </optgroup>
                      )}
                    </select>

                    <select
                      value={rule.operator}
                      onChange={(e) => handleEditRuleChange(idx, "operator", e.target.value)}
                      className={styles.select}
                      aria-label={`Rule ${idx + 1} operator`}
                    >
                      {operators.map((op) => (
                        <option key={op.value} value={op.value}>
                          {op.label}
                        </option>
                      ))}
                    </select>

                    <input
                      type="text"
                      placeholder="Value"
                      value={rule.value}
                      onChange={(e) => handleEditRuleChange(idx, "value", e.target.value)}
                      className={styles.input}
                      style={{ flex: 1 }}
                      aria-label={`Rule ${idx + 1} value`}
                    />

                    {editForm.rules.length > 1 && (
                      <button
                        type="button"
                        className={styles.viewButton}
                        onClick={() => handleRemoveEditRule(idx)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                );
              })}

              <button
                type="button"
                className={styles.viewButton}
                onClick={handleAddEditRule}
                style={{ marginTop: 4, marginBottom: 20 }}
              >
                + Add rule
              </button>

              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className={styles.modalCloseButton}
                  onClick={() => setEditingSegment(null)}
                >
                  Cancel
                </button>
                <button type="submit" disabled={updating} className={styles.submit}>
                  {updating ? "Saving..." : "Save changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Segment Confirmation Modal */}
      {deletingSegment && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget && !deleting) setDeletingSegment(null);
          }}
        >
          <div className={styles.modalContent} style={{ maxWidth: 480 }}>
            <div className={styles.modalHeader}>
              <h3 className={styles.name} style={{ fontSize: 18, margin: 0, color: "#dc2626" }}>
                Delete Segment
              </h3>
              <button
                type="button"
                className={styles.modalCloseButton}
                disabled={deleting}
                onClick={() => setDeletingSegment(null)}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>

            <div style={{ margin: "16px 0", fontSize: 14, color: "var(--color-dark-text)" }}>
              Are you sure you want to delete the segment{" "}
              <strong>&ldquo;{deletingSegment.name}&rdquo;</strong>?
              <div style={{ marginTop: 8, fontSize: 12.5, color: "var(--color-slate)" }}>
                This will remove the segment configuration. Contacts in your database will not be
                deleted.
              </div>
            </div>

            {deleteError && (
              <div
                style={{
                  padding: "12px 14px",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: 8,
                  color: "#991b1b",
                  fontSize: 13,
                  marginBottom: 16,
                  lineHeight: 1.4,
                }}
              >
                ⚠️ <strong>Cannot Delete Segment:</strong>
                <div style={{ marginTop: 4 }}>{deleteError}</div>
              </div>
            )}

            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 20 }}>
              <button
                type="button"
                disabled={deleting}
                className={styles.modalCloseButton}
                onClick={() => setDeletingSegment(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={handleDeleteConfirm}
                className={styles.submit}
                style={{
                  background: "#dc2626",
                  boxShadow: "0 2px 10px rgba(220, 38, 38, 0.3)",
                }}
              >
                {deleting ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Segment Members Modal */}
      {selectedSegment && (
        <div
          className={styles.modalBackdrop}
          onClick={(e) => {
            if (e.target === e.currentTarget) closeMemberModal();
          }}
        >
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <div>
                <h3 className={styles.name} style={{ fontSize: 18, margin: "0 0 4px" }}>
                  {selectedSegment.name}
                </h3>
                <span className={styles.typeBadge}>
                  {selectedSegment.type === "DYNAMIC" ? "Dynamic Segment" : "Saved Segment"}
                </span>
              </div>
              <button
                type="button"
                className={styles.modalCloseButton}
                onClick={closeMemberModal}
                aria-label="Close modal"
              >
                Close
              </button>
            </div>

            <div className={styles.detailMeta} style={{ flexDirection: "column", gap: 6 }}>
              <div style={{ fontWeight: 700, color: "var(--color-dark-text)" }}>Rules:</div>
              {selectedSegment.rules.length === 0 ? (
                <div>No rules configured.</div>
              ) : (
                selectedSegment.rules.map((rule) => (
                  <div key={rule.id}>
                    {ruleSummary(rule.field, rule.operator, rule.value, customFields)}
                  </div>
                ))
              )}
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                margin: "20px 0 12px",
                gap: 12,
                flexWrap: "wrap",
              }}
            >
              <h4 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
                Matching Contacts ({filteredMembers.length}
                {memberSearch.trim() ? ` of ${members.length}` : ""})
              </h4>
              <input
                type="text"
                placeholder="🔍 Search name, email, phone…"
                value={memberSearch}
                onChange={(e) => setMemberSearch(e.target.value)}
                className={styles.input}
                style={{ maxWidth: 240, padding: "6px 12px", fontSize: 12 }}
                aria-label="Search matching contacts"
              />
            </div>

            {membersLoading ? (
              <div className={styles.description}>Loading matching contacts…</div>
            ) : members.length === 0 ? (
              <div className={styles.description}>
                No contacts match this segment rule currently.
              </div>
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
                  No contacts match &ldquo;{memberSearch}&rdquo;
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
                {filteredMembers.map((contact) => (
                  <div
                    key={contact.id}
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
                        {[contact.first_name, contact.last_name].filter(Boolean).join(" ") ||
                          "No name"}
                      </div>
                      <div className={styles.email}>
                        {contact.email}
                        {contact.phone ? ` · ${contact.phone}` : ""}
                      </div>
                    </div>
                    <span
                      className={styles.statusActive}
                      style={{
                        padding: "2px 8px",
                        borderRadius: 999,
                        fontSize: 11,
                        fontWeight: 700,
                      }}
                    >
                      {contact.status}
                    </span>
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
