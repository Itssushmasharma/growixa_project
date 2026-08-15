"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { StatCard } from "@/components/stat-card/stat-card";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { TEMPLATE_PRESETS } from "./presets";
import styles from "./templates-page.module.css";
import type { EmailTemplate, MeResponse } from "./types";

const VIEW_PERMISSION = "campaigns.view";
const MANAGE_PERMISSION = "campaigns.manage";

type SortOption = "updated" | "name";
type ViewMode = "grid" | "list";
type CategoryFilter = "All" | "Marketing" | "Onboarding" | "Announcement" | "Newsletter";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function TemplatePreviewModal({
  template,
  onClose,
}: {
  template: EmailTemplate;
  onClose: () => void;
}) {
  const [deviceMode, setDeviceMode] = useState<"desktop" | "mobile">("desktop");

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!template.current_version) return null;

  return (
    <div className={styles.modalBackdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.modalTitleGroup}>
            <h3 className={styles.modalTitle}>{template.name}</h3>
            <span className={styles.modalSubject}>Subject: {template.current_version.subject}</span>
          </div>

          <div className={styles.deviceToggleGroup}>
            <button
              type="button"
              className={`${styles.deviceButton} ${
                deviceMode === "desktop" ? styles.deviceButtonActive : ""
              }`}
              onClick={() => setDeviceMode("desktop")}
            >
              🖥️ Desktop
            </button>
            <button
              type="button"
              className={`${styles.deviceButton} ${
                deviceMode === "mobile" ? styles.deviceButtonActive : ""
              }`}
              onClick={() => setDeviceMode("mobile")}
            >
              📱 Mobile
            </button>
          </div>

          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close preview"
          >
            ✕
          </button>
        </div>

        <div className={styles.modalBody}>
          <iframe
            title="Template preview"
            className={
              deviceMode === "desktop" ? styles.modalIframeDesktop : styles.modalIframeMobile
            }
            sandbox=""
            srcDoc={template.current_version.body_html}
          />
        </div>
      </div>
    </div>
  );
}

export function TemplatesPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);

  const [previewingTemplate, setPreviewingTemplate] = useState<EmailTemplate | null>(null);
  const [deletingTemplateId, setDeletingTemplateId] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("updated");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("All");

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));

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
      let detail = "Could not delete that template.";
      if (error instanceof ApiError) {
        try {
          const parsed = JSON.parse(error.message) as { detail?: string };
          if (parsed.detail) detail = parsed.detail;
        } catch {
          // Keep generic message
        }
      }
      showToast("error", detail);
    } finally {
      setDeletingTemplateId(null);
    }
  }

  const visibleTemplates = useMemo(() => {
    const query = search.trim().toLowerCase();
    let filtered = query
      ? templates.filter(
          (t) =>
            t.name.toLowerCase().includes(query) ||
            (t.current_version?.subject.toLowerCase().includes(query) ?? false),
        )
      : templates;

    if (categoryFilter !== "All") {
      filtered = filtered.filter((t) => {
        const nameLower = t.name.toLowerCase();
        const categoryLower = categoryFilter.toLowerCase();
        return nameLower.includes(categoryLower);
      });
    }

    const sorted = [...filtered];
    if (sortBy === "name") {
      sorted.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      sorted.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    }
    return sorted;
  }, [templates, search, sortBy, categoryFilter]);

  const latestUpdatedDate = useMemo(() => {
    if (templates.length === 0) return "N/A";
    const sorted = [...templates].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    return sorted[0] ? formatDate(sorted[0].updated_at) : "N/A";
  }, [templates]);

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
      {/* Page Header */}
      <PageHeader
        icon="📋"
        title="Email Templates"
        description="Browse, customize, and manage reusable responsive email templates."
        actions={
          canManage ? (
            <Link href="/dashboard/templates/new" className={styles.actionButton}>
              + New template
            </Link>
          ) : undefined
        }
      />

      {/* Metric Summary Cards */}
      <section className={styles.metricsGrid} aria-label="Template Library Overview KPIs">
        <StatCard label="Total Templates" value={templates.length} subtext="Account library" />
        <StatCard
          label="Starter Presets"
          value={TEMPLATE_PRESETS.length}
          subtext="Built-in starter layouts"
        />
        <StatCard label="Custom Built" value={templates.length} subtext="Created by your team" />
        <StatCard
          label="Recently Updated"
          value={latestUpdatedDate}
          subtext="Last modified template"
        />
      </section>

      {/* Main Templates Workspace */}
      <div className={styles.card}>
        {/* Toolbar & View Switcher */}
        {templates.length > 0 && (
          <div className={styles.toolbar}>
            <div className={styles.toolbarLeft}>
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

              <div className={styles.categoryPills}>
                {(["All", "Marketing", "Onboarding", "Announcement", "Newsletter"] as const).map(
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

            <div className={styles.viewModeToggle}>
              <button
                type="button"
                className={`${styles.viewModeBtn} ${
                  viewMode === "grid" ? styles.viewModeBtnActive : ""
                }`}
                onClick={() => setViewMode("grid")}
                aria-label="Grid View"
              >
                🎴 Grid
              </button>
              <button
                type="button"
                className={`${styles.viewModeBtn} ${
                  viewMode === "list" ? styles.viewModeBtnActive : ""
                }`}
                onClick={() => setViewMode("list")}
                aria-label="List View"
              >
                📋 List
              </button>
            </div>
          </div>
        )}

        {templates.length === 0 && <p className={styles.hint}>No email templates yet.</p>}
        {templates.length > 0 && visibleTemplates.length === 0 && (
          <p className={styles.hint}>No templates match &quot;{search}&quot;.</p>
        )}

        {/* Visual Card Grid View */}
        {viewMode === "grid" && visibleTemplates.length > 0 && (
          <div className={styles.gridContainer}>
            {visibleTemplates.map((template) => (
              <div className={styles.templateCard} key={template.id}>
                <div className={styles.cardPreviewArea}>
                  {template.current_version ? (
                    <iframe
                      title={`Thumbnail for ${template.name}`}
                      className={styles.cardPreviewIframe}
                      sandbox=""
                      srcDoc={template.current_version.body_html}
                    />
                  ) : (
                    <div className={styles.hint} style={{ padding: "20px" }}>
                      No preview available
                    </div>
                  )}
                </div>

                <div className={styles.cardBody}>
                  <div className={styles.cardTitleRow}>
                    <h4 className={styles.cardName}>{template.name}</h4>
                    <span className={styles.versionBadge}>
                      v{template.current_version?.version_number ?? 0}
                    </span>
                  </div>

                  <p className={styles.cardSubject}>
                    {template.current_version?.subject ?? "No subject"}
                  </p>

                  <div className={styles.cardMetaRow}>
                    <span className={styles.hint}>Updated {formatDate(template.updated_at)}</span>

                    <div className={styles.cardActions}>
                      {template.current_version && (
                        <button
                          type="button"
                          className={styles.secondaryButton}
                          onClick={() => setPreviewingTemplate(template)}
                        >
                          Preview
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
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Table List View */}
        {viewMode === "list" && visibleTemplates.length > 0 && (
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
                        onClick={() => setPreviewingTemplate(template)}
                      >
                        Preview
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
              </div>
            ))}
          </div>
        )}
      </div>

      {previewingTemplate && (
        <TemplatePreviewModal
          template={previewingTemplate}
          onClose={() => setPreviewingTemplate(null)}
        />
      )}
    </div>
  );
}
