import React, { type ReactNode } from "react";
import type { DocCalloutType } from "@/lib/docs/types";
import styles from "./docs-components.module.css";

interface DocsCalloutProps {
  type?: DocCalloutType;
  title?: string;
  children: ReactNode;
}

const CALLOUT_ICONS: Record<DocCalloutType, string> = {
  note: "ℹ️",
  tip: "💡",
  warning: "⚠️",
  important: "🚨",
};

const CALLOUT_TITLES: Record<DocCalloutType, string> = {
  note: "Note",
  tip: "Pro Tip",
  warning: "Warning",
  important: "Important",
};

export function DocsCallout({ type = "note", title, children }: DocsCalloutProps) {
  const displayTitle = title || CALLOUT_TITLES[type];
  const icon = CALLOUT_ICONS[type];

  return (
    <div className={`${styles.callout} ${styles[`callout_${type}`]}`} role="alert">
      <div className={styles.calloutHeader}>
        <span className={styles.calloutIcon}>{icon}</span>
        <span className={styles.calloutTitle}>{displayTitle}</span>
      </div>
      <div className={styles.calloutContent}>{children}</div>
    </div>
  );
}
