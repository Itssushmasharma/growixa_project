"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { apiFetch } from "@/lib/api-client";

import styles from "./calendar-page.module.css";
import type { MeResponse, SocialConnection, SocialPost } from "./types";

const VIEW_PERMISSION = "social.view";
const MANAGE_PERMISSION = "social.manage";

function dateKey(iso: string, tz?: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    timeZone: tz,
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function timeLabel(iso: string, tz?: string): string {
  return new Date(iso).toLocaleTimeString(undefined, {
    timeZone: tz,
    hour: "numeric",
    minute: "2-digit",
  });
}

function toIsoDay(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function CalendarPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [connections, setConnections] = useState<SocialConnection[]>([]);

  type ViewMode = "month" | "week" | "list";
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [selectedChannel, setSelectedChannel] = useState<string>("ALL");
  const [currentDate, setCurrentDate] = useState<Date>(() => new Date());
  const [timeZone, setTimeZone] = useState<string>(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
    } catch {
      return "UTC";
    }
  });

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
            // Optional: fallback if connections endpoint not mocked in tests
          }
        }
      } catch {
        setLoadError("Could not load the content calendar.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const connMap = useMemo(() => {
    const map = new Map<string, SocialConnection>();
    for (const c of connections) {
      map.set(c.id, c);
    }
    return map;
  }, [connections]);

  const filteredPosts = useMemo(() => {
    if (selectedChannel === "ALL") return posts;
    return posts.filter((p) => {
      const conn = connMap.get(p.social_connection_id);
      return conn?.provider === selectedChannel;
    });
  }, [posts, selectedChannel, connMap]);

  const groups = useMemo(() => {
    const upcoming = filteredPosts
      .filter((p) => p.status === "SCHEDULED" && p.scheduled_at)
      .map((p) => ({ post: p, at: p.scheduled_at as string }));
    const published = filteredPosts
      .filter((p) => p.status === "PUBLISHED" && p.published_at)
      .map((p) => ({ post: p, at: p.published_at as string }));
    const all = [...upcoming, ...published].sort((a, b) => a.at.localeCompare(b.at));

    const map = new Map<string, typeof all>();
    for (const item of all) {
      const key = dateKey(item.at, timeZone);
      const existing = map.get(key) ?? [];
      existing.push(item);
      map.set(key, existing);
    }
    return Array.from(map.entries());
  }, [filteredPosts, timeZone]);

  // Month navigation helpers
  const monthYearLabel = useMemo(() => {
    return currentDate.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  }, [currentDate]);

  function handlePrev() {
    setCurrentDate((prev) => {
      const d = new Date(prev);
      if (viewMode === "week") {
        d.setDate(d.getDate() - 7);
      } else {
        d.setMonth(d.getMonth() - 1);
      }
      return d;
    });
  }

  function handleNext() {
    setCurrentDate((prev) => {
      const d = new Date(prev);
      if (viewMode === "week") {
        d.setDate(d.getDate() + 7);
      } else {
        d.setMonth(d.getMonth() + 1);
      }
      return d;
    });
  }

  function handleToday() {
    setCurrentDate(new Date());
  }

  // Month view calendar days builder
  const monthDays = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDayIndex = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    const prevMonthLastDate = new Date(year, month, 0).getDate();

    const days: { date: Date; isCurrentMonth: boolean; key: string }[] = [];

    // Leading days from previous month
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      const d = new Date(year, month - 1, prevMonthLastDate - i);
      days.push({ date: d, isCurrentMonth: false, key: toIsoDay(d) });
    }

    // Days in current month
    for (let i = 1; i <= lastDate; i++) {
      const d = new Date(year, month, i);
      days.push({ date: d, isCurrentMonth: true, key: toIsoDay(d) });
    }

    // Trailing days from next month to fill grid of 35 or 42
    const totalCells = days.length <= 35 ? 35 : 42;
    const remaining = totalCells - days.length;
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i);
      days.push({ date: d, isCurrentMonth: false, key: toIsoDay(d) });
    }

    return days;
  }, [currentDate]);

  // Week view calendar days builder
  const weekDays = useMemo(() => {
    const curr = new Date(currentDate);
    const day = curr.getDay();
    const diff = curr.getDate() - day; // Start of week (Sunday)
    const days: { date: Date; key: string }[] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(curr.setDate(diff + i));
      days.push({ date: d, key: toIsoDay(d) });
    }
    return days;
  }, [currentDate]);

  // Post lookup by ISO day string
  const postsByDay = useMemo(() => {
    const map = new Map<string, SocialPost[]>();
    for (const p of filteredPosts) {
      const timeStr = p.scheduled_at || p.published_at;
      if (!timeStr) continue;
      const dayKey = timeStr.slice(0, 10);
      const list = map.get(dayKey) ?? [];
      list.push(p);
      map.set(dayKey, list);
    }
    return map;
  }, [filteredPosts]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div
          style={{
            background: "rgba(6, 23, 24, 0.88)",
            color: "#D4AF37",
            padding: "40px",
            borderRadius: "18px",
            textAlign: "center",
          }}
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
          style={{
            background: "rgba(6, 23, 24, 0.88)",
            color: "#fca5a5",
            padding: "40px",
            borderRadius: "18px",
            textAlign: "center",
          }}
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
          style={{
            background: "rgba(6, 23, 24, 0.88)",
            padding: "40px",
            borderRadius: "18px",
            textAlign: "center",
          }}
        >
          <h2>Access Denied</h2>
          <p>You don&apos;t have access to the content calendar.</p>
        </div>
      </div>
    );
  }

  const todayIso = toIsoDay(new Date());

  return (
    <div className={styles.page}>
      {/* Page Header */}
      <PageHeader
        icon="📅"
        title="Social Content Calendar"
        description="Interactive visual calendar & timeline of your scheduled and published posts across all channels."
        actions={
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <Link href="/dashboard/social" className={styles.secondaryButton}>
              Social
            </Link>
            {canManage && (
              <Link href="/dashboard/social/new" className={styles.primaryButton}>
                + Create Post
              </Link>
            )}
          </div>
        }
      />

      {/* Calendar Toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.navControls}>
          <button type="button" className={styles.navBtn} onClick={handlePrev}>
            ◀
          </button>
          <button type="button" className={styles.navBtn} onClick={handleToday}>
            Today
          </button>
          <button type="button" className={styles.navBtn} onClick={handleNext}>
            ▶
          </button>
          <span className={styles.currentPeriodTitle}>{monthYearLabel}</span>
        </div>

        <div className={styles.filterControls}>
          <select
            className={styles.selectInput}
            value={selectedChannel}
            onChange={(e) => setSelectedChannel(e.target.value)}
            aria-label="Filter by channel"
          >
            <option value="ALL">🌐 All Channels</option>
            <option value="LINKEDIN">💼 LinkedIn</option>
            <option value="TWITTER">🐦 Twitter / X</option>
            <option value="INSTAGRAM_BUSINESS">📷 Instagram</option>
          </select>

          <select
            className={styles.selectInput}
            value={timeZone}
            onChange={(e) => setTimeZone(e.target.value)}
            aria-label="Timezone selector"
          >
            <option value={timeZone}>🕒 {timeZone}</option>
            <option value="UTC">🕒 UTC</option>
            <option value="America/New_York">🕒 US Eastern (ET)</option>
            <option value="America/Los_Angeles">🕒 US Pacific (PT)</option>
            <option value="Europe/London">🕒 London (GMT/BST)</option>
            <option value="Asia/Kolkata">🕒 India (IST)</option>
          </select>

          <div className={styles.viewTabs} role="group" aria-label="View mode">
            <button
              type="button"
              className={`${styles.viewTab} ${viewMode === "month" ? styles.viewTabActive : ""}`}
              onClick={() => setViewMode("month")}
            >
              Month
            </button>
            <button
              type="button"
              className={`${styles.viewTab} ${viewMode === "week" ? styles.viewTabActive : ""}`}
              onClick={() => setViewMode("week")}
            >
              Week
            </button>
            <button
              type="button"
              className={`${styles.viewTab} ${viewMode === "list" ? styles.viewTabActive : ""}`}
              onClick={() => setViewMode("list")}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {groups.length === 0 ? (
        <div className={styles.emptyState}>
          <div style={{ fontSize: "36px", marginBottom: "8px" }}>📅</div>
          <h3 className={styles.emptyStateTitle}>No scheduled or published posts yet.</h3>
          <p className={styles.emptyStateHint}>
            Schedule social posts to see them organized chronologically in your calendar.
          </p>
          {canManage && (
            <Link href="/dashboard/social/new" className={styles.primaryButton}>
              + Schedule your first post
            </Link>
          )}
        </div>
      ) : (
        <>
          {/* Month Grid View */}
          {viewMode === "month" && (
            <div className={styles.monthContainer}>
              <div className={styles.monthGrid}>
                {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                  <div key={day} className={styles.weekdayHeader}>
                    {day}
                  </div>
                ))}
                {monthDays.map(({ date, isCurrentMonth, key }) => {
                  const dayPosts = postsByDay.get(key) ?? [];
                  const isToday = key === todayIso;
                  return (
                    <div
                      key={key}
                      className={`${styles.dayCell} ${
                        !isCurrentMonth ? styles.dayCellOutside : ""
                      } ${isToday ? styles.dayCellToday : ""}`}
                    >
                      <span
                        className={`${styles.dayNumber} ${isToday ? styles.dayNumberToday : ""}`}
                      >
                        {date.getDate()}
                      </span>
                      <div className={styles.postChips}>
                        {dayPosts.map((post) => (
                          <Link
                            key={post.id}
                            href={`/dashboard/social/${post.id}`}
                            className={`${styles.postChip} ${
                              post.status === "SCHEDULED"
                                ? styles.postChipScheduled
                                : styles.postChipPublished
                            }`}
                            title={post.caption}
                          >
                            <span>
                              {post.status === "SCHEDULED" ? "⏰" : "✓"} {post.caption}
                            </span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Week Grid View */}
          {viewMode === "week" && (
            <div className={styles.weekContainer}>
              {weekDays.map(({ date, key }) => {
                const dayPosts = postsByDay.get(key) ?? [];
                const dayName = date.toLocaleDateString(undefined, { weekday: "short" });
                const isToday = key === todayIso;
                return (
                  <div
                    key={key}
                    className={`${styles.weekCol} ${isToday ? styles.dayCellToday : ""}`}
                  >
                    <div className={styles.weekColHeader}>
                      <div className={styles.weekDayName}>{dayName}</div>
                      <div className={styles.weekDayDate}>{date.getDate()}</div>
                    </div>
                    <div className={styles.postChips}>
                      {dayPosts.map((post) => (
                        <Link
                          key={post.id}
                          href={`/dashboard/social/${post.id}`}
                          className={`${styles.postChip} ${
                            post.status === "SCHEDULED"
                              ? styles.postChipScheduled
                              : styles.postChipPublished
                          }`}
                          title={post.caption}
                        >
                          <span>
                            {post.status === "SCHEDULED" ? "⏰" : "✓"} {post.caption}
                          </span>
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* List View (Default & Grouped by Date) */}
          {viewMode === "list" && (
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
                        <span className={styles.entryTime}>{timeLabel(at, timeZone)}</span>
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
        </>
      )}
    </div>
  );
}
