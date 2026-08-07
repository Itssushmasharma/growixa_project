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
  timezone: "Asia/Kolkata",
  default_language: "en",
  legal_footer: "",
};

const EMPTY_BRAND: BrandFormState = {
  brand_voice: "",
  forbidden_claims: "",
  required_facts: "",
};

const COMMON_TIMEZONES = [
  "Asia/Kolkata",
  "America/New_York",
  "America/Los_Angeles",
  "America/Chicago",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Dubai",
  "UTC",
];

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
            timezone: companyProfile.timezone ?? "Asia/Kolkata",
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

  function handleAppendTone(tone: string) {
    if (!canEdit) return;
    setBrand((current) => ({
      ...current,
      brand_voice: current.brand_voice
        ? `${current.brand_voice}, ${tone.toLowerCase()}`
        : `Our brand tone is ${tone.toLowerCase()}`,
    }));
  }

  if (loading) {
    return <div className={styles.card}>Loading settings…</div>;
  }

  const readinessPercent = brand.brand_voice.length > 20 ? 100 : brand.brand_voice ? 60 : 30;

  return (
    <div className={styles.page}>
      {/* AI Readiness Banner */}
      <div className={styles.readinessCard}>
        <div className={styles.readinessContent}>
          <span className={styles.readinessBadge}>🤖 AI Brand Voice Profile</span>
          <h3 className={styles.readinessTitle}>Company Identity &amp; AI Copy Guidelines</h3>
          <p className={styles.readinessSubtitle}>
            Configure your brand voice, legal compliance disclosures, forbidden claims, and required
            facts. Growixa AI Assistant enforces these guidelines on every generated campaign and
            email.
          </p>
        </div>
        <div className={styles.readinessStat}>
          <span className={styles.readinessPercent}>{readinessPercent}%</span>
          <span className={styles.readinessLabel}>Profile Readiness</span>
        </div>
      </div>

      {!canEdit && (
        <p className={styles.readOnlyNote}>You have view-only access to company settings.</p>
      )}

      <form onSubmit={handleSubmit} className={styles.page}>
        <div className={styles.formGrid}>
          {/* Card A: General Company Profile */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardHeaderIcon}>🏢</span>
              <div>
                <h3 className={styles.cardHeaderTitle}>Company Profile</h3>
                <p className={styles.cardHeaderSubtitle}>
                  Primary company details used for footers &amp; CAN-SPAM compliance.
                </p>
              </div>
            </div>

            <div className={styles.inputGrid}>
              <div className={`${styles.field} ${styles.fullWidth}`}>
                <label className={styles.label} htmlFor="company-name">
                  Company Name *
                </label>
                <input
                  id="company-name"
                  className={styles.input}
                  required
                  disabled={!canEdit}
                  placeholder="e.g. Growixa Inc."
                  value={company.name}
                  onChange={(event) => setCompany({ ...company, name: event.target.value })}
                />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="company-website">
                  Website URL
                </label>
                <input
                  id="company-website"
                  type="url"
                  className={styles.input}
                  disabled={!canEdit}
                  placeholder="https://example.com"
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
                  placeholder="e.g. SaaS / E-commerce"
                  value={company.industry}
                  onChange={(event) => setCompany({ ...company, industry: event.target.value })}
                />
              </div>

              <div className={`${styles.field} ${styles.fullWidth}`}>
                <label className={styles.label} htmlFor="company-timezone">
                  Timezone
                </label>
                <select
                  id="company-timezone"
                  className={styles.select}
                  disabled={!canEdit}
                  value={company.timezone}
                  onChange={(event) => setCompany({ ...company, timezone: event.target.value })}
                >
                  {COMMON_TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>
                      {tz}
                    </option>
                  ))}
                  {!COMMON_TIMEZONES.includes(company.timezone) && company.timezone && (
                    <option value={company.timezone}>{company.timezone}</option>
                  )}
                </select>
              </div>

              <div className={`${styles.field} ${styles.fullWidth}`}>
                <label className={styles.label} htmlFor="company-legal-footer">
                  Legal Address &amp; Unsubscribe Footer
                </label>
                <textarea
                  id="company-legal-footer"
                  className={styles.textarea}
                  disabled={!canEdit}
                  placeholder="123 Growth Way, San Francisco, CA 94107 · All rights reserved."
                  value={company.legal_footer}
                  onChange={(event) => setCompany({ ...company, legal_footer: event.target.value })}
                />
                <p className={styles.hint}>
                  Appears automatically in campaign footer templates to satisfy anti-spam
                  regulations.
                </p>
              </div>
            </div>
          </div>

          {/* Column 2: Brand Voice & AI Rules */}
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Card B: Brand Persona */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardHeaderIcon}>🗣️</span>
                <div>
                  <h3 className={styles.cardHeaderTitle}>AI Brand Voice &amp; Persona</h3>
                  <p className={styles.cardHeaderSubtitle}>
                    Describe the tone, vocabulary, and personality for AI copy.
                  </p>
                </div>
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="brand-voice">
                  Brand Persona Description
                </label>
                <textarea
                  id="brand-voice"
                  className={styles.textarea}
                  disabled={!canEdit}
                  placeholder="Our brand tone is professional yet approachable, bold, confident, and focused on clear ROI for founders."
                  value={brand.brand_voice}
                  onChange={(event) => setBrand({ ...brand, brand_voice: event.target.value })}
                />
                <div className={styles.chipGroup}>
                  <span className={styles.hint}>Add tone helpers:</span>
                  {["Professional", "Friendly", "Authoritative", "Innovative", "Casual"].map(
                    (tone) => (
                      <button
                        key={tone}
                        type="button"
                        className={styles.chip}
                        disabled={!canEdit}
                        onClick={() => handleAppendTone(tone)}
                      >
                        + {tone}
                      </button>
                    ),
                  )}
                </div>
              </div>
            </div>

            {/* Card C: AI Compliance & Guardrails */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.cardHeaderIcon}>🛡️</span>
                <div>
                  <h3 className={styles.cardHeaderTitle}>Compliance &amp; AI Guardrails</h3>
                  <p className={styles.cardHeaderSubtitle}>
                    Strict boundaries AI content must avoid or always include.
                  </p>
                </div>
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="brand-forbidden-claims">
                  Forbidden Claims (Never say)
                </label>
                <textarea
                  id="brand-forbidden-claims"
                  className={styles.textarea}
                  disabled={!canEdit}
                  placeholder="Guaranteed 100% ROI&#10;No risk involved&#10;Instant results"
                  value={brand.forbidden_claims}
                  onChange={(event) => setBrand({ ...brand, forbidden_claims: event.target.value })}
                />
                <p className={styles.hint}>Enter one claim per line.</p>
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor="brand-required-facts">
                  Required Disclosures &amp; Key Facts
                </label>
                <textarea
                  id="brand-required-facts"
                  className={styles.textarea}
                  disabled={!canEdit}
                  placeholder="ISO 27001 Certified&#10;24/7 Priority Support included"
                  value={brand.required_facts}
                  onChange={(event) => setBrand({ ...brand, required_facts: event.target.value })}
                />
                <p className={styles.hint}>Enter one fact per line.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Save Bar */}
        {canEdit && (
          <div className={styles.actionsBar}>
            <button type="submit" className={styles.submit} disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}
