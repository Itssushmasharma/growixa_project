"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

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

    const byDate = new Map<string, { post: SocialPost; at: string }[]>();
    for (const item of all) {
      const key = dateKey(item.at);
      const existing = byDate.get(key) ?? [];
      existing.push(item);
      byDate.set(key, existing);
    }
    return byDate;
  }, [posts]);

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
        <div className={styles.card}>You don&apos;t have access to the content calendar.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/dashboard/social">Social</Link>
        <span aria-hidden="true"> / </span>
        <span>Calendar</span>
      </nav>

      {groups.size === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>No scheduled or published posts yet.</p>
        </div>
      )}

      <div className={styles.groups}>
        {Array.from(groups.entries()).map(([date, items]) => (
          <div className={styles.dateGroup} key={date}>
            <h3 className={styles.dateHeading}>{date}</h3>
            <div className={styles.items}>
              {items.map(({ post, at }) => (
                <Link href={`/dashboard/social/${post.id}`} className={styles.item} key={post.id}>
                  {post.media[0] && (
                    <img src={post.media[0].public_url} alt="" className={styles.thumbnail} />
                  )}
                  <div className={styles.itemBody}>
                    <span
                      className={`${styles.statusBadge} ${
                        post.status === "PUBLISHED"
                          ? styles.statusPublished
                          : styles.statusScheduled
                      }`}
                    >
                      {post.status === "PUBLISHED" ? "Published" : "Scheduled"} · {timeLabel(at)}
                    </span>
                    <p className={styles.itemCaption}>{post.caption || "(no caption)"}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
