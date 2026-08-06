"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./templates-page.module.css";
import type { EmailTemplate, MeResponse } from "./types";

const VIEW_PERMISSION = "campaigns.view";
const MANAGE_PERMISSION = "campaigns.manage";

type SortOption = "updated" | "name";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// sandbox="" (no allow-scripts, no allow-same-origin) renders the markup/inline styles
// a template author would see in an email client, without letting any script content
// run against this app's origin.
function TemplatePreview({ html }: { html: string }) {
  return (
    <iframe title="Template preview" className={styles.previewFrame} sandbox="" srcDoc={html} />
  );
}

export function TemplatesPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);

  const [previewingTemplateId, setPreviewingTemplateId] = useState<string | null>(null);
  const [deletingTemplateId, setDeletingTemplateId] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("updated");

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));

        // /templates is itself campaigns.view-gated on the backend, so a user without
        // it would get a 403 here rather than an empty list — skip the fetch entirely
        // for them, matching the pattern established in the integrations page.
        if (hasView) {
          const list = await apiFetch<EmailTemplate[]>("/templates");
          setTemplates(list);
        }
      } catch {
        setLoadError("Could not load email templates.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleDelete(template: EmailTemplate) {
    if (!window.confirm(`Delete "${template.name}"? This can't be undone.`)) {
      return;
    }
    setDeletingTemplateId(template.id);
    try {
      await apiFetch<void>(`/templates/${template.id}`, { method: "DELETE" });
      setTemplates((current) => current.filter((t) => t.id !== template.id));
      showToast("success", "Template deleted.");
    } catch (error) {
      // Same reasoning as the SMTP test-connection button: show the backend's real
      // detail (e.g. "referenced by a campaign") rather than a canned message, since
      // that's the one piece of information the user actually needs here.
      let detail = "Could not delete that template.";
      if (error instanceof ApiError) {
        try {
          const parsed = JSON.parse(error.message) as { detail?: string };
          if (parsed.detail) detail = parsed.detail;
        } catch {
          // Not JSON — keep the generic message.
        }
      }
      showToast("error", detail);
    } finally {
      setDeletingTemplateId(null);
    }
  }

  const visibleTemplates = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = query
      ? templates.filter(
          (t) =>
            t.name.toLowerCase().includes(query) ||
            (t.current_version?.subject.toLowerCase().includes(query) ?? false),
        )
      : templates;
    const sorted = [...filtered];
    if (sortBy === "name") {
      sorted.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      sorted.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    }
    return sorted;
  }, [templates, search, sortBy]);

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
        <div className={styles.card}>You don&apos;t have access to email templates.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.headerRow}>
          <div>
            <h2 className={styles.headerTitle}>Email templates</h2>
            <p className={styles.headerSubtitle}>
              Reusable subject + body content for campaigns. Editing a template saves a new version
              — past versions are never overwritten.
            </p>
          </div>
          {canManage && (
            <Link href="/dashboard/templates/new" className={styles.actionButton}>
              + New template
            </Link>
          )}
        </div>

        {templates.length > 0 && (
          <div className={styles.toolbar}>
            <input
              type="search"
              className={styles.searchInput}
              placeholder="Search by name or subject…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search templates"
            />
            <select
              className={styles.sortSelect}
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as SortOption)}
              aria-label="Sort templates"
            >
              <option value="updated">Sort by: Last updated</option>
              <option value="name">Sort by: Name</option>
            </select>
          </div>
        )}

        {templates.length === 0 && <p className={styles.hint}>No email templates yet.</p>}
        {templates.length > 0 && visibleTemplates.length === 0 && (
          <p className={styles.hint}>No templates match &quot;{search}&quot;.</p>
        )}

        <div className={styles.list}>
          {visibleTemplates.map((template) => (
            <div className={styles.templateRow} key={template.id}>
              <div className={styles.templateSummary}>
                <div>
                  <div className={styles.templateName}>{template.name}</div>
                  <div className={styles.templateSubject}>
                    {template.current_version?.subject ?? "No content yet"}
                  </div>
                </div>
                <div className={styles.templateMeta}>
                  <span className={styles.versionBadge}>
                    v{template.current_version?.version_number ?? 0}
                  </span>
                  <span className={styles.hint}>Updated {formatDate(template.updated_at)}</span>
                  {template.current_version && (
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() =>
                        setPreviewingTemplateId(
                          previewingTemplateId === template.id ? null : template.id,
                        )
                      }
                    >
                      {previewingTemplateId === template.id ? "Hide preview" : "Preview"}
                    </button>
                  )}
                  {canManage && (
                    <Link
                      href={`/dashboard/templates/${template.id}/edit`}
                      className={styles.secondaryButton}
                    >
                      Edit
                    </Link>
                  )}
                  {canManage && (
                    <Link
                      href={`/dashboard/templates/new?duplicateFrom=${template.id}`}
                      className={styles.secondaryButton}
                    >
                      Duplicate
                    </Link>
                  )}
                  {canManage && (
                    <button
                      type="button"
                      className={styles.dangerButton}
                      disabled={deletingTemplateId === template.id}
                      onClick={() => handleDelete(template)}
                    >
                      {deletingTemplateId === template.id ? "Deleting…" : "Delete"}
                    </button>
                  )}
                </div>
              </div>

              {previewingTemplateId === template.id && template.current_version && (
                <TemplatePreview html={template.current_version.body_html} />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
