"use client";

import type { ReactNode } from "react";

import { AuthCard } from "./auth-card";
import { AuthShowcase } from "./auth-showcase";
import styles from "./auth.module.css";

interface AuthSplitLayoutProps {
  mode: "login" | "register";
  children: ReactNode;
}

export function AuthSplitLayout({ mode, children }: AuthSplitLayoutProps) {
  return (
    <main className={styles.splitLayout}>
      {/* Left Showcase (Brand Highlights, Floating Metric Cards, Flowing Ribbon Wave) */}
      <AuthShowcase />

      {/* Right Floating Authentication Card */}
      <section className={styles.authSection} aria-label="Account Authentication">
        <AuthCard mode={mode}>{children}</AuthCard>
      </section>
    </main>
  );
}
