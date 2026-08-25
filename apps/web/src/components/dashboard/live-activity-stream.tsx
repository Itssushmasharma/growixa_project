import Link from "next/link";
import React from "react";

import type { ActivityStreamItem } from "@/app/(dashboard)/dashboard/types";

import styles from "./live-activity-stream.module.css";

interface LiveActivityStreamProps {
  items: ActivityStreamItem[];
}

function formatTimeAgo(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function LiveActivityStream({ items }: LiveActivityStreamProps) {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.title}>Live recipient activity</h3>
        <div className={styles.liveBadge}>
          <span className={styles.livePulse} />
          LIVE
        </div>
      </div>

      {items.length === 0 ? (
        <div className={styles.emptyState}>
          No recent recipient interactions yet. Opens &amp; clicks will appear here in real time.
        </div>
      ) : (
        <ul className={styles.list}>
          {items.map((item) => {
            const isClick = item.event_type === "CLICKED";
            return (
              <li key={item.id} className={styles.item}>
                <div
                  className={`${styles.iconWrapper} ${
                    isClick ? styles.iconClicked : styles.iconOpened
                  }`}
                >
                  {isClick ? "🔗" : "👁️"}
                </div>
                <div className={styles.details}>
                  <div className={styles.emailRow}>
                    <span className={styles.contactEmail} title={item.contact_email}>
                      {item.contact_email}
                    </span>
                    <span className={styles.timeAgo}>{formatTimeAgo(item.occurred_at)}</span>
                  </div>
                  <div className={styles.eventAction}>
                    {isClick ? "Clicked link in " : "Opened "}
                    <Link
                      href={`/dashboard/campaigns/${item.campaign_id}`}
                      className={styles.campaignName}
                    >
                      {item.campaign_name}
                    </Link>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
