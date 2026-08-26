"use client";

import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { useToast } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { AIPreviewTab } from "./components/ai-preview-tab";
import { BrandVoiceTab } from "./components/brand-voice-tab";
import { CompanyProfileTab } from "./components/company-profile-tab";
import { GuardrailsTab } from "./components/guardrails-tab";
import { ProfileReadiness } from "./components/profile-readiness";
import { type SettingsTab, SettingsTabs } from "./components/settings-tabs";
import { StickySaveBar } from "./components/sticky-save-bar";
import styles from "./company-settings-form.module.css";
import type { BrandProfile, CompanyProfile, MeResponse, VoiceSettings } from "./types";

const EDIT_PERMISSION = "company.settings.edit";

export interface CompanyDraft {
  name: string;
  website: string;
  industry: string;
  timezone: string;
  default_language: string;
  legal_footer: string;
  business_address: string;
  description: string;
  support_email: string;
  sender_name: string;
  logo_url: string;
}

export interface BrandDraft {
  brand_voice: string;
  forbidden_claims: string[];
  required_facts: string[];
  persona_tags: string[];
  voice_settings: VoiceSettings;
}

const EMPTY_COMPANY: CompanyDraft = {
  name: "",
  website: "",
  industry: "",
  timezone: "Asia/Kolkata",
  default_language: "en",
  legal_footer: "",
  business_address: "",
  description: "",
  support_email: "",
  sender_name: "",
  logo_url: "",
};

const EMPTY_BRAND: BrandDraft = {
  brand_voice: "",
  forbidden_claims: [],
  required_facts: [],
  persona_tags: [],
  voice_settings: {},
};

const TABS: SettingsTab[] = [
  { id: "company-profile", label: "Company Profile" },
  { id: "brand-voice", label: "Brand Voice" },
  { id: "ai-guardrails", label: "AI Guardrails" },
  { id: "ai-preview", label: "AI Preview" },
];

function companyToDraft(profile: CompanyProfile): CompanyDraft {
  return {
    name: profile.name,
    website: profile.website ?? "",
    industry: profile.industry ?? "",
    timezone: profile.timezone ?? "Asia/Kolkata",
    default_language: profile.default_language,
    legal_footer: profile.legal_footer ?? "",
    business_address: profile.business_address ?? "",
    description: profile.description ?? "",
    support_email: profile.support_email ?? "",
    sender_name: profile.sender_name ?? "",
    logo_url: profile.logo_url ?? "",
  };
}

function brandToDraft(profile: BrandProfile): BrandDraft {
  return {
    brand_voice: profile.brand_voice ?? "",
    forbidden_claims: profile.forbidden_claims,
    required_facts: profile.required_facts,
    persona_tags: profile.persona_tags,
    voice_settings: profile.voice_settings,
  };
}

function cleanList(items: string[]): string[] {
  return items.map((item) => item.trim()).filter((item) => item.length > 0);
}

export function CompanySettingsForm() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [canEdit, setCanEdit] = useState(false);
  const [activeTab, setActiveTab] = useState(TABS[0]!.id);
  const [saving, setSaving] = useState(false);

  const [savedCompany, setSavedCompany] = useState<CompanyProfile | null>(null);
  const [savedBrand, setSavedBrand] = useState<BrandProfile | null>(null);
  const [contactDetails, setContactDetails] = useState<Record<string, unknown>>({});

  const [company, setCompany] = useState<CompanyDraft>(EMPTY_COMPANY);
  const [brand, setBrand] = useState<BrandDraft>(EMPTY_BRAND);
  const [initialCompany, setInitialCompany] = useState<CompanyDraft>(EMPTY_COMPANY);
  const [initialBrand, setInitialBrand] = useState<BrandDraft>(EMPTY_BRAND);

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
          setSavedCompany(companyProfile);
          setContactDetails(companyProfile.contact_details);
          const draft = companyToDraft(companyProfile);
          setCompany(draft);
          setInitialCompany(draft);
        }

        if (brandProfile) {
          setSavedBrand(brandProfile);
          const draft = brandToDraft(brandProfile);
          setBrand(draft);
          setInitialBrand(draft);
        }
      } catch {
        showToast("error", "Could not load company settings.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [showToast]);

  const dirty = useMemo(
    () =>
      JSON.stringify(company) !== JSON.stringify(initialCompany) ||
      JSON.stringify(brand) !== JSON.stringify(initialBrand),
    [company, initialCompany, brand, initialBrand],
  );

  // Warns before closing/refreshing the tab with unsaved edits. In-app client-side
  // navigation isn't guarded (Next.js App Router has no built-in route-leave
  // confirmation hook), so this covers what the current architecture supports.
  useEffect(() => {
    if (!dirty) return;
    function handleBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [dirty]);

  function handleDiscard() {
    setCompany(initialCompany);
    setBrand(initialBrand);
  }

  async function handleSave() {
    setSaving(true);
    try {
      const companyResponse = await apiFetch<CompanyProfile>("/company/profile", {
        method: "PUT",
        body: JSON.stringify({
          name: company.name,
          website: company.website || null,
          industry: company.industry || null,
          timezone: company.timezone || null,
          default_language: company.default_language,
          legal_footer: company.legal_footer || null,
          business_address: company.business_address || null,
          description: company.description || null,
          support_email: company.support_email || null,
          sender_name: company.sender_name || null,
          logo_url: company.logo_url || null,
          contact_details: contactDetails,
        }),
      });

      const brandResponse = await apiFetch<BrandProfile>("/brand/profile", {
        method: "PUT",
        body: JSON.stringify({
          brand_voice: brand.brand_voice || null,
          forbidden_claims: cleanList(brand.forbidden_claims),
          required_facts: cleanList(brand.required_facts),
          persona_tags: brand.persona_tags,
          voice_settings: brand.voice_settings,
        }),
      });

      setSavedCompany(companyResponse);
      setSavedBrand(brandResponse);
      const nextCompanyDraft = companyToDraft(companyResponse);
      const nextBrandDraft = brandToDraft(brandResponse);
      setCompany(nextCompanyDraft);
      setBrand(nextBrandDraft);
      setInitialCompany(nextCompanyDraft);
      setInitialBrand(nextBrandDraft);

      showToast("success", "Settings saved.");
    } catch {
      showToast("error", "Could not save settings. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingCard}>Loading settings…</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <PageHeader
        icon="⚙️"
        title="Company & Brand Settings"
        description="Manage your company profile, brand voice, AI guardrails, and how Growixa represents your organization."
        actions={<ProfileReadiness company={savedCompany} brand={savedBrand} />}
      />

      {!canEdit && (
        <p className={styles.readOnlyNote}>You have view-only access to company settings.</p>
      )}

      <SettingsTabs tabs={TABS} activeTab={activeTab} onChange={setActiveTab} />

      <div role="tabpanel" id={`tabpanel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
        {activeTab === "company-profile" && (
          <CompanyProfileTab company={company} canEdit={canEdit} onChange={setCompany} />
        )}
        {activeTab === "brand-voice" && (
          <BrandVoiceTab brand={brand} canEdit={canEdit} onChange={setBrand} />
        )}
        {activeTab === "ai-guardrails" && (
          <GuardrailsTab brand={brand} canEdit={canEdit} onChange={setBrand} />
        )}
        {activeTab === "ai-preview" && (
          <AIPreviewTab forbiddenClaims={cleanList(brand.forbidden_claims)} />
        )}
      </div>

      {canEdit && (
        <StickySaveBar
          dirty={dirty}
          saving={saving}
          onDiscard={handleDiscard}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
