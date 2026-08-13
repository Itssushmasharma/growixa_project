"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./ai-config-page.module.css";
import { type AIProvider, PROVIDER_DEFINITIONS, type PlatformAIProviderConfig } from "./types";

interface FormState {
  provider: AIProvider;
  base_url: string;
  api_key: string;
  default_model: string;
}

function definitionFor(provider: AIProvider) {
  return PROVIDER_DEFINITIONS.find((d) => d.key === provider) ?? PROVIDER_DEFINITIONS[0]!;
}

function blankForm(): FormState {
  return { provider: "OPENAI", base_url: "", api_key: "", default_model: "" };
}

function formFromConfig(config: PlatformAIProviderConfig): FormState {
  return {
    provider: config.provider,
    base_url: config.base_url ?? "",
    api_key: "",
    default_model: config.default_model,
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

export function AIConfigPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [config, setConfig] = useState<PlatformAIProviderConfig | null>(null);
  const [form, setForm] = useState<FormState>(blankForm());
  const [showApiKey, setShowApiKey] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const current = await apiFetch<PlatformAIProviderConfig | null>("/platform/ai-config");
        setConfig(current);
        setForm(current ? formFromConfig(current) : blankForm());
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to configure the AI provider.");
        } else {
          setLoadError("Could not load the AI provider configuration.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const definition = definitionFor(form.provider);

  function handleProviderChange(provider: AIProvider) {
    setForm((current) => ({ ...current, provider, base_url: "" }));
  }

  async function handleTestConnection() {
    setTesting(true);
    try {
      await apiFetch<void>("/platform/ai-config/test", {
        method: "POST",
        body: JSON.stringify({
          provider: form.provider,
          api_key: form.api_key || null,
          base_url: form.base_url || null,
          default_model: form.default_model,
        }),
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
      const saved = await apiFetch<PlatformAIProviderConfig>("/platform/ai-config", {
        method: "PUT",
        body: JSON.stringify({
          provider: form.provider,
          api_key: form.api_key || null,
          base_url: form.base_url || null,
          default_model: form.default_model,
        }),
      });
      setConfig(saved);
      setForm(formFromConfig(saved));
      showToast("success", "Platform default AI provider saved.");
    } catch (err) {
      showToast("error", errorDetail(err, "Could not save the AI provider configuration."));
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
            <h2 className={styles.headerTitle}>Platform default LLM provider</h2>
            <p className={styles.headerSubtitle}>
              Used for any account that hasn&apos;t configured its own bring-your-own AI provider.
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
              <span className={styles.summaryLabel}>Default model</span>
              <span>{config.default_model}</span>
            </div>
            {config.base_url && (
              <div className={styles.summaryRow}>
                <span className={styles.summaryLabel}>Base URL</span>
                <span className={styles.summaryValueMono}>{config.base_url}</span>
              </div>
            )}
            <div className={styles.summaryRow}>
              <span className={styles.summaryLabel}>Last updated</span>
              <span>{new Date(config.updated_at).toLocaleString()}</span>
            </div>
          </div>
        )}
      </div>

      <div className={styles.card}>
        <h3 className={styles.headerTitle}>AI provider settings</h3>
        <p className={styles.headerSubtitle}>
          {config
            ? "Saving replaces the current default — the previous one is deactivated, not deleted."
            : "No default provider is configured yet — customers without their own connection cannot generate AI content until one is set."}
        </p>

        <form className={styles.form} onSubmit={handleSave}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="ai-provider">
              Provider
            </label>
            <select
              id="ai-provider"
              className={styles.select}
              value={form.provider}
              onChange={(event) => handleProviderChange(event.target.value as AIProvider)}
            >
              {PROVIDER_DEFINITIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.displayName}
                </option>
              ))}
            </select>
          </div>

          {(definition.requiresBaseUrl || form.provider === "OPENAI") && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="ai-base-url">
                Base URL{definition.requiresBaseUrl ? "" : " (optional)"}
              </label>
              <input
                id="ai-base-url"
                className={styles.input}
                required={definition.requiresBaseUrl}
                placeholder={
                  definition.requiresBaseUrl
                    ? "https://your-resource.openai.azure.com"
                    : "https://api.openai.com (leave blank for the default)"
                }
                value={form.base_url}
                onChange={(event) => setForm({ ...form, base_url: event.target.value })}
              />
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="ai-api-key">
              API key{form.provider === "OLLAMA" ? " (optional)" : ""}
            </label>
            <div className={styles.apiKeyRow}>
              <input
                id="ai-api-key"
                type={showApiKey ? "text" : "password"}
                className={styles.input}
                required={form.provider !== "OLLAMA"}
                value={form.api_key}
                onChange={(event) => setForm({ ...form, api_key: event.target.value })}
                placeholder="sk-..."
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

          <div className={styles.field}>
            <label className={styles.label} htmlFor="ai-default-model">
              Default model
            </label>
            <input
              id="ai-default-model"
              className={styles.input}
              required
              placeholder={definition.modelPlaceholder}
              value={form.default_model}
              onChange={(event) => setForm({ ...form, default_model: event.target.value })}
            />
          </div>

          <div className={styles.formActions}>
            <button
              type="button"
              className={styles.secondaryButton}
              disabled={
                testing ||
                !form.default_model ||
                (form.provider !== "OLLAMA" && !form.api_key) ||
                (definition.requiresBaseUrl && !form.base_url)
              }
              onClick={handleTestConnection}
            >
              {testing ? "Testing…" : "Test connection"}
            </button>
            <button
              type="submit"
              className={styles.actionButton}
              disabled={
                saving ||
                !form.default_model ||
                (form.provider !== "OLLAMA" && !form.api_key) ||
                (definition.requiresBaseUrl && !form.base_url)
              }
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
