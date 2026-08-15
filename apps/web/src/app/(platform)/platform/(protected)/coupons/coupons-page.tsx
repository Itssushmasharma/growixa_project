"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import type { BillingCreditType, Coupon, CouponDiscountType } from "../accounts/types";
import styles from "./coupons-page.module.css";

const CREDIT_TYPE_OPTIONS: BillingCreditType[] = [
  "AI_RUNS",
  "EMAIL_SENDS",
  "CONTACT_SLOTS",
  "SOCIAL_POSTS",
];

const DISCOUNT_TYPE_OPTIONS: { value: CouponDiscountType; label: string }[] = [
  { value: "PERCENTAGE", label: "Percentage off (top-up only)" },
  { value: "FIXED_AMOUNT", label: "Fixed amount off (top-up only)" },
  { value: "CREDIT_GRANT", label: "Free credit grant" },
];

function errorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string | { message?: string } };
      if (typeof parsed.detail === "string") return parsed.detail;
      if (parsed.detail?.message) return parsed.detail.message;
    } catch {
      // Not JSON
    }
  }
  return fallback;
}

interface CouponFormState {
  code: string;
  discount_type: CouponDiscountType;
  discount_value: string;
  credit_type: BillingCreditType;
  applicable_plan_slugs: string;
  max_redemptions: string;
  expires_at: string;
}

function blankCouponForm(): CouponFormState {
  return {
    code: "",
    discount_type: "PERCENTAGE",
    discount_value: "",
    credit_type: "AI_RUNS",
    applicable_plan_slugs: "",
    max_redemptions: "",
    expires_at: "",
  };
}

function formatDiscount(coupon: Coupon): string {
  switch (coupon.discount_type) {
    case "PERCENTAGE":
      return `${coupon.discount_value}% off`;
    case "FIXED_AMOUNT":
      return `${coupon.discount_value} off (major currency unit)`;
    case "CREDIT_GRANT":
      return `${coupon.discount_value} ${coupon.credit_type} credits`;
    default:
      return "";
  }
}

