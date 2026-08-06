"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatHtml } from "@/lib/format-html";

import type { EmailTemplate } from "../templates/types";
import styles from "./campaign-form-page.module.css";
import type {
  Campaign,
  CampaignReport,
  ContactListSummary,
  MeResponse,
  RecipientType,
  SegmentSummary,
  SenderIdentity,
} from "./types";

const VIEW_PERMISSION = "campaigns.view";
const MANAGE_PERMISSION = "campaigns.manage";
const SEND_PERMISSION = "campaigns.send";

interface FormState {
  name: string;
  subject: string;
  body_html: string;
  body_text: string;
  sender_identity_id: string;
  recipient_type: RecipientType;
  recipient_target_id: string;
  template_id: string | null;
}

const EMPTY_FORM: FormState = {
  name: "",
  subject: "",
  body_html: "",
  body_text: "",
  sender_identity_id: "",
  recipient_type: "ALL_CONTACTS",
  recipient_target_id: "",
  template_id: null,
};

function campaignToForm(campaign: Campaign): FormState {
  return {
    name: campaign.name,
    subject: campaign.subject,
    body_html: campaign.body_html,
    body_text: campaign.body_text ?? "",
    sender_identity_id: campaign.sender_identity_id,
    recipient_type: campaign.recipient_type,
    recipient_target_id: campaign.recipient_list_id ?? campaign.recipient_segment_id ?? "",
    template_id: campaign.template_id,
  };
}

interface CampaignFormPageProps {
  mode: "create" | "edit";
  campaignId?: string;
}

