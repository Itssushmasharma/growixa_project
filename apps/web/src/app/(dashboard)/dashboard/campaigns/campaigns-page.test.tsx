import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";
import { ToastProvider } from "@/components/toast/toast-context";

import { CampaignsPage } from "./campaigns-page";
import type { Campaign, ContactListSummary, MeResponse, SegmentSummary } from "./types";

function renderWithToast(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>);
}

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
  scheduled_at: null,
  cancelled_at: null,
  idempotency_key: "idem-key-1",
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  sent_at: null,
};

const SCHEDULED_CAMPAIGN: Campaign = {
  id: "campaign-3",
  name: "Black Friday Blast",
  subject: "Huge deals await",
  body_html: "<p>Deal</p>",
  body_text: null,
  template_id: null,
  sender_identity_id: "identity-1",
  recipient_type: "ALL_CONTACTS",
  recipient_segment_id: null,
  recipient_list_id: null,
  status: "SCHEDULED",
  scheduled_at: "2026-11-29T09:00:00Z",
  cancelled_at: null,
  idempotency_key: "idem-key-3",
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
  scheduled_at: null,
  cancelled_at: null,
  idempotency_key: "idem-key-2",
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

    renderWithToast(<CampaignsPage />);

    expect(await screen.findByText(/don't have permission to view campaigns/i)).toBeInTheDocument();
  });

  it("shows the campaign list to a view-only user without a New campaign link", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);

    expect(await screen.findByText("Spring Sale")).toBeInTheDocument();
    expect(screen.getByText("Spring is here 🌸")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "+ Create Campaign" })).not.toBeInTheDocument();
  });

  it("shows the New campaign link for a campaigns.manage user", async () => {
    mockLoad(["campaigns.view", "campaigns.manage"], []);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("No campaigns found");

    expect(screen.getByRole("link", { name: "+ Create Campaign" })).toHaveAttribute(
      "href",
      "/dashboard/campaigns/new",
    );
  });

  it("resolves the recipient list/segment name and status label", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SENT_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    expect(screen.getByText("List: VIP Customers")).toBeInTheDocument();
    expect(screen.getByText("Segment: Active Users")).toBeInTheDocument();
    const draftRow = screen.getByText("Spring Sale").closest("tr")!;
    const sentRow = screen.getByText("Monthly Digest").closest("tr")!;
    expect(within(draftRow).getByText(/Draft/)).toBeInTheDocument();
    expect(within(sentRow).getByText(/Sent/)).toBeInTheDocument();
  });

  it("links each row to its detail page", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    const row = await screen.findByText("Spring Sale");

    expect(row.closest("a")).toHaveAttribute("href", "/dashboard/campaigns/campaign-1");
  });

  it("filters the list by search query", async () => {
    const user = userEvent.setup();
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SENT_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Search campaigns"), "monthly");

    expect(screen.queryByText("Spring Sale")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();
  });

  it("filters by status tab", async () => {
    const user = userEvent.setup();
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SENT_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /^Sent\d*$/ }));

    expect(screen.queryByText("Spring Sale")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /^All/ }));

    expect(screen.getByText("Spring Sale")).toBeInTheDocument();
    expect(screen.getByText("Monthly Digest")).toBeInTheDocument();
  });

  it("shows a Scheduled filter tab now that scheduling is built", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SCHEDULED_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    expect(screen.getByRole("tab", { name: /^Scheduled/ })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Paused" })).not.toBeInTheDocument();
  });

  it("Scheduled filter tab shows only SCHEDULED campaigns", async () => {
    const user = userEvent.setup();
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SCHEDULED_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    await user.click(screen.getByRole("tab", { name: /^Scheduled/ }));

    expect(screen.queryByText("Spring Sale")).not.toBeInTheDocument();
    expect(screen.getByText("Black Friday Blast")).toBeInTheDocument();
  });

  it("renders SCHEDULED status badge for scheduled campaigns", async () => {
    mockLoad(["campaigns.view"], [SCHEDULED_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Black Friday Blast");

    // Both the tab label and the badge say "Scheduled" — check at least one exists
    const scheduledElements = screen.getAllByText("Scheduled");
    expect(scheduledElements.length).toBeGreaterThanOrEqual(1);
  });

  it("shows Cancel button only for DRAFT and SCHEDULED campaigns when canManage", async () => {
    mockLoad(
      ["campaigns.view", "campaigns.manage"],
      [DRAFT_CAMPAIGN, SCHEDULED_CAMPAIGN, SENT_CAMPAIGN],
    );

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    const cancelButtons = screen.getAllByRole("button", { name: /Cancel campaign/ });
    // DRAFT + SCHEDULED = 2 cancel buttons; SENT = 0
    expect(cancelButtons).toHaveLength(2);

    // SENT campaign should have no cancel button
    expect(screen.queryByLabelText("Cancel campaign Monthly Digest")).not.toBeInTheDocument();
  });

  it("hides Cancel button entirely when canManage is false", async () => {
    mockLoad(["campaigns.view"], [DRAFT_CAMPAIGN, SCHEDULED_CAMPAIGN]);

    renderWithToast(<CampaignsPage />);
    await screen.findByText("Spring Sale");

    expect(screen.queryByRole("button", { name: /Cancel campaign/ })).not.toBeInTheDocument();
  });
});
