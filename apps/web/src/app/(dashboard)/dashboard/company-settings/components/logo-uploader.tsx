import { useState } from "react";

import styles from "./components.module.css";

interface LogoUploaderProps {
  logoUrl: string;
  disabled: boolean;
  onChange: (url: string) => void;
}

/**
 * No file-upload/storage backend exists yet for this product (checked: no upload
 * endpoint anywhere in growixa_api). `company_profile.logo_url` is a real, already-
 * persisted field, so this lets an editor set it directly by URL — a real, working
 * mechanism, not a placeholder. The "Upload a file" affordance is disabled and labeled
 * as a future integration point rather than faking upload behavior.
 */
export function LogoUploader({ logoUrl, disabled, onChange }: LogoUploaderProps) {
  const [editingUrl, setEditingUrl] = useState(false);
  const [draftUrl, setDraftUrl] = useState(logoUrl);

  function startEditing() {
    setDraftUrl(logoUrl);
    setEditingUrl(true);
  }

  function commitUrl() {
    onChange(draftUrl.trim());
    setEditingUrl(false);
  }

  return (
    <div className={styles.field}>
      <span className={styles.label}>Company Logo</span>
      <div className={styles.logoRow}>
        <div className={styles.logoPreview}>
          {logoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element -- external, account-supplied URL
            <img src={logoUrl} alt="Company logo" />
          ) : (
            <span className={styles.logoEmptyIcon} aria-hidden="true">
              🏢
            </span>
          )}
        </div>
        <div className={styles.logoActions}>
          {editingUrl ? (
            <div className={styles.logoActionsRow}>
              <input
                type="url"
                className={styles.logoUrlInput}
                placeholder="https://example.com/logo.png"
                value={draftUrl}
                onChange={(event) => setDraftUrl(event.target.value)}
                aria-label="Logo URL"
              />
              <button type="button" className={styles.logoButton} onClick={commitUrl}>
                Save
              </button>
              <button
                type="button"
                className={styles.logoButton}
                onClick={() => setEditingUrl(false)}
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className={styles.logoActionsRow}>
              <button
                type="button"
                className={styles.logoButton}
                disabled={disabled}
                onClick={startEditing}
              >
                {logoUrl ? "Change logo URL" : "Set logo URL"}
              </button>
              <button type="button" className={styles.logoButton} disabled title="Coming soon">
                Upload a file
              </button>
            </div>
          )}
          <span className={styles.hint}>
            PNG, JPG or SVG, ideally square, up to 2MB. File upload isn&apos;t available yet — paste
            a hosted image URL for now.
          </span>
        </div>
      </div>
    </div>
  );
}
