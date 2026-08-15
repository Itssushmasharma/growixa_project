"use client";

import {
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";
import { getApiUrl } from "@/lib/env";

import shared from "../shared.module.css";
import type { EmailValidationResult, EmailValidationSummary, MeResponse } from "../types";
import pageStyles from "./verify-email-page.module.css";

const VIEW_PERMISSION = "contacts.view";

const STATUS_LABEL: Record<EmailValidationResult["status"], string> = {
  VALID: "Valid",
  INVALID: "Invalid",
  DISPOSABLE: "Disposable",
  ROLE: "Role account",
};

const STATUS_COLOR: Record<EmailValidationResult["status"], string> = {
  VALID: "var(--color-success)",
  INVALID: "var(--color-error)",
  DISPOSABLE: "var(--color-purple)",
  ROLE: "#d97706",
};

const STATUS_CLASS: Record<EmailValidationResult["status"], string> = {
  VALID: shared.statusSubscribed ?? "",
  INVALID: shared.statusBounced ?? "",
  DISPOSABLE: shared.statusArchived ?? "",
  ROLE: shared.statusUnsubscribed ?? "",
};

type Tab = "single" | "bulk";

export function VerifyEmailPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);

  const [tab, setTab] = useState<Tab>("single");

  const [email, setEmail] = useState("");
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<EmailValidationResult | null>(null);

  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkSummary, setBulkSummary] = useState<EmailValidationSummary | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        setCanView(me.permissions.includes(VIEW_PERMISSION));
      } catch {
        setLoadError("Could not load this page.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  async function handleCheckSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setChecking(true);
    setResult(null);
    try {
      const checked = await apiFetch<EmailValidationResult>("/email-validation/check", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setResult(checked);
    } catch {
      showToast("error", "Could not check this email.");
    } finally {
      setChecking(false);
    }
  }

  async function submitBulkFile(file: File) {
    setBulkLoading(true);
    setBulkSummary(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${getApiUrl()}/email-validation/bulk-csv`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || "Bulk validation failed.");
      }

      const summaryHeader = response.headers.get("x-validation-summary");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "email-validation-results.csv";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      if (summaryHeader) {
        setBulkSummary(JSON.parse(summaryHeader) as EmailValidationSummary);
      }
      showToast("success", "Validation complete — results downloaded.");
    } catch (err) {
      showToast(
        "error",
        err instanceof Error && err.message ? err.message : "Could not validate CSV.",
      );
    } finally {
      setBulkLoading(false);
    }
  }

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) void submitBulkFile(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void submitBulkFile(file);
  }

  if (loading) {
    return <div className={shared.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={shared.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={shared.card}>You don&apos;t have access to verify emails.</div>;
  }

  return (
    <div>
      <div className={pageStyles.hero}>
        <h1 className={pageStyles.heroTitle}>Verify emails before you send</h1>
        <p className={pageStyles.heroSubtitle}>
          Catch typos, dead domains, throwaway inboxes, and shared role accounts before a campaign
          goes out — free, no third-party provider, no credits used.
        </p>
      </div>

      <div className={pageStyles.layout}>
        <div className={shared.card}>
          <div className={pageStyles.tabBar}>
            <button
              type="button"
              className={`${pageStyles.tab} ${tab === "single" ? pageStyles.tabActive : ""}`}
              onClick={() => setTab("single")}
            >
              Single Email
            </button>
            <button
              type="button"
              className={`${pageStyles.tab} ${tab === "bulk" ? pageStyles.tabActive : ""}`}
              onClick={() => setTab("bulk")}
            >
              Bulk Upload
            </button>
          </div>

          {tab === "single" ? (
            <div>
              <form onSubmit={handleCheckSubmit} style={{ display: "flex", gap: 10 }}>
                <input
                  type="email"
                  required
                  placeholder="someone@example.com"
                  className={shared.input}
                  style={{ flex: 1 }}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  aria-label="Email"
                />
                <button type="submit" disabled={checking} className={shared.submit}>
                  {checking ? "Checking..." : "Verify email"}
                </button>
              </form>

              {result && (
                <div className={pageStyles.resultRow}>
                  <span
                    className={pageStyles.resultDot}
                    style={{ background: STATUS_COLOR[result.status] }}
                  />
                  <span className={pageStyles.resultEmail}>{result.email}</span>
                  <span className={`${shared.statusBadge} ${STATUS_CLASS[result.status]}`}>
                    {STATUS_LABEL[result.status]}
                  </span>
                  <span className={shared.description}>
                    {result.reasons.length > 0 ? result.reasons.join("; ") : "No issues found."}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,text/csv"
                style={{ display: "none" }}
                onChange={handleFileInputChange}
              />
              <div
                className={`${pageStyles.dropzone} ${dragActive ? pageStyles.dropzoneActive : ""}`}
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
              >
                <div className={pageStyles.dropzoneIcon}>📄</div>
                <div className={pageStyles.dropzoneTitle}>
                  {bulkLoading ? "Checking your list…" : "Upload or drop a CSV file here"}
                </div>
                <button type="button" className={shared.addButton} disabled={bulkLoading}>
                  {bulkLoading ? "Checking…" : "Choose file"}
                </button>
                <div className={pageStyles.dropzoneHint}>
                  Needs a column named <code>email</code> — up to 2,000 rows per upload.
                </div>
              </div>

              {bulkSummary && (
                <div className={shared.metricsGrid} style={{ marginTop: 20 }}>
                  <div className={shared.metricCard}>
                    <div className={shared.metricLabel}>Total Checked</div>
                    <div className={shared.metricValue}>{bulkSummary.total}</div>
                  </div>
                  <div className={shared.metricCard}>
                    <div className={shared.metricLabel}>Valid</div>
                    <div className={shared.metricValue} style={{ color: "var(--color-success)" }}>
                      {bulkSummary.valid}
                    </div>
                  </div>
                  <div className={shared.metricCard}>
                    <div className={shared.metricLabel}>Invalid</div>
                    <div className={shared.metricValue} style={{ color: "var(--color-error)" }}>
                      {bulkSummary.invalid}
                    </div>
                  </div>
                  <div className={shared.metricCard}>
                    <div className={shared.metricLabel}>Disposable</div>
                    <div className={shared.metricValue} style={{ color: "var(--color-purple)" }}>
                      {bulkSummary.disposable}
                    </div>
                  </div>
                  <div className={shared.metricCard}>
                    <div className={shared.metricLabel}>Role Accounts</div>
                    <div className={shared.metricValue} style={{ color: "#d97706" }}>
                      {bulkSummary.role}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className={pageStyles.sidePanel}>
          <h3 className={pageStyles.sidePanelTitle}>What we check</h3>
          <ul className={pageStyles.checkList}>
            <li className={pageStyles.checkItem}>
              <span className={pageStyles.checkIcon}>✓</span>
              Syntax — catches malformed addresses
            </li>
            <li className={pageStyles.checkItem}>
              <span className={pageStyles.checkIcon}>✓</span>
              Domain mail-server (MX/A record) — catches dead or misspelled domains
            </li>
            <li className={pageStyles.checkItem}>
              <span className={pageStyles.checkIcon}>✓</span>
              Known disposable / throwaway providers
            </li>
            <li className={pageStyles.checkItem}>
              <span className={pageStyles.checkIcon}>✓</span>
              Shared role accounts (info@, admin@, noreply@, ...)
            </li>
          </ul>
          <div className={pageStyles.limitBox}>
            <strong>Doesn&apos;t check:</strong> whether a specific mailbox actually exists, or
            catch-all domain scoring — both need a paid, real-time SMTP-probing provider.
          </div>
        </div>
      </div>
    </div>
  );
}
