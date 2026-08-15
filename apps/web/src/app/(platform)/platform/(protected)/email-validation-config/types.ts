export type EmailValidationProvider = "CLEAROUT";

export interface PlatformEmailValidationProviderConfig {
  id: string;
  provider: EmailValidationProvider;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderDefinition {
  key: EmailValidationProvider;
  displayName: string;
}

// Add a new entry here (and a matching backend adapter under
// email_validation/providers/) when a second vendor is actually built -- not before,
// per this codebase's "extend when built" discipline (see AI/email provider configs).
export const PROVIDER_DEFINITIONS: ProviderDefinition[] = [
  { key: "CLEAROUT", displayName: "Clearout.io" },
];
