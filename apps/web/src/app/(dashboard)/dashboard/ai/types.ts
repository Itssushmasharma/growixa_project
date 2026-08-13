export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export type AICapability =
  "SUBJECT_LINE" | "BODY_COPY" | "SOCIAL_CAPTION" | "REWRITE" | "HASHTAGS" | "POSTING_TIME";

export type AIGenerationStatus = "COMPLETE" | "FAILED";

export interface AIGeneration {
  id: string;
  capability: AICapability;
  output: { text: string } | null;
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
}
