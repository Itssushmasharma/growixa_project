"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "../login/login.module.css";

type ResetStatus = "form" | "success" | "expired";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordContent />
    </Suspense>
  );
}

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { showToast } = useToast();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<ResetStatus>(token ? "form" : "expired");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      setStatus("expired");
      return;
    }
    if (newPassword !== confirmPassword) {
      showToast("error", "Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch("/auth/password-reset/complete", {
        method: "POST",
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      setStatus("success");
    } catch {
      setStatus("expired");
    } finally {
      setSubmitting(false);
    }
  }

  if (status === "success") {
    return (
      <main className={styles.page}>
        <div className={styles.card}>
          <div className={styles.successIcon}>✓</div>
          <h1 className={styles.successTitle}>Password updated</h1>
          <p className={styles.successBody}>Your password has been reset. You can now sign in.</p>
          <div className={styles.footer}>
            <Link href="/login" className={styles.footerLink}>
              Sign in
            </Link>
          </div>
        </div>
      </main>
    );
  }

  if (status === "expired") {
    return (
      <main className={styles.page}>
        <div className={styles.card}>
          <div className={styles.successIcon} style={{ color: "var(--send)" }}>
            ✕
          </div>
          <h1 className={styles.successTitle}>Link expired</h1>
          <p className={styles.successBody}>
            This password reset link is invalid, expired, or has already been used.
          </p>
          <div className={styles.footer}>
            <Link href="/forgot-password" className={styles.footerLink}>
              Request a new reset link
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <Link href="/" className={styles.brand}>
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
          <div>
            <div className={styles.brandName}>Growixa</div>
            <div className={styles.brandCaption}>BY IITDEVELOPER</div>
          </div>
        </Link>

        <form onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="new-password">
              New password
            </label>
            <input
              id="new-password"
              type="password"
              required
              autoComplete="new-password"
              className={styles.input}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="••••••••"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="confirm-password">
              Confirm password
            </label>
            <input
              id="confirm-password"
              type="password"
              required
              autoComplete="new-password"
              className={styles.input}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="••••••••"
            />
          </div>

          <button type="submit" className={styles.submit} disabled={submitting}>
            {submitting ? "Resetting password…" : "Reset password"}
          </button>
        </form>
      </div>
    </main>
  );
}
