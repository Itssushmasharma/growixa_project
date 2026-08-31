import type { CSSProperties, ReactNode } from "react";
import styles from "./chip.module.css";

export interface ChipProps {
  hue?: string;
  className?: string;
  children: ReactNode;
}

export default function Chip({ hue = "create", className = "", children }: ChipProps) {
  const customStyle = {
    "--c": `var(--${hue})`,
    "--cl": `var(--${hue}-l)`,
    "--cd": `var(--${hue}-d)`,
  } as CSSProperties & Record<string, string>;

  return (
    <span className={`${styles.chip} ${className}`} style={customStyle}>
      {children}
    </span>
  );
}
