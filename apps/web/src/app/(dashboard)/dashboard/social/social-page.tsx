"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { StatCard } from "@/components/stat-card/stat-card";
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

  const totalPosts = posts.length;
  const publishedPosts = posts.filter((p) => p.status === "PUBLISHED").length;
  const scheduledPosts = posts.filter(
    (p) => p.status === "SCHEDULED" || p.status === "DISPATCHING" || p.status === "PUBLISHING",
  ).length;
  const draftPosts = posts.filter((p) => p.status === "DRAFT").length;

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
        title="Social Media"
        description="Create, schedule, and publish posts across your connected social platforms."
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

      {/* KPI Stats Deck (Real Derived Counts) */}
      <section className={styles.statsDeck} aria-label="Social Posts Overview KPIs">
        <StatCard label="Total Posts" value={totalPosts} subtext="All platforms" />
        <StatCard label="Published" value={publishedPosts} subtext="Delivered live" />
        <StatCard label="Scheduled" value={scheduledPosts} subtext="Upcoming queue" />
        <StatCard label="Drafts" value={draftPosts} subtext="In creation" />
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
            const canCancel = canManage && (post.status === "DRAFT" || post.status === "SCHEDULED");

            return (
              <Link key={post.id} href={`/dashboard/social/${post.id}`} className={styles.postCard}>
                <div className={styles.postCardHeader}>
                  <span className={styles.providerBadge}>📸 Instagram</span>
                  <span className={`${styles.statusBadge} ${statusClass}`}>
                    ● {STATUS_LABEL[post.status]}
                  </span>
                </div>

                <p className={styles.postCaption}>{post.caption}</p>

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
    </div>
  );
}
