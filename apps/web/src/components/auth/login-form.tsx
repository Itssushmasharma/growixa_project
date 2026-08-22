"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { ArrowRightIcon, MailIcon } from "./auth-icons";
import { PasswordField } from "./password-field";
import styles from "./auth.module.css";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const nextParam = searchParams.get("next");
  const registerQuery = nextParam ? `?next=${encodeURIComponent(nextParam)}` : "";

  useEffect(() => {
    const oauthError = searchParams.get("oauth_error");
    if (oauthError) {
      if (oauthError === "OAuthEmailUnverifiedError") {
        showToast("error", "Your Google account email is not verified.");
      } else {
        showToast("error", "Google sign-in was interrupted or failed. Please try again.");
      }
    }
  }, [searchParams, showToast]);

  function getSafeRedirectUrl(next: string | null): string {
    if (next && next.startsWith("/") && !next.startsWith("//")) {
      return next;
    }
    return "/dashboard";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const destination = getSafeRedirectUrl(nextParam);
      router.push(destination);
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        showToast("error", "Invalid email or password.");
      } else if (err instanceof ApiError && err.status === 429) {
        showToast("error", "Too many attempts. Please try again later.");
      } else {
        showToast("error", "Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      {/* Work Email Field */}
      <div className={styles.fieldGroup}>
        <label htmlFor="email" className={styles.label}>
          Work email
        </label>
        <div className={styles.inputWrapper}>
          <span className={styles.inputIcon} aria-hidden="true">
            <MailIcon />
          </span>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            className={styles.inputWithIcons}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
        </div>
      </div>

      {/* Password Field */}
      <PasswordField
        id="password"
        label="Password"
        required
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="••••••••"
      />

      {/* Options Row: Remember Me + Forgot Password */}
      <div className={styles.optionsRow}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            className={styles.checkbox}
          />
          <span>Remember me</span>
        </label>

        <Link href="/forgot-password" className={styles.forgotLink}>
          Forgot password?
        </Link>
      </div>

      {/* Submit Button */}
      <button type="submit" disabled={submitting} className={styles.submitButton}>
        {submitting ? (
          <span className={styles.buttonSpinnerContent}>
            <span className={styles.spinner} aria-hidden="true" />
            <span>Signing you in…</span>
          </span>
        ) : (
          <span className={styles.buttonContent}>
            <span>Login to Growixa</span>
            <ArrowRightIcon className={styles.buttonArrow} />
          </span>
        )}
      </button>

      {/* Switch Link */}
      <div className={styles.switchRow}>
        <span>Don&apos;t have an account?</span>{" "}
        <Link href={`/register${registerQuery}`} className={styles.switchLink}>
          Sign up
        </Link>
      </div>
    </form>
  );
}
