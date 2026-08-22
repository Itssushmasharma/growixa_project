"use client";

import Image from "next/image";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type FormEvent, Suspense, useState } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";
import { AuthDivider } from "@/components/auth/auth-divider";
import { GoogleButton } from "@/components/auth/google-button";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./register.module.css";

// Matches the real subscription_plans catalog (GRX-BILL-002) -- Enterprise is
// contact-sales, never a self-serve registration option (DEC-GRX-030).
type PlanSlug = "free" | "starter" | "pro";

const PLANS: { slug: PlanSlug; name: string; price: string }[] = [
  { slug: "free", name: "Free", price: "$0/mo" },
  { slug: "starter", name: "Starter", price: "$19/mo" },
  { slug: "pro", name: "Pro", price: "$49/mo" },
];

function isPlanSlug(value: string | null): value is PlanSlug {
  return value === "free" || value === "starter" || value === "pro";
}

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterContent />
    </Suspense>
  );
}

function RegisterContent() {
  const searchParams = useSearchParams();
  const { showToast } = useToast();

  const [accountName, setAccountName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [planSlug, setPlanSlug] = useState<PlanSlug>(() => {
    const fromQuery = searchParams.get("plan");
    return isPlanSlug(fromQuery) ? fromQuery : "free";
  });
  const [submitting, setSubmitting] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);

    try {
      await apiFetch("/accounts/register", {
        method: "POST",
        body: JSON.stringify({
          account_name: accountName,
          full_name: fullName,
          email,
          password,
          plan_slug: planSlug,
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
      <main className={styles.page}>
        <div className={styles.card}>
          <div className={styles.successIcon}>✓</div>
          <div className={styles.successTitle}>Check your email</div>
          <p className={styles.successBody}>
            We sent a verification link to <strong>{registeredEmail}</strong>. Click it to activate
            your account, then sign in.
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

        <GoogleButton label="Sign up with Google" />

        <AuthDivider text="or create account" />

        <form onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="accountName">
              Company name
            </label>
            <input
              id="accountName"
              type="text"
              required
              className={styles.input}
              value={accountName}
              onChange={(event) => setAccountName(event.target.value)}
              placeholder="Acme Inc"
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="fullName">
              Your name
            </label>
            <input
              id="fullName"
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
            <label className={styles.label} htmlFor="email">
              Work email
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
            <span className={styles.label}>Plan</span>
            <div className={styles.planGroup} role="radiogroup" aria-label="Plan">
              {PLANS.map((plan) => (
                <label
                  key={plan.slug}
                  className={
                    plan.slug === planSlug
                      ? `${styles.planOption} ${styles.planOptionSelected}`
                      : styles.planOption
                  }
                >
                  <input
                    type="radio"
                    name="plan"
                    value={plan.slug}
                    checked={plan.slug === planSlug}
                    onChange={() => setPlanSlug(plan.slug)}
                    className={styles.visuallyHiddenRadio}
                  />
                  <span className={styles.planOptionName}>{plan.name}</span>
                  <span className={styles.planOptionPrice}>{plan.price}</span>
                </label>
              ))}
            </div>
          </div>

          <button type="submit" className={styles.submit} disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </button>
        </form>

        <div className={styles.footer}>
          Already have an account?{" "}
          <Link href="/login" className={styles.footerLink}>
            Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
