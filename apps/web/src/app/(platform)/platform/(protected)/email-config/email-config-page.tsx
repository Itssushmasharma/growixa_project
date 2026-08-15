"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./email-config-page.module.css";
import {
  type EmailProvider,
  PROVIDER_DEFINITIONS,
  type PlatformEmailProviderConfig,
} from "./types";

interface FormState {
  provider: EmailProvider;
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password: string;
  from_email: string;
  from_name: string;
}

function definitionFor(provider: EmailProvider) {
  return PROVIDER_DEFINITIONS.find((d) => d.key === provider) ?? PROVIDER_DEFINITIONS[0]!;
}

function blankForm(): FormState {
  const postmark = definitionFor("POSTMARK");
  return {
    provider: "POSTMARK",
    smtp_host: postmark.defaultHost,
    smtp_port: String(postmark.defaultPort),
    smtp_username: "",
    smtp_password: "",
    from_email: "",
    from_name: "Growixa",
  };
}

function formFromConfig(config: PlatformEmailProviderConfig): FormState {
  return {
    provider: config.provider,
    smtp_host: config.smtp_host,
    smtp_port: String(config.smtp_port),
    smtp_username: config.smtp_username,
    smtp_password: "",
    from_email: config.from_email,
    from_name: config.from_name,
  };
}

function errorDetail(error: unknown, fallback: string): string {
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

export function EmailConfigPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [config, setConfig] = useState<PlatformEmailProviderConfig | null>(null);
  const [form, setForm] = useState<FormState>(blankForm());
  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const current = await apiFetch<PlatformEmailProviderConfig | null>(
          "/platform/email-config",
        );
        setConfig(current);
        setForm(current ? formFromConfig(current) : blankForm());
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to configure the email provider.");
        } else {
          setLoadError("Could not load the email provider configuration.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  function handleProviderChange(provider: EmailProvider) {
    const definition = definitionFor(provider);
    setForm((current) => ({
      ...current,
      provider,
      smtp_host: definition.defaultHost || current.smtp_host,
      smtp_port: String(definition.defaultPort),
    }));
  }

  function payload() {
    return {
      provider: form.provider,
      smtp_host: form.smtp_host,
      smtp_port: Number(form.smtp_port),
      smtp_username: form.smtp_username,
      smtp_password: form.smtp_password,
      from_email: form.from_email,
      from_name: form.from_name,
    };
  }

  const isValid =
    form.smtp_host.trim() !== "" &&
    form.smtp_port.trim() !== "" &&
    form.smtp_username.trim() !== "" &&
    form.smtp_password.trim() !== "" &&
    form.from_email.trim() !== "" &&
    form.from_name.trim() !== "";

  async function handleTestConnection() {
    setTesting(true);
    try {
      await apiFetch<void>("/platform/email-config/test", {
        method: "POST",
        body: JSON.stringify(payload()),
      });
      showToast("success", "Connection successful — credentials are valid.");
    } catch (err) {
      showToast("error", errorDetail(err, "Connection test failed."));
    } finally {
      setTesting(false);
    }
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    try {
      const saved = await apiFetch<PlatformEmailProviderConfig>("/platform/email-config", {
        method: "PUT",
        body: JSON.stringify(payload()),
      });
      setConfig(saved);
      setForm(formFromConfig(saved));
      showToast("success", "Platform email provider saved.");
    } catch (err) {
      showToast("error", errorDetail(err, "Could not save the email provider configuration."));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.headerTitle}>Platform email provider</h2>
            <p className={styles.headerSubtitle}>
              Used for system/transactional email (e.g. registration verification links). Falls back
              to the legacy .env-configured SMTP settings when nothing is saved here.
            </p>
          </div>
          <span
            className={`${styles.statusBadge} ${config ? styles.statusActive : styles.statusUnconfigured}`}
          >
            {config ? "Configured" : "Using .env fallback"}
          </span>
        </div>

        {config && (
          <div className={styles.connectionDetails}>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Provider</span>
              <span>{definitionFor(config.provider).displayName}</span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>SMTP host</span>
              <span className={styles.summaryValueMono}>
                {config.smtp_host}:{config.smtp_port}
              </span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>From</span>
              <span>
                {config.from_name} &lt;{config.from_email}&gt;
              </span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Last updated</span>
              <span>{new Date(config.updated_at).toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      <div className={styles.card}>
        <h3 className={styles.headerTitle}>Email provider settings</h3>
        <p className={styles.headerSubtitle}>
          {config
            ? "Saving replaces the current config — the previous one is deactivated, not deleted."
            : "No provider is configured yet — the .env-only PLATFORM_SMTP_* settings are used until one is saved here."}
        </p>

        <form className={styles.form} onSubmit={handleSave}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="email-provider">
              Provider
            </label>
            <select
              id="email-provider"
              className={styles.select}
              value={form.provider}
              onChange={(event) => handleProviderChange(event.target.value as EmailProvider)}
            >
              {PROVIDER_DEFINITIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.displayName}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.fieldRow}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="email-smtp-host">
                SMTP host
              </label>
              <input
                id="email-smtp-host"
                className={styles.input}
                required
                placeholder="smtp.postmarkapp.com"
                value={form.smtp_host}
                onChange={(event) => setForm({ ...form, smtp_host: event.target.value })}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="email-smtp-port">
                Port
              </label>
              <input
                id="email-smtp-port"
                type="number"
                className={styles.input}
                required
                value={form.smtp_port}
                onChange={(event) => setForm({ ...form, smtp_port: event.target.value })}
              />
            </div>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="email-smtp-username">
              {form.provider === "POSTMARK" ? "Server token (username)" : "SMTP username"}
            </label>
            <input
              id="email-smtp-username"
              className={styles.input}
              required
              value={form.smtp_username}
              onChange={(event) => setForm({ ...form, smtp_username: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="email-smtp-password">
              {form.provider === "POSTMARK" ? "Server token (password)" : "SMTP password"}
            </label>
            <div className={styles.apiKeyRow}>
              <input
                id="email-smtp-password"
                type={showPassword ? "text" : "password"}
                className={styles.input}
                required
                value={form.smtp_password}
                onChange={(event) => setForm({ ...form, smtp_password: event.target.value })}
              />
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setShowPassword((v) => !v)}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            {config && (
              <p className={styles.hint}>
                A credential is already saved. Re-enter it (or a new one) to save changes — saving
                always replaces the stored credential.
              </p>
            )}
            {form.provider === "POSTMARK" && (
              <p className={styles.hint}>
                Postmark&apos;s Server API Token is used as both the SMTP username and password.
              </p>
            )}
          </div>

          <div className={styles.fieldRow}>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="email-from-email">
                From email
              </label>
              <input
                id="email-from-email"
                type="email"
                className={styles.input}
                required
                placeholder="noreply@growixa.com"
                value={form.from_email}
                onChange={(event) => setForm({ ...form, from_email: event.target.value })}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="email-from-name">
                From name
              </label>
              <input
                id="email-from-name"
                className={styles.input}
                required
                value={form.from_name}
                onChange={(event) => setForm({ ...form, from_name: event.target.value })}
              />
            </div>
          </div>

          <div className={styles.formActions}>
            <button
              type="button"
              className={styles.secondaryButton}
              disabled={testing || !isValid}
              onClick={handleTestConnection}
            >
              {testing ? "Testing…" : "Test connection"}
            </button>
            <button type="submit" className={styles.actionButton} disabled={saving || !isValid}>
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
