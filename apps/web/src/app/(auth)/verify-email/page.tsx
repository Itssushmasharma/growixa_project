"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import styles from "./verify-email.module.css";

type Status = "verifying" | "success" | "error";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  );
}

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<Status>("verifying");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }

    let cancelled = false;
    apiFetch("/accounts/verify-email", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then(() => {
        if (!cancelled) setStatus("success");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        {status === "verifying" && (
          <>
            <div className={styles.icon}>⏳</div>
            <div className={styles.title}>Verifying your email…</div>
          </>
        )}
        {status === "success" && (
          <>
            <div className={styles.icon}>✓</div>
            <div className={styles.title}>Email verified</div>
            <p className={styles.body}>Your account is active. You can now sign in.</p>
            <Link href="/login" className={styles.link}>
              Sign in
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <div className={styles.icon}>✕</div>
            <div className={styles.title}>Verification failed</div>
            <p className={styles.body}>
              This link is invalid or has expired. You can register again to get a new one.
            </p>
            <Link href="/register" className={styles.link}>
              Back to sign up
            </Link>
          </>
        )}
      </div>
    </main>
  );
}
