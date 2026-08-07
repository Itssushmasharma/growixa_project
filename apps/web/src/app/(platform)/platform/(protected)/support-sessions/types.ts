export interface SupportSessionCompany {
  name: string;
  website: string | null;
  industry: string | null;
}

export interface SupportSessionContact {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  status: string;
}

export interface AuditEvent {
  id: string;
  action: string;
  entity_type: string;
  actor_user_id: string | null;
  event_metadata: Record<string, unknown>;
  created_at: string;
}

export interface SupportSessionMeta {
  id: string;
  account_id: string;
  platform_admin_id: string;
  reason: string;
  ticket_number: string;
  access_level: "READ" | "WRITE";
  started_at: string;
  expires_at: string;
  ended_at: string | null;
}

export interface SupportSessionOverview {
  session: SupportSessionMeta;
  company: SupportSessionCompany | null;
  contacts: SupportSessionContact[];
  audit_events: AuditEvent[];
}
