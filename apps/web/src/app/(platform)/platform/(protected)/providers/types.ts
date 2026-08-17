import type { PlatformAIProviderConfig } from "../ai-config/types";
import type { PlatformEmailProviderConfig } from "../email-config/types";
import type { PlatformEmailValidationProviderConfig } from "../email-validation-config/types";

export interface ProvidersState {
  ai: PlatformAIProviderConfig | null;
  email: PlatformEmailProviderConfig | null;
  validation: PlatformEmailValidationProviderConfig | null;
}

export type ConnectionStatus = "idle" | "testing" | "success" | "failed";

export interface ProviderHealthState {
  ai: { status: ConnectionStatus; message?: string };
  email: { status: ConnectionStatus; message?: string };
  validation: { status: ConnectionStatus; message?: string };
}
