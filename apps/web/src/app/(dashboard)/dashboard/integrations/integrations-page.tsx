"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";
import { getApiUrl } from "@/lib/env";

import styles from "./integrations-page.module.css";
import {
  AI_PROVIDER_DEFINITIONS,
  type AIProvider,
  type AIProviderConnection,
  type EmailProvider,
  type EmailProviderConnection,
  type MeResponse,
  PROVIDER_REGISTRY,
  type ProviderDefinition,
  type SenderIdentity,
  type SocialConnection,
  type VerificationStatus,
} from "./types";

const MANAGE_PERMISSION = "integrations.manage";

type CategoryFilter = "All Transports" | "Email Transports" | "SMS Gateways" | "Webhooks";

interface ConnectionFormState {
  name: string;
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password: string;
}

function emptyConnectionForm(definition: ProviderDefinition): ConnectionFormState {
  return {
    name: definition.displayName,
    smtp_host: definition.defaultHost,
    smtp_port: definition.defaultPort,
    smtp_username: "",
    smtp_password: "",
  };
}

const BLANK_CONNECTION_FORM: ConnectionFormState = {
  name: "",
  smtp_host: "",
  smtp_port: "587",
  smtp_username: "",
  smtp_password: "",
};

interface AIConnectionFormState {
  provider: AIProvider;
  base_url: string;
  api_key: string;
  default_model: string;
}

function blankAIConnectionForm(): AIConnectionFormState {
  return { provider: "OPENAI", base_url: "", api_key: "", default_model: "" };
}

function aiDefinitionFor(provider: AIProvider) {
  return AI_PROVIDER_DEFINITIONS.find((d) => d.key === provider) ?? AI_PROVIDER_DEFINITIONS[0]!;
}

function apiErrorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      // Not JSON
    }
  }
  return fallback;
}

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
  if (name.includes("Instagram")) icon = "📸";
  if (name.includes("AI Model")) icon = "🤖";

  return <span className={styles.providerIcon}>{icon}</span>;
}

