"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./integrations-page.module.css";
import {
  type EmailProvider,
  type EmailProviderConnection,
  type MeResponse,
  PROVIDER_REGISTRY,
  type ProviderDefinition,
  type SenderIdentity,
  type VerificationStatus,
} from "./types";

const MANAGE_PERMISSION = "integrations.manage";

type CategoryFilter = "All Transports" | "Email Transports" | "SMS Gateways" | "Webhooks";

interface ConnectionFormState {
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password: string;
}

function emptyConnectionForm(definition: ProviderDefinition): ConnectionFormState {
  return {
    smtp_host: definition.defaultHost,
    smtp_port: definition.defaultPort,
    smtp_username: "",
    smtp_password: "",
  };
}

const BLANK_CONNECTION_FORM: ConnectionFormState = {
  smtp_host: "",
  smtp_port: "587",
  smtp_username: "",
  smtp_password: "",
};

interface IdentityFormState {
  from_email: string;
  from_name: string;
  reply_to_email: string;
}

const EMPTY_IDENTITY_FORM: IdentityFormState = {
  from_email: "",
  from_name: "",
  reply_to_email: "",
};

function statusBadgeClass(status: VerificationStatus): string | undefined {
  if (status === "VERIFIED") return styles.statusActive;
  if (status === "FAILED") return styles.statusFailed;
  return styles.statusPending;
}

function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/);
  const initials =
    parts.length > 1 ? `${parts[0]?.[0] ?? ""}${parts[1]?.[0] ?? ""}` : parts[0]?.slice(0, 2);
  return (initials || "?").toUpperCase();
}

function ProviderIcon({ name }: { name: string }) {
  let icon = "⚡";
  if (name.includes("Postmark")) icon = "📬";
  if (name.includes("SMTP")) icon = "✉️";
  if (name.includes("Amazon")) icon = "📦";
  if (name.includes("SendGrid")) icon = "🚀";
  if (name.includes("Twilio")) icon = "💬";
  if (name.includes("Webhook")) icon = "🔗";

  return <span className={styles.providerIcon}>{icon}</span>;
}

