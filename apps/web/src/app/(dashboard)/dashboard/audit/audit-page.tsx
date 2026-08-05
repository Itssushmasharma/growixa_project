"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import styles from "./audit-page.module.css";
import type { AuditLogEntry, MeResponse, UserSummary } from "./types";

const VIEW_PERMISSION = "audit.view";

export function AuditPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [events, setEvents] = useState<AuditLogEntry[]>([]);
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [entityTypeFilter, setEntityTypeFilter] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasAccess = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasAccess);
        if (hasAccess) {
          // /users is gated on users.manage, not audit.view — safe today because both
          // permissions have identical Super Admin/Admin-only grants per RBAC.md (same
          // reasoning as roles/api.py's list endpoint), used here only to resolve an
          // actor's email for display.
          const [eventList, userList] = await Promise.all([
            apiFetch<AuditLogEntry[]>("/audit"),
            apiFetch<UserSummary[]>("/users"),
          ]);
          setEvents(eventList);
          setUsers(userList);
        }
      } catch {
        setLoadError("Could not load the audit log.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const entityTypes = useMemo(
    () => Array.from(new Set(events.map((event) => event.entity_type))).sort(),
    [events],
  );

  const filteredEvents = entityTypeFilter
    ? events.filter((event) => event.entity_type === entityTypeFilter)
    : events;

  function actorLabel(actorUserId: string | null): string {
    if (!actorUserId) return "System";
    return users.find((user) => user.id === actorUserId)?.email ?? actorUserId;
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view the audit log.</div>;
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Audit log <span className={styles.headerCount}>· {filteredEvents.length}</span>
        </h2>
        {entityTypes.length > 0 && (
          <select
            className={styles.filterSelect}
            aria-label="Filter by entity type"
            value={entityTypeFilter}
            onChange={(event) => setEntityTypeFilter(event.target.value)}
          >
            <option value="">All entity types</option>
            {entityTypes.map((entityType) => (
              <option key={entityType} value={entityType}>
                {entityType}
              </option>
            ))}
          </select>
        )}
      </div>

      {filteredEvents.length === 0 && <p className={styles.emptyState}>No audit events yet.</p>}

      {filteredEvents.map((event) => (
        <div className={styles.row} key={event.id}>
          <div className={styles.identity}>
            <div className={styles.name}>{event.action}</div>
            <div className={styles.description}>
              {actorLabel(event.actor_user_id)} · {new Date(event.created_at).toLocaleString()}
              {Object.keys(event.event_metadata).length > 0
                ? ` · ${JSON.stringify(event.event_metadata)}`
                : ""}
            </div>
          </div>
          <span className={styles.typeBadge}>{event.entity_type}</span>
        </div>
      ))}
    </div>
  );
}
