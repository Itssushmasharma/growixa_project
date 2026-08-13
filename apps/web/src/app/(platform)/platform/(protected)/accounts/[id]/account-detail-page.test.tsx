import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { AccountDetailPage } from "./account-detail-page";
import type { AccountBillingOverview, AccountDetail } from "../types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const ACTIVE_ACCOUNT: AccountDetail = {
  id: "acc-1",
  name: "Acme Corp",
  status: "ACTIVE",
  selected_plan_slug: "starter",
  created_at: "2026-08-01T00:00:00Z",
  users: [
    {
      id: "user-1",
      email: "owner@acme.example.com",
      full_name: "Acme Owner",
      status: "ACTIVE",
      last_login_at: "2026-08-06T00:00:00Z",
    },
  ],
  security_activity: [
    {
      id: "event-1",
      action: "user.login",
      entity_type: "user",
      actor_user_id: "user-1",
      event_metadata: {},
      created_at: "2026-08-06T00:00:00Z",
    },
  ],
};

const BILLING_OVERVIEW: AccountBillingOverview = {
  plan: {
    id: "plan-starter",
    slug: "starter",
    name: "Starter",
    price_usd: 19,
    price_inr: 1499,
    max_contacts: 2500,
    max_monthly_emails: 15000,
    max_monthly_ai_runs: 150,
    max_social_accounts: 3,
    max_user_seats: 3,
    allow_byo_ai_key: false,
    allow_byo_smtp: true,
    audit_export_enabled: true,
    audit_api_enabled: false,
  },
  status: "ACTIVE",
  currency: "USD",
  current_period_start: "2026-08-01T00:00:00Z",
  current_period_end: "2026-08-31T00:00:00Z",
  period_email_used: 0,
  period_ai_used: 0,
  credit_balances: [],
};

function renderPage() {
  return render(
    <ToastProvider>
      <AccountDetailPage accountId="acc-1" />
    </ToastProvider>,
  );
}

// Path-based (not positional) mocking -- AccountDetailPage renders BillingPanel and
// SupportSessionPanel as sibling components, each firing its own apiFetch calls from
// independent effects, so the order across them isn't deterministic.
function mockApiFetch(overrides?: { account?: AccountDetail; billing?: AccountBillingOverview }) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/platform/accounts/acc-1") {
      return Promise.resolve(overrides?.account ?? ACTIVE_ACCOUNT);
    }
    if (path === "/platform/accounts/acc-1/subscription") {
      return Promise.resolve(overrides?.billing ?? BILLING_OVERVIEW);
    }
    if (path === "/platform/subscription-plans") return Promise.resolve([BILLING_OVERVIEW.plan]);
    if (path === "/platform/accounts/acc-1/support-sessions") return Promise.resolve([]);
    if (path === "/platform/auth/me") return Promise.resolve({ permissions: [] });
    if (path === "/platform/accounts/acc-1/status") {
      return Promise.resolve({ ...ACTIVE_ACCOUNT, status: "SUSPENDED" });
    }
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("AccountDetailPage", () => {
  it("renders the account's users and security activity", async () => {
    mockApiFetch();

    renderPage();

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Acme Owner")).toBeInTheDocument();
    expect(screen.getByText("owner@acme.example.com")).toBeInTheDocument();
    expect(screen.getByText("user.login")).toBeInTheDocument();
  });

  it("suspends the account via the Suspend button and refetches", async () => {
    const user = userEvent.setup();
    mockApiFetch();

    renderPage();
    await screen.findByText("Acme Corp");

    await user.click(screen.getByRole("button", { name: "Suspend" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/accounts/acc-1/status", {
        method: "PATCH",
        body: JSON.stringify({ status: "SUSPENDED" }),
      });
    });
    expect(await screen.findByText("Account suspended.")).toBeInTheDocument();
  });

  it("renders the account's billing panel", async () => {
    mockApiFetch();

    renderPage();

    expect(await screen.findByText("Billing")).toBeInTheDocument();
    expect(screen.getAllByText("Starter").length).toBeGreaterThan(0);
  });
});
