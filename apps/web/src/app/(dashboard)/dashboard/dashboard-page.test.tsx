import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "@/lib/api-client";
import { DashboardPage } from "./dashboard-page";
import type { DashboardOverview } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);
const OVERVIEW: DashboardOverview = {
  total_contacts: 1338,
  active_campaigns: 0,
  scheduled_social_posts: 2,
  email_open_rate_pct: 31,
  email_click_rate_pct: 8.4,
  email_ctor_pct: 27.1,
  quota: {
    plan_name: "Growth",
    contact_usage: 1338,
    contact_limit: 5000,
    email_usage: 2400,
    email_limit: 10000,
    ai_usage: 25,
    ai_limit: 100,
    ai_credits_remaining: 75,
  },
  campaign_status_breakdown: {
    draft: 1,
    scheduled: 0,
    sending: 0,
    sent: 4,
    cancelled: 0,
    failed: 0,
  },
  contact_growth_6_months: [{ month: "2026-09", contacts: 1338 }],
  recent_campaigns: [],
  recent_activity: [],
};

beforeEach(() => mockedApiFetch.mockReset());

describe("DashboardPage command center", () => {
  it("shows functional growth actions and real overview data", async () => {
    mockedApiFetch.mockResolvedValue(OVERVIEW);
    render(<DashboardPage />);

    expect(
      await screen.findByRole("heading", { name: "What do you want to grow today?" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ask Growixa/i })).toHaveAttribute(
      "href",
      "/dashboard/ai",
    );
    expect(screen.getByRole("link", { name: /Add contacts/i })).toHaveAttribute(
      "href",
      "/dashboard/contacts/imports",
    );
    expect(screen.getAllByText("1,338").length).toBeGreaterThan(0);
    expect(screen.getByText("8.4%")).toBeInTheDocument();
    expect(screen.getByText("Turn your audience into a campaign")).toBeInTheDocument();
  });

  it("prioritizes campaign failures as the next action", async () => {
    mockedApiFetch.mockResolvedValue({
      ...OVERVIEW,
      campaign_status_breakdown: { ...OVERVIEW.campaign_status_breakdown, failed: 2 },
    });
    render(<DashboardPage />);

    expect(await screen.findByText("2 campaign failures")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Review campaigns/i })).toHaveAttribute(
      "href",
      "/dashboard/campaigns?status=failed",
    );
  });
});
