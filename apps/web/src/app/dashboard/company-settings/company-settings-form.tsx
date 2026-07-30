"use client";

import { type FormEvent, useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import styles from "./company-settings-form.module.css";
import type { BrandProfile, CompanyProfile, MeResponse } from "./types";

const EDIT_PERMISSION = "company.settings.edit";

interface CompanyFormState {
  name: string;
  website: string;
  industry: string;
  timezone: string;
  default_language: string;
  legal_footer: string;
}

interface BrandFormState {
  brand_voice: string;
  forbidden_claims: string;
  required_facts: string;
}

const EMPTY_COMPANY: CompanyFormState = {
  name: "",
  website: "",
  industry: "",
  timezone: "",
  default_language: "en",
  legal_footer: "",
};

const EMPTY_BRAND: BrandFormState = {
  brand_voice: "",
  forbidden_claims: "",
  required_facts: "",
};

function linesToList(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

export function CompanySettingsForm() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [canEdit, setCanEdit] = useState(false);
  const [company, setCompany] = useState<CompanyFormState>(EMPTY_COMPANY);
  const [brand, setBrand] = useState<BrandFormState>(EMPTY_BRAND);
  const [contactDetails, setContactDetails] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [me, companyProfile, brandProfile] = await Promise.all([
          apiFetch<MeResponse>("/auth/me"),
          apiFetch<CompanyProfile | null>("/company/profile"),
          apiFetch<BrandProfile | null>("/brand/profile"),
        ]);

        setCanEdit(me.permissions.includes(EDIT_PERMISSION));

        if (companyProfile) {
          setCompany({
            name: companyProfile.name,
            website: companyProfile.website ?? "",
            industry: companyProfile.industry ?? "",
            timezone: companyProfile.timezone ?? "",
            default_language: companyProfile.default_language,
            legal_footer: companyProfile.legal_footer ?? "",
          });
          setContactDetails(companyProfile.contact_details);
        }

        if (brandProfile) {
          setBrand({
            brand_voice: brandProfile.brand_voice ?? "",
            forbidden_claims: brandProfile.forbidden_claims.join("\n"),
            required_facts: brandProfile.required_facts.join("\n"),
          });
        }
      } catch {
        showToast("error", "Could not load company settings.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [showToast]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);

    try {
      await apiFetch<CompanyProfile>("/company/profile", {
        method: "PUT",
        body: JSON.stringify({
          name: company.name,
          website: company.website || null,
          industry: company.industry || null,
          timezone: company.timezone || null,
          default_language: company.default_language,
          legal_footer: company.legal_footer || null,
          contact_details: contactDetails,
        }),
      });

      await apiFetch<BrandProfile>("/brand/profile", {
        method: "PUT",
        body: JSON.stringify({
          brand_voice: brand.brand_voice || null,
          forbidden_claims: linesToList(brand.forbidden_claims),
          required_facts: linesToList(brand.required_facts),
        }),
      });

      showToast("success", "Settings saved.");
    } catch {
      showToast("error", "Could not save settings. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  return (
    <div className={styles.card}>
      {!canEdit && (
        <p className={styles.readOnlyNote}>You have view-only access to company settings.</p>
      )}

      <form onSubmit={handleSubmit}>
        <h2 className={styles.sectionHeading}>Company profile</h2>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="company-name">
            Company name
          </label>
          <input
            id="company-name"
            className={styles.input}
            required
            disabled={!canEdit}
            value={company.name}
            onChange={(event) => setCompany({ ...company, name: event.target.value })}
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="company-website">
            Website
          </label>
          <input
            id="company-website"
            className={styles.input}
            disabled={!canEdit}
            value={company.website}
            onChange={(event) => setCompany({ ...company, website: event.target.value })}
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="company-industry">
            Industry
          </label>
          <input
            id="company-industry"
            className={styles.input}
            disabled={!canEdit}
            value={company.industry}
            onChange={(event) => setCompany({ ...company, industry: event.target.value })}
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="company-timezone">
            Timezone
          </label>
          <input
            id="company-timezone"
            className={styles.input}
            disabled={!canEdit}
            placeholder="e.g. Asia/Kolkata"
            value={company.timezone}
            onChange={(event) => setCompany({ ...company, timezone: event.target.value })}
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="company-legal-footer">
            Legal footer
          </label>
          <textarea
            id="company-legal-footer"
            className={styles.textarea}
            disabled={!canEdit}
            value={company.legal_footer}
            onChange={(event) => setCompany({ ...company, legal_footer: event.target.value })}
          />
        </div>

        <h2 className={styles.sectionHeading}>Brand voice</h2>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="brand-voice">
            Brand voice
          </label>
          <textarea
            id="brand-voice"
            className={styles.textarea}
            disabled={!canEdit}
            placeholder="Describe the tone and style AI-generated content should follow."
            value={brand.brand_voice}
            onChange={(event) => setBrand({ ...brand, brand_voice: event.target.value })}
          />
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="brand-forbidden-claims">
            Forbidden claims
          </label>
          <textarea
            id="brand-forbidden-claims"
            className={styles.textarea}
            disabled={!canEdit}
            value={brand.forbidden_claims}
            onChange={(event) => setBrand({ ...brand, forbidden_claims: event.target.value })}
          />
          <p className={styles.hint}>One per line.</p>
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="brand-required-facts">
            Required facts
          </label>
          <textarea
            id="brand-required-facts"
            className={styles.textarea}
            disabled={!canEdit}
            value={brand.required_facts}
            onChange={(event) => setBrand({ ...brand, required_facts: event.target.value })}
          />
          <p className={styles.hint}>One per line.</p>
        </div>

        {canEdit && (
          <button type="submit" className={styles.submit} disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </button>
        )}
      </form>
    </div>
  );
}
