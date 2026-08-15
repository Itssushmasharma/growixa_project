"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import type { BillingCreditType, BillingSubscriptionPlan, CreditPack } from "../accounts/types";
import styles from "./subscriptions-page.module.css";

const CREDIT_TYPE_OPTIONS: BillingCreditType[] = [
  "AI_RUNS",
  "EMAIL_SENDS",
  "CONTACT_SLOTS",
  "SOCIAL_POSTS",
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

function parseOptionalNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

interface PlanFormState {
  slug: string;
  name: string;
  price_usd: string;
  price_inr: string;
  max_contacts: string;
  max_monthly_emails: string;
  max_monthly_ai_runs: string;
  max_social_accounts: string;
  max_user_seats: string;
  allow_byo_ai_key: boolean;
  allow_byo_smtp: boolean;
  audit_export_enabled: boolean;
  audit_api_enabled: boolean;
}

function blankPlanForm(): PlanFormState {
  return {
    slug: "",
    name: "",
    price_usd: "",
    price_inr: "",
    max_contacts: "",
    max_monthly_emails: "",
    max_monthly_ai_runs: "",
    max_social_accounts: "",
    max_user_seats: "",
    allow_byo_ai_key: false,
    allow_byo_smtp: false,
    audit_export_enabled: false,
    audit_api_enabled: false,
  };
}

function planFormFrom(plan: BillingSubscriptionPlan): PlanFormState {
  return {
    slug: plan.slug,
    name: plan.name,
    price_usd: plan.price_usd?.toString() ?? "",
    price_inr: plan.price_inr?.toString() ?? "",
    max_contacts: plan.max_contacts?.toString() ?? "",
    max_monthly_emails: plan.max_monthly_emails?.toString() ?? "",
    max_monthly_ai_runs: plan.max_monthly_ai_runs?.toString() ?? "",
    max_social_accounts: plan.max_social_accounts?.toString() ?? "",
    max_user_seats: plan.max_user_seats?.toString() ?? "",
    allow_byo_ai_key: plan.allow_byo_ai_key,
    allow_byo_smtp: plan.allow_byo_smtp,
    audit_export_enabled: plan.audit_export_enabled,
    audit_api_enabled: plan.audit_api_enabled,
  };
}

interface PackFormState {
  slug: string;
  name: string;
  credit_type: BillingCreditType;
  credits: string;
  price_usd: string;
  price_inr: string;
  is_active: boolean;
}

function blankPackForm(): PackFormState {
  return {
    slug: "",
    name: "",
    credit_type: "AI_RUNS",
    credits: "",
    price_usd: "",
    price_inr: "",
    is_active: true,
  };
}

function packFormFrom(pack: CreditPack): PackFormState {
  return {
    slug: pack.slug,
    name: pack.name,
    credit_type: pack.credit_type,
    credits: pack.credits.toString(),
    price_usd: pack.price_usd?.toString() ?? "",
    price_inr: pack.price_inr?.toString() ?? "",
    is_active: pack.is_active,
  };
}

export function SubscriptionsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [plans, setPlans] = useState<BillingSubscriptionPlan[]>([]);
  const [packs, setPacks] = useState<CreditPack[]>([]);

  const [planFormOpenFor, setPlanFormOpenFor] = useState<string | "new" | null>(null);
  const [planForm, setPlanForm] = useState<PlanFormState>(blankPlanForm());
  const [planSaving, setPlanSaving] = useState(false);

  const [packFormOpenFor, setPackFormOpenFor] = useState<string | "new" | null>(null);
  const [packForm, setPackForm] = useState<PackFormState>(blankPackForm());
  const [packSaving, setPackSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [planList, packList] = await Promise.all([
          apiFetch<BillingSubscriptionPlan[]>("/platform/subscription-plans"),
          apiFetch<CreditPack[]>("/platform/credit-packs"),
        ]);
        setPlans(planList);
        setPacks(packList);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to manage subscriptions.");
        } else {
          setLoadError("Could not load the plan/credit-pack catalog.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  function openNewPlanForm() {
    setPlanForm(blankPlanForm());
    setPlanFormOpenFor("new");
  }

  function openEditPlanForm(plan: BillingSubscriptionPlan) {
    setPlanForm(planFormFrom(plan));
    setPlanFormOpenFor(plan.slug);
  }

  async function handlePlanSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPlanSaving(true);
    const body = {
      name: planForm.name,
      price_usd: parseOptionalNumber(planForm.price_usd),
      price_inr: parseOptionalNumber(planForm.price_inr),
      max_contacts: parseOptionalNumber(planForm.max_contacts),
      max_monthly_emails: parseOptionalNumber(planForm.max_monthly_emails),
      max_monthly_ai_runs: parseOptionalNumber(planForm.max_monthly_ai_runs),
      max_social_accounts: parseOptionalNumber(planForm.max_social_accounts),
      max_user_seats: parseOptionalNumber(planForm.max_user_seats),
      allow_byo_ai_key: planForm.allow_byo_ai_key,
      allow_byo_smtp: planForm.allow_byo_smtp,
      audit_export_enabled: planForm.audit_export_enabled,
      audit_api_enabled: planForm.audit_api_enabled,
    };
    try {
      if (planFormOpenFor === "new") {
        const created = await apiFetch<BillingSubscriptionPlan>("/platform/subscription-plans", {
          method: "POST",
          body: JSON.stringify({ slug: planForm.slug, ...body }),
        });
        setPlans((current) => [...current, created]);
        showToast("success", `Plan "${created.name}" created.`);
      } else {
        const existing = plans.find((plan) => plan.slug === planFormOpenFor);
        if (!existing) return;
        const updated = await apiFetch<BillingSubscriptionPlan>(
          `/platform/subscription-plans/${existing.id}`,
          { method: "PUT", body: JSON.stringify(body) },
        );
        setPlans((current) => current.map((plan) => (plan.id === updated.id ? updated : plan)));
        showToast("success", `Plan "${updated.name}" updated.`);
      }
      setPlanFormOpenFor(null);
    } catch (err) {
      showToast("error", errorDetail(err, "Could not save the plan."));
    } finally {
      setPlanSaving(false);
    }
  }

  function openNewPackForm() {
    setPackForm(blankPackForm());
    setPackFormOpenFor("new");
  }

  function openEditPackForm(pack: CreditPack) {
    setPackForm(packFormFrom(pack));
    setPackFormOpenFor(pack.slug);
  }

  async function handlePackSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPackSaving(true);
    const body = {
      name: packForm.name,
      credit_type: packForm.credit_type,
      credits: Number(packForm.credits),
      price_usd: parseOptionalNumber(packForm.price_usd),
      price_inr: parseOptionalNumber(packForm.price_inr),
      is_active: packForm.is_active,
    };
    try {
      if (packFormOpenFor === "new") {
        const created = await apiFetch<CreditPack>("/platform/credit-packs", {
          method: "POST",
          body: JSON.stringify({ slug: packForm.slug, ...body }),
        });
        setPacks((current) => [...current, created]);
        showToast("success", `Credit pack "${created.name}" created.`);
      } else {
        const existing = packs.find((pack) => pack.slug === packFormOpenFor);
        if (!existing) return;
        const updated = await apiFetch<CreditPack>(`/platform/credit-packs/${existing.id}`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        setPacks((current) => current.map((pack) => (pack.id === updated.id ? updated : pack)));
        showToast("success", `Credit pack "${updated.name}" updated.`);
      }
      setPackFormOpenFor(null);
    } catch (err) {
      showToast("error", errorDetail(err, "Could not save the credit pack."));
    } finally {
      setPackSaving(false);
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
          <h2 className={styles.headerTitle}>Subscription plans</h2>
          <button type="button" className={styles.actionButton} onClick={openNewPlanForm}>
            + New plan
          </button>
        </div>

        {planFormOpenFor && (
          <form onSubmit={handlePlanSubmit} className={styles.form}>
            <div className={styles.formHeading}>
              {planFormOpenFor === "new" ? "New plan" : `Edit ${planFormOpenFor}`}
            </div>
            <div className={styles.fieldGrid}>
              {planFormOpenFor === "new" && (
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="plan-slug">
                    Slug
                  </label>
                  <input
                    id="plan-slug"
                    className={styles.input}
                    required
                    pattern="[a-z0-9_-]+"
                    value={planForm.slug}
                    onChange={(event) => setPlanForm({ ...planForm, slug: event.target.value })}
                    placeholder="e.g. growth"
                  />
                </div>
              )}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-name">
                  Name
                </label>
                <input
                  id="plan-name"
                  className={styles.input}
                  required
                  value={planForm.name}
                  onChange={(event) => setPlanForm({ ...planForm, name: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-price-usd">
                  Price (USD, blank = not available)
                </label>
                <input
                  id="plan-price-usd"
                  className={styles.input}
                  type="number"
                  value={planForm.price_usd}
                  onChange={(event) => setPlanForm({ ...planForm, price_usd: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-price-inr">
                  Price (INR, blank = not available)
                </label>
                <input
                  id="plan-price-inr"
                  className={styles.input}
                  type="number"
                  value={planForm.price_inr}
                  onChange={(event) => setPlanForm({ ...planForm, price_inr: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-max-contacts">
                  Max contacts (blank = unlimited)
                </label>
                <input
                  id="plan-max-contacts"
                  className={styles.input}
                  type="number"
                  value={planForm.max_contacts}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, max_contacts: event.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-max-emails">
                  Max monthly emails (blank = unlimited)
                </label>
                <input
                  id="plan-max-emails"
                  className={styles.input}
                  type="number"
                  value={planForm.max_monthly_emails}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, max_monthly_emails: event.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-max-ai-runs">
                  Max monthly AI runs (blank = unlimited)
                </label>
                <input
                  id="plan-max-ai-runs"
                  className={styles.input}
                  type="number"
                  value={planForm.max_monthly_ai_runs}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, max_monthly_ai_runs: event.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-max-social">
                  Max social accounts (blank = unlimited)
                </label>
                <input
                  id="plan-max-social"
                  className={styles.input}
                  type="number"
                  value={planForm.max_social_accounts}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, max_social_accounts: event.target.value })
                  }
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="plan-max-seats">
                  Max user seats (blank = unlimited)
                </label>
                <input
                  id="plan-max-seats"
                  className={styles.input}
                  type="number"
                  value={planForm.max_user_seats}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, max_user_seats: event.target.value })
                  }
                />
              </div>
            </div>
            <div className={styles.checkboxRow}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={planForm.allow_byo_ai_key}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, allow_byo_ai_key: event.target.checked })
                  }
                />
                BYO AI key
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={planForm.allow_byo_smtp}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, allow_byo_smtp: event.target.checked })
                  }
                />
                BYO SMTP
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={planForm.audit_export_enabled}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, audit_export_enabled: event.target.checked })
                  }
                />
                Audit export
              </label>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={planForm.audit_api_enabled}
                  onChange={(event) =>
                    setPlanForm({ ...planForm, audit_api_enabled: event.target.checked })
                  }
                />
                Audit API
              </label>
            </div>
            <div className={styles.formActions}>
              <button type="submit" className={styles.actionButton} disabled={planSaving}>
                {planSaving ? "Saving…" : "Save plan"}
              </button>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setPlanFormOpenFor(null)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className={styles.list}>
          {plans.map((plan) => (
            <div className={styles.row} key={plan.id}>
              <div className={styles.rowMain}>
                <span className={styles.rowName}>{plan.name}</span>
                <span className={styles.rowSlug}>{plan.slug}</span>
              </div>
              <span className={styles.rowPrice}>
                {plan.price_usd !== null ? `$${plan.price_usd}` : "—"} /{" "}
                {plan.price_inr !== null ? `₹${plan.price_inr}` : "—"}
              </span>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => openEditPlanForm(plan)}
              >
                Edit
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.header}>
          <h2 className={styles.headerTitle}>Credit packs</h2>
          <button type="button" className={styles.actionButton} onClick={openNewPackForm}>
            + New pack
          </button>
        </div>

        {packFormOpenFor && (
          <form onSubmit={handlePackSubmit} className={styles.form}>
            <div className={styles.formHeading}>
              {packFormOpenFor === "new" ? "New credit pack" : `Edit ${packFormOpenFor}`}
            </div>
            <div className={styles.fieldGrid}>
              {packFormOpenFor === "new" && (
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="pack-slug">
                    Slug
                  </label>
                  <input
                    id="pack-slug"
                    className={styles.input}
                    required
                    value={packForm.slug}
                    onChange={(event) => setPackForm({ ...packForm, slug: event.target.value })}
                    placeholder="e.g. ai_runs_500"
                  />
                </div>
              )}
              <div className={styles.field}>
                <label className={styles.label} htmlFor="pack-name">
                  Name
                </label>
                <input
                  id="pack-name"
                  className={styles.input}
                  required
                  value={packForm.name}
                  onChange={(event) => setPackForm({ ...packForm, name: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="pack-credit-type">
                  Credit type
                </label>
                <select
                  id="pack-credit-type"
                  className={styles.select}
                  value={packForm.credit_type}
                  onChange={(event) =>
                    setPackForm({
                      ...packForm,
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
              <div className={styles.field}>
                <label className={styles.label} htmlFor="pack-credits">
                  Credits
                </label>
                <input
                  id="pack-credits"
                  className={styles.input}
                  type="number"
                  required
                  min={1}
                  value={packForm.credits}
                  onChange={(event) => setPackForm({ ...packForm, credits: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="pack-price-usd">
                  Price (USD, blank = not available)
                </label>
                <input
                  id="pack-price-usd"
                  className={styles.input}
                  type="number"
                  value={packForm.price_usd}
                  onChange={(event) => setPackForm({ ...packForm, price_usd: event.target.value })}
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label} htmlFor="pack-price-inr">
                  Price (INR, blank = not available)
                </label>
                <input
                  id="pack-price-inr"
                  className={styles.input}
                  type="number"
                  value={packForm.price_inr}
                  onChange={(event) => setPackForm({ ...packForm, price_inr: event.target.value })}
                />
              </div>
            </div>
            <div className={styles.checkboxRow}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={packForm.is_active}
                  onChange={(event) =>
                    setPackForm({ ...packForm, is_active: event.target.checked })
                  }
                />
                Active (purchasable)
              </label>
            </div>
            <div className={styles.formActions}>
              <button type="submit" className={styles.actionButton} disabled={packSaving}>
                {packSaving ? "Saving…" : "Save pack"}
              </button>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => setPackFormOpenFor(null)}
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className={styles.list}>
          {packs.map((pack) => (
            <div className={styles.row} key={pack.id}>
              <div className={styles.rowMain}>
                <span className={styles.rowName}>{pack.name}</span>
                <span className={styles.rowSlug}>
                  {pack.slug} · {pack.credit_type}
                  {!pack.is_active && " · inactive"}
                </span>
              </div>
              <span className={styles.rowPrice}>
                {pack.price_usd !== null ? `$${pack.price_usd}` : "—"} /{" "}
                {pack.price_inr !== null ? `₹${pack.price_inr}` : "—"}
              </span>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => openEditPackForm(pack)}
              >
                Edit
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
