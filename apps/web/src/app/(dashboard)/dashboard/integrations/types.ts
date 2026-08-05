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
