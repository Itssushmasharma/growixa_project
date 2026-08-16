"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import type { PlatformAIProviderConfig } from "../ai-config/types";
import type { PlatformEmailProviderConfig } from "../email-config/types";
import type { PlatformEmailValidationProviderConfig } from "../email-validation-config/types";
import styles from "./providers-page.module.css";
import type { ProviderHealthState, ProvidersState } from "./types";

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

export function ProvidersPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [providers, setProviders] = useState<ProvidersState>({
    ai: null,
    email: null,
    validation: null,
  });

  const [health, setHealth] = useState<ProviderHealthState>({
    ai: { status: "idle" },
    email: { status: "idle" },
    validation: { status: "idle" },
  });

  const [testingAll, setTestingAll] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [ai, email, validation] = await Promise.all([
          apiFetch<PlatformAIProviderConfig | null>("/platform/ai-config").catch(() => null),
          apiFetch<PlatformEmailProviderConfig | null>("/platform/email-config").catch(() => null),
          apiFetch<PlatformEmailValidationProviderConfig | null>(
            "/platform/email-validation-config",
          ).catch(() => null),
        ]);
        setProviders({ ai, email, validation });
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to view platform provider configurations.");
        } else {
          setLoadError("Failed to load provider configurations.");
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function testAIConnection() {
    if (!providers.ai) return;
    setHealth((prev) => ({ ...prev, ai: { status: "testing" } }));
    try {
      await apiFetch<void>("/platform/ai-config/test", {
        method: "POST",
        body: JSON.stringify({
          provider: providers.ai.provider,
          base_url: providers.ai.base_url ?? "",
          api_key: "",
          default_model: providers.ai.default_model,
        }),
      });
      setHealth((prev) => ({
        ...prev,
        ai: { status: "success", message: "AI API connection verified" },
      }));
      showToast("success", "AI connection verified successfully");
    } catch (err) {
      const msg = errorDetail(err, "AI connection test failed");
      setHealth((prev) => ({
        ...prev,
        ai: { status: "failed", message: msg },
      }));
      showToast("error", msg);
    }
  }

  async function testEmailConnection() {
    if (!providers.email) return;
    setHealth((prev) => ({ ...prev, email: { status: "testing" } }));
    try {
      await apiFetch<void>("/platform/email-config/test", {
        method: "POST",
        body: JSON.stringify({
          provider: providers.email.provider,
          smtp_host: providers.email.smtp_host,
          smtp_port: providers.email.smtp_port,
          smtp_username: providers.email.smtp_username,
          smtp_password: "",
          from_email: providers.email.from_email,
          from_name: providers.email.from_name,
        }),
      });
      setHealth((prev) => ({
        ...prev,
        email: { status: "success", message: "SMTP relay connection verified" },
      }));
      showToast("success", "Email SMTP relay connection verified successfully");
    } catch (err) {
      const msg = errorDetail(err, "SMTP connection test failed");
      setHealth((prev) => ({
        ...prev,
        email: { status: "failed", message: msg },
      }));
      showToast("error", msg);
    }
  }

  async function testValidationConnection() {
    if (!providers.validation) return;
    setHealth((prev) => ({ ...prev, validation: { status: "testing" } }));
    try {
      await apiFetch<void>("/platform/email-validation-config/test", {
        method: "POST",
        body: JSON.stringify({
          provider: providers.validation.provider,
          api_key: "",
        }),
      });
      setHealth((prev) => ({
        ...prev,
        validation: { status: "success", message: "Validation API connection verified" },
      }));
      showToast("success", "Email validation service connection verified");
    } catch (err) {
      const msg = errorDetail(err, "Email validation connection test failed");
      setHealth((prev) => ({
        ...prev,
        validation: { status: "failed", message: msg },
      }));
      showToast("error", msg);
    }
  }

  async function testAllConnections() {
    setTestingAll(true);
    try {
      if (providers.ai?.is_active) await testAIConnection();
      if (providers.email?.is_active) await testEmailConnection();
      if (providers.validation?.is_active) await testValidationConnection();
    } finally {
      setTestingAll(false);
    }
  }

  if (loading) {
    return <div className={styles.emptyNote}>Loading platform provider configurations...</div>;
  }

  if (loadError) {
    return <div className={styles.accessDenied}>{loadError}</div>;
  }

  const activeCount = [
    providers.ai?.is_active,
    providers.email?.is_active,
    providers.validation?.is_active,
  ].filter(Boolean).length;

  return (
    <div className={styles.page}>
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Configured Providers</div>
          <div className={styles.statValue}>{activeCount} / 3</div>
          <div className={styles.statHint}>Platform-wide fallback infrastructure</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>System Health</div>
          <div
            className={styles.statValue}
            style={{ color: activeCount > 0 ? "#15803d" : "#b45309" }}
          >
            {activeCount === 3 ? "Operational" : "Partial"}
          </div>
          <div className={styles.statHint}>
            {activeCount === 3 ? "All fallback services active" : "Some providers unconfigured"}
          </div>
        </div>
      </div>

      <div className={styles.actionBar}>
        <div>
          <h2 style={{ margin: 0, fontSize: "16px", fontWeight: 800 }}>Platform Services</h2>
          <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--color-slate)" }}>
            Review, live-test, and update credentials for platform fallback providers
          </p>
        </div>
        <button
          type="button"
          className={styles.btnSecondary}
          onClick={testAllConnections}
          disabled={testingAll || activeCount === 0}
        >
          {testingAll ? "Testing All..." : "⚡ Test All Active"}
        </button>
      </div>

      <div className={styles.providersGrid}>
        {/* 1. AI / LLM Provider */}
        <div className={styles.providerCard}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitleWrapper}>
              <span className={styles.cardIcon}>🤖</span>
              <div>
                <h3 className={styles.cardTitle}>AI & LLM Engine</h3>
                <p className={styles.cardSubtitle}>Content generation & suggestions</p>
              </div>
            </div>
            <span
              className={`${styles.statusBadge} ${
                providers.ai?.is_active ? styles.statusActive : styles.statusUnconfigured
              }`}
            >
              {providers.ai?.is_active ? "Active" : "Unconfigured"}
            </span>
          </div>

          {providers.ai ? (
            <div className={styles.detailsList}>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Provider</span>
                <span className={styles.detailValue}>{providers.ai.provider}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Default Model</span>
                <span className={styles.detailValue}>{providers.ai.default_model}</span>
              </div>
              {providers.ai.base_url && (
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Base URL</span>
                  <span className={styles.detailValue}>{providers.ai.base_url}</span>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.emptyNote}>No platform AI provider configured.</div>
          )}

          {health.ai.status !== "idle" && (
            <div
              className={`${styles.testResultBanner} ${
                health.ai.status === "success"
                  ? styles.testSuccess
                  : health.ai.status === "failed"
                    ? styles.testFailed
                    : ""
              }`}
            >
              {health.ai.status === "testing" && "Testing AI endpoint..."}
              {health.ai.status === "success" && `✓ ${health.ai.message}`}
              {health.ai.status === "failed" && `✕ ${health.ai.message}`}
            </div>
          )}

          <div className={styles.cardActions}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={testAIConnection}
              disabled={!providers.ai?.is_active || health.ai.status === "testing"}
            >
              {health.ai.status === "testing" ? "Testing..." : "Test Connection"}
            </button>
            <Link href="/platform/ai-config" className={styles.btnPrimary}>
              Configure AI →
            </Link>
          </div>
        </div>

        {/* 2. Outbound Email Provider */}
        <div className={styles.providerCard}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitleWrapper}>
              <span className={styles.cardIcon}>✉️</span>
              <div>
                <h3 className={styles.cardTitle}>Outbound Email Relay</h3>
                <p className={styles.cardSubtitle}>Transactional & campaign SMTP</p>
              </div>
            </div>
            <span
              className={`${styles.statusBadge} ${
                providers.email?.is_active ? styles.statusActive : styles.statusUnconfigured
              }`}
            >
              {providers.email?.is_active ? "Active" : "Unconfigured"}
            </span>
          </div>

          {providers.email ? (
            <div className={styles.detailsList}>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Provider</span>
                <span className={styles.detailValue}>{providers.email.provider}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>SMTP Host</span>
                <span className={styles.detailValue}>
                  {providers.email.smtp_host}:{providers.email.smtp_port}
                </span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Sender Email</span>
                <span className={styles.detailValue}>{providers.email.from_email}</span>
              </div>
            </div>
          ) : (
            <div className={styles.emptyNote}>No platform SMTP relay configured.</div>
          )}

          {health.email.status !== "idle" && (
            <div
              className={`${styles.testResultBanner} ${
                health.email.status === "success"
                  ? styles.testSuccess
                  : health.email.status === "failed"
                    ? styles.testFailed
                    : ""
              }`}
            >
              {health.email.status === "testing" && "Testing SMTP handshake..."}
              {health.email.status === "success" && `✓ ${health.email.message}`}
              {health.email.status === "failed" && `✕ ${health.email.message}`}
            </div>
          )}

          <div className={styles.cardActions}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={testEmailConnection}
              disabled={!providers.email?.is_active || health.email.status === "testing"}
            >
              {health.email.status === "testing" ? "Testing..." : "Test Connection"}
            </button>
            <Link href="/platform/email-config" className={styles.btnPrimary}>
              Configure SMTP →
            </Link>
          </div>
        </div>

        {/* 3. Email Validation Provider */}
        <div className={styles.providerCard}>
          <div className={styles.cardHeader}>
            <div className={styles.cardTitleWrapper}>
              <span className={styles.cardIcon}>🔍</span>
              <div>
                <h3 className={styles.cardTitle}>Email Validation</h3>
                <p className={styles.cardSubtitle}>Deliverability & syntax checks</p>
              </div>
            </div>
            <span
              className={`${styles.statusBadge} ${
                providers.validation?.is_active ? styles.statusActive : styles.statusUnconfigured
              }`}
            >
              {providers.validation?.is_active ? "Active" : "Unconfigured"}
            </span>
          </div>

          {providers.validation ? (
            <div className={styles.detailsList}>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>Vendor</span>
                <span className={styles.detailValue}>{providers.validation.provider}</span>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.detailLabel}>API Key</span>
                <span className={styles.detailValue}>••••••••••••</span>
              </div>
            </div>
          ) : (
            <div className={styles.emptyNote}>No validation provider configured.</div>
          )}

          {health.validation.status !== "idle" && (
            <div
              className={`${styles.testResultBanner} ${
                health.validation.status === "success"
                  ? styles.testSuccess
                  : health.validation.status === "failed"
                    ? styles.testFailed
                    : ""
              }`}
            >
              {health.validation.status === "testing" && "Testing Validation API..."}
              {health.validation.status === "success" && `✓ ${health.validation.message}`}
              {health.validation.status === "failed" && `✕ ${health.validation.message}`}
            </div>
          )}

          <div className={styles.cardActions}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={testValidationConnection}
              disabled={!providers.validation?.is_active || health.validation.status === "testing"}
            >
              {health.validation.status === "testing" ? "Testing..." : "Test Connection"}
            </button>
            <Link href="/platform/email-validation-config" className={styles.btnPrimary}>
              Configure API →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
