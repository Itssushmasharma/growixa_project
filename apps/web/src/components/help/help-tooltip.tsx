"use client";

import React, { useState } from "react";
import Link from "next/link";
import styles from "./help-components.module.css";

interface HelpTooltipProps {
  text: string;
  docPath?: string;
  docTitle?: string;
  className?: string;
}

export function HelpTooltip({
  text,
  docPath,
  docTitle = "Read guide",
  className = "",
}: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span
      className={`${styles.tooltipContainer} ${className}`}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
      tabIndex={0}
      role="tooltip"
      aria-label={text}
    >
      <span className={styles.tooltipIcon}>?</span>
      {isVisible && (
        <div className={styles.tooltipBubble}>
          <div className={styles.tooltipText}>{text}</div>
          {docPath && (
            <Link
              href={docPath}
              className={styles.tooltipLink}
              target="_blank"
              rel="noopener noreferrer"
            >
              📖 {docTitle} →
            </Link>
          )}
        </div>
      )}
    </span>
  );
}
