export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export type SocialPostStatus =
  "DRAFT" | "SCHEDULED" | "DISPATCHING" | "PUBLISHING" | "PUBLISHED" | "CANCELLED" | "FAILED";

export interface ChannelCapability {
  provider_name: string;
  display_name: string;
  max_characters: number;
  supported_media_types: string[];
  max_media_count: number;
  requires_media: boolean;
  supports_video: boolean;
  supports_scheduling: boolean;
  is_configured: boolean;
  setup_guide: string | null;
}

export interface SocialConnection {
  id: string;
  provider: string;
  provider_account_id?: string | null;
  provider_username?: string | null;
  provider_account_name?: string | null;
  ig_business_account_id?: string | null;
  ig_username?: string | null;
  facebook_page_id?: string | null;
  is_active: boolean;
  last_connected_at: string;
  last_error: string | null;
  token_expires_at?: string | null;
}

export interface SocialPostMedia {
  id: string;
  media_type: string;
  public_url: string;
  position: number;
  file_size_bytes?: number | null;
  mime_type?: string | null;
}

export interface SocialPost {
  id: string;
  social_connection_id: string;
  caption: string;
  status: SocialPostStatus;
  scheduled_at: string | null;
  cancelled_at: string | null;
  published_at: string | null;
  campaign_id?: string | null;
  utm_source?: string | null;
  utm_medium?: string | null;
  utm_campaign?: string | null;
  utm_content?: string | null;
  ig_media_id: string | null;
  ig_permalink: string | null;
  provider_post_id?: string | null;
  provider_permalink?: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
  media: SocialPostMedia[];
}

export interface SocialPostJob {
  job_id: string;
}

export interface MediaFolder {
  id: string;
  account_id: string;
  name: string;
  parent_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaAsset {
  id: string;
  account_id: string;
  folder_id: string | null;
  filename: string;
  file_name?: string;
  storage_path: string;
  public_url: string;
  media_type: string;
  mime_type: string;
  file_size_bytes: number;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface MediaListResponse {
  assets: MediaAsset[];
  folders: MediaFolder[];
  total_assets: number;
  total_bytes: number;
}