export function CampaignFormPage({ mode, campaignId }: CampaignFormPageProps) {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [canSend, setCanSend] = useState(false);

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [report, setReport] = useState<CampaignReport | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);

  const [senderIdentities, setSenderIdentities] = useState<SenderIdentity[]>([]);
  const [lists, setLists] = useState<ContactListSummary[]>([]);
  const [segments, setSegments] = useState<SegmentSummary[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);

  const [testEmail, setTestEmail] = useState("");
  const [testSending, setTestSending] = useState(false);
  const [sendingNow, setSendingNow] = useState(false);

  // Send Mode: only visible to canManage users on DRAFT campaigns
  type SendMode = "now" | "schedule";
  const [sendMode, setSendMode] = useState<SendMode>("now");
  const [scheduledAt, setScheduledAt] = useState("");
  const [scheduling, setScheduling] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        const hasManage = me.permissions.includes(MANAGE_PERMISSION);
        setCanManage(hasManage);
        setCanSend(me.permissions.includes(SEND_PERMISSION));

        if (mode === "create" && !hasManage) {
          setLoading(false);
          return;
        }
        if (mode === "edit" && !hasView) {
          setLoading(false);
          return;
        }

        const [identities, listResults, segmentResults, templateResults] = await Promise.all([
          apiFetch<SenderIdentity[]>("/integrations/sender-identities"),
          apiFetch<ContactListSummary[]>("/contacts/lists"),
          apiFetch<SegmentSummary[]>("/contacts/segments"),
          apiFetch<EmailTemplate[]>("/templates"),
        ]);
        setSenderIdentities(identities);
        setLists(listResults);
        setSegments(segmentResults);
        setTemplates(templateResults);

        if (mode === "edit" && campaignId) {
          const loaded = await apiFetch<Campaign>(`/campaigns/${campaignId}`);
          setCampaign(loaded);
          setForm(campaignToForm(loaded));
          if (loaded.status !== "DRAFT") {
            // Best-effort: the report is supplementary, so a failure here shouldn't
            // block the rest of the page (which already loaded successfully) from rendering.
            try {
              const reportData = await apiFetch<CampaignReport>(`/campaigns/${campaignId}/report`);
              setReport(reportData);
            } catch {
              // Leave report null — no report section renders.
            }
          }
        }
      } catch {
        setLoadError("Could not load this campaign.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [mode, campaignId]);

  const editable = canManage && (mode === "create" || campaign?.status === "DRAFT");

  function buildPayload() {
    return {
      name: form.name,
      subject: form.subject,
      body_html: form.body_html,
      body_text: form.body_text || null,
      template_id: form.template_id,
      sender_identity_id: form.sender_identity_id,
      recipient_type: form.recipient_type,
      recipient_segment_id: form.recipient_type === "SEGMENT" ? form.recipient_target_id : null,
      recipient_list_id: form.recipient_type === "LIST" ? form.recipient_target_id : null,
    };
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      if (mode === "create") {
        const created = await apiFetch<Campaign>("/campaigns", {
          method: "POST",
          body: JSON.stringify(buildPayload()),
        });
        showToast("success", "Campaign created.");
        router.push(`/dashboard/campaigns/${created.id}`);
      } else if (campaignId) {
        const updated = await apiFetch<Campaign>(`/campaigns/${campaignId}`, {
          method: "PATCH",
          body: JSON.stringify(buildPayload()),
        });
        setCampaign(updated);
        setForm(campaignToForm(updated));
        showToast("success", "Campaign saved.");
      }
    } catch {
      showToast(
        "error",
        mode === "create"
          ? "Could not create that campaign. Please try again."
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

  function handleSelectTemplate(templateId: string) {
    if (!templateId) return;
    const template = templates.find((t) => t.id === templateId);
    if (template?.current_version) {
      setForm((prev) => ({
        ...prev,
        subject: template.current_version!.subject,
        body_html: template.current_version!.body_html,
        body_text: template.current_version!.body_text ?? "",
        template_id: template.id,
      }));
      showToast("success", `Loaded content from "${template.name}".`);
    }
  }

  async function handleTestSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!campaignId) return;
    setTestSending(true);
    try {
      await apiFetch<void>(`/campaigns/${campaignId}/test-send`, {
        method: "POST",
        body: JSON.stringify({ to_email: testEmail }),
      });
      showToast("success", `Test email sent to ${testEmail}.`);
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not send that test email."));
    } finally {
      setTestSending(false);
    }
  }

  async function handleSendNow() {
    if (!campaign) return;
    if (!window.confirm(`Send "${campaign.name}" now? This cannot be undone.`)) {
      return;
    }
    setSendingNow(true);
    try {
      await apiFetch<{ job_id: string }>(`/campaigns/${campaign.id}/send`, { method: "POST" });
      setCampaign((prev) => (prev ? { ...prev, status: "SENDING" } : prev));
      showToast("success", "Campaign is sending — check back shortly for delivery status.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not send that campaign."));
    } finally {
      setSendingNow(false);
    }
  }

  async function handleSchedule() {
    if (!campaign || !scheduledAt) return;
    // Convert local datetime-local value to UTC ISO string
    const utcIso = new Date(scheduledAt).toISOString();
    setScheduling(true);
    try {
      const updated = await apiFetch<Campaign>(`/campaigns/${campaign.id}/schedule`, {
        method: "POST",
        body: JSON.stringify({ scheduled_at: utcIso }),
      });
      setCampaign(updated);
      showToast(
        "success",
        `Campaign scheduled for ${new Date(utcIso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}.`,
      );
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not schedule that campaign."));
    } finally {
      setScheduling(false);
    }
  }

  // Minimum selectable datetime: now + 10 minutes (UX safeguard)
  function minDatetimeLocal(): string {
    const d = new Date(Date.now() + 10 * 60 * 1000);
    // datetime-local requires "YYYY-MM-DDTHH:mm"
    return d.toISOString().slice(0, 16);
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

  if (mode === "create" && !canManage) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to create campaigns.</div>
      </div>
    );
  }

  if (mode === "edit" && !campaign) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to campaigns.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/dashboard/campaigns">Campaigns</Link>
        <span aria-hidden="true"> / </span>
        <span>{mode === "create" ? "New campaign" : form.name || "Campaign"}</span>
      </nav>

      <div className={styles.split}>
        <form className={styles.formCard} onSubmit={handleSubmit}>
          <h2 className={styles.heading}>{mode === "create" ? "New campaign" : form.name}</h2>
          {campaign && (
            <span className={`${styles.statusBadge} ${styles[`status${campaign.status}`]}`}>
              {campaign.status}
            </span>
          )}
          {mode === "edit" && campaign && campaign.status !== "DRAFT" && (
            <p className={styles.hint}>
              This campaign is no longer a draft and can&apos;t be edited.
            </p>
          )}

          {editable && templates.length > 0 && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="load-template">
                Load content from a template (optional)
              </label>
              <select
                id="load-template"
                className={styles.input}
                defaultValue=""
                onChange={(event) => handleSelectTemplate(event.target.value)}
              >
                <option value="" disabled>
                  -- Select a template --
                </option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className={styles.field}>
            <label className={styles.label} htmlFor="campaign-name">
              Campaign name
            </label>
            <input
              id="campaign-name"
              className={styles.input}
              required
              disabled={!editable}
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="campaign-subject">
              Email subject
            </label>
            <input
              id="campaign-subject"
              className={styles.input}
              required
              disabled={!editable}
              value={form.subject}
              onChange={(event) => setForm({ ...form, subject: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="sender-identity">
              Sender identity
            </label>
            <select
              id="sender-identity"
              className={styles.input}
              required
              disabled={!editable}
              value={form.sender_identity_id}
              onChange={(event) => setForm({ ...form, sender_identity_id: event.target.value })}
            >
              <option value="" disabled>
                -- Select a sender --
              </option>
              {senderIdentities.map((identity) => (
                <option key={identity.id} value={identity.id}>
                  {identity.from_name} &lt;{identity.from_email}&gt;
                </option>
              ))}
            </select>
            {senderIdentities.length === 0 && (
              <p className={styles.hint}>
                No sender identities configured yet — add one under Integrations first.
              </p>
            )}
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="recipient-type">
              Recipients
            </label>
            <select
              id="recipient-type"
              className={styles.input}
              disabled={!editable}
              value={form.recipient_type}
              onChange={(event) =>
                setForm({
                  ...form,
                  recipient_type: event.target.value as RecipientType,
                  recipient_target_id: "",
                })
              }
            >
              <option value="ALL_CONTACTS">All contacts</option>
              <option value="LIST">A specific list</option>
              <option value="SEGMENT">A specific segment</option>
            </select>
          </div>

          {form.recipient_type === "LIST" && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="recipient-list">
                List
              </label>
              <select
                id="recipient-list"
                className={styles.input}
                required
                disabled={!editable}
                value={form.recipient_target_id}
                onChange={(event) => setForm({ ...form, recipient_target_id: event.target.value })}
              >
                <option value="" disabled>
                  -- Select a list --
                </option>
                {lists.map((list) => (
                  <option key={list.id} value={list.id}>
                    {list.name} ({list.member_count})
                  </option>
                ))}
              </select>
            </div>
          )}

          {form.recipient_type === "SEGMENT" && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="recipient-segment">
                Segment
              </label>
              <select
                id="recipient-segment"
                className={styles.input}
                required
                disabled={!editable}
                value={form.recipient_target_id}
                onChange={(event) => setForm({ ...form, recipient_target_id: event.target.value })}
              >
                <option value="" disabled>
                  -- Select a segment --
                </option>
                {segments.map((segment) => (
                  <option key={segment.id} value={segment.id}>
                    {segment.name} ({segment.member_count})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className={styles.field}>
            <div className={styles.fieldHeader}>
              <label className={styles.label} htmlFor="campaign-body-html">
                HTML body
              </label>
              {editable && (
                <div className={styles.fieldActions}>
                  <button type="button" className={styles.miniButton} onClick={handleFormatHtml}>
                    Format
                  </button>
                  <button type="button" className={styles.miniButton} onClick={handleCopyHtml}>
                    Copy
                  </button>
                </div>
              )}
            </div>
            <textarea
              id="campaign-body-html"
              className={styles.codeTextarea}
              required
              disabled={!editable}
              value={form.body_html}
              onChange={(event) => setForm({ ...form, body_html: event.target.value })}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="campaign-body-text">
              Plain-text body (optional)
            </label>
            <textarea
              id="campaign-body-text"
              className={styles.textarea}
              disabled={!editable}
              value={form.body_text}
              onChange={(event) => setForm({ ...form, body_text: event.target.value })}
            />
          </div>

          {editable && (
            <div className={styles.formActions}>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => router.back()}
              >
                Cancel
              </button>
              <button type="submit" className={styles.actionButton} disabled={submitting}>
                {submitting
                  ? mode === "create"
                    ? "Creating…"
                    : "Saving…"
                  : mode === "create"
                    ? "Create campaign"
                    : "Save changes"}
              </button>
            </div>
          )}
        </form>

        <div className={styles.sideColumn}>
          <div className={styles.previewCard}>
            <h3 className={styles.previewHeading}>Live preview</h3>
            {form.body_html ? (
              <iframe
                title="Campaign preview"
                className={styles.previewFrame}
                sandbox=""
                srcDoc={form.body_html}
              />
            ) : (
              <p className={styles.hint}>Start typing the HTML body to see a preview.</p>
            )}
          </div>

          {report && (
            <div className={styles.reportCard}>
              <h3 className={styles.previewHeading}>Delivery report</h3>
              <div className={styles.reportGrid}>
                <div className={styles.reportStat}>
                  <span className={styles.reportValue}>{report.sent}</span>
                  <span className={styles.reportLabel}>Sent</span>
                </div>
                <div className={styles.reportStat}>
                  <span className={styles.reportValue}>
                    {formatMetric(report.delivered, report.sent)}
                  </span>
                  <span className={styles.reportLabel}>Delivered</span>
                </div>
                <div className={styles.reportStat}>
                  <span className={styles.reportValue}>
                    {formatMetric(report.opened, report.delivered)}
                  </span>
                  <span className={styles.reportLabel}>Opened</span>
                </div>
                <div className={styles.reportStat}>
                  <span className={styles.reportValue}>
                    {formatMetric(report.clicked, report.delivered)}
                  </span>
                  <span className={styles.reportLabel}>Clicked</span>
                </div>
                <div className={styles.reportStat}>
                  <span className={styles.reportValue}>
                    {formatMetric(report.bounced, report.sent)}
                  </span>
                  <span className={styles.reportLabel}>Bounced</span>
                </div>
                <div className={styles.reportStat}>
                  <span className={styles.reportValue}>
                    {formatMetric(report.complained, report.sent)}
                  </span>
                  <span className={styles.reportLabel}>Complained</span>
                </div>
              </div>
            </div>
          )}

          {mode === "edit" && campaign && canSend && (
            <div className={styles.sendCard}>
              <h3 className={styles.previewHeading}>Test &amp; send</h3>
              <form className={styles.testSendForm} onSubmit={handleTestSend}>
                <label className={styles.label} htmlFor="test-send-email">
                  Send a test email
                </label>
                <div className={styles.testSendRow}>
                  <input
                    id="test-send-email"
                    type="email"
                    className={styles.input}
                    required
                    placeholder="you@example.com"
                    value={testEmail}
                    onChange={(event) => setTestEmail(event.target.value)}
                  />
                  <button type="submit" className={styles.secondaryButton} disabled={testSending}>
                    {testSending ? "Sending…" : "Send test"}
                  </button>
                </div>
              </form>

              {campaign.status === "DRAFT" && canManage && (
                <>
                  <div className={styles.sendModeGroup} role="group" aria-label="Send mode">
                    <label className={styles.sendModeOption}>
                      <input
                        type="radio"
                        name="send-mode"
                        value="now"
                        checked={sendMode === "now"}
                        onChange={() => setSendMode("now")}
                      />
                      Send Now
                    </label>
                    <label className={styles.sendModeOption}>
                      <input
                        type="radio"
                        name="send-mode"
                        value="schedule"
                        checked={sendMode === "schedule"}
                        onChange={() => setSendMode("schedule")}
                      />
                      Schedule for Later
                    </label>
                  </div>

                  {sendMode === "now" && (
                    <>
                      <p className={styles.hint}>
                        Sending now enqueues delivery to every resolved recipient. This can&apos;t
                        be undone.
                      </p>
                      <button
                        type="button"
                        className={styles.actionButton}
                        disabled={sendingNow}
                        onClick={handleSendNow}
                      >
                        {sendingNow ? "Starting send…" : "Send now"}
                      </button>
                    </>
                  )}

                  {sendMode === "schedule" && (
                    <>
                      <label className={styles.label} htmlFor="schedule-datetime">
                        Send date &amp; time
                      </label>
                      <input
                        id="schedule-datetime"
                        type="datetime-local"
                        className={`${styles.input} ${styles.schedulePicker}`}
                        min={minDatetimeLocal()}
                        value={scheduledAt}
                        onChange={(e) => setScheduledAt(e.target.value)}
                        required
                      />
                      {scheduledAt && (
                        <p className={styles.scheduleConfirmText}>
                          This campaign will be sent on{" "}
                          {new Date(scheduledAt).toLocaleString(undefined, {
                            weekday: "long",
                            month: "long",
                            day: "numeric",
                            year: "numeric",
                            hour: "numeric",
                            minute: "2-digit",
                          })}
                          .
                        </p>
                      )}
                      <button
                        type="button"
                        className={styles.actionButton}
                        disabled={scheduling || !scheduledAt}
                        onClick={handleSchedule}
                      >
                        {scheduling ? "Scheduling…" : "Confirm schedule"}
                      </button>
                    </>
                  )}
                </>
              )}

              {campaign.status === "SCHEDULED" && (
                <p className={styles.hint}>
                  This campaign is scheduled and will be sent automatically.{" "}
                  {campaign.scheduled_at &&
                    `Scheduled for ${new Date(campaign.scheduled_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}.`}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatMetric(count: number, denominator: number): string {
  if (denominator === 0) return `${count}`;
  const rate = Math.round((count / denominator) * 100);
  return `${count} (${rate}%)`;
}

function parseApiErrorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      // Keep fallback
    }
  }
  return fallback;
}
