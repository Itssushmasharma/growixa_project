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
  contact_details: Record<string, unknown>;
}

export interface BrandProfile {
  id: string;
  company_id: string;
  brand_voice: string | null;
  forbidden_claims: string[];
  required_facts: string[];
}
