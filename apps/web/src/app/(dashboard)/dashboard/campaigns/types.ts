export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export type RecipientType = "SEGMENT" | "LIST" | "ALL_CONTACTS";
export type CampaignStatus = "DRAFT" | "SENDING" | "SENT" | "FAILED";

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
  created_at: string;
  updated_at: string;
  sent_at: string | null;
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
  bounced: number;
  complained: number;
}
