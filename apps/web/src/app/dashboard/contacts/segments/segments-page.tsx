"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
import type { Contact, MeResponse, Segment } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

const FIELD_OPERATORS: Record<string, string[]> = {
  status: ["equals"],
  email: ["equals", "contains"],
  source: ["equals"],
  tag: ["equals"],
  created_at: ["before", "after"],
  custom_field: ["equals", "contains"],
};

const FIELD_LABELS: Record<string, string> = {
  status: "Status",
  email: "Email",
  source: "Source",
  tag: "Tag",
  created_at: "Created at",
  custom_field: "Custom field",
};

interface RuleDraft {
  field: string;
  customFieldKey: string;
  operator: string;
  value: string;
}

function emptyRule(): RuleDraft {
  return { field: "status", customFieldKey: "", operator: "equals", value: "" };
}

interface SegmentFormState {
  name: string;
  type: "DYNAMIC" | "SAVED";
  rules: RuleDraft[];
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

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState<SegmentFormState>(emptyForm());
  const [creating, setCreating] = useState(false);

  const [expandedId, setExpandedId] = useState<string | null>(null);
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

  function updateRule(index: number, patch: Partial<RuleDraft>) {
    setCreateForm((current) => ({
      ...current,
      rules: current.rules.map((rule, i) => (i === index ? { ...rule, ...patch } : rule)),
    }));
  }

  function addRuleRow() {
    setCreateForm((current) => ({ ...current, rules: [...current.rules, emptyRule()] }));
  }

  function removeRuleRow(index: number) {
    setCreateForm((current) => ({
      ...current,
      rules: current.rules.filter((_, i) => i !== index),
    }));
  }

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);

    try {
      const rules = createForm.rules.map((rule) => ({
        field: rule.field === "custom_field" ? `custom_field:${rule.customFieldKey}` : rule.field,
        operator: rule.operator,
        value: rule.value,
      }));
      const created = await apiFetch<Segment>("/contacts/segments", {
        method: "POST",
        body: JSON.stringify({ name: createForm.name, type: createForm.type, rules }),
      });
      setSegments((current) => [created, ...current]);
      setShowCreateForm(false);
      setCreateForm(emptyForm());
      showToast("success", "Segment created.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 400) {
        showToast("error", "Check your segment rules — one of them isn't valid.");
      } else {
        showToast("error", "Could not create the segment.");
      }
    } finally {
      setCreating(false);
    }
  }

  async function toggleExpand(segment: Segment) {
    if (expandedId === segment.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(segment.id);
    setMembersLoading(true);
    try {
      const memberList = await apiFetch<Contact[]>(`/contacts/segments/${segment.id}/members`);
      setMembers(memberList);
    } catch {
      showToast("error", "Could not load this segment's members.");
    } finally {
      setMembersLoading(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view segments.</div>;
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Segments <span className={styles.headerCount}>· {segments.length}</span>
        </h2>
        {canManage && !showCreateForm && (
          <button
            type="button"
            className={styles.addButton}
            onClick={() => setShowCreateForm(true)}
          >
            + Add segment
          </button>
        )}
      </div>

      {showCreateForm && (
        <form className={styles.createForm} onSubmit={handleCreateSubmit}>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="segment-name">
              Name
            </label>
            <input
              id="segment-name"
              required
              className={styles.input}
              value={createForm.name}
              onChange={(event) =>
                setCreateForm((current) => ({ ...current, name: event.target.value }))
              }
            />
          </div>
          <div className={styles.createField}>
            <label className={styles.label} htmlFor="segment-type">
              Type
            </label>
            <select
              id="segment-type"
              className={styles.select}
              value={createForm.type}
              onChange={(event) =>
                setCreateForm((current) => ({
                  ...current,
                  type: event.target.value as "DYNAMIC" | "SAVED",
                }))
              }
            >
              <option value="DYNAMIC">Dynamic (live)</option>
              <option value="SAVED">Saved (frozen)</option>
            </select>
          </div>

          <div style={{ flexBasis: "100%" }}>
            {createForm.rules.map((rule, index) => (
              <div className={styles.ruleRow} key={index}>
                <select
                  className={styles.select}
                  aria-label={`Rule ${index + 1} field`}
                  value={rule.field}
                  onChange={(event) =>
                    updateRule(index, {
                      field: event.target.value,
                      operator: FIELD_OPERATORS[event.target.value]?.[0] ?? "equals",
                    })
                  }
                >
                  {Object.keys(FIELD_OPERATORS).map((field) => (
                    <option key={field} value={field}>
                      {FIELD_LABELS[field]}
                    </option>
                  ))}
                </select>
                {rule.field === "custom_field" && (
                  <input
                    className={styles.input}
                    placeholder="Custom field key"
                    aria-label={`Rule ${index + 1} custom field key`}
                    value={rule.customFieldKey}
                    onChange={(event) => updateRule(index, { customFieldKey: event.target.value })}
                  />
                )}
                <select
                  className={styles.select}
                  aria-label={`Rule ${index + 1} operator`}
                  value={rule.operator}
                  onChange={(event) => updateRule(index, { operator: event.target.value })}
                >
                  {(FIELD_OPERATORS[rule.field] ?? []).map((operator) => (
                    <option key={operator} value={operator}>
                      {operator}
                    </option>
                  ))}
                </select>
                <input
                  className={styles.input}
                  placeholder="Value"
                  aria-label={`Rule ${index + 1} value`}
                  value={rule.value}
                  onChange={(event) => updateRule(index, { value: event.target.value })}
                />
                {createForm.rules.length > 1 && (
                  <button
                    type="button"
                    className={styles.cancel}
                    onClick={() => removeRuleRow(index)}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
            <button type="button" className={styles.toggleButton} onClick={addRuleRow}>
              + Add rule
            </button>
          </div>

          <button type="submit" className={styles.submit} disabled={creating}>
            {creating ? "Creating…" : "Create segment"}
          </button>
          <button type="button" className={styles.cancel} onClick={() => setShowCreateForm(false)}>
            Cancel
          </button>
        </form>
      )}

      {segments.length === 0 && <p className={styles.emptyState}>No segments yet.</p>}

      {segments.map((segment) => {
        const isExpanded = expandedId === segment.id;
        return (
          <div className={styles.contactBlock} key={segment.id}>
            <div className={styles.row}>
              <div className={styles.identity}>
                <div className={styles.name}>{segment.name}</div>
                <ul className={styles.ruleList}>
                  {segment.rules.map((rule) => (
                    <li key={rule.id}>{ruleSummary(rule.field, rule.operator, rule.value)}</li>
                  ))}
                </ul>
              </div>
              <div className={styles.rowActions}>
                <span className={styles.typeBadge}>
                  {segment.type === "DYNAMIC" ? "Dynamic" : "Saved"}
                </span>
                <span className={styles.countBadge}>{segment.member_count} members</span>
                <button
                  type="button"
                  className={styles.viewButton}
                  onClick={() => toggleExpand(segment)}
                >
                  {isExpanded ? "Close" : "View members"}
                </button>
              </div>
            </div>

            {isExpanded && (
              <div className={styles.detailPanel}>
                {membersLoading && <p className={styles.emptyState}>Loading members…</p>}
                {!membersLoading && members.length === 0 && (
                  <p className={styles.emptyState}>No members match this segment.</p>
                )}
                {!membersLoading && members.length > 0 && (
                  <ul className={styles.ruleList}>
                    {members.map((member) => (
                      <li key={member.id}>{member.email}</li>
                    ))}
                  </ul>
                )}
                {!canManage && (
                  <p className={styles.readOnlyNote}>You have view-only access to segments.</p>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
