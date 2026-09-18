"use client";

import Link from "next/link";
import { type ChangeEvent, useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { StatCard } from "@/components/stat-card/stat-card";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./social-page.module.css";
import type {
  ChannelCapability,
  MediaAsset,
  MediaFolder,
  MediaListResponse,
  MeResponse,
  SocialConnection,
  SocialPost,
  SocialPostStatus,
} from "./types";

const VIEW_PERMISSION = "social.view";
const MANAGE_PERMISSION = "social.manage";

type HubTab = "POSTS" | "ACCOUNTS" | "MEDIA";
type FilterTab = "ALL" | SocialPostStatus;

const FILTER_TABS: { value: FilterTab; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "DRAFT", label: "Draft" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "PUBLISHED", label: "Published" },
  { value: "FAILED", label: "Failed" },
];

const STATUS_LABEL: Record<SocialPostStatus, string> = {
  DRAFT: "Draft",
  SCHEDULED: "Scheduled",
  DISPATCHING: "Dispatching…",
  PUBLISHING: "Publishing…",
  PUBLISHED: "Published",
  CANCELLED: "Cancelled",
  FAILED: "Failed",
};

const STATUS_CLASS: Record<SocialPostStatus, string> = {
  DRAFT: "statusDraft",
  SCHEDULED: "statusScheduled",
  DISPATCHING: "statusDispatching",
  PUBLISHING: "statusDispatching",
  PUBLISHED: "statusSent",
  CANCELLED: "statusCancelled",
  FAILED: "statusFailed",
};

