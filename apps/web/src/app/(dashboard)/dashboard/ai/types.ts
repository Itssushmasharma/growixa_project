export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  company_name?: string;
  permissions: string[];
}

export type AICapability =
  "SUBJECT_LINE" | "BODY_COPY" | "SOCIAL_CAPTION" | "REWRITE" | "HASHTAGS" | "POSTING_TIME";

export type StudioChannel = "Email" | "Social Post" | "SMS" | "Ad Copy" | "Blog";

export type ApprovalStatus = "PENDING_APPROVAL" | "APPROVED" | "DISCARDED";

export type AIGenerationStatus = "COMPLETE" | "FAILED";

export interface AIGeneration {
  id: string;
  capability: AICapability;
  channel?: StudioChannel;
  output: { text: string; subject?: string; body?: string } | null;
  input_context?: {
    brief?: string;
    existing_text?: string;
    instruction?: string;
    campaign?: string;
    audience?: string;
    goal?: string;
  } | null;
  provider: string;
  model: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  estimated_cost_usd: number | null;
  status: AIGenerationStatus;
  error_message: string | null;
  linked_entity_type: string | null;
  linked_entity_id: string | null;
  created_at: string;
  approval_status?: ApprovalStatus;
}

export interface SuggestedPrompt {
  id: string;
  title: string;
  subtitle: string;
  channel: StudioChannel;
  tag: string;
  tagColor: "purple" | "blue" | "green" | "orange";
  campaign?: string;
  audience?: string;
  prompt: string;
  tone: string;
  length: string;
}

export interface CampaignSummary {
  id: string;
  name: string;
  status: string;
}

export interface SegmentSummary {
  id: string;
  name: string;
  contact_count?: number;
}

export interface SubscriptionUsageInfo {
  period_ai_used: number;
  max_monthly_ai_runs: number;
  plan_name: string;
}
