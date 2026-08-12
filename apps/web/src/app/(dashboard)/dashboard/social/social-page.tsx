"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./social-page.module.css";
import type { MeResponse, SocialPost, SocialPostStatus } from "./types";

const VIEW_PERMISSION = "social.view";
const MANAGE_PERMISSION = "social.manage";

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
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");

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
        }
      } catch {
        setLoadError("Could not load social posts.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

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
        <div className={styles.card}>You don&apos;t have access to social posts.</div>
      </div>
    );
  }

  const cancellableStatuses: SocialPostStatus[] = ["DRAFT", "SCHEDULED"];

  return (
    <div className={styles.page}>
      <div className={styles.topRow}>
        <div className={styles.tabs} role="tablist" aria-label="Filter posts by status">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.value}
              className={activeTab === tab.value ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab(tab.value)}
            >
              {tab.label}
              {tab.value !== "ALL" && tabCounts[tab.value] > 0 && (
                <span className={styles.tabCount}>{tabCounts[tab.value]}</span>
              )}
            </button>
          ))}
        </div>
        <div className={styles.topActions}>
          <Link href="/dashboard/social/calendar" className={styles.secondaryLink}>
            Calendar
          </Link>
          {canManage && (
            <Link href="/dashboard/social/new" className={styles.actionButton}>
              + New post
            </Link>
          )}
        </div>
      </div>

      {posts.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>No social posts yet.</p>
        </div>
      )}
      {posts.length > 0 && visiblePosts.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>No posts match this filter.</p>
        </div>
      )}

      <div className={styles.grid}>
        {visiblePosts.map((post) => (
          <Link href={`/dashboard/social/${post.id}`} className={styles.postCard} key={post.id}>
            {post.media[0] && (
              <img
                src={post.media[0].public_url}
                alt=""
                className={styles.thumbnail}
                loading="lazy"
              />
            )}
            <span className={`${styles.statusBadge} ${styles[STATUS_CLASS[post.status]]}`}>
              {STATUS_LABEL[post.status]}
            </span>
            <div className={styles.postCaption}>{post.caption || "(no caption)"}</div>
            {post.status === "SCHEDULED" && post.scheduled_at && (
              <div className={styles.scheduledAtLabel}>
                Scheduled for {formatScheduledAt(post.scheduled_at)}
              </div>
            )}
            <div className={styles.cardFooter}>
              <span className={styles.hint}>{formatScheduledAt(post.updated_at)}</span>
              <div className={styles.cardActions}>
                {canManage && cancellableStatuses.includes(post.status) && (
                  <button
                    type="button"
                    className={styles.cancelButton}
                    disabled={cancellingId === post.id}
                    onClick={(e) => handleCancel(post, e)}
                    aria-label="Cancel post"
                  >
                    {cancellingId === post.id ? "Cancelling…" : "Cancel"}
                  </button>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
