"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { TEMPLATE_PRESETS } from "./presets";
import styles from "./template-form-page.module.css";
import type { EmailTemplate, MeResponse } from "./types";

const MANAGE_PERMISSION = "campaigns.manage";

interface FormState {
  name: string;
  subject: string;
  body_html: string;
  body_text: string;
}

const EMPTY_FORM: FormState = { name: "", subject: "", body_html: "", body_text: "" };

const VOID_ELEMENTS = new Set([
  "area",
  "base",
  "br",
  "col",
  "embed",
  "hr",
  "img",
  "input",
  "link",
  "meta",
  "param",
  "source",
  "track",
  "wbr",
]);

function formatHtml(html: string): string {
  const tokens = html
    .replace(/>\s*</g, "><")
    .match(/<!--[\s\S]*?-->|<!DOCTYPE[^>]*>|<\/?[^>]+>|[^<]+/gi);
  if (!tokens) return html;

  let indent = 0;
  const lines: string[] = [];

  for (const raw of tokens) {
    const token = raw.trim();
    if (!token) continue;

    if (token.startsWith("<!--") || token.startsWith("<!DOCTYPE")) {
      lines.push("  ".repeat(indent) + token);
      continue;
    }

    if (token.startsWith("</")) {
      indent = Math.max(indent - 1, 0);
      lines.push("  ".repeat(indent) + token);
      continue;
    }

    if (token.startsWith("<")) {
      lines.push("  ".repeat(indent) + token);
      const tagName = token.match(/^<([a-zA-Z0-9-]+)/)?.[1]?.toLowerCase();
      const selfClosing = token.endsWith("/>") || (!!tagName && VOID_ELEMENTS.has(tagName));
      if (!selfClosing) indent += 1;
      continue;
    }

    lines.push("  ".repeat(indent) + token);
  }

  return lines.join("\n");
}

interface TemplateFormPageProps {
  mode: "create" | "edit";
  templateId?: string;
}

