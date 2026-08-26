import formStyles from "../company-settings-form.module.css";
import type { BrandDraft } from "../company-settings-form";
import { GuardrailList } from "./guardrail-list";
import { SettingsCard } from "./settings-card";

interface GuardrailsTabProps {
  brand: BrandDraft;
  canEdit: boolean;
  onChange: (next: BrandDraft) => void;
}

export function GuardrailsTab({ brand, canEdit, onChange }: GuardrailsTabProps) {
  return (
    <div className={formStyles.tabStack}>
      <SettingsCard
        icon="🛡️"
        title="Forbidden Claims"
        subtitle="Strict boundaries — AI-generated content must never say these things."
      >
        <GuardrailList
          title="Forbidden Claims"
          addLabel="Add claim"
          icon="forbidden"
          items={brand.forbidden_claims}
          disabled={!canEdit}
          emptyHint="No forbidden claims yet — add one to start guarding AI output."
          onChange={(items) => onChange({ ...brand, forbidden_claims: items })}
        />
      </SettingsCard>

      <SettingsCard
        icon="✅"
        title="Required Facts"
        subtitle="Facts and disclosures AI-generated content should include when relevant."
      >
        <GuardrailList
          title="Required Facts"
          addLabel="Add fact"
          icon="required"
          items={brand.required_facts}
          disabled={!canEdit}
          emptyHint="No required facts yet — add one to start guiding AI output."
          onChange={(items) => onChange({ ...brand, required_facts: items })}
        />
      </SettingsCard>
    </div>
  );
}
