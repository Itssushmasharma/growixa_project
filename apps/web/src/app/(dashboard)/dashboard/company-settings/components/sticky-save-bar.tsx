import styles from "./components.module.css";

interface StickySaveBarProps {
  dirty: boolean;
  saving: boolean;
  onDiscard: () => void;
  onSave: () => void;
}

export function StickySaveBar({ dirty, saving, onDiscard, onSave }: StickySaveBarProps) {
  if (!dirty) return null;

  return (
    <div className={styles.saveBar} role="status">
      <span className={styles.saveBarStatus}>
        <span className={styles.saveBarDot} aria-hidden="true" />
        You have unsaved changes
      </span>
      <div className={styles.saveBarActions}>
        <button
          type="button"
          className={styles.saveBarDiscard}
          disabled={saving}
          onClick={onDiscard}
        >
          Discard changes
        </button>
        <button type="button" className={styles.saveBarSave} disabled={saving} onClick={onSave}>
          {saving ? "Saving…" : "Save changes"}
        </button>
      </div>
    </div>
  );
}