export function TemplateFormPage({ mode, templateId }: TemplateFormPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const duplicateFrom = searchParams.get("duplicateFrom");
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasManage = me.permissions.includes(MANAGE_PERMISSION);
        setCanManage(hasManage);
        if (!hasManage) return;

        if (mode === "edit" && templateId) {
          const template = await apiFetch<EmailTemplate>(`/templates/${templateId}`);
          setForm({
            name: template.name,
            subject: template.current_version?.subject ?? "",
            body_html: template.current_version?.body_html ?? "",
            body_text: template.current_version?.body_text ?? "",
          });
        } else if (mode === "create" && duplicateFrom) {
          const source = await apiFetch<EmailTemplate>(`/templates/${duplicateFrom}`);
          setForm({
            name: `${source.name} (copy)`,
            subject: source.current_version?.subject ?? "",
            body_html: source.current_version?.body_html ?? "",
            body_text: source.current_version?.body_text ?? "",
          });
        }
      } catch {
        setLoadError(
          mode === "edit" ? "Could not load that template." : "Could not load the source template.",
        );
      } finally {
        setLoading(false);
      }
    }

    void load();
    // duplicateFrom/templateId only ever meaningfully change via a fresh navigation to
    // this page, not in-place — safe to treat as load-once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, templateId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      if (mode === "create") {
        await apiFetch<EmailTemplate>("/templates", {
          method: "POST",
          body: JSON.stringify({
            name: form.name,
            subject: form.subject,
            body_html: form.body_html,
            body_text: form.body_text || null,
          }),
        });
        showToast("success", "Template created.");
      } else {
        await apiFetch<EmailTemplate>(`/templates/${templateId}/versions`, {
          method: "POST",
          body: JSON.stringify({
            subject: form.subject,
            body_html: form.body_html,
            body_text: form.body_text || null,
          }),
        });
        showToast("success", "Template updated — a new version was saved.");
      }
      router.push("/dashboard/templates");
    } catch {
      showToast(
        "error",
        mode === "create"
          ? "Could not create that template. Please try again."
          : "Could not save that edit. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  function handleFormatHtml() {
    if (!form.body_html.trim()) return;
    setForm((prev) => ({ ...prev, body_html: formatHtml(prev.body_html) }));
  }

  async function handleCopyHtml() {
    try {
      await navigator.clipboard.writeText(form.body_html);
      showToast("success", "HTML body copied to clipboard.");
    } catch {
      showToast("error", "Could not copy to clipboard.");
    }
  }

  function handleSelectPreset(presetId: string) {
    if (!presetId) return;
    const preset = TEMPLATE_PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setForm({
        name: form.name || preset.name,
        subject: preset.subject,
        body_html: preset.body_html,
        body_text: preset.body_text,
      });
      showToast("success", `Loaded "${preset.name}" starter template.`);
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

  if (!canManage) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to email templates.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/dashboard/templates">Templates</Link>
        <span aria-hidden="true"> / </span>
        <span>{mode === "create" ? "New template" : "Edit template"}</span>
      </nav>

      <div className={styles.split}>
        <form className={styles.formCard} onSubmit={handleSubmit}>
          <h2 className={styles.heading}>{mode === "create" ? "New template" : "Edit template"}</h2>
          {mode === "edit" ? (
            <p className={styles.hint}>
              Saving appends a new version — the template name can&apos;t be changed here.
            </p>
          ) : (
            <div className={styles.field} style={{ marginBottom: "20px" }}>
              <label className={styles.label} htmlFor="preset-select">
                ⚡ Load a Starter Template (Optional)
              </label>
              <select
                id="preset-select"
                className={styles.input}
                defaultValue=""
                onChange={(e) => handleSelectPreset(e.target.value)}
              >
                <option value="" disabled>
                  -- Select a pre-built template to auto-fill --
                </option>
                {TEMPLATE_PRESETS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.category})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="template-name">
              Template name
            </label>
            <input
              id="template-name"
              className={styles.input}
              required
              disabled={mode === "edit"}
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="template-subject">
              Email subject
            </label>
            <input
              id="template-subject"
              className={styles.input}
              required
              value={form.subject}
              onChange={(event) => setForm({ ...form, subject: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <div className={styles.fieldHeader}>
              <label className={styles.label} htmlFor="template-body-html">
                HTML body
              </label>
              <div className={styles.fieldActions}>
                <button type="button" className={styles.miniButton} onClick={handleFormatHtml}>
                  Format
                </button>
                <button type="button" className={styles.miniButton} onClick={handleCopyHtml}>
                  Copy
                </button>
              </div>
            </div>
            <textarea
              id="template-body-html"
              className={styles.codeTextarea}
              required
              value={form.body_html}
              onChange={(event) => setForm({ ...form, body_html: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="template-body-text">
              Plain-text body (optional)
            </label>
            <textarea
              id="template-body-text"
              className={styles.textarea}
              value={form.body_text}
              onChange={(event) => setForm({ ...form, body_text: event.target.value })}
            />
          </div>

          <div className={styles.formActions}>
            <button type="button" className={styles.secondaryButton} onClick={() => router.back()}>
              Cancel
            </button>
            <button type="submit" className={styles.actionButton} disabled={submitting}>
              {submitting
                ? mode === "create"
                  ? "Creating…"
                  : "Saving…"
                : mode === "create"
                  ? "Create template"
                  : "Save new version"}
            </button>
          </div>
        </form>

        <div className={styles.previewCard}>
          <h3 className={styles.previewHeading}>Live preview</h3>
          {form.body_html ? (
            <iframe
              title="Template preview"
              className={styles.previewFrame}
              sandbox=""
              srcDoc={form.body_html}
            />
          ) : (
            <p className={styles.hint}>Start typing the HTML body to see a preview.</p>
          )}
        </div>
      </div>
    </div>
  );
}
