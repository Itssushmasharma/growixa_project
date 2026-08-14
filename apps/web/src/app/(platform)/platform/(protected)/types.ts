export interface PlanDistributionItem {
  plan_slug: string;
  plan_name: string;
  account_count: number;
}

export interface PlatformDashboardSummary {
  total_active_accounts: number;
  total_mrr_usd: number;
  total_mrr_inr: number;
  period_emails_used: number;
  period_ai_runs_used: number;
  plan_distribution: PlanDistributionItem[];
}
