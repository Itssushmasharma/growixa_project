export type AIProvider = "OPENAI" | "AZURE_OPENAI" | "ANTHROPIC" | "OLLAMA";

export interface PlatformAIProviderConfig {
  id: string;
  provider: AIProvider;
  base_url: string | null;
  default_model: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderDefinition {
  key: AIProvider;
  displayName: string;
  // AZURE_OPENAI/OLLAMA have no fixed official endpoint -- both require an admin-
  // supplied base_url, validated server-side (DEC-GRX-027). OPENAI/ANTHROPIC default to
  // their official endpoints; base_url is an optional OpenAI-compatible override for
  // OPENAI only (e.g. a third-party endpoint), not exposed as a required field here.
  requiresBaseUrl: boolean;
  modelPlaceholder: string;
}

export const PROVIDER_DEFINITIONS: ProviderDefinition[] = [
  {
    key: "OPENAI",
    displayName: "OpenAI",
    requiresBaseUrl: false,
    modelPlaceholder: "gpt-4o-mini",
  },
  {
    key: "ANTHROPIC",
    displayName: "Anthropic",
    requiresBaseUrl: false,
    modelPlaceholder: "claude-sonnet-4-5",
  },
  {
    key: "AZURE_OPENAI",
    displayName: "Azure OpenAI",
    requiresBaseUrl: true,
    modelPlaceholder: "your-deployment-name",
  },
  {
    key: "OLLAMA",
    displayName: "Ollama",
    requiresBaseUrl: true,
    modelPlaceholder: "llama3",
  },
];
