"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { avatarColorFor, initialsFor } from "./avatar-color";
import styles from "./team-page.module.css";
import type { InviteResult, MeResponse, Role, TeamMember } from "./types";

const MANAGE_PERMISSION = "users.manage";

export function TeamPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);

  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("All");

  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("");
  const [inviteSubmitting, setInviteSubmitting] = useState(false);
  const [inviteResult, setInviteResult] = useState<InviteResult | null>(null);

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
    setInviteSubmitting(true);

    try {
      const result = await apiFetch<InviteResult>("/users/invitations", {
        method: "POST",
        body: JSON.stringify({ email: inviteEmail, role_name: inviteRole }),
      });
      setInviteResult(result);
      setShowInviteForm(false);
      setInviteEmail("");
      showToast("success", `Invitation sent to ${result.email}`);
    } catch {
      showToast(
        "error",
        "Could not send the invitation. Check the email and role, then try again.",
      );
    } finally {
      setInviteSubmitting(false);
    }
  }

  async function handleRoleChange(userId: string, roleName: string) {
    setPendingRowId(userId);
    try {
      const updated = await apiFetch<TeamMember>(`/users/${userId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role_name: roleName }),
      });
      setMembers((current) => current.map((m) => (m.id === userId ? updated : m)));
      showToast("success", `Role updated to ${roleName}.`);
    } catch {
      showToast("error", "Could not change that user's role.");
    } finally {
      setPendingRowId(null);
    }
  }

  async function handleToggleStatus(userId: string, currentStatus: TeamMember["status"]) {
    const nextStatus = currentStatus === "ACTIVE" ? "DISABLED" : "ACTIVE";
    setPendingRowId(userId);
    try {
      const updated = await apiFetch<TeamMember>(`/users/${userId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      });
      setMembers((current) => current.map((m) => (m.id === userId ? updated : m)));
      showToast("success", nextStatus === "DISABLED" ? "User disabled." : "User enabled.");
    } catch {
      showToast(
        "error",
        nextStatus === "DISABLED"
          ? "Could not disable that user (you cannot disable your own account)."
          : "Could not re-enable that user.",
      );
    } finally {
      setPendingRowId(null);
    }
  }

  const superAdminsCount = useMemo(
    () => members.filter((m) => m.roles.includes("Super Admin")).length,
    [members],
  );

  const adminsCount = useMemo(
    () => members.filter((m) => m.roles.includes("Admin")).length,
    [members],
  );

  const visibleMembers = useMemo(() => {
    const query = search.trim().toLowerCase();
    let filtered = query
      ? members.filter(
          (m) => m.full_name.toLowerCase().includes(query) || m.email.toLowerCase().includes(query),
        )
      : members;

    if (roleFilter !== "All") {
      filtered = filtered.filter((m) => m.roles.includes(roleFilter));
    }

    return filtered;
  }, [members, search, roleFilter]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>Loading team…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>{loadError}</div>
      </div>
    );
  }

  if (!canManage) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to manage the team.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Metric Summary Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>👥</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Total Members</span>
            <span className={styles.metricValue}>{members.length}</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>👑</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Super Admins</span>
            <span className={styles.metricValue}>{superAdminsCount}</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>🛡️</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Admins</span>
            <span className={styles.metricValue}>{adminsCount}</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>✉️</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Pending Invites</span>
            <span className={styles.metricValue}>{inviteResult ? 1 : 0}</span>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className={styles.card}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.headerTitle}>Team &amp; Role Management</h2>
            <p className={styles.headerSubtitle}>
              Invite team members, assign RBAC permissions, and manage active status.
            </p>
          </div>

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

        {/* Toolbar */}
        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <input
              type="search"
              className={styles.searchInput}
              placeholder="Search team members by name or email…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search team members"
            />

            <div className={styles.rolePills}>
              {["All", "Super Admin", "Admin", "Member"].map((roleName) => (
                <button
                  key={roleName}
                  type="button"
                  className={`${styles.rolePill} ${
                    roleFilter === roleName ? styles.rolePillActive : ""
                  }`}
                  onClick={() => setRoleFilter(roleName)}
                >
                  {roleName}
                </button>
              ))}
            </div>
          </div>
        </div>

        {inviteResult && (
          <div className={styles.inviteSuccess}>
            <span>
              ✅ Invitation created for <strong>{inviteResult.email}</strong>. Share this token to
              complete account setup:
            </span>
            <code>{inviteResult.token}</code>
          </div>
        )}

        {/* Invite Form Card */}
        {showInviteForm && (
          <form className={styles.inviteFormCard} onSubmit={handleInviteSubmit}>
            <h4 className={styles.inviteFormTitle}>+ Invite New Team Member</h4>
            <div className={styles.inviteGrid}>
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

              <button
                type="button"
                className={styles.cancel}
                onClick={() => setShowInviteForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {visibleMembers.length === 0 && (
          <p className={styles.hint}>No team members match your filters.</p>
        )}

        {/* Modern Team Member Cards Grid */}
        <div className={styles.membersGrid}>
          {visibleMembers.map((member) => {
            const isSelf = member.id === currentUserId;
            const isPending = pendingRowId === member.id;
            return (
              <div className={styles.memberCard} key={member.id}>
                <div className={styles.memberHeader}>
                  <div
                    className={styles.avatar}
                    style={{ background: avatarColorFor(member.email) }}
                  >
                    {initialsFor(member.full_name)}
                  </div>

                  <div className={styles.identity}>
                    <div className={styles.memberName}>
                      {member.full_name}
                      {isSelf && " (you)"}
                    </div>
                    <div className={styles.memberEmail}>{member.email}</div>
                  </div>

                  <span
                    className={
                      member.status === "ACTIVE" ? styles.statusActive : styles.statusDisabled
                    }
                  >
                    {member.status === "ACTIVE" ? "Active" : "Disabled"}
                  </span>
                </div>

                <div className={styles.memberFooter}>
                  <select
                    className={styles.roleSelect}
                    value={member.roles[0] ?? ""}
                    disabled={isPending}
                    onChange={(event) => handleRoleChange(member.id, event.target.value)}
                    aria-label={`Role for ${member.full_name}`}
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
      </div>
    </div>
  );
}
