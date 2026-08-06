"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
import type { Contact, MeResponse, Segment } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

const FIELD_LABELS: Record<string, string> = {
  status: "Status",
  source: "Source",
  tag: "Tag",
  email: "Email",
  first_name: "First name",
  last_name: "Last name",
  phone: "Phone",
};

const THEMES = [
  { icon: "👥", bg: "rgba(59, 130, 246, 0.12)", color: "#2563eb", bar: "#3b82f6" },
  { icon: "📰", bg: "rgba(16, 185, 129, 0.12)", color: "#059669", bar: "#10b981" },
  { icon: "⏳", bg: "rgba(245, 158, 11, 0.12)", color: "#d97706", bar: "#f59e0b" },
  { icon: "🎯", bg: "rgba(236, 72, 153, 0.12)", color: "#db2777", bar: "#ec4899" },
  { icon: "⭐", bg: "rgba(139, 92, 246, 0.12)", color: "#7c3aed", bar: "#8b5cf6" },
  { icon: "⚠️", bg: "rgba(239, 68, 68, 0.12)", color: "#dc2626", bar: "#ef4444" },
];

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

function ruleSummary(field: string, operator: string, value: string): string {
  const label = field.startsWith("custom_field:")
    ? `Custom field "${field.split(":", 2)[1]}"`
    : (FIELD_LABELS[field] ?? field);
  return `${label} ${operator} "${value}"`;
}

export function SegmentsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [segments, setSegments] = useState<Segment[]>([]);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState<SegmentFormState>(emptyForm());
  const [creating, setCreating] = useState(false);

  const [selectedSegment, setSelectedSegment] = useState<Segment | null>(null);
  const [members, setMembers] = useState<Contact[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [me, segmentList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<Segment[]>("/contacts/segments"),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setSegments(segmentList);
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
      showToast("success", "Segment created.");
    } catch {
      showToast("error", "Could not create segment.");
    } finally {
      setCreating(false);
    }
  }

  async function openMemberModal(segment: Segment) {
    setSelectedSegment(segment);
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
  }

  function handleRuleChange(index: number, key: keyof SegmentRuleInput, value: string) {
    setCreateForm((current) => {
      const updatedRules = [...current.rules];
      const existing = updatedRules[index] ?? emptyRule();
      updatedRules[index] = { ...existing, [key]: value };
      return { ...current, rules: updatedRules };
    });
  }

  function handleAddRuleField() {
    setCreateForm((current) => ({
      ...current,
      rules: [...current.rules, emptyRule()],
    }));
  }

  function handleRemoveRuleField(index: number) {
    setCreateForm((current) => ({
      ...current,
      rules: current.rules.filter((_, i) => i !== index),
    }));
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
            {segments.map((segment, idx) => {
              const theme = THEMES[idx % THEMES.length]!;
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
                      {percentage}% of contacts
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
                      <span className={styles.typeBadge}>
                        {segment.type === "DYNAMIC" ? "Dynamic" : "Saved"}
                      </span>
                      <span className={styles.countBadge}>{segment.member_count} members</span>
                      <span className={styles.ruleList} style={{ fontSize: 12 }}>
                        {segment.rules.length > 0
                          ? ruleSummary(
                              segment.rules[0]!.field,
                              segment.rules[0]!.operator,
                              segment.rules[0]!.value,
                            )
                          : "No filter"}
                      </span>
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
              {createForm.rules.map((rule, idx) => (
                <div key={idx} className={styles.ruleRow} style={{ marginBottom: 10 }}>
                  <select
                    value={rule.field}
                    onChange={(e) => handleRuleChange(idx, "field", e.target.value)}
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
                  </select>

                  <select
                    value={rule.operator}
                    onChange={(e) => handleRuleChange(idx, "operator", e.target.value)}
                    className={styles.select}
                    aria-label={`Rule ${idx + 1} operator`}
                  >
                    <option value="equals">equals</option>
                    <option value="contains">contains</option>
                    <option value="starts_with">starts_with</option>
                    <option value="ends_with">ends_with</option>
                  </select>

                  <input
                    type="text"
                    placeholder="Value"
                    value={rule.value}
                    onChange={(e) => handleRuleChange(idx, "value", e.target.value)}
                    className={styles.input}
                    style={{ flex: 1 }}
                    aria-label={`Rule ${idx + 1} value`}
                  />

                  {createForm.rules.length > 1 && (
                    <button
                      type="button"
                      className={styles.viewButton}
                      onClick={() => handleRemoveRuleField(idx)}
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}

              <button
                type="button"
                className={styles.viewButton}
                onClick={handleAddRuleField}
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
                  <div key={rule.id}>{ruleSummary(rule.field, rule.operator, rule.value)}</div>
                ))
              )}
            </div>

            <h4 style={{ fontSize: 14, fontWeight: 700, margin: "20px 0 10px" }}>
              Matching Contacts ({members.length})
            </h4>

            {membersLoading ? (
              <div className={styles.description}>Loading matching contacts…</div>
            ) : members.length === 0 ? (
              <div className={styles.description}>
                No contacts match this segment rule currently.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {members.map((contact) => (
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
                      <div className={styles.email}>{contact.email}</div>
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
