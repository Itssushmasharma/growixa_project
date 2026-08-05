"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "./integrations-page.module.css";
import type {
  EmailProviderConnection,
  MeResponse,
  SenderIdentity,
  VerificationStatus,
} from "./types";

const MANAGE_PERMISSION = "integrations.manage";

interface ConnectionFormState {
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password: string;
}

const EMPTY_CONNECTION_FORM: ConnectionFormState = {
  smtp_host: "smtp.postmarkapp.com",
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

export function IntegrationsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [connection, setConnection] = useState<EmailProviderConnection | null>(null);
  const [identities, setIdentities] = useState<SenderIdentity[]>([]);

  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [connectionForm, setConnectionForm] = useState<ConnectionFormState>(EMPTY_CONNECTION_FORM);
  const [connectionSaving, setConnectionSaving] = useState(false);
  // The webhook password is only ever returned once, in this response — shown here
  // until the user navigates away, then it's gone for good (matches EmailProviderConnectionOut's
  // documented one-time-reveal convention, same shape as Team's invite-token banner).
  const [webhookReveal, setWebhookReveal] = useState<{ username: string; password: string } | null>(
    null,
  );

  const [showIdentityForm, setShowIdentityForm] = useState(false);
  const [identityForm, setIdentityForm] = useState<IdentityFormState>(EMPTY_IDENTITY_FORM);
  const [identitySaving, setIdentitySaving] = useState(false);
  const [pendingIdentityId, setPendingIdentityId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasAccess = me.permissions.includes(MANAGE_PERMISSION);
        setCanManage(hasAccess);

        // The connection/identity GETs are themselves gated by integrations.manage on
        // the backend (unlike e.g. /users, which any authenticated user can read) — so
        // skip them entirely for a user without access, rather than letting their 403s
        // reject this Promise.all and mask the friendly access-denied message below
        // with a generic load-error one.
        if (hasAccess) {
          const [activeConnection, identityList] = await Promise.all([
            apiFetch<EmailProviderConnection | null>("/integrations/email-provider"),
            apiFetch<SenderIdentity[]>("/integrations/sender-identities"),
          ]);
          setConnection(activeConnection);
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

  async function handleConnectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setConnectionSaving(true);

    try {
      const created = await apiFetch<EmailProviderConnection>("/integrations/email-provider", {
        method: "POST",
        body: JSON.stringify({
          provider: "POSTMARK",
          smtp_host: connectionForm.smtp_host,
          smtp_port: Number(connectionForm.smtp_port),
          smtp_username: connectionForm.smtp_username,
          smtp_password: connectionForm.smtp_password,
        }),
      });
      setConnection(created);
      if (created.webhook_username && created.webhook_password) {
        setWebhookReveal({
          username: created.webhook_username,
          password: created.webhook_password,
        });
      }
      setConnectionForm(EMPTY_CONNECTION_FORM);
      setShowConnectionForm(false);
      showToast("success", "Provider connection saved.");
    } catch {
      showToast("error", "Could not save the provider connection. Please try again.");
    } finally {
      setConnectionSaving(false);
    }
  }

  async function handleIdentitySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
      setShowIdentityForm(false);
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

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canManage) {
    return <div className={styles.card}>You don&apos;t have access to configure integrations.</div>;
  }

  return (
    <>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>Email provider connection</h2>
          {!showConnectionForm && (
            <button
              type="button"
              className={styles.actionButton}
              onClick={() => setShowConnectionForm(true)}
            >
              {connection ? "Replace connection" : "+ Configure connection"}
            </button>
          )}
        </div>

        {webhookReveal && (
          <div className={styles.secretReveal}>
            Webhook credentials generated — copy these now, the password won&apos;t be shown again.
            Configure them as Basic Auth on the Postmark webhook pointed at{" "}
            <code>/webhooks/postmark</code>.
            <code>
              {webhookReveal.username}:{webhookReveal.password}
            </code>
          </div>
        )}

        {connection && !showConnectionForm && (
          <div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Provider</span>
              <span>{connection.provider}</span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>SMTP host</span>
              <span>{connection.smtp_host}</span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>SMTP port</span>
              <span>{connection.smtp_port}</span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>SMTP username</span>
              <span>{connection.smtp_username}</span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Status</span>
              <span className={`${styles.statusBadge} ${styles.statusActive}`}>Active</span>
            </div>
          </div>
        )}

        {!connection && !showConnectionForm && (
          <p className={styles.hint}>No email provider connected yet.</p>
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
              <label className={styles.label} htmlFor="smtp-host">
                SMTP host
              </label>
              <input
                id="smtp-host"
                className={styles.input}
                required
                value={connectionForm.smtp_host}
                onChange={(event) =>
                  setConnectionForm({ ...connectionForm, smtp_host: event.target.value })
                }
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="smtp-port">
                SMTP port
              </label>
              <input
                id="smtp-port"
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
              <label className={styles.label} htmlFor="smtp-username">
                SMTP username
              </label>
              <input
                id="smtp-username"
                className={styles.input}
                required
                value={connectionForm.smtp_username}
                onChange={(event) =>
                  setConnectionForm({ ...connectionForm, smtp_username: event.target.value })
                }
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="smtp-password">
                SMTP password / server token
              </label>
              <input
                id="smtp-password"
                type="password"
                className={styles.input}
                required
                value={connectionForm.smtp_password}
                onChange={(event) =>
                  setConnectionForm({ ...connectionForm, smtp_password: event.target.value })
                }
              />
            </div>
            <button type="submit" className={styles.actionButton} disabled={connectionSaving}>
              {connectionSaving ? "Saving…" : "Save connection"}
            </button>{" "}
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => setShowConnectionForm(false)}
            >
              Cancel
            </button>
          </form>
        )}
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>Sender identities</h2>
          {!showIdentityForm && (
            <button
              type="button"
              className={styles.actionButton}
              disabled={!connection}
              onClick={() => setShowIdentityForm(true)}
            >
              + Add sender identity
            </button>
          )}
        </div>

        {!connection && <p className={styles.hint}>Configure a provider connection first.</p>}

        {showIdentityForm && (
          <form className={styles.form} onSubmit={handleIdentitySubmit}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="identity-from-email">
                From email
              </label>
              <input
                id="identity-from-email"
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
              <label className={styles.label} htmlFor="identity-from-name">
                From name
              </label>
              <input
                id="identity-from-name"
                className={styles.input}
                required
                value={identityForm.from_name}
                onChange={(event) =>
                  setIdentityForm({ ...identityForm, from_name: event.target.value })
                }
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="identity-reply-to">
                Reply-to email (optional)
              </label>
              <input
                id="identity-reply-to"
                type="email"
                className={styles.input}
                value={identityForm.reply_to_email}
                onChange={(event) =>
                  setIdentityForm({ ...identityForm, reply_to_email: event.target.value })
                }
              />
            </div>
            <button type="submit" className={styles.actionButton} disabled={identitySaving}>
              {identitySaving ? "Saving…" : "Add identity"}
            </button>{" "}
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => setShowIdentityForm(false)}
            >
              Cancel
            </button>
          </form>
        )}

        {identities.map((identity) => (
          <div className={styles.identityRow} key={identity.id}>
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
                  handleVerificationChange(identity.id, event.target.value as VerificationStatus)
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
    </>
  );
}
