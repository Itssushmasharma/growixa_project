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
      {/* Aurora Mesh Ambient Background Canvas */}
      <div className={styles.auroraCanvas} aria-hidden="true">
        <div className={styles.auroraMesh} />
        <div className={styles.filmGrain} />
      </div>

      {/* Left Showcase (Brand, Display Headline, Live Engine Telemetry, Proof Badges) */}
      <AuthShowcase />

      {/* Right Floating Authentication Card */}
      <section className={styles.authSection} aria-label="Account Authentication">
        <AuthCard mode={mode}>{children}</AuthCard>
      </section>
    </main>
  );
}
