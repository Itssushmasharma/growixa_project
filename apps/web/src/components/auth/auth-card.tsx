"use client";

import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

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
            <Image src={iconMark} alt="" width={30} height={30} className={styles.cardLogo} />
            <span className={styles.cardBrandName}>Growixa</span>
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
        <span>Your data is safe with us. We never share your information.</span>
      </div>
    </div>
  );
}
