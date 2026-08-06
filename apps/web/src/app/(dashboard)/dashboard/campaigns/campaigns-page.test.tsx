import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { CampaignsPage } from "./campaigns-page";
import type { Campaign, ContactListSummary, MeResponse, SegmentSummary } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const LIST: ContactListSummary = { id: "list-1", name: "VIP Customers", member_count: 42 };
const SEGMENT: SegmentSummary = { id: "segment-1", name: "Active Users", member_count: 120 };

const DRAFT_CAMPAIGN: Campaign = {
  id: "campaign-1",
  name: "Spring Sale",
  subject: "Spring is here 🌸",
  body_html: "<p>Save 20%</p>",
  body_text: null,
  template_id: null,
  sender_identity_id: "identity-1",
  recipient_type: "LIST",
  recipient_segment_id: null,
  recipient_list_id: "list-1",
  status: "DRAFT",
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  sent_at: null,
};

const SENT_CAMPAIGN: Campaign = {
  id: "campaign-2",
  name: "Monthly Digest",
  subject: "Your monthly recap",
  body_html: "<p>Recap</p>",
  body_text: null,
  template_id: null,
  sender_identity_id: "identity-1",
  recipient_type: "SEGMENT",
  recipient_segment_id: "segment-1",
  recipient_list_id: null,
  status: "SENT",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
  sent_at: "2026-08-01T01:00:00Z",
};

function mockLoad(
  permissions: string[],
  campaigns: Campaign[],
  lists: ContactListSummary[] = [LIST],
  segments: SegmentSummary[] = [SEGMENT],
) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/campaigns") return Promise.resolve(campaigns);
    if (path === "/contacts/lists") return Promise.resolve(lists);
    if (path === "/contacts/segments") return Promise.resolve(segments);
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("CampaignsPage", () => {
  it("shows an access-denied message for a user without campaigns.view", async () => {
    mockLoad([], []);

    render(<CampaignsPage />);

    expect(await screen.findByText("You don't have access to campaigns.")).toBeInTheDocument();
  });

  it("shows the campaign list to a view-only user without a New campaign link", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN]);

    render(<CampaignsPage />);

    expect(await screen.findByText("Spring Sale")).toBeInTheDocument();
    expect(screen.getByText("Spring is here 🌸")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "+ New campaign" })).not.toBeInTheDocument();
  });

  it("shows the New campaign link for a campaigns.manage user", async () => {
    mockLoad(["campaigns.view", "campaigns.manage"], []);

    render(<CampaignsPage />);
    await screen.findByText("No campaigns yet.");

    expect(screen.getByRole("link", { name: "+ New campaign" })).toHaveAttribute(
      "href",
      "/dashboard/campaigns/new",
    );
  });

  it("resolves the recipient list/segment name and status label", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SENT_CAMPAIGN]);

    render(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    expect(screen.getByText("List: VIP Customers")).toBeInTheDocument();
    expect(screen.getByText("Segment: Active Users")).toBeInTheDocument();
    const draftCard = screen.getByText("Spring Sale").closest("a")!;
    const sentCard = screen.getByText("Monthly Digest").closest("a")!;
    expect(within(draftCard).getByText("Draft")).toBeInTheDocument();
    expect(within(sentCard).getByText("Sent")).toBeInTheDocument();
  });

  it("links each row to its detail page", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN]);

    render(<CampaignsPage />);
    const row = await screen.findByText("Spring Sale");

    expect(row.closest("a")).toHaveAttribute("href", "/dashboard/campaigns/campaign-1");
  });

  it("filters the list by search query", async () => {
    const user = userEvent.setup();
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SENT_CAMPAIGN]);

    render(<CampaignsPage />);
    await screen.findByText("Spring Sale");
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Search campaigns"), "monthly");

    expect(screen.queryByText("Spring Sale")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();
  });

  it("filters by status tab", async () => {
    const user = userEvent.setup();
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SENT_CAMPAIGN]);

    render(<CampaignsPage />);
    await screen.findByText("Spring Sale");
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /^Sent\d*$/ }));

    expect(screen.queryByText("Spring Sale")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "All" }));

    expect(screen.getByText("Spring Sale")).toBeInTheDocument();
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();
  });

  it("does not show Scheduled or Paused tabs (not a real campaign status yet)", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN]);

    render(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    expect(screen.queryByRole("tab", { name: "Scheduled" })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Paused" })).not.toBeInTheDocument();
  });
});
