export interface FinancialMetrics {
  mrr_by_currency: Record<string, number>;
  arr_by_currency: Record<string, number>;
  active_paying_subscription_count: number;
  churned_last_30_days: number;
  churn_rate_percent: number;
}
