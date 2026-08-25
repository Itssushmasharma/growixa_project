export interface QuotaStatus {
  plan_name: string;
  contact_usage: number;
  contact_limit: number | null;
  email_usage: number;
  email_limit: number | null;
  ai_usage: number;
  ai_limit: number | null;
  ai_credits_remaining: number;
}

export interface CampaignStatusBreakdown {
  draft: number;
  scheduled: number;
  sending: number;
  sent: number;
  cancelled: number;
  failed: number;
}

export interface ContactGrowthPoint {
  month: string;
  contacts: number;
}

export interface RecentCampaign {
  id: string;
  name: string;
  status: string;
  sent_count: number;
  open_rate_pct: number | null;
}

export interface ActivityStreamItem {
  id: string;
  event_type: "OPENED" | "CLICKED" | string;
  contact_email: string;
  campaign_id: string;
  campaign_name: string;
  occurred_at: string;
}

export interface DashboardOverview {
  total_contacts: number;
  active_campaigns: number;
  scheduled_social_posts: number;
  email_open_rate_pct: number | null;
  email_click_rate_pct: number | null;
  email_ctor_pct?: number | null;
  quota: QuotaStatus;
  campaign_status_breakdown: CampaignStatusBreakdown;
  contact_growth_6_months: ContactGrowthPoint[];
  recent_campaigns: RecentCampaign[];
  recent_activity?: ActivityStreamItem[];
}
