"use client";

import { useEffect, useState } from "react";

import styles from "./template-preview-modal.module.css";

export interface TemplatePreviewModalProps {
  templateName: string;
  subject: string;
  bodyHtml: string;
  onClose: () => void;
}

/**
 * Shared full-screen preview modal for email templates.
 * Renders the template HTML in a sandboxed iframe with a desktop/mobile toggle.
 * Used by both the customer-facing dashboard and the platform-admin templates page.
 */
export function TemplatePreviewModal({
  templateName,
  subject,
  bodyHtml,
  onClose,
}: TemplatePreviewModalProps) {
  const [deviceMode, setDeviceMode] = useState<"desktop" | "mobile">("desktop");

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className={styles.modalBackdrop} onClick={onClose} role="dialog" aria-modal="true">
      <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.modalTitleGroup}>
            <h3 className={styles.modalTitle}>{templateName}</h3>
            <span className={styles.modalSubject}>Subject: {subject}</span>
          </div>

          <div className={styles.deviceToggleGroup}>
            <button
              type="button"
              className={`${styles.deviceButton} ${
                deviceMode === "desktop" ? styles.deviceButtonActive : ""
              }`}
              onClick={() => setDeviceMode("desktop")}
            >
              🖥️ Desktop
            </button>
            <button
              type="button"
              className={`${styles.deviceButton} ${
                deviceMode === "mobile" ? styles.deviceButtonActive : ""
              }`}
              onClick={() => setDeviceMode("mobile")}
            >
              📱 Mobile
            </button>
          </div>

          <button
            type="button"
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Close preview"
          >
            ✕
          </button>
        </div>

        <div className={styles.modalBody}>
          <iframe
            title="Template preview"
            className={
              deviceMode === "desktop" ? styles.modalIframeDesktop : styles.modalIframeMobile
            }
            sandbox=""
            srcDoc={bodyHtml}
          />
        </div>
      </div>
    </div>
  );
}
