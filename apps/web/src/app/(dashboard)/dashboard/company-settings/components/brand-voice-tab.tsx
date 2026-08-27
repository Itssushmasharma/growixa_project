import formStyles from "../company-settings-form.module.css";
import type { BrandDraft } from "../company-settings-form";
import type { VoiceSettings } from "../types";
import { BrandPersonaSelector } from "./brand-persona-selector";
import { BrandVoiceSlider } from "./brand-voice-slider";
import styles from "./components.module.css";
import { SettingsCard } from "./settings-card";

const DESCRIPTION_MAX_LENGTH = 800;

const SLIDERS: Array<{
  key: keyof VoiceSettings;
  label: string;
  left: string;
  right: string;
}> = [
  { key: "formality", label: "Formality", left: "Casual", right: "Professional" },
  { key: "energy", label: "Energy", left: "Calm", right: "Energetic" },
  { key: "technical_depth", label: "Technical Depth", left: "Basic", right: "Advanced" },
  { key: "sales_style", label: "Sales Style", left: "Informative", right: "Persuasive" },
];

interface BrandVoiceTabProps {
  brand: BrandDraft;
  canEdit: boolean;
  onChange: (next: BrandDraft) => void;
}

export function BrandVoiceTab({ brand, canEdit, onChange }: BrandVoiceTabProps) {
  function togglePersona(persona: string) {
    if (!canEdit) return;
    const next = brand.persona_tags.includes(persona)
      ? brand.persona_tags.filter((tag) => tag !== persona)
      : [...brand.persona_tags, persona];
    onChange({ ...brand, persona_tags: next });
  }

  function setSlider(key: keyof VoiceSettings, value: number) {
    onChange({ ...brand, voice_settings: { ...brand.voice_settings, [key]: value } });
  }

  return (
    <div className={formStyles.tabStack}>
      <SettingsCard
        icon="🗣️"
        title="Brand Persona"
        subtitle="Select the traits that describe your brand — used to steer AI-generated copy."
      >
        <BrandPersonaSelector
          selected={brand.persona_tags}
          disabled={!canEdit}
          onToggle={togglePersona}
        />
      </SettingsCard>

      <SettingsCard icon="🎚️" title="Voice Controls" subtitle="Fine-tune how AI copy should sound.">
        <div className={styles.sliderGroup}>
          {SLIDERS.map((slider) => (
            <BrandVoiceSlider
              key={slider.key}
              id={`voice-slider-${slider.key}`}
              label={slider.label}
              leftLabel={slider.left}
              rightLabel={slider.right}
              value={brand.voice_settings[slider.key] ?? 50}
              disabled={!canEdit}
              onChange={(value) => setSlider(slider.key, value)}
            />
          ))}
        </div>
      </SettingsCard>

      <SettingsCard
        icon="✍️"
        title="Brand Persona Description"
        subtitle="Describe the tone, vocabulary, and personality for AI copy in your own words."
      >
        <div className={formStyles.field}>
          <label className={formStyles.label} htmlFor="brand-voice">
            Persona Description
          </label>
          <textarea
            id="brand-voice"
            className={formStyles.textarea}
            disabled={!canEdit}
            maxLength={DESCRIPTION_MAX_LENGTH}
            placeholder="Our brand tone is professional yet approachable, bold, confident, and focused on clear ROI for founders."
            value={brand.brand_voice}
            onChange={(event) => onChange({ ...brand, brand_voice: event.target.value })}
          />
          <div className={styles.previewMetaRow}>
            <span className={formStyles.hint}>
              Combine with the persona chips above for the strongest AI guidance.
            </span>
            <span className={formStyles.hint}>
              {brand.brand_voice.length}/{DESCRIPTION_MAX_LENGTH}
            </span>
          </div>
        </div>
      </SettingsCard>
    </div>
  );
}
