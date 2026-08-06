"use client";

import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./imports-page.module.css";
import type { ContactImport, ContactImportRow, CustomField, MeResponse } from "../types";

const VIEW_PERMISSION = "contacts.view";
const MANAGE_PERMISSION = "contacts.manage";

const BASE_TARGET_OPTIONS = [
  { value: "", label: "Ignore this column" },
  { value: "email", label: "Email" },
  { value: "first_name", label: "First name" },
  { value: "last_name", label: "Last name" },
  { value: "phone", label: "Phone" },
  { value: "source", label: "Source" },
];

function guessTarget(header: string): string {
  const normalized = header
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");
  if (normalized === "email" || normalized === "email_address") return "email";
  if (normalized === "first_name" || normalized === "firstname") return "first_name";
  if (normalized === "last_name" || normalized === "lastname") return "last_name";
  if (normalized === "phone" || normalized === "phone_number") return "phone";
  if (normalized === "source") return "source";
  return "";
}

function parseHeaderLine(text: string): string[] {
  const firstLine = text.split(/\r?\n/, 1)[0] ?? "";
  return firstLine
    .split(",")
    .map((header) => header.trim().replace(/^"|"$/g, ""))
    .filter((header) => header.length > 0);
}

function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

function getStatusStyle(status: ContactImport["status"]): string {
  switch (status) {
    case "COMPLETED":
      return `${styles.statusBadge} ${styles.statusCompleted}`;
    case "PROCESSING":
      return `${styles.statusBadge} ${styles.statusProcessing}`;
    case "FAILED":
      return `${styles.statusBadge} ${styles.statusFailed}`;
    default:
      return `${styles.statusBadge} ${styles.statusPending}`;
  }
}

