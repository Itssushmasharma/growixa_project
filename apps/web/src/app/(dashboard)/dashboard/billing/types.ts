export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

// No "free" here -- Free is the default at registration and never self-serve-checked-out
// through this page (DEC-GRX-030 point 4); "enterprise" is contact-sales only, listed in
// the plan catalog for display but never a Subscribe target.
export type SubscribablePlanSlug = "starter" | "pro";

export type BillingCurrency = "USD" | "INR";

export type SubscriptionStatus = "PENDING" | "ACTIVE" | "PAST_DUE" | "CANCELED" | "HALTED";

export type CreditType = "AI_RUNS" | "EMAIL_SENDS" | "CONTACT_SLOTS" | "SOCIAL_POSTS";

export interface SubscriptionPlan {
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

export interface CreditPack {
  id: string;
  slug: string;
  name: string;
  credit_type: CreditType;
  credits: number;
  price_usd: number | null;
  price_inr: number | null;
}

export interface CreditBalance {
  credit_type: CreditType;
  remaining_credits: number;
}

export interface AccountSubscription {
  plan: SubscriptionPlan;
  status: SubscriptionStatus;
  currency: BillingCurrency;
  current_period_start: string;
  current_period_end: string;
  period_email_used: number;
  period_ai_used: number;
  credit_balances: CreditBalance[];
}

export interface SubscribeResponse {
  razorpay_subscription_id: string;
  razorpay_key_id: string;
}

export interface TopUpResponse {
  razorpay_order_id: string;
  razorpay_key_id: string;
  amount_smallest_unit: number;
  currency: BillingCurrency;
}

export const CREDIT_TYPE_LABEL: Record<CreditType, string> = {
  AI_RUNS: "AI runs",
  EMAIL_SENDS: "Email sends",
  CONTACT_SLOTS: "Extra contacts",
  SOCIAL_POSTS: "Extra social posts",
};

export const STATUS_LABEL: Record<SubscriptionStatus, string> = {
  PENDING: "Pending payment",
  ACTIVE: "Active",
  PAST_DUE: "Payment past due",
  CANCELED: "Canceled",
  HALTED: "Payment failing",
};
