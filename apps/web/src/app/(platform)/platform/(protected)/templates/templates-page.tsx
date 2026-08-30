"use client";

import { type FormEvent, useEffect, useState } from "react";

import { TemplatePreviewModal } from "@/components/template-preview/template-preview-modal";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./templates-page.module.css";
import type { EmailTemplate } from "./types";

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

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    subject: "",
    body_html: "",
    body_text: "",
  });
  const [savingEdit, setSavingEdit] = useState(false);

  const [retiringId, setRetiringId] = useState<string | null>(null);
  const [previewingTemplate, setPreviewingTemplate] = useState<EmailTemplate | null>(null);

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

  function openCreateForm() {
    setCreateForm(blankCreateForm());
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
    setEditingId(template.id);
    setEditForm({
      subject: template.current_version?.subject ?? "",
      body_html: template.current_version?.body_html ?? "",
      body_text: template.current_version?.body_text ?? "",
    });
  }

  async function handleEditSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingId) return;
    setSavingEdit(true);
    try {
      const updated = await apiFetch<EmailTemplate>(`/platform/templates/${editingId}/versions`, {
        method: "POST",
        body: JSON.stringify({
          subject: editForm.subject.trim(),
          body_html: editForm.body_html,
          body_text: editForm.body_text.trim() === "" ? null : editForm.body_text,
        }),
      });
      setTemplates((current) => current.map((t) => (t.id === updated.id ? updated : t)));
      showToast(
        "success",
        `"${updated.name}" updated to v${updated.current_version?.version_number}.`,
      );
      setEditingId(null);
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

        {createFormOpen && (
          <form onSubmit={handleCreate} className={styles.form}>
            <div className={styles.formHeading}>New default template</div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="new-template-name">
                Name
              </label>
              <input
                id="new-template-name"
                className={styles.input}
                required
                value={createForm.name}
                onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })}
                placeholder="e.g. Welcome Series Kickoff"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="new-template-subject">
                Subject
              </label>
              <input
                id="new-template-subject"
                className={styles.input}
                required
                value={createForm.subject}
                onChange={(event) => setCreateForm({ ...createForm, subject: event.target.value })}
                placeholder="e.g. Welcome to Growixa, {{first_name}}!"
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label} htmlFor="new-template-body-html">
                Body (HTML)
              </label>
              <textarea
                id="new-template-body-html"
                className={styles.textarea}
                required
                value={createForm.body_html}
                onChange={(event) =>
                  setCreateForm({ ...createForm, body_html: event.target.value })
                }
                placeholder="<p>Hi {{first_name}}...</p>"
              />
            </div>
            {createForm.body_html && (
              <div className={styles.previewPane}>
                <div className={styles.previewLabel}>Live preview</div>
                <iframe
                  title="Create template live preview"
                  className={styles.previewFrame}
                  sandbox=""
                  srcDoc={createForm.body_html}
                />
              </div>
            )}
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
              />
            </div>
            <div className={styles.hint}>
              Only standard recipient/account tokens are allowed (no account-specific custom fields)
              — a default template must render the same for every account.
            </div>
            <div className={styles.formActions}>
              <button type="submit" className={styles.actionButton} disabled={creating}>
                {creating ? "Publishing…" : "Publish"}
              </button>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setCreateFormOpen(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className={styles.list}>
          {templates.length === 0 && !createFormOpen && (
            <div className={styles.rowSubject}>No default templates published yet.</div>
          )}
          {templates.map((template) => (
            <div key={template.id}>
              <div className={styles.row}>
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
                    onClick={() =>
                      editingId === template.id ? setEditingId(null) : openEditForm(template)
                    }
                  >
                    {editingId === template.id ? "Cancel edit" : "Edit"}
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

              {editingId === template.id && (
                <form onSubmit={handleEditSubmit} className={styles.form}>
                  <div className={styles.formHeading}>
                    Edit &quot;{template.name}&quot; — saves as a new version, existing clones are
                    unaffected
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`edit-subject-${template.id}`}>
                      Subject
                    </label>
                    <input
                      id={`edit-subject-${template.id}`}
                      className={styles.input}
                      required
                      value={editForm.subject}
                      onChange={(event) =>
                        setEditForm({ ...editForm, subject: event.target.value })
                      }
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`edit-body-html-${template.id}`}>
                      Body (HTML)
                    </label>
                    <textarea
                      id={`edit-body-html-${template.id}`}
                      className={styles.textarea}
                      required
                      value={editForm.body_html}
                      onChange={(event) =>
                        setEditForm({ ...editForm, body_html: event.target.value })
                      }
                    />
                  </div>
                  {editForm.body_html && (
                    <div className={styles.previewPane}>
                      <div className={styles.previewLabel}>Live preview</div>
                      <iframe
                        title="Edit template live preview"
                        className={styles.previewFrame}
                        sandbox=""
                        srcDoc={editForm.body_html}
                      />
                    </div>
                  )}
                  <div className={styles.field}>
                    <label className={styles.label} htmlFor={`edit-body-text-${template.id}`}>
                      Body (plain text, optional)
                    </label>
                    <textarea
                      id={`edit-body-text-${template.id}`}
                      className={styles.textarea}
                      value={editForm.body_text}
                      onChange={(event) =>
                        setEditForm({ ...editForm, body_text: event.target.value })
                      }
                    />
                  </div>
                  <div className={styles.formActions}>
                    <button type="submit" className={styles.actionButton} disabled={savingEdit}>
                      {savingEdit ? "Saving…" : "Save new version"}
                    </button>
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => setEditingId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          ))}
        </div>
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
