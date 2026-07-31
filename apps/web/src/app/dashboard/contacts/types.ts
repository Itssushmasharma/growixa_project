export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface Contact {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  status: "ACTIVE" | "ARCHIVED";
  source: string | null;
  created_at: string;
  updated_at: string;
  custom_fields: Record<string, string>;
  tags: string[];
  is_suppressed: boolean;
}
