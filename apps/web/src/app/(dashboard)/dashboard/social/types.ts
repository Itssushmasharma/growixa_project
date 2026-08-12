export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export type SocialPostStatus =
  "DRAFT" | "SCHEDULED" | "DISPATCHING" | "PUBLISHING" | "PUBLISHED" | "CANCELLED" | "FAILED";

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

export interface SocialPostMedia {
  id: string;
  media_type: string;
  public_url: string;
  position: number;
}

export interface SocialPost {
  id: string;
  social_connection_id: string;
  caption: string;
  status: SocialPostStatus;
  scheduled_at: string | null;
  cancelled_at: string | null;
  published_at: string | null;
  ig_media_id: string | null;
  ig_permalink: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
  media: SocialPostMedia[];
}

export interface SocialPostJob {
  job_id: string;
}
