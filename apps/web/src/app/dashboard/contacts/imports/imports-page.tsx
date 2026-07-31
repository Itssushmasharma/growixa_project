"use client";

import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "../shared.module.css";
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

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
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

  const hasEmailMapping = headers.some((header) => mapping[header] === "email");

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  if (!canView) {
    return <div className={styles.card}>You don&apos;t have access to view imports.</div>;
  }

  return (
    <>
      {canManage && (
        <div className={styles.card} style={{ marginBottom: 24 }}>
          <div className={styles.header}>
            <h2 className={styles.headerTitle}>Import contacts from CSV</h2>
          </div>

          <form onSubmit={handleUploadSubmit}>
            <div className={styles.createField} style={{ marginBottom: 16 }}>
              <label className={styles.label} htmlFor="import-file">
                CSV file
              </label>
              <input id="import-file" type="file" accept=".csv" onChange={handleFileChange} />
            </div>

            {headers.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                {headers.map((header) => (
                  <div className={styles.ruleRow} key={header}>
                    <span className={styles.typeBadge}>{header}</span>
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
            )}

            <button
              type="submit"
              className={styles.submit}
              disabled={!file || headers.length === 0 || !hasEmailMapping || uploading}
            >
              {uploading ? "Importing…" : "Import contacts"}
            </button>
          </form>

          {lastResult && (
            <p className={styles.readOnlyNote} style={{ marginTop: 16 }}>
              Imported {lastResult.imported_count}, updated {lastResult.updated_count}, skipped{" "}
              {lastResult.skipped_count}, errors {lastResult.error_count} (of{" "}
              {lastResult.total_rows} rows).
            </p>
          )}
        </div>
      )}

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>
            Import history <span className={styles.headerCount}>· {imports.length}</span>
          </h2>
        </div>

        {imports.length === 0 && <p className={styles.emptyState}>No imports yet.</p>}

        {imports.map((contactImport) => {
          const isExpanded = expandedImportId === contactImport.id;
          return (
            <div className={styles.contactBlock} key={contactImport.id}>
              <div className={styles.row}>
                <div className={styles.identity}>
                  <div className={styles.name}>{contactImport.filename}</div>
                  <div className={styles.description}>
                    {new Date(contactImport.created_at).toLocaleString()} · Imported{" "}
                    {contactImport.imported_count}, updated {contactImport.updated_count}, skipped{" "}
                    {contactImport.skipped_count}, errors {contactImport.error_count}
                  </div>
                </div>
                <div className={styles.rowActions}>
                  <span className={styles.typeBadge}>{statusLabel(contactImport.status)}</span>
                  <button
                    type="button"
                    className={styles.viewButton}
                    onClick={() => toggleExpandImport(contactImport)}
                  >
                    {isExpanded ? "Close" : "View rows"}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className={styles.detailPanel}>
                  {rowsLoading && <p className={styles.emptyState}>Loading rows…</p>}
                  {!rowsLoading && (
                    <ul className={styles.ruleList}>
                      {rows.map((row) => (
                        <li key={row.id}>
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
    </>
  );
}
