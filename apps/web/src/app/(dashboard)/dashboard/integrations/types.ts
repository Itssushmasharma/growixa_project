export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

// GRX-EMAIL-011: Postmark plus a generic Custom SMTP provider. Deliberately just these
// two — both are SMTP-relay-based, so no new sending code path is needed. Other
// providers (SendGrid, Resend, AWS SES, Mailgun) aren't listed here at all, since this
// codebase's convention is to not build UI for capabilities that don't exist yet.
export type EmailProvider = "POSTMARK" | "CUSTOM_SMTP";

export interface EmailProviderConnection {
  id: string;
  provider: EmailProvider;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  webhook_username: string | null;
  // Only present on the create response — never returned by GET, never persisted
  // in plaintext, never retrievable again after this one reveal.
  webhook_password?: string | null;
}

export type VerificationStatus = "PENDING" | "VERIFIED" | "FAILED";

export interface SenderIdentity {
  id: string;
  email_provider_connection_id: string;
  from_email: string;
  from_name: string;
  reply_to_email: string | null;
  verification_status: VerificationStatus;
  created_at: string;
  updated_at: string;
}

export interface ProviderDefinition {
  key: EmailProvider;
  displayName: string;
  description: string;
  defaultHost: string;
  defaultPort: string;
  // Postmark's webhook receiver (/webhooks/postmark) is provider-specific — plain SMTP
  // has no bounce/complaint/open/click callback mechanism, so Custom SMTP never gets one.
  hasWebhook: boolean;
}

// Slice 5 (Social Publishing) — Instagram Business, connected via OAuth rather than a
// form (see integrations-page.tsx's Instagram card). Not part of PROVIDER_REGISTRY
// since that registry is SMTP-relay-specific.
export interface SocialConnection {
  id: string;
  provider: string;
  ig_business_account_id: string;
  ig_username: string | null;
  facebook_page_id: string;
  is_active: boolean;
  last_connected_at: string;
  last_error: string | null;
}

// Slice 6 (AI Assistant) -- account-level bring-your-own AI provider connection (see
// integrations-page.tsx's "AI Model Provider" card). Mirrors the platform-admin
// ai-config page's own copy of this same shape (DEC-GRX-026: both are the exact same
// {provider, api_key, base_url, default_model} config, one platform-wide, one per
// account). An account brings *one* model at a time, so this is a single optional
// connection, not a per-provider registry like PROVIDER_REGISTRY above.
export type AIProvider = "OPENAI" | "AZURE_OPENAI" | "ANTHROPIC" | "OLLAMA";

export interface AIProviderConnection {
  id: string;
  provider: AIProvider;
  base_url: string | null;
  default_model: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AIProviderDefinition {
  key: AIProvider;
  displayName: string;
  requiresBaseUrl: boolean;
  modelPlaceholder: string;
}

export const AI_PROVIDER_DEFINITIONS: AIProviderDefinition[] = [
  { key: "OPENAI", displayName: "OpenAI", requiresBaseUrl: false, modelPlaceholder: "gpt-4o-mini" },
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
  { key: "OLLAMA", displayName: "Ollama", requiresBaseUrl: true, modelPlaceholder: "llama3" },
];

export const PROVIDER_REGISTRY: ProviderDefinition[] = [
  {
    key: "POSTMARK",
    displayName: "Postmark",
    description: "Sends campaign email via Postmark's SMTP relay.",
    defaultHost: "smtp.postmarkapp.com",
    defaultPort: "587",
    hasWebhook: true,
  },
  {
    key: "CUSTOM_SMTP",
    displayName: "Custom SMTP",
    description: "Any SMTP relay you already have credentials for.",
    defaultHost: "",
    defaultPort: "587",
    hasWebhook: false,
  },
];
