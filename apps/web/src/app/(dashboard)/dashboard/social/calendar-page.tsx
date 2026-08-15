"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { apiFetch } from "@/lib/api-client";

import styles from "./calendar-page.module.css";
import type { MeResponse, SocialPost } from "./types";

const VIEW_PERMISSION = "social.view";

function dateKey(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

export function CalendarPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [posts, setPosts] = useState<SocialPost[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        if (hasView) {
          const postList = await apiFetch<SocialPost[]>("/social/posts");
          setPosts(postList);
        }
      } catch {
        setLoadError("Could not load the content calendar.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const groups = useMemo(() => {
    const upcoming = posts
      .filter((p) => p.status === "SCHEDULED" && p.scheduled_at)
      .map((p) => ({ post: p, at: p.scheduled_at as string }));
    const published = posts
      .filter((p) => p.status === "PUBLISHED" && p.published_at)
      .map((p) => ({ post: p, at: p.published_at as string }));
    const all = [...upcoming, ...published].sort((a, b) => a.at.localeCompare(b.at));

    const map = new Map<string, typeof all>();
    for (const item of all) {
      const key = dateKey(item.at);
      const existing = map.get(key) ?? [];
      existing.push(item);
      map.set(key, existing);
    }
    return Array.from(map.entries());
  }, [posts]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          Loading calendar…
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
          <h2>Access Denied</h2>
          <p>You don&apos;t have access to the content calendar.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Page Header */}
      <PageHeader
        icon="📅"
        title="Social Content Calendar"
        description="Visual timeline of your scheduled and published social media posts."
        actions={
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <Link href="/dashboard/social" className={styles.secondaryButton}>
              Social
            </Link>
            <Link href="/dashboard/social/new" className={styles.primaryButton}>
              + Create Post
            </Link>
          </div>
        }
      />

      {groups.length === 0 ? (
        <div className={styles.emptyState}>
          <div style={{ fontSize: "36px", marginBottom: "8px" }}>📅</div>
          <h3 className={styles.emptyStateTitle}>No scheduled or published posts yet.</h3>
          <p className={styles.emptyStateHint}>
            Schedule social posts to see them organized chronologically in your calendar.
          </p>
          <Link href="/dashboard/social/new" className={styles.primaryButton}>
            + Schedule your first post
          </Link>
        </div>
      ) : (
        <div className={styles.groups}>
          {groups.map(([date, items]) => (
            <div key={date} className={styles.dateGroup}>
              <h3 className={styles.dateHeading}>📅 {date}</h3>
              <div className={styles.postsList}>
                {items.map(({ post, at }) => (
                  <Link
                    key={post.id}
                    href={`/dashboard/social/${post.id}`}
                    className={styles.calendarEntry}
                  >
                    <span className={styles.entryTime}>{timeLabel(at)}</span>
                    <span className={styles.entryCaption}>{post.caption}</span>
                    <span
                      className={`${styles.statusBadge} ${
                        post.status === "SCHEDULED" ? styles.statusScheduled : styles.statusSent
                      }`}
                    >
                      {post.status === "SCHEDULED" ? "Scheduled" : "Published"}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
