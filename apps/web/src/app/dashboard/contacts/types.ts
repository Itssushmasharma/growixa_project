export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface Tag {
  id: string;
  name: string;
}

export interface ContactList {
  id: string;
  name: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface SegmentRule {
  id: string;
  field: string;
  operator: string;
  value: string;
}

export interface Segment {
  id: string;
  name: string;
  type: "DYNAMIC" | "SAVED";
  member_count: number;
  created_at: string;
  updated_at: string;
  rules: SegmentRule[];
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