export function CouponsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [coupons, setCoupons] = useState<Coupon[]>([]);

  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<CouponFormState>(blankCouponForm());
  const [saving, setSaving] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const list = await apiFetch<Coupon[]>("/platform/coupons");
        setCoupons(list);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to manage coupons.");
        } else {
          setLoadError("Could not load the coupon catalog.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  function openNewForm() {
    setForm(blankCouponForm());
    setFormOpen(true);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    const plan_slugs = form.applicable_plan_slugs
      .split(",")
      .map((slug) => slug.trim())
      .filter((slug) => slug.length > 0);
    const body = {
      code: form.code.trim(),
      discount_type: form.discount_type,
      discount_value: Number(form.discount_value),
      credit_type: form.discount_type === "CREDIT_GRANT" ? form.credit_type : null,
      applicable_plan_slugs: plan_slugs.length > 0 ? plan_slugs : null,
      max_redemptions: form.max_redemptions.trim() === "" ? null : Number(form.max_redemptions),
      expires_at: form.expires_at.trim() === "" ? null : new Date(form.expires_at).toISOString(),
    };
    try {
      const created = await apiFetch<Coupon>("/platform/coupons", {
        method: "POST",
        body: JSON.stringify(body),
      });
      setCoupons((current) => [created, ...current]);
      showToast("success", `Coupon "${created.code}" created.`);
      setFormOpen(false);
    } catch (err) {
      showToast("error", errorDetail(err, "Could not create the coupon."));
    } finally {
      setSaving(false);
    }
  }

  async function handleToggleActive(coupon: Coupon) {
    setTogglingId(coupon.id);
    try {
      const updated = await apiFetch<Coupon>(`/platform/coupons/${coupon.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !coupon.is_active }),
      });
      setCoupons((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      showToast(
        "success",
        `Coupon "${updated.code}" ${updated.is_active ? "activated" : "deactivated"}.`,
      );
    } catch (err) {
      showToast("error", errorDetail(err, "Could not update the coupon."));
    } finally {
      setTogglingId(null);
    }
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>Loading…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>{loadError}</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>Coupons</h2>
          <button type="button" className={styles.actionButton} onClick={openNewForm}>
            + New coupon
          </button>
        </div>

        {formOpen && (
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formHeading}>New coupon</div>
            <div className={styles.fieldGrid}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="coupon-code">
                  Code
                </label>
                <input
                  id="coupon-code"
                  className={styles.input}
                  required
                  value={form.code}
                  onChange={(event) => setForm({ ...form, code: event.target.value.toUpperCase() })}
                  placeholder="e.g. LAUNCH20"
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="coupon-discount-type">
                  Discount type
                </label>
                <select
                  id="coupon-discount-type"
                  className={styles.select}
                  value={form.discount_type}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      discount_type: event.target.value as CouponDiscountType,
                    })
                  }
                >
                  {DISCOUNT_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="coupon-discount-value">
                  {form.discount_type === "CREDIT_GRANT" ? "Credits to grant" : "Discount value"}
                </label>
                <input
                  id="coupon-discount-value"
                  className={styles.input}
                  type="number"
                  required
                  min={0}
                  step={form.discount_type === "PERCENTAGE" ? 1 : "any"}
                  max={form.discount_type === "PERCENTAGE" ? 100 : undefined}
                  value={form.discount_value}
                  onChange={(event) => setForm({ ...form, discount_value: event.target.value })}
                />
              </div>
              {form.discount_type === "CREDIT_GRANT" && (
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="coupon-credit-type">
                    Credit type
                  </label>
                  <select
                    id="coupon-credit-type"
                    className={styles.select}
                    value={form.credit_type}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        credit_type: event.target.value as BillingCreditType,
                      })
                    }
                  >
                    {CREDIT_TYPE_OPTIONS.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="coupon-plan-slugs">
                  Eligible plan slugs (comma-separated, blank = any)
                </label>
                <input
                  id="coupon-plan-slugs"
                  className={styles.input}
                  value={form.applicable_plan_slugs}
                  onChange={(event) =>
                    setForm({ ...form, applicable_plan_slugs: event.target.value })
                  }
                  placeholder="e.g. starter, pro"
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="coupon-max-redemptions">
                  Max redemptions (blank = unlimited)
                </label>
                <input
                  id="coupon-max-redemptions"
                  className={styles.input}
                  type="number"
                  min={1}
                  value={form.max_redemptions}
                  onChange={(event) => setForm({ ...form, max_redemptions: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="coupon-expires-at">
                  Expires at (blank = never)
                </label>
                <input
                  id="coupon-expires-at"
                  className={styles.input}
                  type="datetime-local"
                  value={form.expires_at}
                  onChange={(event) => setForm({ ...form, expires_at: event.target.value })}
                />
              </div>
            </div>
            {(form.discount_type === "PERCENTAGE" || form.discount_type === "FIXED_AMOUNT") && (
              <div className={styles.hint}>
                Percentage/fixed-amount coupons apply at checkout for credit top-ups only —
                Razorpay&apos;s subscription checkout has no discount parameter. Redeem a free
                credit grant coupon via the customer billing page instead.
              </div>
            )}
            <div className={styles.formActions}>
              <button type="submit" className={styles.actionButton} disabled={saving}>
                {saving ? "Saving…" : "Create coupon"}
              </button>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setFormOpen(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className={styles.list}>
          {coupons.length === 0 && !formOpen && (
            <div className={styles.rowSlug}>No coupons yet.</div>
          )}
          {coupons.map((coupon) => (
            <div className={styles.row} key={coupon.id}>
              <div className={styles.rowMain}>
                <span className={styles.rowName}>{coupon.code}</span>
                <span className={styles.rowSlug}>
                  {formatDiscount(coupon)}
                  {coupon.applicable_plan_slugs &&
                    ` · plans: ${coupon.applicable_plan_slugs.join(", ")}`}
                  {coupon.expires_at &&
                    ` · expires ${new Date(coupon.expires_at).toLocaleDateString()}`}
                </span>
              </div>
              <span className={styles.rowMeta}>
                {coupon.redemption_count}
                {coupon.max_redemptions !== null ? ` / ${coupon.max_redemptions}` : ""} redeemed
              </span>
              <span className={coupon.is_active ? styles.badgeActive : styles.badgeInactive}>
                {coupon.is_active ? "Active" : "Inactive"}
              </span>
              <button
                type="button"
                className={styles.secondaryButton}
                disabled={togglingId === coupon.id}
                onClick={() => handleToggleActive(coupon)}
              >
                {coupon.is_active ? "Deactivate" : "Activate"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
