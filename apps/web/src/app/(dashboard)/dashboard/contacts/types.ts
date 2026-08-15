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

export interface CustomField {
  id: string;
  key: string;
  label: string;
  field_type: "TEXT" | "NUMBER" | "DATE" | "BOOLEAN";
}

export interface ContactImport {
  id: string;
  filename: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  column_mapping: Record<string, string>;
  total_rows: number;
  imported_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  created_at: string;
  completed_at: string | null;
}

export interface ContactImportRow {
  id: string;
  row_number: number;
  email: string | null;
  status: "IMPORTED" | "UPDATED" | "SKIPPED" | "ERROR";
  error_message: string | null;
}

export interface ConsentRecord {
  id: string;
  channel: "EMAIL" | "SMS";
  status: "GRANTED" | "WITHDRAWN" | "UNKNOWN";
  source: string | null;
  recorded_at: string;
}

export interface SuppressionEntry {
  id: string;
  email: string | null;
  domain: string | null;
  reason: "UNSUBSCRIBED" | "BOUNCED" | "COMPLAINED" | "MANUAL";
  contact_id: string | null;
  suppressed_at: string;
}

export interface SuppressionImportResult {
  created: number;
  skipped: number;
  total_rows: number;
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
  tags: (Tag | string)[];
  is_suppressed: boolean;
}
