import formStyles from "../company-settings-form.module.css";
import { AICopyPreview } from "./ai-copy-preview";
import { SettingsCard } from "./settings-card";

interface AIPreviewTabProps {
  forbiddenClaims: string[];
}

export function AIPreviewTab({ forbiddenClaims }: AIPreviewTabProps) {
  return (
    <div className={formStyles.tabStack}>
      <SettingsCard
        icon="🤖"
        title="AI Copy Preview"
        subtitle="See how your current brand configuration affects generated content."
      >
        <AICopyPreview forbiddenClaims={forbiddenClaims} />
      </SettingsCard>
    </div>
  );
}
