"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";

import { TemplatePreviewModal } from "@/components/template-preview/template-preview-modal";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./templates-page.module.css";
import type { EmailTemplate } from "./types";

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

function errorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (typeof parsed.detail === "string") return parsed.detail;
    } catch {
      // Not JSON
    }
  }
  return fallback;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

interface CreateFormState {
  name: string;
  subject: string;
  body_html: string;
  body_text: string;
}

function blankCreateForm(): CreateFormState {
  return { name: "", subject: "", body_html: "", body_text: "" };
}

interface EditFormState {
  subject: string;
  body_html: string;
  body_text: string;
}

export function PlatformTemplatesPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);

  const [createFormOpen, setCreateFormOpen] = useState(false);
  const [createForm, setCreateForm] = useState<CreateFormState>(blankCreateForm());
  const [creating, setCreating] = useState(false);

  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    subject: "",
    body_html: "",
    body_text: "",
  });
  const [savingEdit, setSavingEdit] = useState(false);

  const [editorDeviceMode, setEditorDeviceMode] = useState<"desktop" | "mobile">("desktop");
  const [retiringId, setRetiringId] = useState<string | null>(null);
  const [previewingTemplate, setPreviewingTemplate] = useState<EmailTemplate | null>(null);

  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("updated");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("All");

  useEffect(() => {
    async function load() {
      try {
        const list = await apiFetch<EmailTemplate[]>("/platform/templates");
        setTemplates(list);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to manage platform default templates.");
        } else {
          setLoadError("Could not load platform default templates.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  // Close modals on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        if (createFormOpen) setCreateFormOpen(false);
        if (editingTemplate) setEditingTemplate(null);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [createFormOpen, editingTemplate]);

  function openCreateForm() {
    setCreateForm(blankCreateForm());
    setEditorDeviceMode("desktop");
    setCreateFormOpen(true);
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreating(true);
    try {
      const created = await apiFetch<EmailTemplate>("/platform/templates", {
        method: "POST",
        body: JSON.stringify({
          name: createForm.name.trim(),
          subject: createForm.subject.trim(),
          body_html: createForm.body_html,
          body_text: createForm.body_text.trim() === "" ? null : createForm.body_text,
        }),
      });
      setTemplates((current) => [created, ...current]);
      showToast("success", `"${created.name}" published as a default template.`);
      setCreateFormOpen(false);
    } catch (err) {
      showToast("error", errorDetail(err, "Could not publish that template."));
    } finally {
      setCreating(false);
    }
  }

  function openEditForm(template: EmailTemplate) {
    setEditingTemplate(template);
    setEditorDeviceMode("desktop");
    setEditForm({
      subject: template.current_version?.subject ?? "",
      body_html: template.current_version?.body_html ?? "",
      body_text: template.current_version?.body_text ?? "",
    });
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingTemplate) return;
    setSavingEdit(true);
    try {
      const updated = await apiFetch<EmailTemplate>(
        `/platform/templates/${editingTemplate.id}/versions`,
        {
          method: "POST",
          body: JSON.stringify({
            subject: editForm.subject.trim(),
            body_html: editForm.body_html,
            body_text: editForm.body_text.trim() === "" ? null : editForm.body_text,
          }),
        },
      );
      setTemplates((current) => current.map((t) => (t.id === updated.id ? updated : t)));
      showToast(
        "success",
        `"${updated.name}" updated to v${updated.current_version?.version_number}.`,
      );
      setEditingTemplate(null);
    } catch (err) {
      showToast("error", errorDetail(err, "Could not update that template."));
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleRetire(template: EmailTemplate) {
    if (
      !window.confirm(
        `Retire "${template.name}"? Accounts that already cloned it keep their own independent copy — this only removes it from the Default Templates section for everyone else.`,
      )
    ) {
      return;
    }
    setRetiringId(template.id);
    try {
      await apiFetch<void>(`/platform/templates/${template.id}`, { method: "DELETE" });
      setTemplates((current) => current.filter((t) => t.id !== template.id));
      showToast("success", `"${template.name}" retired.`);
    } catch (err) {
      showToast("error", errorDetail(err, "Could not retire that template."));
    } finally {
      setRetiringId(null);
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

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.headerTitle}>Default Templates</h2>
            <p className={styles.headerHint}>
              Published here, every account can browse and clone these into their own library
              (read-only for them — clone-not-edit). Retiring or updating one never affects a copy
              an account already cloned.
            </p>
          </div>
          <button type="button" className={styles.actionButton} onClick={openCreateForm}>
            + New default template
          </button>
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
                placeholder="Search default templates…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                aria-label="Search default templates"
              />
            </div>

            <select
              className={styles.sortSelect}
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value as SortOption)}
              aria-label="Sort default templates"
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

        {/* Empty States */}
        {templates.length === 0 && !createFormOpen && (
          <div className={styles.emptyState}>
            <p className={styles.emptyStateTitle}>No default templates published yet.</p>
            <p className={styles.emptyStateSubtitle}>
              Click &quot;+ New default template&quot; to publish the first responsive email design.
            </p>
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
                    <span className={styles.badge}>
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
                      <button
                        type="button"
                        className={styles.secondaryButton}
                        onClick={() => openEditForm(template)}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className={styles.dangerButton}
                        disabled={retiringId === template.id}
                        onClick={() => handleRetire(template)}
                      >
                        {retiringId === template.id ? "Retiring…" : "Retire"}
                      </button>
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
              <div className={styles.row} key={template.id}>
                <div className={styles.rowMain}>
                  <span className={styles.rowName}>{template.name}</span>
                  <span className={styles.rowSubject}>
                    {template.current_version?.subject ?? "No subject"}
                  </span>
                </div>
                <span className={styles.badge}>
                  v{template.current_version?.version_number ?? 0}
                </span>
                <span className={styles.rowMeta}>Updated {formatDate(template.updated_at)}</span>
                <div className={styles.rowActions}>
                  {template.current_version && (
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => setPreviewingTemplate(template)}
                    >
                      Preview
                    </button>
                  )}
                  <button
                    type="button"
                    className={styles.secondaryButton}
                    onClick={() => openEditForm(template)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className={styles.dangerButton}
                    disabled={retiringId === template.id}
                    onClick={() => handleRetire(template)}
                  >
                    {retiringId === template.id ? "Retiring…" : "Retire"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* =========================================================================
         Side-by-Side Modal: Create New Default Template
         ========================================================================= */}
      {createFormOpen && (
        <div
          className={styles.editorModalBackdrop}
          onClick={() => setCreateFormOpen(false)}
          role="dialog"
          aria-modal="true"
        >
          <div className={styles.editorModalCard} onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleCreate} style={{ display: "contents" }}>
              <div className={styles.editorModalHeader}>
                <div className={styles.editorModalTitleGroup}>
                  <h3 className={styles.editorModalTitle}>✨ New Default Template</h3>
                  <p className={styles.editorModalSubtitle}>
                    Published template will be available in the starter library for all accounts
                  </p>
                </div>
                <button
                  type="button"
                  className={styles.closeButton}
                  onClick={() => setCreateFormOpen(false)}
                  aria-label="Close dialog"
                >
                  ✕
                </button>
              </div>

              <div className={styles.editorModalBody}>
                {/* Left Form Column */}
                <div className={styles.editorFormColumn}>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor="new-template-name">
                      Template Name *
                    </label>
                    <input
                      id="new-template-name"
                      className={styles.input}
                      required
                      value={createForm.name}
                      onChange={(event) =>
                        setCreateForm({ ...createForm, name: event.target.value })
                      }
                      placeholder="e.g. Welcome Series Kickoff"
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label} htmlFor="new-template-subject">
                      Subject Line *
                    </label>
                    <input
                      id="new-template-subject"
                      className={styles.input}
                      required
                      value={createForm.subject}
                      onChange={(event) =>
                        setCreateForm({ ...createForm, subject: event.target.value })
                      }
                      placeholder="e.g. Welcome to Growixa, {{first_name}}!"
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label} htmlFor="new-template-body-html">
                      Body (HTML) *
                    </label>
                    <textarea
                      id="new-template-body-html"
                      className={styles.htmlTextarea}
                      required
                      value={createForm.body_html}
                      onChange={(event) =>
                        setCreateForm({ ...createForm, body_html: event.target.value })
                      }
                      placeholder="<p>Hi {{first_name}}...</p>"
                    />
                  </div>

                  <div className={styles.field}>
                    <label className={styles.label} htmlFor="new-template-body-text">
                      Body (plain text, optional)
                    </label>
                    <textarea
                      id="new-template-body-text"
                      className={styles.textarea}
                      value={createForm.body_text}
                      onChange={(event) =>
                        setCreateForm({ ...createForm, body_text: event.target.value })
                      }
                      placeholder="Plain text fallback..."
                    />
                  </div>

                  <div className={styles.hint}>
                    💡 Only standard recipient tokens are allowed: <code>{"{{first_name}}"}</code>,{" "}
                    <code>{"{{last_name}}"}</code>, <code>{"{{email}}"}</code>,{" "}
                    <code>{"{{company_name}}"}</code>.
                  </div>
                </div>

                {/* Right Live Preview Column */}
                <div className={styles.editorPreviewColumn}>
                  <div className={styles.editorPreviewHeader}>
                    <span className={styles.editorPreviewTitle}>Live Email Preview</span>
                    <div className={styles.deviceToggleGroup}>
                      <button
                        type="button"
                        className={`${styles.deviceButton} ${
                          editorDeviceMode === "desktop" ? styles.deviceButtonActive : ""
                        }`}
                        onClick={() => setEditorDeviceMode("desktop")}
                      >
                        🖥️ Desktop
                      </button>
                      <button
                        type="button"
                        className={`${styles.deviceButton} ${
                          editorDeviceMode === "mobile" ? styles.deviceButtonActive : ""
                        }`}
                        onClick={() => setEditorDeviceMode("mobile")}
                      >
                        📱 Mobile
                      </button>
                    </div>
                  </div>

                  <div className={styles.editorPreviewFrameContainer}>
                    {createForm.body_html ? (
                      <iframe
                        title="Create template live preview"
                        className={
                          editorDeviceMode === "desktop"
                            ? styles.editorPreviewFrameDesktop
                            : styles.editorPreviewFrameMobile
                        }
                        sandbox=""
                        srcDoc={createForm.body_html}
                      />
                    ) : (
                      <div className={styles.editorPreviewPlaceholder}>
                        <p style={{ fontSize: "28px", margin: "0 0 8px 0" }}>✉️</p>
                        <strong>No HTML entered yet</strong>
                        <p style={{ margin: "4px 0 0 0", fontSize: "12.5px" }}>
                          Type or paste HTML in the left editor to preview your email in real-time.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className={styles.editorModalFooter}>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={() => setCreateFormOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className={styles.actionButton} disabled={creating}>
                  {creating ? "Publishing…" : "Publish Default Template"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =========================================================================
         Side-by-Side Modal: Edit Default Template (New Version)
         ========================================================================= */}
      {editingTemplate && (
        <div
          className={styles.editorModalBackdrop}
          onClick={() => setEditingTemplate(null)}
          role="dialog"
          aria-modal="true"
        >
          <div className={styles.editorModalCard} onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleEditSubmit} style={{ display: "contents" }}>
              <div className={styles.editorModalHeader}>
                <div className={styles.editorModalTitleGroup}>
                  <h3 className={styles.editorModalTitle}>
                    ✏️ Edit &quot;{editingTemplate.name}&quot;
                  </h3>
                  <p className={styles.editorModalSubtitle}>
                    Saves as v{(editingTemplate.current_version?.version_number ?? 0) + 1}. Accounts
                    that already cloned keep their independent copy.
                  </p>
                </div>
                <button
                  type="button"
                  className={styles.closeButton}
                  onClick={() => setEditingTemplate(null)}
                  aria-label="Close dialog"
                >
                  ✕
                </button>
              </div>

              <div className={styles.editorModalBody}>
                {/* Left Form Column */}
                <div className={styles.editorFormColumn}>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`edit-subject-${editingTemplate.id}`}>
                      Subject Line *
                    </label>
                    <input
                      id={`edit-subject-${editingTemplate.id}`}
                      className={styles.input}
                      required
                      value={editForm.subject}
                      onChange={(event) =>
                        setEditForm({ ...editForm, subject: event.target.value })
                      }
                    />
                  </div>

                  <div className={styles.field}>
                    <label
                      className={styles.label}
                      htmlFor={`edit-body-html-${editingTemplate.id}`}
                    >
                      Body (HTML) *
                    </label>
                    <textarea
                      id={`edit-body-html-${editingTemplate.id}`}
                      className={styles.htmlTextarea}
                      required
                      value={editForm.body_html}
                      onChange={(event) =>
                        setEditForm({ ...editForm, body_html: event.target.value })
                      }
                    />
                  </div>

                  <div className={styles.field}>
                    <label
                      className={styles.label}
                      htmlFor={`edit-body-text-${editingTemplate.id}`}
                    >
                      Body (plain text, optional)
                    </label>
                    <textarea
                      id={`edit-body-text-${editingTemplate.id}`}
                      className={styles.textarea}
                      value={editForm.body_text}
                      onChange={(event) =>
                        setEditForm({ ...editForm, body_text: event.target.value })
                      }
                    />
                  </div>

                  <div className={styles.hint}>
                    💡 Only standard recipient tokens are allowed: <code>{"{{first_name}}"}</code>,{" "}
                    <code>{"{{last_name}}"}</code>, <code>{"{{email}}"}</code>,{" "}
                    <code>{"{{company_name}}"}</code>.
                  </div>
                </div>

                {/* Right Live Preview Column */}
                <div className={styles.editorPreviewColumn}>
                  <div className={styles.editorPreviewHeader}>
                    <span className={styles.editorPreviewTitle}>Live Email Preview</span>
                    <div className={styles.deviceToggleGroup}>
                      <button
                        type="button"
                        className={`${styles.deviceButton} ${
                          editorDeviceMode === "desktop" ? styles.deviceButtonActive : ""
                        }`}
                        onClick={() => setEditorDeviceMode("desktop")}
                      >
                        🖥️ Desktop
                      </button>
                      <button
                        type="button"
                        className={`${styles.deviceButton} ${
                          editorDeviceMode === "mobile" ? styles.deviceButtonActive : ""
                        }`}
                        onClick={() => setEditorDeviceMode("mobile")}
                      >
                        📱 Mobile
                      </button>
                    </div>
                  </div>

                  <div className={styles.editorPreviewFrameContainer}>
                    {editForm.body_html ? (
                      <iframe
                        title="Edit template live preview"
                        className={
                          editorDeviceMode === "desktop"
                            ? styles.editorPreviewFrameDesktop
                            : styles.editorPreviewFrameMobile
                        }
                        sandbox=""
                        srcDoc={editForm.body_html}
                      />
                    ) : (
                      <div className={styles.editorPreviewPlaceholder}>
                        <p style={{ fontSize: "28px", margin: "0 0 8px 0" }}>✉️</p>
                        <strong>No HTML entered</strong>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className={styles.editorModalFooter}>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={() => setEditingTemplate(null)}
                >
                  Cancel
                </button>
                <button type="submit" className={styles.actionButton} disabled={savingEdit}>
                  {savingEdit ? "Saving…" : "Save New Version"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Fullscreen Preview Modal */}
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