function statusLabel(status: ContactImport["status"]): string {
  switch (status) {
    case "COMPLETED":
      return "Completed";
    case "PROCESSING":
      return "Processing";
    case "FAILED":
      return "Failed";
    default:
      return "Pending";
  }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ImportsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [customFields, setCustomFields] = useState<CustomField[]>([]);
  const [imports, setImports] = useState<ContactImport[]>([]);

  const [file, setFile] = useState<File | null>(null);
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);
  const [lastResult, setLastResult] = useState<ContactImport | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const [expandedImportId, setExpandedImportId] = useState<string | null>(null);
  const [rows, setRows] = useState<ContactImportRow[]>([]);
  const [rowsLoading, setRowsLoading] = useState(false);

  const targetOptions = [
    ...BASE_TARGET_OPTIONS,
    ...customFields.map((field) => ({
      value: `custom_field:${field.key}`,
      label: `Custom field: ${field.label}`,
    })),
  ];

  useEffect(() => {
    async function load() {
      try {
        const [me, importList, customFieldList] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<ContactImport[]>("/contacts/imports"),
          apiFetch<CustomField[]>("/contacts/custom-fields"),
        ]);
        setCanView(me.permissions.includes(VIEW_PERMISSION));
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));
        setImports(importList);
        setCustomFields(customFieldList);
      } catch {
        setLoadError("Could not load import history.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function processSelectedFile(selected: File | null) {
    setFile(selected);
    setLastResult(null);

    if (!selected) {
      setHeaders([]);
      setMapping({});
      return;
    }

    try {
      const text = await readFileAsText(selected);
      const parsedHeaders = parseHeaderLine(text);
      setHeaders(parsedHeaders);
      setMapping(Object.fromEntries(parsedHeaders.map((header) => [header, guessTarget(header)])));
    } catch {
      showToast("error", "Could not read that file.");
      setHeaders([]);
      setMapping({});
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    await processSelectedFile(selected);
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
  }

  async function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files?.[0] ?? null;
    if (droppedFile) {
      if (droppedFile.name.toLowerCase().endsWith(".csv")) {
        await processSelectedFile(droppedFile);
      } else {
        showToast("error", "Please upload a valid .csv file.");
      }
    }
  }

  async function handleUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    setUploading(true);

    try {
      const columnMapping = Object.fromEntries(
        headers.filter((header) => mapping[header]).map((header) => [header, mapping[header]]),
      );
      const formData = new FormData();
      formData.append("file", file);
      formData.append("column_mapping", JSON.stringify(columnMapping));

      const created = await apiFetch<ContactImport>("/contacts/imports", {
        method: "POST",
        body: formData,
      });
      setLastResult(created);
      setImports((current) => [created, ...current]);
      setFile(null);
      setHeaders([]);
      setMapping({});
      showToast("success", "Import completed.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 400) {
        showToast("error", "Check your column mapping — a column must be mapped to Email.");
      } else {
        showToast("error", "Could not import that file.");
      }
    } finally {
      setUploading(false);
    }
  }

  async function toggleExpandImport(contactImport: ContactImport) {
    if (expandedImportId === contactImport.id) {
      setExpandedImportId(null);
      return;
    }
    setExpandedImportId(contactImport.id);
    setRowsLoading(true);
    try {
      const rowList = await apiFetch<ContactImportRow[]>(
        `/contacts/imports/${contactImport.id}/rows`,
      );
      setRows(rowList);
    } catch {
      showToast("error", "Could not load this import's row detail.");
    } finally {
      setRowsLoading(false);
    }
  }

  function handleExportCsv() {
    if (imports.length === 0) {
      showToast("error", "No import history available to export.");
      return;
    }
    const csvHeaders = [
      "Import ID",
      "Filename",
      "Status",
      "Total Rows",
      "Imported",
      "Updated",
      "Skipped",
      "Errors",
      "Created At",
    ];
    const csvRows = imports.map((item) => [
      item.id,
      `"${item.filename.replace(/"/g, '""')}"`,
      item.status,
      item.total_rows,
      item.imported_count,
      item.updated_count,
      item.skipped_count,
      item.error_count,
      `"${new Date(item.created_at).toLocaleString()}"`,
    ]);
    const csvContent = [csvHeaders.join(","), ...csvRows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `growixa_import_history_${new Date().toISOString().slice(0, 10)}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("success", "Exported import history to CSV.");
  }

  const hasEmailMapping = headers.some((header) => mapping[header] === "email");
  const totalImportedCount = imports.reduce((acc, item) => acc + item.imported_count, 0);
  const totalUpdatedCount = imports.reduce((acc, item) => acc + item.updated_count, 0);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>Loading…</div>
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

  if (!canView) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to view imports.</div>
      </div>
    );
  }

  const step = !file ? 1 : headers.length > 0 && !hasEmailMapping ? 2 : 3;

  return (
    <div className={styles.page}>
      {canManage && (
        <div className={styles.card}>
          <div className={styles.headerRow}>
            <div>
              <h2 className={styles.headerTitle}>Import contacts from CSV</h2>
              <p className={styles.headerSubtitle}>
                Upload a CSV file to bulk import or update contacts and custom fields in Growixa.
              </p>
            </div>
          </div>

          {/* 3-Step Progress Indicator */}
          <div className={styles.stepBar}>
            <div className={`${styles.stepItem} ${step >= 1 ? styles.stepItemActive : ""}`}>
              <span className={styles.stepNumber}>1</span> Select CSV File
            </div>
            <div className={styles.stepDivider} />
            <div className={`${styles.stepItem} ${step >= 2 ? styles.stepItemActive : ""}`}>
              <span className={styles.stepNumber}>2</span> Map Columns
            </div>
            <div className={styles.stepDivider} />
            <div className={`${styles.stepItem} ${step >= 3 ? styles.stepItemActive : ""}`}>
              <span className={styles.stepNumber}>3</span> Import Contacts
            </div>
          </div>

          <form onSubmit={handleUploadSubmit}>
            {!file ? (
              <div
                className={`${styles.dropzone} ${isDragOver ? styles.dropzoneActive : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById("import-file")?.click()}
              >
                <div className={styles.dropzoneIcon}>📄</div>
                <div className={styles.dropzoneTitle}>Drag and drop your CSV file here</div>
                <div className={styles.dropzoneSubtitle}>
                  Supports .csv files up to 10MB (columns auto-detected)
                </div>
                <span className={styles.browseButton}>Browse file</span>
                <input
                  id="import-file"
                  type="file"
                  accept=".csv"
                  aria-label="CSV file"
                  style={{ display: "none" }}
                  onChange={handleFileChange}
                />
              </div>
            ) : (
              <div className={styles.fileCard}>
                <div>
                  <div className={styles.fileName}>{file.name}</div>
                  <div className={styles.fileSize}>{formatBytes(file.size)}</div>
                </div>
                <button
                  type="button"
                  className={styles.removeFile}
                  onClick={() => processSelectedFile(null)}
                >
                  Remove file
                </button>
              </div>
            )}

            {headers.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <h4 style={{ margin: "0 0 10px", fontSize: 14, fontWeight: 700 }}>
                  Map CSV Columns to Contact Fields
                </h4>
                <div className={styles.mappingGrid}>
                  {headers.map((header) => (
                    <div className={styles.mappingRow} key={header}>
                      <div className={styles.mappingHeader}>
                        <span>🏷️ {header}</span>
                        {mapping[header] && (
                          <span
                            style={{
                              fontSize: 11,
                              background: "#e0e7ff",
                              color: "#4338ca",
                              padding: "2px 6px",
                              borderRadius: 4,
                            }}
                          >
                            Auto-matched
                          </span>
                        )}
                      </div>
                      <select
                        className={styles.select}
                        aria-label={`Map column ${header}`}
                        value={mapping[header] ?? ""}
                        onChange={(event) =>
                          setMapping((current) => ({ ...current, [header]: event.target.value }))
                        }
                      >
                        {targetOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {file && (
              <div style={{ marginTop: 20, textAlign: "right" }}>
                <button
                  type="submit"
                  className={styles.submitButton}
                  disabled={!file || headers.length === 0 || !hasEmailMapping || uploading}
                >
                  {uploading ? "Importing…" : "Import contacts"}
                </button>
              </div>
            )}
          </form>

          {lastResult && (
            <p className={styles.headerSubtitle} style={{ marginTop: 12, color: "#16a34a" }}>
              ✅ Last import result: {lastResult.imported_count} created, {lastResult.updated_count}{" "}
              updated, {lastResult.skipped_count} skipped, {lastResult.error_count} errors (of{" "}
              {lastResult.total_rows} rows).
            </p>
          )}
        </div>
      )}

      {/* Import Metrics Summary */}
      {imports.length > 0 && (
        <div className={styles.metricsGrid}>
          <div className={styles.metricCard}>
            <span className={styles.metricValue}>{imports.length}</span>
            <span className={styles.metricLabel}>Total Imports</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricValue}>{totalImportedCount}</span>
            <span className={styles.metricLabel}>New Contacts Added</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricValue}>{totalUpdatedCount}</span>
            <span className={styles.metricLabel}>Contacts Updated</span>
          </div>
        </div>
      )}

      {/* History Card */}
      <div className={styles.card}>
        <div className={styles.headerRow}>
          <div>
            <h2 className={styles.headerTitle}>
              Import history <span className={styles.headerSubtitle}>· {imports.length}</span>
            </h2>
          </div>
          {imports.length > 0 && (
            <button type="button" className={styles.exportButton} onClick={handleExportCsv}>
              📥 Export CSV
            </button>
          )}
        </div>

        {imports.length === 0 && <p className={styles.headerSubtitle}>No imports yet.</p>}

        <div className={styles.historyList}>
          {imports.map((contactImport) => {
            const isExpanded = expandedImportId === contactImport.id;
            return (
              <div className={styles.historyRow} key={contactImport.id}>
                <div className={styles.historySummary}>
                  <div>
                    <div className={styles.fileName}>{contactImport.filename}</div>
                    <div className={styles.headerSubtitle}>
                      {new Date(contactImport.created_at).toLocaleString()} · Imported{" "}
                      {contactImport.imported_count}, updated {contactImport.updated_count}, skipped{" "}
                      {contactImport.skipped_count}, errors {contactImport.error_count}
                    </div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span className={getStatusStyle(contactImport.status)}>
                      {statusLabel(contactImport.status)}
                    </span>
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => toggleExpandImport(contactImport)}
                    >
                      {isExpanded ? "Close" : "View rows"}
                    </button>
                  </div>
                </div>

                {isExpanded && (
                  <div className={styles.detailPanel}>
                    {rowsLoading && <p className={styles.headerSubtitle}>Loading rows…</p>}
                    {!rowsLoading && (
                      <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {rows.map((row) => (
                          <li key={row.id} style={{ marginBottom: 4 }}>
                            Row {row.row_number}: {row.email ?? "(no email)"} — {row.status}
                            {row.error_message ? ` (${row.error_message})` : ""}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
