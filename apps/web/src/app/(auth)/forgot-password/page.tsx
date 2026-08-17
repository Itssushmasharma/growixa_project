"use client";

import Image from "next/image";
import Link from "next/link";
import { type FormEvent, useState } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "../login/login.module.css";

export default function ForgotPasswordPage() {
  const { showToast } = useToast();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await apiFetch("/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setSubmittedEmail(email);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        showToast("error", "Too many attempts. Please try again later.");
      } else {
        showToast("error", "Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (submittedEmail) {
    return (
      <main className={styles.page}>
        <div className={styles.card}>
          <div className={styles.successIcon}>✓</div>
          <div className={styles.successTitle}>Check your email</div>
          <p className={styles.successBody}>
            If an account with <strong>{submittedEmail}</strong> exists, we sent a password reset
            link. It expires in 30 minutes and can be used once.
          </p>
          <div className={styles.footer}>
            <Link href="/login" className={styles.footerLink}>
              Back to sign in
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <div className={styles.brand}>
          <Image src={iconMark} alt="" width={36} height={36} />
          <div>
            <div className={styles.brandName}>Growixa</div>
            <div className={styles.brandCaption}>BY IITDEVELOPER</div>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="email">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              className={styles.input}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@company.com"
            />
          </div>

          <button type="submit" className={styles.submit} disabled={submitting}>
            {submitting ? "Sending reset link…" : "Send reset link"}
          </button>
        </form>

        <div className={styles.footer}>
          <Link href="/login" className={styles.footerLink}>
            Back to sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
