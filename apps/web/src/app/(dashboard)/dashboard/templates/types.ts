export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface EmailTemplateVersion {
  id: string;
  template_id: string;
  version_number: number;
  subject: string;
  body_html: string;
  body_text: string | null;
  created_at: string;
}

export interface EmailTemplate {
  id: string;
  name: string;
  is_platform_default: boolean;
  created_at: string;
  updated_at: string;
  current_version: EmailTemplateVersion | null;
}
