"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { ShieldCheckIcon } from "./auth-icons";
import { AuthTabs } from "./auth-tabs";
import { GoogleAuthButton } from "./google-auth-button";
import styles from "./auth.module.css";

interface AuthCardProps {
  mode: "login" | "register";
  children: ReactNode;
}

export function AuthCard({ mode, children }: AuthCardProps) {
  return (
    <div className={styles.cardContainer}>
      <div className={styles.authCard}>
        {/* Top Tab Switcher */}
        <AuthTabs activeTab={mode} />

        {/* Card Brand Header */}
        <div className={styles.cardBrandHeader}>
          <Link href="/" className={styles.cardBrandLink} aria-label="Growixa Home">
            <div className={styles.brandMark} aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
            </div>
            <span>Growixa</span>
          </Link>
        </div>

        {/* Headline */}
        <h2 className={styles.cardTitle}>
          Grow Faster <span className={styles.cardTitleGradient}>With AI</span>
        </h2>
        <p className={styles.cardSubtitle}>
          {mode === "login"
            ? "Enter your credentials to access your Growixa workspace."
            : "Join 10,000+ businesses growing smarter with Growixa. Free to get started — no credit card required."}
        </p>

        {/* Google SSO Button */}
        <GoogleAuthButton label="Continue with Google" />

        {/* Divider */}
        <div className={styles.dividerRow}>
          <div className={styles.dividerLine} />
          <span className={styles.dividerText}>OR</span>
          <div className={styles.dividerLine} />
        </div>

        {/* Form Body */}
        {children}
      </div>

      {/* Security Trust Badge */}
      <div className={styles.securityBadge}>
        <ShieldCheckIcon className={styles.securityIcon} />
        <span>Enterprise-grade 256-bit encryption &bull; SOC2 compliant</span>
      </div>
    </div>
  );
}
