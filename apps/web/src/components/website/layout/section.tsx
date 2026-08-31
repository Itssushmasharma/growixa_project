import type { CSSProperties, ReactNode } from "react";
import styles from "./section.module.css";

export function hueVars(hue?: string): (CSSProperties & Record<string, string>) | undefined {
  if (!hue) return undefined;
  return {
    "--hue": `var(--${hue})`,
    "--hue-l": `var(--${hue}-l)`,
    "--hue-d": `var(--${hue}-d)`,
  } as CSSProperties & Record<string, string>;
}

export interface SectionProps {
  id?: string;
  tint?: boolean;
  dark?: boolean;
  hue?: string;
  className?: string;
  children: ReactNode;
}

export default function Section({ id, tint, dark, hue, className = "", children }: SectionProps) {
  const cls = [styles.sec, tint && styles.tint, dark && styles.dark, className]
    .filter(Boolean)
    .join(" ");
  return (
    <section id={id} className={cls} style={hueVars(hue)}>
      {children}
    </section>
  );
}
