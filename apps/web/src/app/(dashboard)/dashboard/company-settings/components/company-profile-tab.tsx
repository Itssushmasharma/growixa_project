import formStyles from "../company-settings-form.module.css";
import type { CompanyDraft } from "../company-settings-form";
import { LogoUploader } from "./logo-uploader";
import styles from "./components.module.css";
import { SettingsCard } from "./settings-card";

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

const DESCRIPTION_MAX_LENGTH = 600;

interface CompanyProfileTabProps {
  company: CompanyDraft;
  canEdit: boolean;
  onChange: (next: CompanyDraft) => void;
}

export function CompanyProfileTab({ company, canEdit, onChange }: CompanyProfileTabProps) {
  function set<K extends keyof CompanyDraft>(key: K, value: CompanyDraft[K]) {
    onChange({ ...company, [key]: value });
  }

  return (
    <div className={formStyles.tabStack}>
      <SettingsCard
        icon="🏢"
        title="Company Information"
        subtitle="Primary company details used across the product and in campaign footers."
      >
        <div className={formStyles.inputGrid}>
          <div className={formStyles.field}>
            <label className={formStyles.label} htmlFor="company-name">
              Company Name *
            </label>
            <input
              id="company-name"
              className={formStyles.input}
              required
              disabled={!canEdit}
              placeholder="e.g. Growixa Inc."
              value={company.name}
              onChange={(event) => set("name", event.target.value)}
            />
          </div>

          <div className={formStyles.field}>
            <label className={formStyles.label} htmlFor="company-website">
              Website URL
            </label>
            <input
              id="company-website"
              type="url"
              className={formStyles.input}
              disabled={!canEdit}
              placeholder="https://example.com"
              value={company.website}
              onChange={(event) => set("website", event.target.value)}
            />
          </div>

          <div className={formStyles.field}>
            <label className={formStyles.label} htmlFor="company-industry">
              Industry
            </label>
            <input
              id="company-industry"
              className={formStyles.input}
              disabled={!canEdit}
              placeholder="e.g. SaaS / E-commerce"
              value={company.industry}
              onChange={(event) => set("industry", event.target.value)}
            />
          </div>

          <div className={formStyles.field}>
            <label className={formStyles.label} htmlFor="company-timezone">
              Timezone
            </label>
            <select
              id="company-timezone"
              className={formStyles.select}
              disabled={!canEdit}
              value={company.timezone}
              onChange={(event) => set("timezone", event.target.value)}
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

          <div className={`${formStyles.field} ${formStyles.fullWidth}`}>
            <label className={formStyles.label} htmlFor="company-address">
              Business / Legal Address
            </label>
            <input
              id="company-address"
              className={formStyles.input}
              disabled={!canEdit}
              placeholder="123 Growth Way, San Francisco, CA 94107"
              value={company.business_address}
              onChange={(event) => set("business_address", event.target.value)}
            />
          </div>

          <div className={formStyles.field}>
            <label className={formStyles.label} htmlFor="company-support-email">
              Support Email
            </label>
            <input
              id="company-support-email"
              type="email"
              className={formStyles.input}
              disabled={!canEdit}
              placeholder="support@example.com"
              value={company.support_email}
              onChange={(event) => set("support_email", event.target.value)}
            />
          </div>

          <div className={formStyles.field}>
            <label className={formStyles.label} htmlFor="company-sender-name">
              Default Sender / From Name
            </label>
            <input
              id="company-sender-name"
              className={formStyles.input}
              disabled={!canEdit}
              placeholder="e.g. The Growixa Team"
              value={company.sender_name}
              onChange={(event) => set("sender_name", event.target.value)}
            />
          </div>
        </div>
      </SettingsCard>

      <SettingsCard
        icon="🖼️"
        title="Company Logo"
        subtitle="Shown across the dashboard and in campaign headers."
      >
        <LogoUploader
          logoUrl={company.logo_url}
          disabled={!canEdit}
          onChange={(url) => set("logo_url", url)}
        />
      </SettingsCard>

      <SettingsCard
        icon="📝"
        title="Company Description"
        subtitle="Used by Growixa AI to understand your organization when generating content."
      >
        <div className={formStyles.field}>
          <label className={formStyles.label} htmlFor="company-description">
            What does your company do?
          </label>
          <textarea
            id="company-description"
            className={formStyles.textarea}
            disabled={!canEdit}
            maxLength={DESCRIPTION_MAX_LENGTH}
            placeholder="Growixa helps SMB marketers plan, personalize, and send AI-assisted email campaigns."
            value={company.description}
            onChange={(event) => set("description", event.target.value)}
          />
          <div className={styles.previewMetaRow}>
            <span className={formStyles.hint}>
              A clear description improves AI-generated copy quality.
            </span>
            <span className={formStyles.hint}>
              {company.description.length}/{DESCRIPTION_MAX_LENGTH}
            </span>
          </div>
        </div>
      </SettingsCard>

      <SettingsCard
        icon="📧"
        title="Email Footer & Unsubscribe"
        subtitle="Appears automatically in outbound campaign footers to satisfy anti-spam regulations. Kept separate from your business address above."
      >
        <div className={formStyles.field}>
          <label className={formStyles.label} htmlFor="company-legal-footer">
            Footer / Disclosure Text
          </label>
          <textarea
            id="company-legal-footer"
            className={formStyles.textarea}
            disabled={!canEdit}
            placeholder="© Growixa Inc. · All rights reserved. · Unsubscribe anytime."
            value={company.legal_footer}
            onChange={(event) => set("legal_footer", event.target.value)}
          />
          <p className={formStyles.hint}>
            Used in every outbound campaign, separate from your address.
          </p>
        </div>
      </SettingsCard>
    </div>
  );
}
