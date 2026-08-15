"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./email-validation-config-page.module.css";
import {
  type EmailValidationProvider,
  PROVIDER_DEFINITIONS,
  type PlatformEmailValidationProviderConfig,
} from "./types";

interface FormState {
  provider: EmailValidationProvider;
  api_key: string;
}

function definitionFor(provider: EmailValidationProvider) {
  return PROVIDER_DEFINITIONS.find((d) => d.key === provider) ?? PROVIDER_DEFINITIONS[0]!;
}

function blankForm(): FormState {
  return { provider: "CLEAROUT", api_key: "" };
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

export function EmailValidationConfigPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [config, setConfig] = useState<PlatformEmailValidationProviderConfig | null>(null);
  const [form, setForm] = useState<FormState>(blankForm());
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const current = await apiFetch<PlatformEmailValidationProviderConfig | null>(
          "/platform/email-validation-config",
        );
        setConfig(current);
        setForm(current ? { provider: current.provider, api_key: "" } : blankForm());
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to configure email validation.");
        } else {
          setLoadError("Could not load the email-validation provider configuration.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const definition = definitionFor(form.provider);

  async function handleTestConnection() {
    setTesting(true);
    try {
      await apiFetch<void>("/platform/email-validation-config/test", {
        method: "POST",
        body: JSON.stringify({ provider: form.provider, api_key: form.api_key }),
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
      const saved = await apiFetch<PlatformEmailValidationProviderConfig>(
        "/platform/email-validation-config",
        {
          method: "PUT",
          body: JSON.stringify({ provider: form.provider, api_key: form.api_key }),
        },
      );
      setConfig(saved);
      setForm({ provider: saved.provider, api_key: "" });
      showToast("success", "Platform email-validation provider saved.");
    } catch (err) {
      showToast("error", errorDetail(err, "Could not save the provider configuration."));
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
            <h2 className={styles.headerTitle}>Real-time email verification vendor</h2>
            <p className={styles.headerSubtitle}>
              Used for real-time, mailbox-level checks (does this specific address actually exist)
              on paid-plan accounts only. Free-plan accounts always get the free
              syntax/MX/disposable/role check regardless of this setting.
            </p>
          </div>
          <span
            className={`${styles.statusBadge} ${config ? styles.statusActive : styles.statusUnconfigured}`}
          >
            {config ? "Configured" : "Not configured"}
          </span>
        </div>

        {config && (
          <div className={styles.connectionDetails}>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Provider</span>
              <span>{definitionFor(config.provider).displayName}</span>
            </div>
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Last updated</span>
              <span>{new Date(config.updated_at).toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      <div className={styles.card}>
        <h3 className={styles.headerTitle}>Provider settings</h3>
        <p className={styles.headerSubtitle}>
          {config
            ? "Saving replaces the current vendor — the previous one is deactivated, not deleted."
            : "No vendor is configured yet — paid-plan accounts get the free basic check only until one is set."}
        </p>

        <form className={styles.form} onSubmit={handleSave}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="validation-provider">
              Provider
            </label>
            <select
              id="validation-provider"
              className={styles.select}
              value={form.provider}
              onChange={(event) =>
                setForm({ ...form, provider: event.target.value as EmailValidationProvider })
              }
            >
              {PROVIDER_DEFINITIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.displayName}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="validation-api-key">
              API key
            </label>
            <div className={styles.apiKeyRow}>
              <input
                id="validation-api-key"
                type={showApiKey ? "text" : "password"}
                className={styles.input}
                required
                value={form.api_key}
                onChange={(event) => setForm({ ...form, api_key: event.target.value })}
                placeholder={`${definition.displayName} API key`}
              />
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setShowApiKey((v) => !v)}
              >
                {showApiKey ? "Hide" : "Show"}
              </button>
            </div>
            {config && (
              <p className={styles.hint}>
                A key is already saved. Re-enter it (or a new one) to save changes — saving always
                replaces the stored credential.
              </p>
            )}
          </div>

          <div className={styles.formActions}>
            <button
              type="button"
              className={styles.secondaryButton}
              disabled={testing || !form.api_key}
              onClick={handleTestConnection}
            >
              {testing ? "Testing…" : "Test connection"}
            </button>
            <button
              type="submit"
              className={styles.actionButton}
              disabled={saving || !form.api_key}
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
