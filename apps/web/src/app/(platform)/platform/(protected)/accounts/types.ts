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

// --- Billing (GRX-SAAS-006) ---

export type BillingSubscriptionStatus = "PENDING" | "ACTIVE" | "PAST_DUE" | "CANCELED" | "HALTED";

export type BillingCreditType = "AI_RUNS" | "EMAIL_SENDS" | "CONTACT_SLOTS" | "SOCIAL_POSTS";

export interface BillingSubscriptionPlan {
  id: string;
  slug: string;
  name: string;
  price_usd: number | null;
  price_inr: number | null;
  max_contacts: number | null;
  max_monthly_emails: number | null;
  max_monthly_ai_runs: number | null;
  max_social_accounts: number | null;
  max_user_seats: number | null;
  allow_byo_ai_key: boolean;
  allow_byo_smtp: boolean;
  audit_export_enabled: boolean;
  audit_api_enabled: boolean;
}

export interface BillingCreditBalance {
  credit_type: BillingCreditType;
  remaining_credits: number;
}

export interface CreditPack {
  id: string;
  slug: string;
  name: string;
  credit_type: BillingCreditType;
  credits: number;
  price_usd: number | null;
  price_inr: number | null;
  is_active: boolean;
}

export interface AccountBillingOverview {
  plan: BillingSubscriptionPlan;
  status: BillingSubscriptionStatus;
  currency: "USD" | "INR";
  current_period_start: string;
  current_period_end: string;
  period_email_used: number;
  period_ai_used: number;
  credit_balances: BillingCreditBalance[];
}

// --- Coupons (GRX-SAAS-012) ---

export type CouponDiscountType = "PERCENTAGE" | "FIXED_AMOUNT" | "CREDIT_GRANT";

export interface Coupon {
  id: string;
  code: string;
  discount_type: CouponDiscountType;
  discount_value: number;
  credit_type: BillingCreditType | null;
  applicable_plan_slugs: string[] | null;
  max_redemptions: number | null;
  redemption_count: number;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
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
