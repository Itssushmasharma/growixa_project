export type AccountStatus = "ACTIVE" | "SUSPENDED" | "CLOSED";

export interface AccountListItem {
  id: string;
  name: string;
  status: AccountStatus;
  selected_plan_slug: string | null;
  created_at: string;
  user_count: number;
}

export interface AccountUser {
  id: string;
  email: string;
  full_name: string;
  status: string;
  last_login_at: string | null;
}

export interface SecurityEvent {
  id: string;
  action: string;
  entity_type: string;
  actor_user_id: string | null;
  event_metadata: Record<string, unknown>;
  created_at: string;
}

export interface AccountDetail {
  id: string;
  name: string;
  status: AccountStatus;
  selected_plan_slug: string | null;
  created_at: string;
  users: AccountUser[];
  security_activity: SecurityEvent[];
}

export type SupportSessionAccessLevel = "READ" | "WRITE";

export interface SupportSession {
  id: string;
  account_id: string;
  platform_admin_id: string;
  reason: string;
  ticket_number: string;
  access_level: SupportSessionAccessLevel;
  started_at: string;
  expires_at: string;
  ended_at: string | null;
}
