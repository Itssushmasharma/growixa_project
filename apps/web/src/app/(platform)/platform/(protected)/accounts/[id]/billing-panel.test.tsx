import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { AccountBillingOverview, BillingSubscriptionPlan } from "../types";
import { BillingPanel } from "./billing-panel";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const FREE_PLAN: BillingSubscriptionPlan = {
  id: "plan-free",
  slug: "free",
  name: "Free",
  price_usd: 0,
  price_inr: 0,
  max_contacts: 250,
  max_monthly_emails: 1000,
  max_monthly_ai_runs: 10,
  max_social_accounts: 1,
  max_user_seats: 1,
  allow_byo_ai_key: false,
  allow_byo_smtp: false,
  audit_export_enabled: false,
  audit_api_enabled: false,
};

const PRO_PLAN: BillingSubscriptionPlan = {
  ...FREE_PLAN,
  id: "plan-pro",
  slug: "pro",
  name: "Pro",
  price_usd: 49,
  price_inr: 3999,
};

const OVERVIEW: AccountBillingOverview = {
  plan: FREE_PLAN,
  status: "ACTIVE",
  currency: "USD",
  current_period_start: "2026-08-01T00:00:00Z",
  current_period_end: "2026-08-31T00:00:00Z",
  period_email_used: 100,
  period_ai_used: 5,
  credit_balances: [{ credit_type: "AI_RUNS", remaining_credits: 20 }],
};

function mockLoad(overview: AccountBillingOverview = OVERVIEW) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/platform/accounts/acc-1/subscription") return Promise.resolve(overview);
    if (path === "/platform/subscription-plans") return Promise.resolve([FREE_PLAN, PRO_PLAN]);
    if (path === "/platform/accounts/acc-1/credits/grant") {
      return Promise.resolve({ credit_type: "AI_RUNS", remaining_credits: 120 });
    }
    throw new Error(`unexpected path: ${path}`);
  });
}

function renderPanel() {
  return render(
    <ToastProvider>
      <BillingPanel accountId="acc-1" />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("BillingPanel", () => {
  it("shows the account's current plan, status, and credit balances", async () => {
    mockLoad();

    renderPanel();

    expect(await screen.findByText("Billing")).toBeInTheDocument();
    expect(screen.getAllByText("Free").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ACTIVE").length).toBeGreaterThan(0);
    expect(screen.getByText("AI_RUNS: 20")).toBeInTheDocument();
    expect(screen.getByText("EMAIL_SENDS: 0")).toBeInTheDocument();
  });

  it("overrides the plan and refetches the overview", async () => {
    const user = userEvent.setup();
    mockLoad();

    renderPanel();
    await screen.findByText("Billing");

    await user.selectOptions(screen.getByLabelText("Plan"), "pro");
    await user.click(screen.getByRole("button", { name: "Apply override" }));

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/platform/accounts/acc-1/subscription",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ plan_slug: "pro", status: null }),
      }),
    );
    expect(await screen.findByText("Subscription updated.")).toBeInTheDocument();
  });

  it("grants credits and refetches the overview", async () => {
    const user = userEvent.setup();
    mockLoad();

    renderPanel();
    await screen.findByText("Billing");

    await user.type(screen.getByLabelText("Credits"), "50");
    await user.click(screen.getByRole("button", { name: "Grant credits" }));

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/platform/accounts/acc-1/credits/grant",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ credit_type: "AI_RUNS", credits: 50 }),
      }),
    );
    expect(await screen.findByText("Credits granted.")).toBeInTheDocument();
  });
});
