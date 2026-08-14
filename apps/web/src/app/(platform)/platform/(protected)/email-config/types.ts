export type EmailProvider = "POSTMARK" | "CUSTOM_SMTP";

export interface PlatformEmailProviderConfig {
  id: string;
  provider: EmailProvider;
  smtp_host: string;
  smtp_port: number;
  smtp_username: string;
  from_email: string;
  from_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderDefinition {
  key: EmailProvider;
  displayName: string;
  // Postmark is just SMTP pointed at its own relay with the server token as both
  // username and password -- no separate code path exists for it anywhere in this
  // codebase, so the form only pre-fills the host as a convenience.
  defaultHost: string;
  defaultPort: number;
}

export const PROVIDER_DEFINITIONS: ProviderDefinition[] = [
  {
    key: "POSTMARK",
    displayName: "Postmark",
    defaultHost: "smtp.postmarkapp.com",
    defaultPort: 587,
  },
  {
    key: "CUSTOM_SMTP",
    displayName: "Custom SMTP",
    defaultHost: "",
    defaultPort: 587,
  },
];
