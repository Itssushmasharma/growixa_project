"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";

import { AIGenerateButton } from "@/components/ai/ai-generate-button";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./post-form-page.module.css";
import type { MeResponse, SocialConnection, SocialPost } from "./types";

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
  const [canGenerateAI, setCanGenerateAI] = useState(false);

  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [post, setPost] = useState<SocialPost | null>(null);
  const [selectedConnectionIds, setSelectedConnectionIds] = useState<Set<string>>(new Set());
  const [caption, setCaption] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // UTM Parameters
  const [utmCampaign, setUtmCampaign] = useState("");
  const [utmSource, setUtmSource] = useState("");
  const [utmMedium, setUtmMedium] = useState("");
  const [utmContent, setUtmContent] = useState("");

  // Previews
  type PreviewPlatform = "LINKEDIN" | "TWITTER" | "INSTAGRAM_BUSINESS";
  const [previewTab, setPreviewTab] = useState<PreviewPlatform>("LINKEDIN");

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
          if (connectionList.length > 0) {
            const first = connectionList[0];
            if (first) {
              setSelectedConnectionIds(new Set([first.id]));
              setPreviewTab(first.provider as PreviewPlatform);
            }
          }
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

  const editable = canManage && (mode === "create" || post?.status === "DRAFT");

  const toggleConnection = (id: string, provider: string) => {
    if (!editable) return;
    const next = new Set(selectedConnectionIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
      setPreviewTab(provider as PreviewPlatform); // Focus preview on newly selected
    }
    setSelectedConnectionIds(next);
  };

  const currentProvider = previewTab;
  const maxChars = currentProvider === "TWITTER" ? 280 : currentProvider === "LINKEDIN" ? 3000 : 2200;
  const charsRemaining = maxChars - caption.length;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    try {
      if (mode === "create") {
        if (selectedConnectionIds.size === 0) {
          showToast("error", "Please select at least one social account.");
          setSubmitting(false);
          return;
        }
        
        // Create a draft for each selected connection
        for (const connId of Array.from(selectedConnectionIds)) {
          const payload: Record<string, unknown> = {
            social_connection_id: connId,
            caption,
          };
          if (utmCampaign) payload.utm_campaign = utmCampaign;
          if (utmSource) payload.utm_source = utmSource;
          if (utmMedium) payload.utm_medium = utmMedium;
          if (utmContent) payload.utm_content = utmContent;

          await apiFetch<SocialPost>("/social/posts", {
            method: "POST",
            body: JSON.stringify(payload),
          });
        }
        
        showToast("success", `${selectedConnectionIds.size} Drafts created!`);
        router.push(`/dashboard/social`);
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
          ? "Could not create drafts. Please try again."
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

  if (loading) return <div className={styles.page}>Loading…</div>;
  if (loadError) return <div className={styles.page}>{loadError}</div>;

  const hasMedia = mode === "edit" && (post?.media.length ?? 0) > 0;

  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/dashboard/social">Social</Link>
        <span aria-hidden="true"> / </span>
        <span>{mode === "create" ? "New post" : "Post"}</span>
      </nav>

      <div className={styles.split}>
        {/* Left Side: Composer */}
        <form className={styles.formCard} onSubmit={handleSubmit}>
          {mode === "create" && (
            <div className={styles.networkSelector}>
              <span className={styles.networkLabel}>Post to:</span>
              <div className={styles.networkIcons}>
                {connections.map((conn) => {
                  const isActive = selectedConnectionIds.has(conn.id);
                  const iconMap: Record<string, string> = {
                    TWITTER: "𝕏",
                    LINKEDIN: "in",
                    INSTAGRAM_BUSINESS: "📸",
                  };
                  return (
                    <button
                      key={conn.id}
                      type="button"
                      className={`${styles.networkIcon} ${isActive ? styles.networkIconActive : ""}`}
                      onClick={() => toggleConnection(conn.id, conn.provider)}
                      title={conn.provider_account_name || conn.ig_username || conn.provider}
                    >
                      {iconMap[conn.provider] || "🌐"}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className={styles.composerArea}>
            <textarea
              className={styles.textarea}
              placeholder="What do you want to share?"
              disabled={!editable}
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
            />
            {editable && canGenerateAI && (
              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <AIGenerateButton
                  capability="SOCIAL_CAPTION"
                  triggerLabel="✨ Rewrite with AI"
                  briefPlaceholder="e.g. a product launch announcement"
                  onInsert={(text) => setCaption(text)}
                  linkedEntityType="social_post"
                  linkedEntityId={postId}
                />
              </div>
            )}
            
            {/* Display Media if attached (only single-draft mode currently supported for media upload) */}
            {mode === "edit" && post && post.media.length > 0 && (
              <div className={styles.attachedMediaGrid}>
                {post.media.map((media) => (
                  <div key={media.id} className={styles.attachedMediaItem}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={media.public_url} alt="Attached media" />
                    {editable && (
                      <button type="button" className={styles.removeMediaBtn} onClick={() => handleRemoveMedia(media.id)}>✕</button>
                    )}
                  </div>
                ))}
              </div>
            )}

            {mode === "edit" && !hasMedia && editable && (
              <label className={styles.mediaZone}>
                <div className={styles.mediaIcon}>📁</div>
                <p>Click to browse or drag and drop an image</p>
                <input
                  type="file"
                  accept="image/jpeg"
                  style={{ display: "none" }}
                  onChange={handleFileChange}
                />
              </label>
            )}
            {mode === "create" && (
              <div className={styles.mediaZone}>
                <div className={styles.mediaIcon}>🔒</div>
                <p>Save draft first to attach media across selected channels.</p>
              </div>
            )}
          </div>

          <div className={styles.formActions}>
            <div className={styles.actionLeft}>
              <span style={{ fontSize: "12px", color: charsRemaining < 0 ? "red" : "#94a3b8" }}>
                {caption.length} / {maxChars}
              </span>
            </div>
            <div className={styles.actionRight}>
              <button type="button" className={styles.btnSecondary} onClick={() => router.back()}>Cancel</button>
              <button type="submit" className={styles.btnPrimary} disabled={submitting}>
                {submitting ? "Saving..." : (mode === "create" ? "Save Drafts" : "Save Changes")}
              </button>
            </div>
          </div>
        </form>

        {/* Right Side: Preview Pane */}
        <div className={styles.sideColumn}>
          <div className={styles.previewTabs}>
            <button
              className={`${styles.previewTab} ${previewTab === "LINKEDIN" ? styles.previewTabActive : ""}`}
              onClick={() => setPreviewTab("LINKEDIN")}
            >LinkedIn</button>
            <button
              className={`${styles.previewTab} ${previewTab === "TWITTER" ? styles.previewTabActive : ""}`}
              onClick={() => setPreviewTab("TWITTER")}
            >Twitter / X</button>
            <button
              className={`${styles.previewTab} ${previewTab === "INSTAGRAM_BUSINESS" ? styles.previewTabActive : ""}`}
              onClick={() => setPreviewTab("INSTAGRAM_BUSINESS")}
            >Instagram</button>
          </div>

          <div className={styles.phoneFrame}>
            <div className={styles.previewContent}>
              
              {previewTab === "LINKEDIN" && (
                <div className={styles.socialPostCard}>
                  <div className={styles.postHeader}>
                    <div className={styles.avatar}>G</div>
                    <div className={styles.authorInfo}>
                      <span className={styles.authorName}>Growixa Inc.</span>
                      <span className={styles.authorMeta}>Just now • 🌐</span>
                    </div>
                  </div>
                  <div className={styles.postBody}>{caption || "Your post text will appear here..."}</div>
                  {post?.media[0] && (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={post.media[0].public_url} alt="Preview" className={styles.postImage} />
                  )}
                  <div className={styles.postActions}>
                    <span>👍 Like</span>
                    <span>💬 Comment</span>
                    <span>🔁 Repost</span>
                    <span>🚀 Send</span>
                  </div>
                </div>
              )}

              {previewTab === "TWITTER" && (
                <div className={styles.socialPostCard}>
                  <div className={styles.postHeader}>
                    <div className={styles.avatar}>𝕏</div>
                    <div className={styles.authorInfo}>
                      <span className={styles.authorName}>Growixa</span>
                      <span className={styles.authorMeta}>@growixa • Just now</span>
                    </div>
                  </div>
                  <div className={styles.postBody}>{caption || "What is happening?!"}</div>
                  {post?.media[0] && (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={post.media[0].public_url} alt="Preview" className={styles.postImage} />
                  )}
                  <div className={styles.postActions}>
                    <span>💬 12</span>
                    <span>🔁 48</span>
                    <span>❤️ 192</span>
                    <span>📊 2.4K</span>
                  </div>
                </div>
              )}

              {previewTab === "INSTAGRAM_BUSINESS" && (
                <div className={styles.socialPostCard}>
                  <div className={styles.postHeader}>
                    <div className={styles.avatar}>📸</div>
                    <div className={styles.authorInfo}>
                      <span className={styles.authorName}>growixa_official</span>
                      <span className={styles.authorMeta}>Just now</span>
                    </div>
                  </div>
                  {post?.media[0] ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img src={post.media[0].public_url} alt="Preview" className={styles.postImage} />
                  ) : (
                    <div style={{ height: '200px', background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem', color: '#94a3b8' }}>
                      No Image Attached
                    </div>
                  )}
                  <div className={styles.postActions} style={{ justifyContent: 'flex-start', gap: '1rem', paddingBottom: '0.5rem', borderBottom: 'none' }}>
                    <span>❤️</span>
                    <span>💬</span>
                    <span>🚀</span>
                  </div>
                  <div className={styles.postBody} style={{ fontSize: '0.85rem' }}>
                    <strong>growixa_official</strong> {caption || "Caption preview..."}
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
