"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";

import { AIGenerateButton } from "@/components/ai/ai-generate-button";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./post-form-page.module.css";
import type { MediaAsset, MeResponse, SocialConnection, SocialPost } from "./types";

const VIEW_PERMISSION = "social.view";
const MANAGE_PERMISSION = "social.manage";
const PUBLISH_PERMISSION = "social.publish";
const AI_MANAGE_PERMISSION = "ai.manage";

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

interface PostFormPageProps {
  mode: "create" | "edit";
  postId?: string;
}

export function PostFormPage({ mode, postId }: PostFormPageProps) {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [canPublish, setCanPublish] = useState(false);
  const [canGenerateAI, setCanGenerateAI] = useState(false);

  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [post, setPost] = useState<SocialPost | null>(null);
  const [connectionId, setConnectionId] = useState("");
  const [caption, setCaption] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [removingMediaId, setRemovingMediaId] = useState<string | null>(null);

  // UTM Parameters
  const [utmCampaign, setUtmCampaign] = useState("");
  const [utmSource, setUtmSource] = useState("");
  const [utmMedium, setUtmMedium] = useState("");
  const [utmContent, setUtmContent] = useState("");

  // Platform Preview Tab
  type PreviewPlatform = "LINKEDIN" | "TWITTER" | "INSTAGRAM_BUSINESS";
  const [previewTab, setPreviewTab] = useState<PreviewPlatform>("INSTAGRAM_BUSINESS");

  // Media Library Picker Modal
  const [showMediaModal, setShowMediaModal] = useState(false);
  const [mediaAssets, setMediaAssets] = useState<MediaAsset[]>([]);
  const [loadingMedia, setLoadingMedia] = useState(false);

  const [publishing, setPublishing] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [retrying, setRetrying] = useState(false);

  type ActionMode = "now" | "schedule";
  const [actionMode, setActionMode] = useState<ActionMode>("now");
  const [scheduledAt, setScheduledAt] = useState("");
  const [scheduling, setScheduling] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        const hasManage = me.permissions.includes(MANAGE_PERMISSION);
        setCanManage(hasManage);
        setCanPublish(me.permissions.includes(PUBLISH_PERMISSION));
        setCanGenerateAI(me.permissions.includes(AI_MANAGE_PERMISSION));

        if (mode === "create" && !hasManage) {
          setLoading(false);
          return;
        }
        if (mode === "edit" && !hasView) {
          setLoading(false);
          return;
        }

        if (mode === "create") {
          const connectionList = await apiFetch<SocialConnection[]>("/social/connections");
          setConnections(connectionList);
        }

        if (mode === "edit" && postId) {
          const loaded = await apiFetch<SocialPost>(`/social/posts/${postId}`);
          setPost(loaded);
          setCaption(loaded.caption);
          setUtmCampaign(loaded.utm_campaign ?? "");
          setUtmSource(loaded.utm_source ?? "");
          setUtmMedium(loaded.utm_medium ?? "");
          setUtmContent(loaded.utm_content ?? "");
        }
      } catch {
        setLoadError("Could not load this post.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [mode, postId]);

  async function fetchMediaLibrary() {
    setLoadingMedia(true);
    try {
      const assets = await apiFetch<MediaAsset[]>("/media");
      setMediaAssets(assets);
    } catch {
      showToast("error", "Could not load media library.");
    } finally {
      setLoadingMedia(false);
    }
  }

  const editable = canManage && (mode === "create" || post?.status === "DRAFT");

  const selectedConnection = connections.find(
    (c) => c.id === (mode === "create" ? connectionId : post?.social_connection_id),
  );
  const currentProvider =
    selectedConnection?.provider ??
    (previewTab === "TWITTER"
      ? "TWITTER"
      : previewTab === "LINKEDIN"
        ? "LINKEDIN"
        : "INSTAGRAM_BUSINESS");
  const maxChars =
    currentProvider === "TWITTER" ? 280 : currentProvider === "LINKEDIN" ? 3000 : 2200;
  const charsRemaining = maxChars - caption.length;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      if (mode === "create") {
        const payload: Record<string, unknown> = {
          social_connection_id: connectionId,
          caption,
        };
        if (utmCampaign) payload.utm_campaign = utmCampaign;
        if (utmSource) payload.utm_source = utmSource;
        if (utmMedium) payload.utm_medium = utmMedium;
        if (utmContent) payload.utm_content = utmContent;

        const created = await apiFetch<SocialPost>("/social/posts", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        showToast("success", "Draft created — now add an image.");
        router.push(`/dashboard/social/${created.id}`);
      } else if (postId) {
        const payload: Record<string, unknown> = {
          caption,
        };
        if (utmCampaign !== undefined) payload.utm_campaign = utmCampaign || null;
        if (utmSource !== undefined) payload.utm_source = utmSource || null;
        if (utmMedium !== undefined) payload.utm_medium = utmMedium || null;
        if (utmContent !== undefined) payload.utm_content = utmContent || null;

        const updated = await apiFetch<SocialPost>(`/social/posts/${postId}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
        setPost(updated);
        showToast("success", "Post saved.");
      }
    } catch {
      showToast(
        "error",
        mode === "create"
          ? "Could not create that post. Please try again."
          : "Could not save that edit. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    event.target.value = "";
    if (!file || !postId) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await apiFetch(`/social/posts/${postId}/media`, { method: "POST", body: formData });
      const refreshed = await apiFetch<SocialPost>(`/social/posts/${postId}`);
      setPost(refreshed);
      showToast("success", "Image added.");
    } catch (error) {
      showToast(
        "error",
        parseApiErrorDetail(error, "Could not upload that image — JPEG only, up to 8MB."),
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleSelectFromMediaLibrary(asset: MediaAsset) {
    if (!postId) return;
    setUploading(true);
    setShowMediaModal(false);
    try {
      const res = await fetch(asset.public_url);
      const blob = await res.blob();
      const file = new File([blob], asset.filename, { type: asset.mime_type || "image/jpeg" });
      const formData = new FormData();
      formData.append("file", file);
      await apiFetch(`/social/posts/${postId}/media`, { method: "POST", body: formData });
      const refreshed = await apiFetch<SocialPost>(`/social/posts/${postId}`);
      setPost(refreshed);
      showToast("success", `Attached ${asset.filename} from Media Library.`);
    } catch {
      showToast("error", "Could not attach image from Media Library.");
    } finally {
      setUploading(false);
    }
  }

  async function handleRemoveMedia(mediaId: string) {
    if (!postId) return;
    setRemovingMediaId(mediaId);
    try {
      await apiFetch(`/social/posts/${postId}/media/${mediaId}`, { method: "DELETE" });
      const refreshed = await apiFetch<SocialPost>(`/social/posts/${postId}`);
      setPost(refreshed);
      showToast("success", "Image removed.");
    } catch {
      showToast("error", "Could not remove that image.");
    } finally {
      setRemovingMediaId(null);
    }
  }

  async function handlePublishNow() {
    if (!post) return;
    const channelName =
      currentProvider === "TWITTER"
        ? "Twitter / X"
        : currentProvider === "LINKEDIN"
          ? "LinkedIn"
          : "Instagram";
    if (!window.confirm(`Publish this post to ${channelName} now? This cannot be undone.`)) return;
    setPublishing(true);
    try {
      await apiFetch<{ job_id: string }>(`/social/posts/${post.id}/publish`, { method: "POST" });
      setPost((prev) => (prev ? { ...prev, status: "DISPATCHING" } : prev));
      showToast("success", "Publishing — check back shortly for status.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not publish this post."));
    } finally {
      setPublishing(false);
    }
  }

  async function handleSchedule() {
    if (!post || !scheduledAt) return;
    const utcIso = new Date(scheduledAt).toISOString();
    setScheduling(true);
    try {
      const updated = await apiFetch<SocialPost>(`/social/posts/${post.id}/schedule`, {
        method: "POST",
        body: JSON.stringify({ scheduled_at: utcIso }),
      });
      setPost(updated);
      showToast("success", `Post scheduled for ${formatFull(utcIso)}.`);
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not schedule this post."));
    } finally {
      setScheduling(false);
    }
  }

  async function handleCancel() {
    if (!post) return;
    if (!window.confirm("Cancel this post?")) return;
    setCancelling(true);
    try {
      const updated = await apiFetch<SocialPost>(`/social/posts/${post.id}/cancel`, {
        method: "POST",
      });
      setPost(updated);
      showToast("success", "Post cancelled.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not cancel this post."));
    } finally {
      setCancelling(false);
    }
  }

  async function handleRetry() {
    if (!post) return;
    setRetrying(true);
    try {
      await apiFetch<{ job_id: string }>(`/social/posts/${post.id}/retry`, { method: "POST" });
      setPost((prev) => (prev ? { ...prev, status: "DISPATCHING" } : prev));
      showToast("success", "Retrying — check back shortly for status.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not retry this post."));
    } finally {
      setRetrying(false);
    }
  }

  function minDatetimeLocal(): string {
    const d = new Date(Date.now() + 10 * 60 * 1000);
    return d.toISOString().slice(0, 16);
  }

  function formatFull(iso: string): string {
    return new Date(iso).toLocaleString(undefined, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
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
        <div className={styles.card}>You don&apos;t have access to create posts.</div>
      </div>
    );
  }

  if (mode === "edit" && !post) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to social posts.</div>
      </div>
    );
  }

  const hasMedia = mode === "edit" && (post?.media.length ?? 0) > 0;

  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/dashboard/social">Social</Link>
        <span aria-hidden="true"> / </span>
        <span>{mode === "create" ? "New post" : "Post"}</span>
      </nav>

      <div className={styles.split}>
        <form className={styles.formCard} onSubmit={handleSubmit}>
          <h2 className={styles.heading}>{mode === "create" ? "New post" : "Edit post"}</h2>
          {post && (
            <span className={`${styles.statusBadge} ${styles[`status${post.status}`]}`}>
              {post.status}
            </span>
          )}
          {mode === "edit" && post && post.status !== "DRAFT" && (
            <p className={styles.hint}>This post is no longer a draft and can&apos;t be edited.</p>
          )}
          {post?.last_error && <p className={styles.errorText}>Error: {post.last_error}</p>}

          {mode === "create" && (
            <div className={styles.field}>
              <label className={styles.label} htmlFor="post-connection">
                Instagram connection
              </label>
              <select
                id="post-connection"
                className={styles.input}
                required
                value={connectionId}
                onChange={(event) => {
                  setConnectionId(event.target.value);
                  const chosen = connections.find((c) => c.id === event.target.value);
                  if (chosen?.provider === "TWITTER" || chosen?.provider === "LINKEDIN") {
                    setPreviewTab(chosen.provider);
                  } else {
                    setPreviewTab("INSTAGRAM_BUSINESS");
                  }
                }}
              >
                <option value="" disabled>
                  -- Select a connection --
                </option>
                {connections.map((connection) => {
                  const providerName =
                    connection.provider === "LINKEDIN"
                      ? "LinkedIn"
                      : connection.provider === "TWITTER"
                        ? "Twitter / X"
                        : "Instagram";
                  const name = connection.ig_username ?? connection.ig_business_account_id;
                  return (
                    <option key={connection.id} value={connection.id}>
                      {name} ({providerName})
                    </option>
                  );
                })}
              </select>
              {connections.length === 0 && (
                <p className={styles.hint}>
                  No accounts connected yet — connect LinkedIn, Twitter/X, or Instagram under
                  Integrations first.
                </p>
              )}
            </div>
          )}

          <div className={styles.field}>
            <div className={styles.fieldHeader}>
              <label className={styles.label} htmlFor="post-caption">
                Caption
              </label>
              {editable && canGenerateAI && (
                <div className={styles.fieldActions}>
                  <AIGenerateButton
                    capability="SOCIAL_CAPTION"
                    triggerLabel="Generate with AI"
                    briefPlaceholder="e.g. a 20% off sale on running shoes this weekend"
                    onInsert={(text) => setCaption(text)}
                    linkedEntityType="social_post"
                    linkedEntityId={postId}
                  />
                  <AIGenerateButton
                    capability="HASHTAGS"
                    triggerLabel="Suggest hashtags"
                    briefPlaceholder="e.g. running shoes sale"
                    onInsert={(text) => setCaption((prev) => (prev ? `${prev}\n\n${text}` : text))}
                    linkedEntityType="social_post"
                    linkedEntityId={postId}
                  />
                </div>
              )}
            </div>
            <textarea
              id="post-caption"
              className={styles.textarea}
              disabled={!editable}
              value={caption}
              onChange={(event) => setCaption(event.target.value)}
            />
            <div className={styles.charCountRow}>
              <span
                className={`${styles.charCount} ${
                  charsRemaining < 0
                    ? styles.charCountError
                    : charsRemaining <= 50
                      ? styles.charCountWarn
                      : ""
                }`}
              >
                {caption.length} / {maxChars} characters
                {charsRemaining < 0 && ` (${Math.abs(charsRemaining)} over limit)`}
              </span>
            </div>
          </div>

          {/* Collapsible UTM Tracking Section */}
          <details className={styles.accordion}>
            <summary className={styles.accordionSummary}>
              <span>Campaign &amp; UTM Tracking (Optional)</span>
              <span style={{ fontSize: "11px", opacity: 0.8 }}>▼</span>
            </summary>
            <div className={styles.accordionBody}>
              <div className={styles.utmGrid}>
                <div>
                  <label className={styles.label} htmlFor="utm-campaign">
                    Campaign Name
                  </label>
                  <input
                    id="utm-campaign"
                    type="text"
                    placeholder="e.g. spring_launch"
                    className={styles.input}
                    disabled={!editable}
                    value={utmCampaign}
                    onChange={(e) => setUtmCampaign(e.target.value)}
                  />
                </div>
                <div>
                  <label className={styles.label} htmlFor="utm-source">
                    Source
                  </label>
                  <input
                    id="utm-source"
                    type="text"
                    placeholder="e.g. linkedin, twitter, instagram"
                    className={styles.input}
                    disabled={!editable}
                    value={utmSource}
                    onChange={(e) => setUtmSource(e.target.value)}
                  />
                </div>
                <div>
                  <label className={styles.label} htmlFor="utm-medium">
                    Medium
                  </label>
                  <input
                    id="utm-medium"
                    type="text"
                    placeholder="e.g. social, organic"
                    className={styles.input}
                    disabled={!editable}
                    value={utmMedium}
                    onChange={(e) => setUtmMedium(e.target.value)}
                  />
                </div>
                <div>
                  <label className={styles.label} htmlFor="utm-content">
                    Content / Creative Tag
                  </label>
                  <input
                    id="utm-content"
                    type="text"
                    placeholder="e.g. variant_a"
                    className={styles.input}
                    disabled={!editable}
                    value={utmContent}
                    onChange={(e) => setUtmContent(e.target.value)}
                  />
                </div>
              </div>
              {(utmCampaign || utmSource || utmMedium || utmContent) && (
                <div className={styles.utmPreviewBox}>
                  <strong>Generated Tracking Params: </strong>
                  {[
                    utmSource && `utm_source=${encodeURIComponent(utmSource)}`,
                    utmMedium && `utm_medium=${encodeURIComponent(utmMedium)}`,
                    utmCampaign && `utm_campaign=${encodeURIComponent(utmCampaign)}`,
                    utmContent && `utm_content=${encodeURIComponent(utmContent)}`,
                  ]
                    .filter(Boolean)
                    .join("&")}
                </div>
              )}
            </div>
          </details>

          {mode === "edit" && (
            <div className={styles.field}>
              <span className={styles.label}>Image</span>
              {post?.media.map((media) => (
                <div className={styles.mediaRow} key={media.id}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={media.public_url} alt="" className={styles.mediaThumb} />
                  {editable && (
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      disabled={removingMediaId === media.id}
                      onClick={() => handleRemoveMedia(media.id)}
                    >
                      {removingMediaId === media.id ? "Removing…" : "Remove"}
                    </button>
                  )}
                </div>
              ))}
              {editable && !hasMedia && (
                <>
                  <label className={styles.label} htmlFor="post-media-file">
                    Upload image
                  </label>
                  <input
                    type="file"
                    accept="image/jpeg"
                    id="post-media-file"
                    className={styles.fileInput}
                    disabled={uploading}
                    onChange={handleFileChange}
                  />
                  <div className={styles.mediaButtonsRow}>
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      disabled={uploading}
                      onClick={() => {
                        setShowMediaModal(true);
                        void fetchMediaLibrary();
                      }}
                    >
                      🖼️ Choose from Media Library
                    </button>
                  </div>
                  <p className={styles.hint}>JPEG only, up to 8MB. Exactly one image per post.</p>
                </>
              )}
            </div>
          )}

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
                    ? "Create draft"
                    : "Save changes"}
              </button>
            </div>
          )}
        </form>

        {mode === "edit" && post && (
          <div className={styles.sideColumn}>
            <div className={styles.previewCard}>
              <h3 className={styles.previewHeading}>Live Platform Simulator</h3>
              <div className={styles.previewTabs}>
                <button
                  type="button"
                  className={`${styles.previewTab} ${
                    previewTab === "LINKEDIN" ? styles.previewTabActive : ""
                  }`}
                  onClick={() => setPreviewTab("LINKEDIN")}
                >
                  💼 LinkedIn
                </button>
                <button
                  type="button"
                  className={`${styles.previewTab} ${
                    previewTab === "TWITTER" ? styles.previewTabActive : ""
                  }`}
                  onClick={() => setPreviewTab("TWITTER")}
                >
                  🐦 Twitter / X
                </button>
                <button
                  type="button"
                  className={`${styles.previewTab} ${
                    previewTab === "INSTAGRAM_BUSINESS" ? styles.previewTabActive : ""
                  }`}
                  onClick={() => setPreviewTab("INSTAGRAM_BUSINESS")}
                >
                  📷 Instagram
                </button>
              </div>

              {previewTab === "LINKEDIN" && (
                <div className={styles.simulator}>
                  <div className={styles.liHeader}>
                    <div className={styles.liAvatar}>G</div>
                    <div className={styles.liMeta}>
                      <span className={styles.liName}>Growixa Professional</span>
                      <span className={styles.liSub}>Growth &amp; Marketing Engine • 1st</span>
                      <span className={styles.liTime}>Just now • 🌐</span>
                    </div>
                  </div>
                  <div className={styles.liBody}>
                    {caption || "Your post text will appear here…"}
                  </div>
                  {post.media[0] && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={post.media[0].public_url} alt="" className={styles.liImage} />
                  )}
                  <div className={styles.liActions}>
                    <span>👍 Like</span>
                    <span>💬 Comment</span>
                    <span>🔁 Repost</span>
                    <span>🚀 Send</span>
                  </div>
                </div>
              )}

              {previewTab === "TWITTER" && (
                <div className={styles.xCard}>
                  <div className={styles.xHeader}>
                    <div className={styles.xAvatar}>𝕏</div>
                    <div className={styles.xNameCol}>
                      <span className={styles.xName}>Growixa</span>
                      <span className={styles.xHandle}>@growixa · Just now</span>
                    </div>
                  </div>
                  <div className={styles.xBody}>{caption || "What is happening?!"}</div>
                  {post.media[0] && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={post.media[0].public_url} alt="" className={styles.xImage} />
                  )}
                  <div className={styles.xActions}>
                    <span>💬 12</span>
                    <span>🔁 48</span>
                    <span>❤️ 192</span>
                    <span>📊 2.4K</span>
                    <span>📤</span>
                  </div>
                </div>
              )}

              {previewTab === "INSTAGRAM_BUSINESS" && (
                <div className={styles.igCard}>
                  <div className={styles.igHeader}>
                    <div className={styles.igAvatar}>📸</div>
                    <span className={styles.igUsername}>growixa_official</span>
                  </div>
                  {post.media[0] ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={post.media[0].public_url} alt="" className={styles.igImage} />
                  ) : (
                    <div className={styles.igImagePlaceholder}>No image attached</div>
                  )}
                  <div className={styles.igActions}>
                    <div>❤️ 💬 🚀</div>
                    <div>🔖</div>
                  </div>
                  <div className={styles.igCaption}>
                    <strong>growixa_official</strong> {caption || "Caption preview…"}
                  </div>
                </div>
              )}
            </div>

            {post.ig_permalink && (
              <div className={styles.previewCard}>
                <h3 className={styles.previewHeading}>Published on Instagram</h3>
                <a href={post.ig_permalink} target="_blank" rel="noreferrer">
                  View on Instagram
                </a>
              </div>
            )}
            {post.provider_permalink && (
              <div className={styles.previewCard}>
                <h3 className={styles.previewHeading}>Published Post</h3>
                <a href={post.provider_permalink} target="_blank" rel="noreferrer">
                  View Live Post ↗
                </a>
              </div>
            )}

            {canPublish && hasMedia && post.status === "DRAFT" && (
              <div className={styles.sendCard}>
                <h3 className={styles.previewHeading}>Publish</h3>
                <div className={styles.sendModeGroup} role="group" aria-label="Publish mode">
                  <label className={styles.sendModeOption}>
                    <input
                      type="radio"
                      name="action-mode"
                      value="now"
                      checked={actionMode === "now"}
                      onChange={() => setActionMode("now")}
                    />
                    Publish Now
                  </label>
                  <label className={styles.sendModeOption}>
                    <input
                      type="radio"
                      name="action-mode"
                      value="schedule"
                      checked={actionMode === "schedule"}
                      onChange={() => setActionMode("schedule")}
                    />
                    Schedule for Later
                  </label>
                </div>

                {actionMode === "now" && (
                  <>
                    <p className={styles.hint}>
                      Publishing now sends this post immediately. This can&apos;t be undone.
                    </p>
                    <button
                      type="button"
                      className={styles.actionButton}
                      disabled={publishing}
                      onClick={handlePublishNow}
                    >
                      {publishing ? "Starting…" : "Publish now"}
                    </button>
                  </>
                )}

                {actionMode === "schedule" && (
                  <>
                    <label className={styles.label} htmlFor="schedule-datetime">
                      Publish date &amp; time
                    </label>
                    <input
                      id="schedule-datetime"
                      type="datetime-local"
                      className={styles.input}
                      min={minDatetimeLocal()}
                      value={scheduledAt}
                      onChange={(event) => setScheduledAt(event.target.value)}
                      required
                    />
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
              </div>
            )}

            {canPublish && post.status === "SCHEDULED" && (
              <div className={styles.sendCard}>
                <p className={styles.hint}>
                  This post is scheduled and will publish automatically.{" "}
                  {post.scheduled_at && `Scheduled for ${formatFull(post.scheduled_at)}.`}
                </p>
                <button
                  type="button"
                  className={styles.secondaryButton}
                  disabled={cancelling}
                  onClick={handleCancel}
                >
                  {cancelling ? "Cancelling…" : "Cancel"}
                </button>
              </div>
            )}

            {canPublish && post.status === "FAILED" && (
              <div className={styles.sendCard}>
                <button
                  type="button"
                  className={styles.actionButton}
                  disabled={retrying}
                  onClick={handleRetry}
                >
                  {retrying ? "Retrying…" : "Retry"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {showMediaModal && (
        <div className={styles.modalOverlay} onClick={() => setShowMediaModal(false)}>
          <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Select from Media Library</h3>
              <button
                type="button"
                className={styles.modalCloseBtn}
                onClick={() => setShowMediaModal(false)}
              >
                ✕
              </button>
            </div>
            <div className={styles.modalBody}>
              {loadingMedia ? (
                <p style={{ color: "#a3c2c2", textAlign: "center" }}>Loading media assets…</p>
              ) : mediaAssets.length === 0 ? (
                <p style={{ color: "#a3c2c2", textAlign: "center" }}>
                  No media assets found in library.
                </p>
              ) : (
                <div className={styles.mediaPickerGrid}>
                  {mediaAssets.map((asset) => (
                    <div
                      key={asset.id}
                      className={styles.mediaPickerItem}
                      onClick={() => void handleSelectFromMediaLibrary(asset)}
                      title={`Select ${asset.filename}`}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={asset.public_url}
                        alt={asset.filename}
                        className={styles.mediaPickerThumb}
                      />
                      <span className={styles.mediaPickerName}>{asset.filename}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
