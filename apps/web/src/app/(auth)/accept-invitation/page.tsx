"use client";

import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useState } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";
import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "../login/login.module.css";

type AcceptStatus = "form" | "success" | "expired";

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={null}>
      <AcceptInvitationContent />
    </Suspense>
  );
}

function AcceptInvitationContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const { showToast } = useToast();
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<AcceptStatus>(token ? "form" : "expired");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      setStatus("expired");
      return;
    }
    if (password !== confirmPassword) {
      showToast("error", "Passwords do not match.");
      return;
    }

    setSubmitting(true);
    try {
      await apiFetch("/users/invitations/accept", {
        method: "POST",
        body: JSON.stringify({ token, password, full_name: fullName }),
      });
      setStatus("success");
    } catch {
      // The API deliberately returns one indistinguishable error for missing, unknown,
      // expired, and already-accepted tokens, so there is nothing more specific to say.
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
          <div className={styles.successTitle}>Account ready</div>
          <p className={styles.successBody}>Your account has been created. You can now sign in.</p>
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
          <div className={styles.successIcon}>✕</div>
          <div className={styles.successTitle}>Invitation unavailable</div>
          <p className={styles.successBody}>
            This invitation link is invalid, expired, or has already been used. Ask an administrator
            on your team to send a new one.
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
            <label className={styles.label} htmlFor="full-name">
              Full name
            </label>
            <input
              id="full-name"
              type="text"
              required
              autoComplete="name"
              className={styles.input}
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Ada Lovelace"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="new-password"
              className={styles.input}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
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
            {submitting ? "Creating account…" : "Accept invitation"}
          </button>
        </form>
      </div>
    </main>
  );
}
