import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";
import { openRazorpayCheckout } from "@/lib/razorpay";

import { BillingPage } from "./billing-page";
import type { AccountSubscription, CreditPack, MeResponse, SubscriptionPlan } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

vi.mock("@/lib/razorpay", () => ({
  openRazorpayCheckout: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("@/components/toast/toast-context", () => ({
  useToast: () => ({ showToast: vi.fn() }),
}));

const mockedApiFetch = vi.mocked(apiFetch);
const mockedOpenCheckout = vi.mocked(openRazorpayCheckout);

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const FREE_PLAN: SubscriptionPlan = {
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

const PRO_PLAN: SubscriptionPlan = {
  id: "plan-pro",
  slug: "pro",
  name: "Pro",
  price_usd: 49,
  price_inr: 3999,
  max_contacts: 15000,
  max_monthly_emails: 100000,
  max_monthly_ai_runs: 1000,
  max_social_accounts: 10,
  max_user_seats: 10,
  allow_byo_ai_key: true,
  allow_byo_smtp: true,
  audit_export_enabled: true,
  audit_api_enabled: true,
};

const AI_RUNS_PACK: CreditPack = {
  id: "pack-1",
  slug: "ai_runs_250",
  name: "250 AI Runs",
  credit_type: "AI_RUNS",
  credits: 250,
  price_usd: null,
  price_inr: 400,
};

const SUBSCRIPTION: AccountSubscription = {
  plan: FREE_PLAN,
  status: "ACTIVE",
  currency: "INR",
  current_period_start: "2026-08-01T00:00:00Z",
  current_period_end: "2026-08-31T00:00:00Z",
  period_email_used: 100,
  period_ai_used: 5,
  credit_balances: [{ credit_type: "AI_RUNS", remaining_credits: 20 }],
};

function mockLoad(
  permissions: string[],
  overrides?: { subscription?: AccountSubscription; plans?: SubscriptionPlan[] },
) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/billing/subscription")
      return Promise.resolve(overrides?.subscription ?? SUBSCRIPTION);
    if (path === "/billing/plans")
      return Promise.resolve(overrides?.plans ?? [FREE_PLAN, PRO_PLAN]);
    if (path === "/billing/credit-packs") return Promise.resolve([AI_RUNS_PACK]);
    if (path === "/billing/subscribe")
      return Promise.resolve({ razorpay_subscription_id: "sub_123", razorpay_key_id: "key_123" });
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockedOpenCheckout.mockClear();
});

describe("BillingPage", () => {
  it("shows an access-denied message for a user without billing.view", async () => {
    mockLoad([]);

    render(<BillingPage />);

    expect(await screen.findByText("You don't have access to billing.")).toBeInTheDocument();
  });

  it("shows the current plan, status, and usage for a billing.view user", async () => {
    mockLoad(["billing.view"]);

    render(<BillingPage />);

    expect(await screen.findByText("Free plan")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("100 / 1,000")).toBeInTheDocument();
    expect(screen.getByText("5 / 10")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  it("marks the account's current plan in the plan list", async () => {
    mockLoad(["billing.view"]);

    render(<BillingPage />);

    await screen.findByText("Free plan");
    expect(screen.getByText("Current plan")).toBeInTheDocument();
  });

  it("hides Subscribe/Buy actions for a view-only user", async () => {
    mockLoad(["billing.view"]);

    render(<BillingPage />);

    await screen.findByText("Free plan");
    expect(screen.queryByRole("button", { name: "Subscribe" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Buy" })).not.toBeInTheDocument();
  });

  it("lets a billing.manage user subscribe to a different plan via Razorpay Checkout", async () => {
    const user = userEvent.setup();
    mockLoad(["billing.view", "billing.manage"]);

    render(<BillingPage />);

    await screen.findByText("Free plan");
    await user.click(screen.getByRole("button", { name: "Subscribe" }));

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/billing/subscribe",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ plan_slug: "pro", currency: "INR" }),
      }),
    );
    expect(mockedOpenCheckout).toHaveBeenCalledWith(
      expect.objectContaining({
        key: "key_123",
        subscription_id: "sub_123",
      }),
    );
  });

  it("switches displayed prices when the currency toggle changes", async () => {
    const user = userEvent.setup();
    mockLoad(["billing.view", "billing.manage"]);

    render(<BillingPage />);

    await screen.findByText("Free plan");
    expect(screen.getByText("₹3,999/mo")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "$ USD" }));

    expect(screen.getByText("$49/mo")).toBeInTheDocument();
  });
});
