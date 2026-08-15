export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export type AICapability =
  | "SUBJECT_LINE"
  | "BODY_COPY"
  | "SOCIAL_CAPTION"
  | "REWRITE"
  | "HASHTAGS"
  | "POSTING_TIME";

export type StudioContentType =
  | "SUBJECT_LINE"
  | "BODY_COPY"
  | "SOCIAL_CAPTION"
  | "HASHTAGS"
  | "CTA"
  | "REWRITE"
  | "POSTING_TIME";

export type ApprovalStatus = "PENDING_APPROVAL" | "APPROVED" | "DISCARDED";

export type AIGenerationStatus = "COMPLETE" | "FAILED";

export interface AIGeneration {
  id: string;
  capability: AICapability;
  output: { text: string } | null;
  input_context?: { brief?: string; existing_text?: string; instruction?: string } | null;
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

export interface SubscriptionUsageInfo {
  period_ai_used: number;
  max_monthly_ai_runs: number;
  plan_name: string;
}
