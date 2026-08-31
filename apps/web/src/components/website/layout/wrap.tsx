import type { ReactNode } from "react";
import styles from "./wrap.module.css";

export interface WrapProps {
  className?: string;
  children: ReactNode;
}

export default function Wrap({ className = "", children }: WrapProps) {
  return <div className={`${styles.wrap} ${className}`}>{children}</div>;
}