export function IntegrationsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [connections, setConnections] = useState<
    Partial<Record<EmailProvider, EmailProviderConnection>>
  >({});
  const [identities, setIdentities] = useState<SenderIdentity[]>([]);

  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("All Transports");

  const [connectionFormFor, setConnectionFormFor] = useState<EmailProvider | null>(null);
  const [connectionForm, setConnectionForm] = useState<ConnectionFormState>(BLANK_CONNECTION_FORM);
  const [connectionSaving, setConnectionSaving] = useState(false);
  const [connectionTesting, setConnectionTesting] = useState(false);
  const [webhookReveal, setWebhookReveal] = useState<{
    provider: EmailProvider;
    username: string;
    password: string;
  } | null>(null);

  const [expandedIdentitiesFor, setExpandedIdentitiesFor] = useState<EmailProvider | null>(null);
  const [identityFormFor, setIdentityFormFor] = useState<EmailProvider | null>(null);
  const [identityForm, setIdentityForm] = useState<IdentityFormState>(EMPTY_IDENTITY_FORM);
  const [identitySaving, setIdentitySaving] = useState(false);
  const [pendingIdentityId, setPendingIdentityId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasAccess = me.permissions.includes(MANAGE_PERMISSION);
        setCanManage(hasAccess);

        if (hasAccess) {
          const [connectionList, identityList] = await Promise.all([
            apiFetch<EmailProviderConnection[]>("/integrations/email-providers"),
            apiFetch<SenderIdentity[]>("/integrations/sender-identities"),
          ]);
          const byProvider: Partial<Record<EmailProvider, EmailProviderConnection>> = {};
          for (const connection of connectionList) {
            byProvider[connection.provider] = connection;
          }
          setConnections(byProvider);
          setIdentities(identityList);
        }
      } catch {
        setLoadError("Could not load integration settings.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  function openConnectionForm(definition: ProviderDefinition) {
    setConnectionForm(emptyConnectionForm(definition));
    setConnectionFormFor(definition.key);
  }

  async function handleTestConnection() {
    setConnectionTesting(true);
    try {
      await apiFetch<void>("/integrations/email-providers/test", {
        method: "POST",
        body: JSON.stringify({
          smtp_host: connectionForm.smtp_host,
          smtp_port: Number(connectionForm.smtp_port),
          smtp_username: connectionForm.smtp_username,
          smtp_password: connectionForm.smtp_password,
        }),
      });
      showToast("success", "Connection successful — credentials are valid.");
    } catch (error) {
      let detail = "Connection test failed.";
      if (error instanceof ApiError) {
        try {
          const parsed = JSON.parse(error.message) as { detail?: string };
          if (parsed.detail) detail = parsed.detail;
        } catch {
          // Not JSON
        }
      }
      showToast("error", detail);
    } finally {
      setConnectionTesting(false);
    }
  }

  async function handleConnectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!connectionFormFor) return;
    setConnectionSaving(true);

    try {
      const created = await apiFetch<EmailProviderConnection>("/integrations/email-provider", {
        method: "POST",
        body: JSON.stringify({
          provider: connectionFormFor,
          smtp_host: connectionForm.smtp_host,
          smtp_port: Number(connectionForm.smtp_port),
          smtp_username: connectionForm.smtp_username,
          smtp_password: connectionForm.smtp_password,
        }),
      });
      setConnections((current) => ({ ...current, [connectionFormFor]: created }));
      if (created.webhook_username && created.webhook_password) {
        setWebhookReveal({
          provider: connectionFormFor,
          username: created.webhook_username,
          password: created.webhook_password,
        });
      }
      setConnectionFormFor(null);
      showToast("success", "Provider connection saved.");
    } catch {
      showToast("error", "Could not save the provider connection. Please try again.");
    } finally {
      setConnectionSaving(false);
    }
  }

  async function handleIdentitySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const connection = identityFormFor ? connections[identityFormFor] : undefined;
    if (!connection) return;
    setIdentitySaving(true);

    try {
      const created = await apiFetch<SenderIdentity>("/integrations/sender-identities", {
        method: "POST",
        body: JSON.stringify({
          email_provider_connection_id: connection.id,
          from_email: identityForm.from_email,
          from_name: identityForm.from_name,
          reply_to_email: identityForm.reply_to_email || null,
        }),
      });
      setIdentities((current) => [...current, created]);
      setIdentityForm(EMPTY_IDENTITY_FORM);
      setIdentityFormFor(null);
      showToast("success", "Sender identity added.");
    } catch {
      showToast("error", "Could not add that sender identity. Please try again.");
    } finally {
      setIdentitySaving(false);
    }
  }

  async function handleVerificationChange(identityId: string, status: VerificationStatus) {
    setPendingIdentityId(identityId);
    try {
      const updated = await apiFetch<SenderIdentity>(
        `/integrations/sender-identities/${identityId}/status`,
        { method: "PATCH", body: JSON.stringify({ verification_status: status }) },
      );
      setIdentities((current) => current.map((i) => (i.id === identityId ? updated : i)));
      showToast("success", "Verification status updated.");
    } catch {
      showToast("error", "Could not update the verification status.");
    } finally {
      setPendingIdentityId(null);
    }
  }

  const activeConnectionsCount = useMemo(
    () => Object.values(connections).filter(Boolean).length,
    [connections],
  );

  const activeIdentitiesCount = useMemo(
    () => identities.filter((i) => i.verification_status === "VERIFIED").length,
    [identities],
  );

  const primaryRelayHost = useMemo(() => {
    const active = Object.values(connections).find(Boolean);
    return active ? `${active.smtp_host}:${active.smtp_port}` : "None configured";
  }, [connections]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>Loading integration settings…</div>
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
        <div className={styles.card}>You don&apos;t have access to configure integrations.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Metric Summary Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>🔌</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Active Transports</span>
            <span className={styles.metricValue}>{activeConnectionsCount} Active</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>✉️</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Sender Identities</span>
            <span className={styles.metricValue}>{activeIdentitiesCount} Verified</span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>⚡</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Primary Relay</span>
            <span
              className={styles.metricValue}
              style={{ fontSize: "14px", wordBreak: "break-all" }}
            >
              {primaryRelayHost}
            </span>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>🛡️</div>
          <div className={styles.metricContent}>
            <span className={styles.metricLabel}>Delivery Security</span>
            <span className={styles.metricValue} style={{ fontSize: "15px", color: "#15803d" }}>
              🟢 TLS Verified
            </span>
          </div>
        </div>
      </div>

      {/* Toolbar & Category Pills */}
      <div className={styles.toolbar}>
        <div className={styles.categoryPills}>
          {(["All Transports", "Email Transports", "SMS Gateways", "Webhooks"] as const).map(
            (cat) => (
              <button
                key={cat}
                type="button"
                className={`${styles.categoryPill} ${
                  categoryFilter === cat ? styles.categoryPillActive : ""
                }`}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat}
              </button>
            ),
          )}
        </div>
      </div>

      {/* Active & Available Provider Cards */}
      <div className={styles.grid}>
        {PROVIDER_REGISTRY.map((definition) => {
          const connection = connections[definition.key];
          const connectionIdentities = connection
            ? identities.filter((i) => i.email_provider_connection_id === connection.id)
            : [];
          const showConnectionForm = connectionFormFor === definition.key;
          const showIdentityForm = identityFormFor === definition.key;
          const identitiesExpanded = expandedIdentitiesFor === definition.key;

          return (
            <div className={styles.card} key={definition.key}>
              <div className={styles.header}>
                <div className={styles.headerTitleGroup}>
                  <ProviderIcon name={definition.displayName} />
                  <div>
                    <h3 className={styles.headerTitle}>{definition.displayName}</h3>
                    <p className={styles.headerSubtitle}>{definition.description}</p>
                  </div>
                </div>

                <span
                  className={`${styles.statusBadge} ${
                    connection ? styles.statusActive : styles.statusUnconfigured
                  }`}
                >
                  {connection ? "Connected" : "Unconfigured"}
                </span>
              </div>

              <div className={styles.summaryGrid}>
                <div className={styles.summaryCell}>
                  <span className={styles.summaryLabel}>Identities</span>
                  <span className={styles.summaryValue}>{connectionIdentities.length} active</span>
                </div>
              </div>

              {webhookReveal?.provider === definition.key && (
                <div className={styles.secretReveal}>
                  Webhook credentials generated — copy these now, the password won&apos;t be shown
                  again.
                  {definition.hasWebhook && (
                    <>
                      {" "}
                      Configure them as Basic Auth on the Postmark webhook pointed at{" "}
                      <code>/webhooks/postmark</code>.
                    </>
                  )}
                  <code>
                    {webhookReveal.username}:{webhookReveal.password}
                  </code>
                </div>
              )}

              {connection && !showConnectionForm && (
                <div className={styles.connectionDetails}>
                  <div className={styles.summaryRow}>
                    <span className={styles.summaryLabel}>SMTP Host</span>
                    <span>{connection.smtp_host}</span>
                  </div>
                  <div className={styles.summaryRow}>
                    <span className={styles.summaryLabel}>SMTP Port</span>
                    <span>{connection.smtp_port}</span>
                  </div>
                  <div className={styles.summaryRow}>
                    <span className={styles.summaryLabel}>SMTP User</span>
                    <span>{connection.smtp_username}</span>
                  </div>
                </div>
              )}

              {!connection && !showConnectionForm && (
                <p className={styles.hint}>No connection configured yet.</p>
              )}

              {showConnectionForm && (
                <form className={styles.form} onSubmit={handleConnectionSubmit}>
                  {connection && (
                    <p className={styles.replaceNotice}>
                      Saving replaces the current connection — the previous one is deactivated, not
                      deleted.
                    </p>
                  )}
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`smtp-host-${definition.key}`}>
                      SMTP host
                    </label>
                    <input
                      id={`smtp-host-${definition.key}`}
                      className={styles.input}
                      required
                      value={connectionForm.smtp_host}
                      onChange={(event) =>
                        setConnectionForm({ ...connectionForm, smtp_host: event.target.value })
                      }
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`smtp-port-${definition.key}`}>
                      SMTP port
                    </label>
                    <input
                      id={`smtp-port-${definition.key}`}
                      type="number"
                      className={styles.input}
                      required
                      value={connectionForm.smtp_port}
                      onChange={(event) =>
                        setConnectionForm({ ...connectionForm, smtp_port: event.target.value })
                      }
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`smtp-username-${definition.key}`}>
                      SMTP username
                    </label>
                    <input
                      id={`smtp-username-${definition.key}`}
                      className={styles.input}
                      required
                      value={connectionForm.smtp_username}
                      onChange={(event) =>
                        setConnectionForm({ ...connectionForm, smtp_username: event.target.value })
                      }
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`smtp-password-${definition.key}`}>
                      SMTP password / server token
                    </label>
                    <input
                      id={`smtp-password-${definition.key}`}
                      type="password"
                      className={styles.input}
                      required
                      value={connectionForm.smtp_password}
                      onChange={(event) =>
                        setConnectionForm({ ...connectionForm, smtp_password: event.target.value })
                      }
                    />
                  </div>
                  <div className={styles.formActions}>
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      disabled={
                        connectionTesting ||
                        !connectionForm.smtp_host ||
                        !connectionForm.smtp_port ||
                        !connectionForm.smtp_username ||
                        !connectionForm.smtp_password
                      }
                      onClick={handleTestConnection}
                    >
                      {connectionTesting ? "Testing…" : "Test connection"}
                    </button>
                    <button
                      type="submit"
                      className={styles.actionButton}
                      disabled={connectionSaving}
                    >
                      {connectionSaving ? "Saving…" : "Save connection"}
                    </button>
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => setConnectionFormFor(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}

              <div className={styles.cardActions}>
                {!showConnectionForm && (
                  <button
                    type="button"
                    className={styles.secondaryButton}
                    onClick={() => openConnectionForm(definition)}
                  >
                    {connection ? "Replace connection" : "+ Configure connection"}
                  </button>
                )}
                <button
                  type="button"
                  className={styles.secondaryButton}
                  disabled={!connection}
                  onClick={() =>
                    setExpandedIdentitiesFor(identitiesExpanded ? null : definition.key)
                  }
                >
                  Manage identities
                </button>
              </div>

              {identitiesExpanded && connection && (
                <div className={styles.identitiesSection}>
                  {!showIdentityForm && (
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => setIdentityFormFor(definition.key)}
                    >
                      + Add sender identity
                    </button>
                  )}

                  {showIdentityForm && (
                    <form className={styles.form} onSubmit={handleIdentitySubmit}>
                      <div className={styles.field}>
                        <label
                          className={styles.label}
                          htmlFor={`identity-from-email-${definition.key}`}
                        >
                          From email
                        </label>
                        <input
                          id={`identity-from-email-${definition.key}`}
                          type="email"
                          className={styles.input}
                          required
                          value={identityForm.from_email}
                          onChange={(event) =>
                            setIdentityForm({ ...identityForm, from_email: event.target.value })
                          }
                        />
                      </div>
                      <div className={styles.field}>
                        <label
                          className={styles.label}
                          htmlFor={`identity-from-name-${definition.key}`}
                        >
                          From name
                        </label>
                        <input
                          id={`identity-from-name-${definition.key}`}
                          className={styles.input}
                          required
                          value={identityForm.from_name}
                          onChange={(event) =>
                            setIdentityForm({ ...identityForm, from_name: event.target.value })
                          }
                        />
                      </div>
                      <div className={styles.field}>
                        <label
                          className={styles.label}
                          htmlFor={`identity-reply-to-${definition.key}`}
                        >
                          Reply-to email (optional)
                        </label>
                        <input
                          id={`identity-reply-to-${definition.key}`}
                          type="email"
                          className={styles.input}
                          value={identityForm.reply_to_email}
                          onChange={(event) =>
                            setIdentityForm({ ...identityForm, reply_to_email: event.target.value })
                          }
                        />
                      </div>
                      <div className={styles.formActions}>
                        <button
                          type="submit"
                          className={styles.actionButton}
                          disabled={identitySaving}
                        >
                          {identitySaving ? "Saving…" : "Add identity"}
                        </button>
                        <button
                          type="button"
                          className={styles.secondaryButton}
                          onClick={() => setIdentityFormFor(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}

                  {connectionIdentities.length === 0 && !showIdentityForm && (
                    <p className={styles.hint}>No sender identities yet.</p>
                  )}

                  {connectionIdentities.map((identity) => (
                    <div className={styles.identityRow} key={identity.id}>
                      <div className={styles.identityAvatar}>{initialsFor(identity.from_name)}</div>
                      <div className={styles.identity}>
                        <div className={styles.identityName}>{identity.from_name}</div>
                        <div className={styles.identityEmail}>{identity.from_email}</div>
                      </div>
                      <div className={styles.identityActions}>
                        <span
                          className={`${styles.statusBadge} ${statusBadgeClass(identity.verification_status)}`}
                        >
                          {identity.verification_status}
                        </span>
                        <select
                          className={styles.select}
                          value={identity.verification_status}
                          disabled={pendingIdentityId === identity.id}
                          onChange={(event) =>
                            handleVerificationChange(
                              identity.id,
                              event.target.value as VerificationStatus,
                            )
                          }
                        >
                          <option value="PENDING">PENDING</option>
                          <option value="VERIFIED">VERIFIED</option>
                          <option value="FAILED">FAILED</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Upcoming Provider Placeholders */}
        {(categoryFilter === "All Transports" || categoryFilter === "Email Transports") && (
          <>
            <div className={`${styles.card} ${styles.cardDisabled}`}>
              <div className={styles.header}>
                <div className={styles.headerTitleGroup}>
                  <ProviderIcon name="Amazon SES" />
                  <div>
                    <h3 className={styles.headerTitle}>Amazon SES</h3>
                    <p className={styles.headerSubtitle}>High-volume AWS SMTP / API relay.</p>
                  </div>
                </div>
                <span className={styles.comingSoonBadge}>Coming Soon</span>
              </div>
              <p className={styles.hint}>Native AWS SES SDK integration for bulk campaigns.</p>
            </div>

            <div className={`${styles.card} ${styles.cardDisabled}`}>
              <div className={styles.header}>
                <div className={styles.headerTitleGroup}>
                  <ProviderIcon name="SendGrid" />
                  <div>
                    <h3 className={styles.headerTitle}>SendGrid</h3>
                    <p className={styles.headerSubtitle}>Twilio SendGrid API engine.</p>
                  </div>
                </div>
                <span className={styles.comingSoonBadge}>Coming Soon</span>
              </div>
              <p className={styles.hint}>SendGrid transactional and marketing web API.</p>
            </div>
          </>
        )}

        {(categoryFilter === "All Transports" || categoryFilter === "SMS Gateways") && (
          <div className={`${styles.card} ${styles.cardDisabled}`}>
            <div className={styles.header}>
              <div className={styles.headerTitleGroup}>
                <ProviderIcon name="Twilio SMS" />
                <div>
                  <h3 className={styles.headerTitle}>Twilio SMS</h3>
                  <p className={styles.headerSubtitle}>Global SMS messaging &amp; OTP gateway.</p>
                </div>
              </div>
              <span className={styles.comingSoonBadge}>Coming Soon</span>
            </div>
            <p className={styles.hint}>Multi-channel SMS campaigns and 2FA notifications.</p>
          </div>
        )}
      </div>
    </div>
  );
}