export function IntegrationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [connections, setConnections] = useState<
    Partial<Record<EmailProvider, EmailProviderConnection>>
  >({});
  const [identities, setIdentities] = useState<SenderIdentity[]>([]);
  const [socialConnection, setSocialConnection] = useState<SocialConnection | null>(null);
  const [aiConnection, setAiConnection] = useState<AIProviderConnection | null>(null);
  const [aiFormOpen, setAiFormOpen] = useState(false);
  const [aiForm, setAiForm] = useState<AIConnectionFormState>(blankAIConnectionForm());
  const [showAiApiKey, setShowAiApiKey] = useState(false);
  const [aiTesting, setAiTesting] = useState(false);
  const [aiSaving, setAiSaving] = useState(false);
  const [aiDeactivating, setAiDeactivating] = useState(false);

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
          const [connectionList, identityList, socialConnections, aiConnections] =
            await Promise.all([
              apiFetch<EmailProviderConnection[]>("/integrations/email-providers"),
              apiFetch<SenderIdentity[]>("/integrations/sender-identities"),
              apiFetch<SocialConnection[]>("/social/connections"),
              apiFetch<AIProviderConnection[]>("/ai/connections"),
            ]);
          const byProvider: Partial<Record<EmailProvider, EmailProviderConnection>> = {};
          for (const connection of connectionList) {
            byProvider[connection.provider] = connection;
          }
          setConnections(byProvider);
          setIdentities(identityList);
          setSocialConnection(socialConnections[0] ?? null);
          setAiConnection(aiConnections[0] ?? null);
        }
      } catch {
        setLoadError("Could not load integration settings.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  // GRX-SOCIAL-003: Meta redirects the browser back here after the OAuth flow completes
  // (success or failure) — surface the outcome as a toast, then strip the query params
  // so a page refresh doesn't re-show it.
  useEffect(() => {
    const instagramResult = searchParams.get("instagram");
    if (!instagramResult) return;
    if (instagramResult === "connected") {
      showToast("success", "Instagram account connected.");
    } else {
      const reason = searchParams.get("reason");
      showToast(
        "error",
        reason === "denied"
          ? "Instagram connection was cancelled."
          : "Could not connect that Instagram account. Please try again.",
      );
    }
    router.replace("/dashboard/integrations");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

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
      const payloadName =
        connectionForm.name.trim() ||
        (connectionFormFor === "POSTMARK"
          ? "Postmark"
          : connectionForm.smtp_host || "Primary SMTP");
      const existingConn = connections[connectionFormFor];
      const created = await apiFetch<EmailProviderConnection>("/integrations/email-provider", {
        method: "POST",
        body: JSON.stringify({
          name: payloadName,
          provider: connectionFormFor,
          smtp_host: connectionForm.smtp_host,
          smtp_port: Number(connectionForm.smtp_port),
          smtp_username: connectionForm.smtp_username,
          smtp_password: connectionForm.smtp_password,
          replacing_connection_id: existingConn ? existingConn.id : undefined,
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
      try {
        const refreshedIdentities = await apiFetch<SenderIdentity[]>(
          "/integrations/sender-identities",
        );
        setIdentities(refreshedIdentities);
      } catch {
        // Non-blocking fallback
      }
      setConnectionFormFor(null);
      showToast("success", "Provider connection saved.");
    } catch (error) {
      showToast(
        "error",
        apiErrorDetail(error, "Could not save the provider connection. Please try again."),
      );
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

  async function handleDeleteIdentity(identity: SenderIdentity) {
    if (
      !window.confirm(
        `Are you sure you want to delete sender identity "${identity.from_email}"? This action cannot be undone.`,
      )
    ) {
      return;
    }
    setPendingIdentityId(identity.id);
    try {
      await apiFetch<void>(`/integrations/sender-identities/${identity.id}`, {
        method: "DELETE",
      });
      setIdentities((current) => current.filter((i) => i.id !== identity.id));
      showToast("success", `Sender identity "${identity.from_email}" deleted.`);
    } catch (error) {
      showToast("error", apiErrorDetail(error, "Could not delete sender identity."));
    } finally {
      setPendingIdentityId(null);
    }
  }

  function openAiConnectionForm() {
    setAiForm(blankAIConnectionForm());
    setShowAiApiKey(false);
    setAiFormOpen(true);
  }

  function handleAiProviderChange(provider: AIProvider) {
    setAiForm((current) => ({ ...current, provider, base_url: "" }));
  }

  async function handleAiTestConnection() {
    setAiTesting(true);
    try {
      await apiFetch<void>("/ai/connections/test", {
        method: "POST",
        body: JSON.stringify({
          provider: aiForm.provider,
          api_key: aiForm.api_key || null,
          base_url: aiForm.base_url || null,
          default_model: aiForm.default_model,
        }),
      });
      showToast("success", "Connection successful — credentials are valid.");
    } catch (error) {
      showToast("error", apiErrorDetail(error, "Connection test failed."));
    } finally {
      setAiTesting(false);
    }
  }

  async function handleAiConnectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAiSaving(true);
    try {
      const created = await apiFetch<AIProviderConnection>("/ai/connections", {
        method: "POST",
        body: JSON.stringify({
          provider: aiForm.provider,
          api_key: aiForm.api_key || null,
          base_url: aiForm.base_url || null,
          default_model: aiForm.default_model,
        }),
      });
      setAiConnection(created);
      setAiFormOpen(false);
      showToast("success", "AI provider connection saved.");
    } catch (error) {
      showToast("error", apiErrorDetail(error, "Could not save the AI provider connection."));
    } finally {
      setAiSaving(false);
    }
  }

  async function handleAiDisconnect() {
    if (!aiConnection) return;
    setAiDeactivating(true);
    try {
      await apiFetch<AIProviderConnection>(`/ai/connections/${aiConnection.id}/deactivate`, {
        method: "POST",
      });
      setAiConnection(null);
      showToast("success", "AI provider connection removed — the platform default will be used.");
    } catch {
      showToast("error", "Could not remove the AI provider connection.");
    } finally {
      setAiDeactivating(false);
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

      {/* Social Publishing (Slice 5) */}
      <div className={styles.grid}>
        <div className={styles.card}>
          <div className={styles.header}>
            <div className={styles.headerTitleGroup}>
              <ProviderIcon name="Instagram" />
              <div>
                <h3 className={styles.headerTitle}>Instagram Business</h3>
                <p className={styles.headerSubtitle}>
                  Publish and schedule posts to your connected Instagram Business account.
                </p>
              </div>
            </div>
            <span
              className={`${styles.statusBadge} ${
                socialConnection ? styles.statusActive : styles.statusUnconfigured
              }`}
            >
              {socialConnection ? "Connected" : "Unconfigured"}
            </span>
          </div>

          {socialConnection ? (
            <div className={styles.connectionDetails}>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Account</span>
                <span>
                  {socialConnection.ig_username ?? socialConnection.ig_business_account_id}
                </span>
              </div>
              {socialConnection.last_error && (
                <p className={styles.hint}>Last error: {socialConnection.last_error}</p>
              )}
            </div>
          ) : (
            <p className={styles.hint}>No Instagram account connected yet.</p>
          )}

          {/* Plain navigation, not apiFetch -- the user must interact with Meta's own
              consent screen, which a fetch/XHR call cannot do. */}
          <div className={styles.cardActions}>
            <a
              href={`${getApiUrl()}/integrations/instagram/oauth/authorize`}
              className={styles.secondaryButton}
            >
              {socialConnection ? "Reconnect Instagram" : "+ Connect Instagram"}
            </a>
          </div>
        </div>

        {/* AI Model Provider (Slice 6, GRX-AI-010) -- bring-your-own AI credentials for
            this account, overriding the platform-wide default (DEC-GRX-026). */}
        <div className={styles.card}>
          <div className={styles.header}>
            <div className={styles.headerTitleGroup}>
              <ProviderIcon name="AI Model" />
              <div>
                <h3 className={styles.headerTitle}>AI Model Provider</h3>
                <p className={styles.headerSubtitle}>
                  Bring your own OpenAI, Azure OpenAI, Anthropic, or Ollama credentials — overrides
                  the platform default for this account.
                </p>
              </div>
            </div>
            <span
              className={`${styles.statusBadge} ${
                aiConnection ? styles.statusActive : styles.statusUnconfigured
              }`}
            >
              {aiConnection ? "Connected" : "Unconfigured"}
            </span>
          </div>

          {aiConnection && !aiFormOpen && (
            <div className={styles.connectionDetails}>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Provider</span>
                <span>{aiDefinitionFor(aiConnection.provider).displayName}</span>
              </div>
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Model</span>
                <span>{aiConnection.default_model}</span>
              </div>
              {aiConnection.base_url && (
                <div className={styles.summaryRow}>
                  <span className={styles.summaryLabel}>Base URL</span>
                  <span style={{ wordBreak: "break-all" }}>{aiConnection.base_url}</span>
                </div>
              )}
            </div>
          )}

          {!aiConnection && !aiFormOpen && (
            <p className={styles.hint}>No AI provider connected — the platform default is used.</p>
          )}

          {aiFormOpen && (
            <form className={styles.form} onSubmit={handleAiConnectionSubmit}>
              {aiConnection && (
                <p className={styles.replaceNotice}>
                  Saving replaces the current connection — the previous one is deactivated, not
                  deleted.
                </p>
              )}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="ai-connection-provider">
                  Provider
                </label>
                <select
                  id="ai-connection-provider"
                  className={styles.select}
                  value={aiForm.provider}
                  onChange={(event) => handleAiProviderChange(event.target.value as AIProvider)}
                >
                  {AI_PROVIDER_DEFINITIONS.map((option) => (
                    <option key={option.key} value={option.key}>
                      {option.displayName}
                    </option>
                  ))}
                </select>
              </div>

              {(aiDefinitionFor(aiForm.provider).requiresBaseUrl ||
                aiForm.provider === "OPENAI") && (
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="ai-connection-base-url">
                    Base URL
                    {aiDefinitionFor(aiForm.provider).requiresBaseUrl ? "" : " (optional)"}
                  </label>
                  <input
                    id="ai-connection-base-url"
                    className={styles.input}
                    required={aiDefinitionFor(aiForm.provider).requiresBaseUrl}
                    placeholder={
                      aiDefinitionFor(aiForm.provider).requiresBaseUrl
                        ? "https://your-resource.openai.azure.com"
                        : "https://api.openai.com (leave blank for the default)"
                    }
                    value={aiForm.base_url}
                    onChange={(event) => setAiForm({ ...aiForm, base_url: event.target.value })}
                  />
                </div>
              )}

              <div className={styles.field}>
                <label className={styles.label} htmlFor="ai-connection-api-key">
                  API key{aiForm.provider === "OLLAMA" ? " (optional)" : ""}
                </label>
                <div style={{ display: "flex", gap: "8px" }}>
                  <input
                    id="ai-connection-api-key"
                    type={showAiApiKey ? "text" : "password"}
                    className={styles.input}
                    required={aiForm.provider !== "OLLAMA"}
                    value={aiForm.api_key}
                    onChange={(event) => setAiForm({ ...aiForm, api_key: event.target.value })}
                    placeholder="sk-..."
                  />
                  <button
                    type="button"
                    className={styles.secondaryButton}
                    onClick={() => setShowAiApiKey((v) => !v)}
                  >
                    {showAiApiKey ? "Hide" : "Show"}
                  </button>
                </div>
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="ai-connection-model">
                  Default model
                </label>
                <input
                  id="ai-connection-model"
                  className={styles.input}
                  required
                  placeholder={aiDefinitionFor(aiForm.provider).modelPlaceholder}
                  value={aiForm.default_model}
                  onChange={(event) => setAiForm({ ...aiForm, default_model: event.target.value })}
                />
              </div>

              <div className={styles.formActions}>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  disabled={
                    aiTesting ||
                    !aiForm.default_model ||
                    (aiForm.provider !== "OLLAMA" && !aiForm.api_key) ||
                    (aiDefinitionFor(aiForm.provider).requiresBaseUrl && !aiForm.base_url)
                  }
                  onClick={handleAiTestConnection}
                >
                  {aiTesting ? "Testing…" : "Test connection"}
                </button>
                <button
                  type="submit"
                  className={styles.actionButton}
                  disabled={
                    aiSaving ||
                    !aiForm.default_model ||
                    (aiForm.provider !== "OLLAMA" && !aiForm.api_key) ||
                    (aiDefinitionFor(aiForm.provider).requiresBaseUrl && !aiForm.base_url)
                  }
                >
                  {aiSaving ? "Saving…" : "Save connection"}
                </button>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={() => setAiFormOpen(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          <div className={styles.cardActions}>
            {!aiFormOpen && (
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={openAiConnectionForm}
              >
                {aiConnection ? "Replace connection" : "+ Configure connection"}
              </button>
            )}
            {aiConnection && !aiFormOpen && (
              <button
                type="button"
                className={styles.secondaryButton}
                disabled={aiDeactivating}
                onClick={handleAiDisconnect}
              >
                {aiDeactivating ? "Removing…" : "Use platform default instead"}
              </button>
            )}
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
                    <label className={styles.label} htmlFor={`connection-name-${definition.key}`}>
                      Connection name
                    </label>
                    <input
                      id={`connection-name-${definition.key}`}
                      className={styles.input}
                      required
                      placeholder="e.g. Postmark Production, Primary SMTP"
                      value={connectionForm.name}
                      onChange={(event) =>
                        setConnectionForm({ ...connectionForm, name: event.target.value })
                      }
                    />
                  </div>
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
                        {canManage && (
                          <button
                            type="button"
                            className={styles.deleteIdentityButton}
                            disabled={pendingIdentityId === identity.id}
                            title={`Delete ${identity.from_email}`}
                            aria-label={`Delete ${identity.from_email}`}
                            onClick={() => handleDeleteIdentity(identity)}
                          >
                            {pendingIdentityId === identity.id ? "…" : "🗑️ Delete"}
                          </button>
                        )}
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
