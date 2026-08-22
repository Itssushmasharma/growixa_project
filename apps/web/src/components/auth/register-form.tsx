"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type FormEvent, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { ArrowRightIcon, Building2Icon, CheckIcon, MailIcon, UserIcon } from "./auth-icons";
import { PasswordField } from "./password-field";
import styles from "./auth.module.css";

export function RegisterForm() {
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [accountName, setAccountName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreeTerms, setAgreeTerms] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  const nextParam = searchParams.get("next");
  const loginQuery = nextParam ? `?next=${encodeURIComponent(nextParam)}` : "";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!agreeTerms) {
      showToast("error", "Please agree to the Terms of Service and Privacy Policy.");
      return;
    }

    setSubmitting(true);

    try {
      await apiFetch("/accounts/register", {
        method: "POST",
        body: JSON.stringify({
          account_name: accountName,
          full_name: fullName,
          email,
          password,
          plan_slug: "free",
        }),
      });
      setRegisteredEmail(email);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        showToast("error", "An account with this email already exists.");
      } else if (err instanceof ApiError && err.status === 429) {
        showToast("error", "Too many attempts. Please try again later.");
      } else {
        showToast("error", "Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (registeredEmail) {
    return (
      <div className={styles.successCard}>
        <div className={styles.successIconCircle}>
          <CheckIcon width={24} height={24} />
        </div>
        <h3 className={styles.successTitle}>Check your email</h3>
        <p className={styles.successBody}>
          We sent a verification link to <strong>{registeredEmail}</strong>. Click it to activate
          your account, then sign in.
        </p>
        <Link href={`/login${loginQuery}`} className={styles.submitButton}>
          <span className={styles.buttonContent}>
            <span>Back to sign in</span>
            <ArrowRightIcon className={styles.buttonArrow} />
          </span>
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      {/* 2-Column Row 1: Company Name & Full Name */}
      <div className={styles.twoColumnGrid}>
        <div className={styles.fieldGroup}>
          <label htmlFor="accountName" className={styles.label}>
            Company name
          </label>
          <div className={styles.inputWrapper}>
            <span className={styles.inputIcon} aria-hidden="true">
              <Building2Icon />
            </span>
            <input
              id="accountName"
              type="text"
              required
              className={styles.inputWithIcons}
              value={accountName}
              onChange={(e) => setAccountName(e.target.value)}
              placeholder="Acme Inc"
            />
          </div>
        </div>

        <div className={styles.fieldGroup}>
          <label htmlFor="fullName" className={styles.label}>
            Your name
          </label>
          <div className={styles.inputWrapper}>
            <span className={styles.inputIcon} aria-hidden="true">
              <UserIcon />
            </span>
            <input
              id="fullName"
              type="text"
              required
              autoComplete="name"
              className={styles.inputWithIcons}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Ada Lovelace"
            />
          </div>
        </div>
      </div>

      {/* 2-Column Row 2: Work Email & Password */}
      <div className={styles.twoColumnGrid}>
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

        <PasswordField
          id="password"
          label="Password"
          required
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
      </div>

      {/* Terms & Privacy Agreement */}
      <div className={styles.termsRow}>
        <label className={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={agreeTerms}
            onChange={(e) => setAgreeTerms(e.target.checked)}
            className={styles.checkbox}
            required
          />
          <span className={styles.termsText}>
            I agree to the{" "}
            <Link href="/docs/terms" target="_blank" className={styles.inlineLink}>
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/docs/privacy" target="_blank" className={styles.inlineLink}>
              Privacy Policy
            </Link>
            .
          </span>
        </label>
      </div>

      {/* Submit CTA Button */}
      <button type="submit" disabled={submitting} className={styles.submitButton}>
        {submitting ? (
          <span className={styles.buttonSpinnerContent}>
            <span className={styles.spinner} aria-hidden="true" />
            <span>Creating your account…</span>
          </span>
        ) : (
          <span className={styles.buttonContent}>
            <span>Create your account</span>
            <ArrowRightIcon className={styles.buttonArrow} />
          </span>
        )}
      </button>

      {/* Switch to Login Link */}
      <div className={styles.switchRow}>
        <span>Already have an account?</span>{" "}
        <Link href={`/login${loginQuery}`} className={styles.switchLink}>
          Login
        </Link>
      </div>
    </form>
  );
}
