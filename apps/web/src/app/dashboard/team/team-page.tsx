"use client";

import { type FormEvent, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import { avatarColorFor, initialsFor } from "./avatar-color";
import styles from "./team-page.module.css";
import type { InviteResult, MeResponse, Role, TeamMember } from "./types";

const MANAGE_PERMISSION = "users.manage";

export function TeamPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);

  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("");
  const [inviteSubmitting, setInviteSubmitting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteResult, setInviteResult] = useState<InviteResult | null>(null);

  const [rowError, setRowError] = useState<string | null>(null);
  const [pendingRowId, setPendingRowId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [me, userList, roleList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<TeamMember[]>("/users"),
          apiFetch<Role[]>("/roles"),
        ]);
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setCurrentUserId(me.id);
        setMembers(userList);
        setRoles(roleList);
        setInviteRole(roleList[0]?.name ?? "");
      } catch {
        setLoadError("Could not load the team.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleInviteSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setInviteError(null);
    setInviteSubmitting(true);

    try {
      const result = await apiFetch<InviteResult>("/users/invitations", {
        method: "POST",
        body: JSON.stringify({ email: inviteEmail, role_name: inviteRole }),
      });
      setInviteResult(result);
      setShowInviteForm(false);
      setInviteEmail("");
    } catch {
      setInviteError("Could not send the invitation. Check the email and role, then try again.");
    } finally {
      setInviteSubmitting(false);
    }
  }

  async function handleRoleChange(userId: string, roleName: string) {
    setRowError(null);
    setPendingRowId(userId);
    try {
      const updated = await apiFetch<TeamMember>(`/users/${userId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role_name: roleName }),
      });
      setMembers((current) => current.map((m) => (m.id === userId ? updated : m)));
    } catch {
      setRowError("Could not change that user's role.");
    } finally {
      setPendingRowId(null);
    }
  }

  async function handleToggleStatus(userId: string, currentStatus: TeamMember["status"]) {
    const nextStatus = currentStatus === "ACTIVE" ? "DISABLED" : "ACTIVE";
    setRowError(null);
    setPendingRowId(userId);
    try {
      const updated = await apiFetch<TeamMember>(`/users/${userId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setMembers((current) => current.map((m) => (m.id === userId ? updated : m)));
    } catch {
      setRowError(
        nextStatus === "DISABLED"
          ? "Could not disable that user (you cannot disable your own account)."
          : "Could not re-enable that user.",
      );
    } finally {
      setPendingRowId(null);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canManage) {
    return <div className={styles.card}>You don&apos;t have access to manage the team.</div>;
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h2 className={styles.headerTitle}>
          Team &amp; roles <span className={styles.headerCount}>· {members.length} members</span>
        </h2>
        {!showInviteForm && (
          <button
            type="button"
            className={styles.inviteButton}
            onClick={() => setShowInviteForm(true)}
          >
            + Invite user
          </button>
        )}
      </div>

      {inviteResult && (
        <div className={styles.inviteSuccess}>
          Invitation sent to {inviteResult.email}. Since there&apos;s no email delivery yet, share
          this link/token with them directly to finish setting up their account:
          <code>{inviteResult.token}</code>
        </div>
      )}

      {rowError && <p className={styles.error}>{rowError}</p>}

      {showInviteForm && (
        <form className={styles.inviteForm} onSubmit={handleInviteSubmit}>
          {inviteError && <p className={styles.error}>{inviteError}</p>}
          <div className={styles.inviteField}>
            <label className={styles.label} htmlFor="invite-email">
              Email
            </label>
            <input
              id="invite-email"
              type="email"
              required
              className={styles.input}
              placeholder="name@company.com"
              value={inviteEmail}
              onChange={(event) => setInviteEmail(event.target.value)}
            />
          </div>
          <div className={styles.inviteField}>
            <label className={styles.label} htmlFor="invite-role">
              Role
            </label>
            <select
              id="invite-role"
              className={styles.select}
              value={inviteRole}
              onChange={(event) => setInviteRole(event.target.value)}
            >
              {roles.map((role) => (
                <option key={role.id} value={role.name}>
                  {role.name}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className={styles.submit} disabled={inviteSubmitting}>
            {inviteSubmitting ? "Sending…" : "Send invite"}
          </button>
          <button type="button" className={styles.cancel} onClick={() => setShowInviteForm(false)}>
            Cancel
          </button>
        </form>
      )}

      {members.map((member) => {
        const isSelf = member.id === currentUserId;
        const isPending = pendingRowId === member.id;
        return (
          <div className={styles.row} key={member.id}>
            <div className={styles.avatar} style={{ background: avatarColorFor(member.email) }}>
              {initialsFor(member.full_name)}
            </div>
            <div className={styles.identity}>
              <div className={styles.name}>
                {member.full_name}
                {isSelf && " (you)"}
              </div>
              <div className={styles.email}>{member.email}</div>
            </div>
            <div className={styles.rowActions}>
              <span
                className={`${styles.statusBadge} ${
                  member.status === "ACTIVE" ? styles.statusActive : styles.statusDisabled
                }`}
              >
                {member.status === "ACTIVE" ? "Active" : "Disabled"}
              </span>
              <select
                className={styles.roleSelect}
                value={member.roles[0] ?? ""}
                disabled={isPending}
                onChange={(event) => handleRoleChange(member.id, event.target.value)}
              >
                {roles.map((role) => (
                  <option key={role.id} value={role.name}>
                    {role.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className={styles.toggleButton}
                disabled={isPending || (isSelf && member.status === "ACTIVE")}
                onClick={() => handleToggleStatus(member.id, member.status)}
              >
                {member.status === "ACTIVE" ? "Disable" : "Enable"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
