export type CampaignOversightStatus = "SCHEDULED" | "DISPATCHING" | "SENDING" | "FAILED";

export interface CampaignOversightItem {
  id: string;
  account_id: string;
  account_name: string;
  name: string;
  status: CampaignOversightStatus;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
}
