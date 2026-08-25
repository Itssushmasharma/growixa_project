export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export type RecipientType = "SEGMENT" | "LIST" | "ALL_CONTACTS";
export type CampaignStatus =
  "DRAFT" | "SCHEDULED" | "DISPATCHING" | "SENDING" | "SENT" | "CANCELLED" | "FAILED";

export interface Campaign {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  body_text: string | null;
  template_id: string | null;
  sender_identity_id: string;
  recipient_type: RecipientType;
  recipient_segment_id: string | null;
  recipient_list_id: string | null;
  status: CampaignStatus;
  scheduled_at: string | null;
  cancelled_at: string | null;
  idempotency_key: string; // NOT NULL in DB — always returned
  created_at: string;
  updated_at: string;
  sent_at: string | null;
  sent_count?: number | null;
  delivered_count?: number | null;
  opened_count?: number | null;
  clicked_count?: number | null;
  total_opened_count?: number | null;
  total_clicked_count?: number | null;
  open_rate_pct?: number | null;
  click_rate_pct?: number | null;
  click_to_open_rate_pct?: number | null;
}

export interface SenderIdentity {
  id: string;
  email_provider_connection_id: string;
  from_email: string;
  from_name: string;
  reply_to_email: string | null;
  verification_status: string;
}

export interface ContactListSummary {
  id: string;
  name: string;
  member_count: number;
}

export interface SegmentSummary {
  id: string;
  name: string;
  member_count: number;
}

export interface CampaignReport {
  campaign_id: string;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  total_opened?: number;
  total_clicked?: number;
  open_rate_pct?: number | null;
  click_rate_pct?: number | null;
  click_to_open_rate_pct?: number | null;
  bounced: number;
  complained: number;
}
