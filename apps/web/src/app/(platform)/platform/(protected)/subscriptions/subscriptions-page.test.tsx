import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import type { BillingSubscriptionPlan, CreditPack } from "../accounts/types";
import { SubscriptionsPage } from "./subscriptions-page";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const STARTER_PLAN: BillingSubscriptionPlan = {
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
};

const AI_RUNS_PACK: CreditPack = {
  id: "pack-1",
  slug: "ai_runs_250",
  name: "250 AI Runs",
  credit_type: "AI_RUNS",
  credits: 250,
  price_usd: null,
  price_inr: 400,
  is_active: true,
};

function mockLoad(
  plans: BillingSubscriptionPlan[] = [STARTER_PLAN],
  packs: CreditPack[] = [AI_RUNS_PACK],
) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/platform/subscription-plans") return Promise.resolve(plans);
    if (path === "/platform/credit-packs") return Promise.resolve(packs);
    throw new Error(`unexpected path: ${path}`);
  });
}

function renderPage() {
  return render(
    <ToastProvider>
      <SubscriptionsPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("SubscriptionsPage", () => {
  it("shows an access-denied message on a 403", async () => {
    mockedApiFetch.mockRejectedValue(new ApiError(403, "Forbidden"));

    renderPage();

    expect(
      await screen.findByText("You don't have access to manage subscriptions."),
    ).toBeInTheDocument();
  });

  it("lists existing plans and credit packs", async () => {
    mockLoad();

    renderPage();

    expect(await screen.findByText("Starter")).toBeInTheDocument();
    expect(screen.getByText("250 AI Runs")).toBeInTheDocument();
  });

  it("creates a new plan", async () => {
    const user = userEvent.setup();
    mockLoad();
    const createdPlan: BillingSubscriptionPlan = {
      ...STARTER_PLAN,
      id: "plan-growth",
      slug: "growth",
      name: "Growth",
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/platform/subscription-plans" && (!init || init.method === undefined)) {
        return Promise.resolve([STARTER_PLAN]);
      }
      if (path === "/platform/credit-packs" && (!init || init.method === undefined)) {
        return Promise.resolve([AI_RUNS_PACK]);
      }
      if (path === "/platform/subscription-plans" && init?.method === "POST") {
        return Promise.resolve(createdPlan);
      }
      throw new Error(`unexpected call: ${path} ${init?.method ?? "GET"}`);
    });

    renderPage();
    await screen.findByText("Starter");

    await user.click(screen.getByRole("button", { name: "+ New plan" }));
    await user.type(screen.getByLabelText("Slug"), "growth");
    await user.type(screen.getByLabelText("Name"), "Growth");
    await user.click(screen.getByRole("button", { name: "Save plan" }));

    expect(await screen.findByText('Plan "Growth" created.')).toBeInTheDocument();
  });
});
