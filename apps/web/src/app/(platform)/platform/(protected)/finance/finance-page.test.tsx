import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";

import { FinancePage } from "./finance-page";
import type { FinancialMetrics } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("FinancePage", () => {
  it("renders MRR/ARR per currency, active subscriptions, and churn", async () => {
    const data: FinancialMetrics = {
      mrr_by_currency: { USD: 190, INR: 3999 },
      arr_by_currency: { USD: 2280, INR: 47988 },
      active_subscription_count: 12,
      churned_last_30_days: 2,
      churn_rate_percent: 14.29,
    };
    mockedApiFetch.mockResolvedValueOnce(data);

    render(<FinancePage />);

    expect(await screen.findByText("$190")).toBeInTheDocument();
    expect(screen.getByText("₹3,999")).toBeInTheDocument();
    expect(screen.getByText("$2,280")).toBeInTheDocument();
    expect(screen.getByText("₹47,988")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("14.29%")).toBeInTheDocument();
    expect(screen.getByText("2 cancellations in the last 30 days")).toBeInTheDocument();
  });

  it("shows an access-denied message for an admin without platform.monitoring.manage", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(403, "Insufficient permission"));

    render(<FinancePage />);

    expect(
      await screen.findByText("You don't have access to view the financial dashboard."),
    ).toBeInTheDocument();
  });
});
