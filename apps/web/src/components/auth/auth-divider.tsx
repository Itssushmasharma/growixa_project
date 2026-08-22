import styles from "./auth-divider.module.css";

interface AuthDividerProps {
  text?: string;
}

export function AuthDivider({ text = "or" }: AuthDividerProps) {
  return (
    <div className={styles.divider} role="separator" aria-label={text}>
      <span className={styles.text}>{text}</span>
    </div>
  );
}
