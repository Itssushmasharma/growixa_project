export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

export interface Tag {
  id: string;
  name: string;
  contacts_count?: number;
}

export type CompanyLifecycleStage =
  "PROSPECT" | "LEAD" | "QUALIFIED" | "CUSTOMER" | "CHURNED" | "PARTNER" | "OTHER";

export interface Company {
  id: string;
  name: string;
  domain: string | null;
  industry: string | null;
  website: string | null;
  phone: string | null;
  address: string | null;
  lifecycle_stage: CompanyLifecycleStage;
  custom_attributes: Record<string, unknown>;
  contacts_count: number;
  created_at: string;
  updated_at: string;
}

export type ActivityType =
  | "NOTE"
  | "STAGE_CHANGE"
  | "TAG_ADDED"
  | "TAG_REMOVED"
  | "EMAIL_SENT"
  | "EMAIL_OPENED"
  | "IMPORT"
  | "CONSENT_CHANGE"
  | "TASK"
  | "CALL";

export interface ContactActivity {
  id: string;
  contact_id: string;
  activity_type: ActivityType;
  title: string;
  description: string | null;
  metadata: Record<string, unknown>;
  created_by_user_id: string | null;
  created_at: string;
}

export interface ContactStats {
  total: number;
  active: number;
  archived: number;
  suppressed: number;
  new_this_month: number;
}

export interface ContactList {
  id: string;
  name: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export const SEGMENT_RULE_FIELDS = {
  STATUS: "status",
  EMAIL: "email",
  FIRST_NAME: "first_name",
  LAST_NAME: "last_name",
  PHONE: "phone",
  SOURCE: "source",
  TAG: "tag",
  CREATED_AT: "created_at",
  LIFECYCLE_STAGE: "lifecycle_stage",
  JOB_TITLE: "job_title",
  COMPANY: "company",
} as const;

export const SEGMENT_RULE_OPERATORS = {
  EQUALS: "equals",
  NOT_EQUALS: "not_equals",
  CONTAINS: "contains",
  STARTS_WITH: "starts_with",
  ENDS_WITH: "ends_with",
  IS_EMPTY: "is_empty",
  IS_NOT_EMPTY: "is_not_empty",
  WITHIN_DAYS: "within_days",
  HAS_TAG: "has_tag",
  HAS_NOT_TAG: "has_not_tag",
  BEFORE: "before",
  AFTER: "after",
  GREATER_THAN: "greater_than",
  LESS_THAN: "less_than",
} as const;

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
  match_type?: "ALL" | "ANY";
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

export interface CSVDetectResult {
  headers: string[];
  sample_rows: string[][];
  suggested_mapping: Record<string, string | null>;
  total_rows_estimate: number;
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
  phone?: string | null;
  reason: "UNSUBSCRIBED" | "BOUNCED" | "COMPLAINED" | "MANUAL";
  contact_id: string | null;
  suppressed_at: string;
}

export interface SuppressionImportResult {
  created: number;
  skipped: number;
  total_rows: number;
}

export type EmailValidationStatus = "VALID" | "INVALID" | "DISPOSABLE" | "ROLE" | "RISKY";

export type EmailValidationLevel = "BASIC" | "REALTIME";

export interface EmailValidationResult {
  email: string;
  status: EmailValidationStatus;
  reasons: string[];
  verification_level: EmailValidationLevel;
}

export interface EmailValidationSummary {
  total: number;
  valid: number;
  invalid: number;
  disposable: number;
  role: number;
}

export type ContactLifecycleStage =
  "SUBSCRIBER" | "LEAD" | "MQL" | "SQL" | "OPPORTUNITY" | "CUSTOMER" | "EVANGELIST" | "OTHER";

export interface Contact {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  company_id?: string | null;
  company_name?: string | null;
  job_title?: string | null;
  lifecycle_stage?: ContactLifecycleStage;
  status: "ACTIVE" | "ARCHIVED";
  source: string | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  custom_fields: Record<string, string>;
  custom_attributes?: Record<string, unknown>;
  tags: (Tag | string)[];
  is_suppressed: boolean;
}
