export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface CompanyProfile {
  id: string;
  name: string;
  logo_url: string | null;
  website: string | null;
  industry: string | null;
  timezone: string | null;
  default_language: string;
  legal_footer: string | null;
  business_address: string | null;
  description: string | null;
  support_email: string | null;
  sender_name: string | null;
  contact_details: Record<string, unknown>;
  updated_at: string;
}

export interface VoiceSettings {
  formality?: number;
  energy?: number;
  technical_depth?: number;
  sales_style?: number;
}

export interface BrandProfile {
  id: string;
  company_id: string;
  brand_voice: string | null;
  forbidden_claims: string[];
  required_facts: string[];
  persona_tags: string[];
  voice_settings: VoiceSettings;
  updated_at: string;
}
