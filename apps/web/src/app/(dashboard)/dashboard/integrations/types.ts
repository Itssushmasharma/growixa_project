export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface EmailProviderConnection {
  id: string;
  provider: string;
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