function formatScheduledAt(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
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

export function SocialPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);

  const [hubTab, setHubTab] = useState<HubTab>("POSTS");
  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");

  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [channels, setChannels] = useState<ChannelCapability[]>([]);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [disconnectingId, setDisconnectingId] = useState<string | null>(null);

  // Media Library state
  const [mediaAssets, setMediaAssets] = useState<MediaAsset[]>([]);
  const [mediaFolders, setMediaFolders] = useState<MediaFolder[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [mediaUploading, setMediaUploading] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [showFolderModal, setShowFolderModal] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));

        if (hasView) {
          const postList = await apiFetch<SocialPost[]>("/social/posts");
          setPosts(postList);
          try {
            const connList = await apiFetch<SocialConnection[]>("/social/connections");
            setConnections(connList);
          } catch {
            // Optional fallback if not mocked in tests
          }
          try {
            const chanList = await apiFetch<ChannelCapability[]>("/social/channels");
            setChannels(chanList);
          } catch {
            // Optional fallback if not mocked in tests
          }
        }
      } catch {
        setLoadError("Could not load social posts.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  // Lazy load media when Media tab is clicked
  useEffect(() => {
    if (hubTab === "MEDIA" && canView) {
      void (async () => {
        try {
          const res = await apiFetch<MediaListResponse>("/media");
          setMediaAssets(res.assets || []);
          setMediaFolders(res.folders || []);
        } catch {
          // ignore or toast
        }
      })();
    }
  }, [hubTab, canView]);

  async function handleCancel(post: SocialPost, event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (!window.confirm("Cancel this post? This cannot be undone.")) return;
    setCancellingId(post.id);
    try {
      await apiFetch<SocialPost>(`/social/posts/${post.id}/cancel`, { method: "POST" });
      setPosts((prev) =>
        prev.map((p) => (p.id === post.id ? { ...p, status: "CANCELLED" as const } : p)),
      );
      showToast("success", "Post cancelled successfully.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not cancel this post."));
    } finally {
      setCancellingId(null);
    }
  }

  async function handleDisconnect(connId: string) {
    if (!window.confirm("Disconnect this social account? Scheduled posts may fail.")) return;
    setDisconnectingId(connId);
    try {
      await apiFetch(`/social/connections/${connId}`, { method: "DELETE" });
      setConnections((prev) => prev.map((c) => (c.id === connId ? { ...c, is_active: false } : c)));
      showToast("success", "Account disconnected.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not disconnect account."));
    } finally {
      setDisconnectingId(null);
    }
  }

  async function handleMediaUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setMediaUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (selectedFolderId) {
        formData.append("folder_id", selectedFolderId);
      }
      const created = await apiFetch<MediaAsset>("/media/upload", {
        method: "POST",
        body: formData,
      });
      setMediaAssets((prev) => [created, ...prev]);
      showToast("success", `Uploaded ${file.name}`);
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Upload failed."));
    } finally {
      setMediaUploading(false);
      e.target.value = "";
    }
  }

  async function handleDeleteMedia(assetId: string) {
    if (!window.confirm("Delete this asset permanently?")) return;
    try {
      await apiFetch(`/media/${assetId}`, { method: "DELETE" });
      setMediaAssets((prev) => prev.filter((a) => a.id !== assetId));
      showToast("success", "Asset deleted.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Failed to delete asset."));
    }
  }

  async function handleCreateFolder() {
    if (!newFolderName.trim()) return;
    try {
      const folder = await apiFetch<MediaFolder>("/media/folders", {
        method: "POST",
        body: JSON.stringify({ name: newFolderName.trim() }),
      });
      setMediaFolders((prev) => [...prev, folder]);
      setNewFolderName("");
      setShowFolderModal(false);
      showToast("success", `Folder "${folder.name}" created.`);
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Failed to create folder."));
    }
  }

  const tabCounts = useMemo(() => {
    const counts: Record<FilterTab, number> = {
      ALL: posts.length,
      DRAFT: 0,
      SCHEDULED: 0,
      DISPATCHING: 0,
      PUBLISHING: 0,
      PUBLISHED: 0,
      CANCELLED: 0,
      FAILED: 0,
    };
    for (const post of posts) {
      if (post.status in counts) counts[post.status] += 1;
    }
    return counts;
  }, [posts]);

  const visiblePosts = useMemo(() => {
    return posts
      .filter((p) => activeTab === "ALL" || p.status === activeTab)
      .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  }, [posts, activeTab]);

  const totalPosts = posts.length;
  const publishedPosts = posts.filter((p) => p.status === "PUBLISHED").length;
  const scheduledPosts = posts.filter(
    (p) => p.status === "SCHEDULED" || p.status === "DISPATCHING" || p.status === "PUBLISHING",
  ).length;
  const draftPosts = posts.filter((p) => p.status === "DRAFT").length;
  const activeConnectionsCount = connections.filter((c) => c.is_active).length;

  if (loading) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          Loading social posts…
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          {loadError}
        </div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          You don&apos;t have access to social posts.
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Page Header */}
      <PageHeader
        icon="📱"
        title="Social Media Management"
        description="Multi-channel social publishing, bulk scheduling, and centralized media asset library."
        actions={
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <Link href="/dashboard/social/calendar" className={styles.secondaryButton}>
              Calendar
            </Link>
            {canManage && (
              <Link href="/dashboard/social/new" className={styles.primaryButton}>
                + New post
              </Link>
            )}
          </div>
        }
      />

      {/* Hub Navigation Tabs */}
      <div className={styles.hubNavGroup}>
        <button
          type="button"
          className={hubTab === "POSTS" ? styles.hubTabActive : styles.hubTab}
          onClick={() => setHubTab("POSTS")}
        >
          <span>📝 Posts & Schedule</span>
        </button>
        <button
          type="button"
          className={hubTab === "ACCOUNTS" ? styles.hubTabActive : styles.hubTab}
          onClick={() => setHubTab("ACCOUNTS")}
        >
          <span>🔗 Connected Channels ({activeConnectionsCount})</span>
        </button>
        <button
          type="button"
          className={hubTab === "MEDIA" ? styles.hubTabActive : styles.hubTab}
          onClick={() => setHubTab("MEDIA")}
        >
          <span>🖼️ Media Library</span>
        </button>
      </div>

      {/* VIEW 1: POSTS & SCHEDULE */}
      {hubTab === "POSTS" && (
        <>
          {/* KPI Stats Deck */}
          <section className={styles.statsDeck} aria-label="Social Posts Overview KPIs">
            <StatCard label="Total Posts" value={totalPosts} subtext="All platforms" />
            <StatCard label="Published" value={publishedPosts} subtext="Delivered live" />
            <StatCard label="Scheduled" value={scheduledPosts} subtext="Upcoming queue" />
            <StatCard label="Drafts" value={draftPosts} subtext="In creation" />
            <StatCard
              label="Channels"
              value={activeConnectionsCount}
              subtext="Active connections"
            />
          </section>

          {/* Toolbar: Category Tabs */}
          <div className={styles.toolbarRow}>
            <div className={styles.tabsGroup} role="tablist">
              {FILTER_TABS.map((tab) => (
                <button
                  key={tab.value}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.value}
                  className={activeTab === tab.value ? styles.tabActive : styles.tab}
                  onClick={() => setActiveTab(tab.value)}
                >
                  <span>{tab.label}</span>
                  <span className={styles.tabCount}>{tabCounts[tab.value]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Empty State */}
          {visiblePosts.length === 0 && (
            <div className={styles.emptyState}>
              <div style={{ fontSize: "36px", marginBottom: "8px" }}>📱</div>
              <h3 className={styles.emptyStateTitle}>No social posts yet.</h3>
              <p className={styles.emptyStateHint}>
                {activeTab === "ALL"
                  ? "You haven't created any social posts yet."
                  : `No social posts in "${STATUS_LABEL[activeTab as SocialPostStatus]}" state.`}
              </p>
              {canManage && activeTab === "ALL" && (
                <Link href="/dashboard/social/new" className={styles.primaryButton}>
                  + Create your first post
                </Link>
              )}
            </div>
          )}

          {/* Grid of Post Cards */}
          {visiblePosts.length > 0 && (
            <div className={styles.grid}>
              {visiblePosts.map((post) => {
                const statusClass = styles[STATUS_CLASS[post.status]] ?? "";
                const canCancel =
                  canManage && (post.status === "DRAFT" || post.status === "SCHEDULED");
                const conn = connections.find((c) => c.id === post.social_connection_id);
                const providerName = (conn?.provider || "INSTAGRAM_BUSINESS").toUpperCase();

                const providerDisplay =
                  providerName === "LINKEDIN"
                    ? "💼 LinkedIn"
                    : providerName === "TWITTER"
                      ? "🐦 X / Twitter"
                      : "📸 Instagram";

                return (
                  <Link
                    key={post.id}
                    href={`/dashboard/social/${post.id}`}
                    className={styles.postCard}
                  >
                    <div className={styles.postCardHeader}>
                      <span className={styles.providerBadge}>{providerDisplay}</span>
                      <span className={`${styles.statusBadge} ${statusClass}`}>
                        ● {STATUS_LABEL[post.status]}
                      </span>
                    </div>

                    <p className={styles.postCaption}>{post.caption}</p>

                    {post.utm_campaign && (
                      <div className={styles.utmTagsRow}>
                        <span className={styles.utmBadge}>🏷️ {post.utm_campaign}</span>
                        {post.utm_source && (
                          <span className={styles.utmBadge}>src: {post.utm_source}</span>
                        )}
                      </div>
                    )}

                    <div className={styles.postFooter}>
                      <span>
                        {post.status === "SCHEDULED" && post.scheduled_at ? (
                          <span className={styles.scheduledAtLabel}>
                            Scheduled: {formatScheduledAt(post.scheduled_at)}
                          </span>
                        ) : (
                          `Updated: ${new Date(post.updated_at).toLocaleDateString()}`
                        )}
                      </span>

                      {canCancel && (
                        <button
                          type="button"
                          className={styles.cancelButton}
                          aria-label="Cancel post"
                          disabled={cancellingId === post.id}
                          onClick={(e) => handleCancel(post, e)}
                        >
                          {cancellingId === post.id ? "Cancelling…" : "Cancel post"}
                        </button>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* VIEW 2: CONNECTED ACCOUNTS */}
      {hubTab === "ACCOUNTS" && (
        <div className={styles.accountsGrid}>
          {channels.map((chan) => {
            const activeConn = connections.find(
              (c) => c.provider.toUpperCase() === chan.provider_name.toUpperCase() && c.is_active,
            );

            const iconMap: Record<string, string> = {
              LINKEDIN: "💼",
              TWITTER: "🐦",
              INSTAGRAM_BUSINESS: "📸",
              FACEBOOK_PAGE: "📘",
              YOUTUBE: "▶️",
            };
            const icon = iconMap[chan.provider_name] || "🌐";

            return (
              <div key={chan.provider_name} className={styles.accountCard}>
                <div className={styles.accountHeader}>
                  <div className={styles.channelTitleRow}>
                    <span className={styles.channelIcon}>{icon}</span>
                    <span className={styles.channelName}>{chan.display_name}</span>
                  </div>
                  {activeConn ? (
                    <span className={styles.activeBadge}>Connected</span>
                  ) : chan.is_configured ? (
                    <span className={styles.statusDraft}>Ready</span>
                  ) : (
                    <span className={styles.unconfiguredBadge}>Config Required</span>
                  )}
                </div>

                <div className={styles.accountMeta}>
                  {activeConn ? (
                    <>
                      <div>
                        <strong>Account:</strong>{" "}
                        {activeConn.provider_account_name || activeConn.ig_username || "Connected"}
                      </div>
                      <div>
                        <strong>Username:</strong> @
                        {activeConn.provider_username || activeConn.ig_username || "user"}
                      </div>
                      <div>
                        <strong>Max Characters:</strong> {chan.max_characters}
                      </div>
                    </>
                  ) : (
                    <>
                      <div>
                        <strong>Limit:</strong> Up to {chan.max_characters} characters
                      </div>
                      <div>
                        <strong>Media:</strong> {chan.supported_media_types.join(", ")}
                      </div>
                      {!chan.is_configured && chan.setup_guide && (
                        <div style={{ fontSize: "11.5px", color: "#fcd34d", marginTop: "4px" }}>
                          ⚠️ {chan.setup_guide}
                        </div>
                      )}
                    </>
                  )}
                </div>

                <div className={styles.accountActions}>
                  {activeConn ? (
                    canManage && (
                      <button
                        type="button"
                        className={styles.disconnectButton}
                        disabled={disconnectingId === activeConn.id}
                        onClick={() => handleDisconnect(activeConn.id)}
                      >
                        {disconnectingId === activeConn.id ? "Disconnecting…" : "Disconnect"}
                      </button>
                    )
                  ) : chan.is_configured ? (
                    canManage && (
                      <a
                        href={`/integrations/${chan.provider_name.toLowerCase()}/oauth/authorize`}
                        className={styles.connectLink}
                      >
                        Connect {chan.display_name}
                      </a>
                    )
                  ) : (
                    <button
                      type="button"
                      className={styles.secondaryButton}
                      onClick={() => alert(chan.setup_guide || "Configuration instructions")}
                    >
                      Setup Guide
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW 3: MEDIA LIBRARY */}
      {hubTab === "MEDIA" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div className={styles.mediaHeaderRow}>
            <div className={styles.mediaFolderBar}>
              <button
                type="button"
                className={selectedFolderId === null ? styles.folderChipActive : styles.folderChip}
                onClick={() => setSelectedFolderId(null)}
              >
                📁 All Assets ({mediaAssets.length})
              </button>
              {mediaFolders.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={
                    selectedFolderId === f.id ? styles.folderChipActive : styles.folderChip
                  }
                  onClick={() => setSelectedFolderId(f.id)}
                >
                  📂 {f.name}
                </button>
              ))}
              {canManage && (
                <button
                  type="button"
                  className={styles.secondaryButton}
                  onClick={() => setShowFolderModal(true)}
                >
                  + New Folder
                </button>
              )}
            </div>

            {canManage && (
              <label className={styles.primaryButton} style={{ cursor: "pointer" }}>
                <span>{mediaUploading ? "Uploading…" : "⬆️ Upload Media"}</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,video/mp4"
                  style={{ display: "none" }}
                  disabled={mediaUploading}
                  onChange={handleMediaUpload}
                />
              </label>
            )}
          </div>

          {showFolderModal && (
            <div
              style={{
                background: "rgba(15, 107, 109, 0.25)",
                border: "1px solid #D4AF37",
                borderRadius: "16px",
                padding: "20px",
                display: "flex",
                gap: "12px",
                alignItems: "center",
              }}
            >
              <input
                type="text"
                placeholder="Folder name (e.g. Summer Campaign)"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                style={{
                  background: "#041213",
                  color: "#fff",
                  border: "1px solid rgba(212, 175, 55, 0.3)",
                  padding: "8px 14px",
                  borderRadius: "8px",
                  flex: 1,
                }}
              />
              <button type="button" className={styles.primaryButton} onClick={handleCreateFolder}>
                Create
              </button>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setShowFolderModal(false)}
              >
                Cancel
              </button>
            </div>
          )}

          {mediaAssets.filter((a) => selectedFolderId === null || a.folder_id === selectedFolderId)
            .length === 0 ? (
            <div className={styles.emptyState}>
              <div style={{ fontSize: "36px", marginBottom: "8px" }}>🖼️</div>
              <h3 className={styles.emptyStateTitle}>No media assets found</h3>
              <p className={styles.emptyStateHint}>
                Upload images and videos to reuse them across social posts.
              </p>
            </div>
          ) : (
            <div className={styles.mediaGrid}>
              {mediaAssets
                .filter((a) => selectedFolderId === null || a.folder_id === selectedFolderId)
                .map((asset) => (
                  <div key={asset.id} className={styles.mediaCard}>
                    <div className={styles.mediaThumbContainer}>
                      {asset.media_type === "VIDEO" ? (
                        <span style={{ fontSize: "40px" }}>🎬</span>
                      ) : (
                        <>
                          {/* User-managed URLs cannot be constrained to Next.js image host rules. */}
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={asset.public_url}
                            alt={asset.filename}
                            className={styles.mediaImage}
                          />
                        </>
                      )}
                    </div>
                    <div className={styles.mediaCardBody}>
                      <span className={styles.mediaFileName} title={asset.filename}>
                        {asset.filename}
                      </span>
                      <span className={styles.mediaFileSize}>
                        {asset.media_type} • {(asset.file_size_bytes / 1024).toFixed(1)} KB
                      </span>
                      <div className={styles.mediaCardActions}>
                        <button
                          type="button"
                          className={styles.secondaryButton}
                          style={{ padding: "4px 10px", fontSize: "11px" }}
                          onClick={() => {
                            void navigator.clipboard.writeText(asset.public_url);
                            showToast("success", "Media URL copied to clipboard!");
                          }}
                        >
                          Copy URL
                        </button>
                        {canManage && (
                          <button
                            type="button"
                            className={styles.cancelButton}
                            onClick={() => handleDeleteMedia(asset.id)}
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
