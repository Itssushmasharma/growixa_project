"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { StatCard } from "@/components/stat-card/stat-card";
import { TemplatePreviewModal } from "@/components/template-preview/template-preview-modal";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { TEMPLATE_PRESETS } from "./presets";
import styles from "./templates-page.module.css";
import type { EmailTemplate, MeResponse } from "./types";

const VIEW_PERMISSION = "campaigns.view";
const MANAGE_PERMISSION = "campaigns.manage";

type SortOption = "updated" | "name";
type ViewMode = "grid" | "list";
type CategoryFilter =
  "All" | "Marketing" | "Onboarding" | "Announcement" | "Newsletter" | "Transactional";

const CATEGORIES: CategoryFilter[] = [
  "All",
  "Marketing",
  "Onboarding",
  "Announcement",
  "Newsletter",
  "Transactional",
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function TemplatesPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [platformDefaults, setPlatformDefaults] = useState<EmailTemplate[]>([]);

  const [previewingTemplate, setPreviewingTemplate] = useState<EmailTemplate | null>(null);
  const [deletingTemplateId, setDeletingTemplateId] = useState<string | null>(null);
  const [cloningTemplateId, setCloningTemplateId] = useState<string | null>(null);

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
          const [list, defaults] = await Promise.all([
            apiFetch<EmailTemplate[]>("/templates"),
            apiFetch<EmailTemplate[]>("/templates/platform-defaults"),
          ]);
          setTemplates(list);
          setPlatformDefaults(defaults);
        }
      } catch {
        setLoadError("Could not load email templates.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handleUseTemplate(template: EmailTemplate) {
    setCloningTemplateId(template.id);
    try {
      const clone = await apiFetch<EmailTemplate>(`/templates/${template.id}/clone`, {
        method: "POST",
      });
      showToast("success", `"${template.name}" added to your templates.`);
      router.push(`/dashboard/templates/${clone.id}/edit`);
    } catch {
      showToast("error", "Could not use that template. Please try again.");
    } finally {
      setCloningTemplateId(null);
    }
  }

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

  const categoryCounts = useMemo(() => {
    const counts: Record<CategoryFilter, number> = {
      All: templates.length,
      Marketing: 0,
      Onboarding: 0,
      Announcement: 0,
      Newsletter: 0,
      Transactional: 0,
    };

    for (const t of templates) {
      const nameLower = t.name.toLowerCase();
      if (
        nameLower.includes("marketing") ||
        nameLower.includes("promo") ||
        nameLower.includes("sale")
      ) {
        counts.Marketing += 1;
      }
      if (nameLower.includes("onboarding") || nameLower.includes("welcome")) {
        counts.Onboarding += 1;
      }
      if (
        nameLower.includes("announcement") ||
        nameLower.includes("update") ||
        nameLower.includes("launch")
      ) {
        counts.Announcement += 1;
      }
      if (
        nameLower.includes("newsletter") ||
        nameLower.includes("digest") ||
        nameLower.includes("roundup")
      ) {
        counts.Newsletter += 1;
      }
      if (
        nameLower.includes("transactional") ||
        nameLower.includes("receipt") ||
        nameLower.includes("alert")
      ) {
        counts.Transactional += 1;
      }
    }

    return counts;
  }, [templates]);

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
        if (categoryFilter === "Marketing") {
          return (
            nameLower.includes("marketing") ||
            nameLower.includes("promo") ||
            nameLower.includes("sale")
          );
        }
        if (categoryFilter === "Onboarding") {
          return nameLower.includes("onboarding") || nameLower.includes("welcome");
        }
        if (categoryFilter === "Announcement") {
          return (
            nameLower.includes("announcement") ||
            nameLower.includes("update") ||
            nameLower.includes("launch")
          );
        }
        if (categoryFilter === "Newsletter") {
          return (
            nameLower.includes("newsletter") ||
            nameLower.includes("digest") ||
            nameLower.includes("roundup")
          );
        }
        if (categoryFilter === "Transactional") {
          return (
            nameLower.includes("transactional") ||
            nameLower.includes("receipt") ||
            nameLower.includes("alert")
          );
        }
        return true;
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

  const updatedThisMonthCount = useMemo(() => {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 30);
    return templates.filter((t) => new Date(t.updated_at) >= cutoff).length;
  }, [templates]);

  const latestUpdatedDate = useMemo(() => {
    if (templates.length === 0) return "N/A";
    const sorted = [...templates].sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    return sorted[0] ? formatDate(sorted[0].updated_at) : "N/A";
  }, [templates]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingCard}>Loading email templates…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div className={styles.errorCard}>{loadError}</div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className={styles.page}>
        <div className={styles.errorCard}>You don&apos;t have access to email templates.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Standardized Page Header */}
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

      {/* Metric Summary Cards (Strictly Derived Data) */}
      <section className={styles.statsDeck} aria-label="Template Library Overview KPIs">
        <StatCard label="Total Templates" value={templates.length} subtext="Account library" />
        <StatCard
          label="Starter Presets"
          value={TEMPLATE_PRESETS.length}
          subtext="Built-in starter layouts"
        />
        <StatCard
          label="Updated (30d)"
          value={updatedThisMonthCount}
          subtext="Updated in last 30 days"
        />
        <StatCard
          label="Recently Updated"
          value={latestUpdatedDate}
          subtext="Last modified template"
        />
      </section>

      {/* Default Templates — platform-published, browse/preview only (GRX-EMAIL-016).
          Separate from "My Templates" below: no Edit/Duplicate/Delete here, since these
          are owned and maintained by Growixa's platform team, never by any account. */}
      {platformDefaults.length > 0 && (
        <div className={styles.card} data-testid="default-templates-section">
          <div className={styles.sectionHeadingRow}>
            <h3 className={styles.sectionHeading}>Default Templates</h3>
            <p className={styles.hint}>
              Built by Growixa. Use one to add an independent, fully editable copy to your own
              library.
            </p>
          </div>

          <div className={styles.gridContainer}>
            {platformDefaults.map((template) => (
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
                  </div>

                  <p className={styles.cardSubject}>
                    {template.current_version?.subject ?? "No subject"}
                  </p>

                  <div className={styles.cardMetaRow}>
                    <span />
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
                        <button
                          type="button"
                          className={styles.actionButton}
                          disabled={cloningTemplateId === template.id}
                          onClick={() => handleUseTemplate(template)}
                        >
                          {cloningTemplateId === template.id ? "Adding…" : "Use this template"}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Templates Workspace */}
      <div className={styles.card}>
        <div className={styles.sectionHeadingRow}>
          <h3 className={styles.sectionHeading}>My Templates</h3>
        </div>

        {/* Toolbar & Filter Pills */}
        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <div className={styles.searchWrapper}>
              <span className={styles.searchIcon} aria-hidden="true">
                🔍
              </span>
              <input
                type="search"
                className={styles.searchInput}
                placeholder="Search by name or subject…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                aria-label="Search templates"
              />
            </div>

            <select
              className={styles.sortSelect}
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as SortOption)}
              aria-label="Sort templates"
            >
              <option value="updated">Sort by: Last updated</option>
              <option value="name">Sort by: Name</option>
            </select>

            <div className={styles.categoryPills} role="tablist" aria-label="Template categories">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  type="button"
                  role="tab"
                  aria-selected={categoryFilter === cat}
                  className={`${styles.categoryPill} ${
                    categoryFilter === cat ? styles.categoryPillActive : ""
                  }`}
                  onClick={() => setCategoryFilter(cat)}
                >
                  <span>{cat}</span>
                  {categoryCounts[cat] > 0 && (
                    <span className={styles.categoryBadge}>{categoryCounts[cat]}</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.viewModeToggle} role="group" aria-label="View Mode">
            <button
              type="button"
              className={`${styles.viewModeBtn} ${
                viewMode === "grid" ? styles.viewModeBtnActive : ""
              }`}
              onClick={() => setViewMode("grid")}
              aria-label="Grid View"
              aria-pressed={viewMode === "grid"}
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
              aria-pressed={viewMode === "list"}
            >
              📋 List
            </button>
          </div>
        </div>

        {templates.length === 0 && (
          <div className={styles.emptyState}>
            <p className={styles.emptyStateTitle}>No email templates yet.</p>
            <p className={styles.emptyStateSubtitle}>
              Get started by creating a new custom email template or selecting from ready presets.
            </p>
            {canManage && (
              <Link href="/dashboard/templates/new" className={styles.actionButton}>
                + Create First Template
              </Link>
            )}
          </div>
        )}

        {templates.length > 0 && visibleTemplates.length === 0 && (
          <div className={styles.emptyState}>
            <p className={styles.emptyStateTitle}>No templates match &quot;{search}&quot;.</p>
            <p className={styles.emptyStateSubtitle}>
              Try refining your search terms or clearing the filter.
            </p>
          </div>
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

      {previewingTemplate && previewingTemplate.current_version && (
        <TemplatePreviewModal
          templateName={previewingTemplate.name}
          subject={previewingTemplate.current_version.subject}
          bodyHtml={previewingTemplate.current_version.body_html}
          onClose={() => setPreviewingTemplate(null)}
        />
      )}
    </div>
  );
}
