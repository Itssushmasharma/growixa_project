import React, { type ComponentPropsWithoutRef, type ElementType, type ReactNode } from "react";
import styles from "./button.module.css";

export type ButtonVariant = "primary" | "glass" | "onstage" | "ghoststage";
export type ButtonSize = "md" | "sm";

export type ButtonProps<T extends ElementType = "button"> = {
  as?: T;
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  children?: ReactNode;
} & ComponentPropsWithoutRef<T>;

export default function Button<T extends ElementType = "button">({
  as,
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...rest
}: ButtonProps<T>) {
  const Component = as || "button";
  const extra =
    Component === "button"
      ? { type: (rest as { type?: "button" | "submit" | "reset" }).type ?? "button" }
      : {};
  return (
    <Component
      className={`${styles.btn} ${styles[variant]} ${styles[size]} ${className}`}
      {...extra}
      {...rest}
    >
      {children}
    </Component>
  );
}
