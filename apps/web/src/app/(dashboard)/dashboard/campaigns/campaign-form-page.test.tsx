import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";
import { ToastProvider } from "@/components/toast/toast-context";

import type { EmailTemplate } from "../templates/types";
import { CampaignFormPage } from "./campaign-form-page";
import type {
  Campaign,
  CampaignReport,
  ContactListSummary,
  MeResponse,
  SegmentSummary,
  SenderIdentity,
} from "./types";

const mockPush = vi.fn();
const mockBack = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderFormPage(props: { mode: "create" | "edit"; campaignId?: string }) {
  return render(
    <ToastProvider>
      <CampaignFormPage {...props} />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const IDENTITY: SenderIdentity = {
  id: "identity-1",
  email_provider_connection_id: "connection-1",
  from_email: "hello@growixa.local",
  from_name: "Growixa",
  reply_to_email: null,
  verification_status: "VERIFIED",
};

const LIST: ContactListSummary = { id: "list-1", name: "VIP Customers", member_count: 42 };
const SEGMENT: SegmentSummary = { id: "segment-1", name: "Active Users", member_count: 120 };

const TEMPLATE: EmailTemplate = {
  id: "template-1",
  name: "Welcome email",
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  current_version: {
    id: "version-1",
    template_id: "template-1",
    version_number: 1,
    subject: "Welcome to Growixa",
    body_html: "<p>Hello</p>",
    body_text: "Hello",
    created_at: "2026-08-06T00:00:00Z",
  },
};

const DRAFT_CAMPAIGN: Campaign = {
  id: "campaign-1",
  name: "Spring Sale",
  subject: "Spring is here",
  body_html: "<p>Save 20%</p>",
  body_text: null,
  template_id: null,
  sender_identity_id: "identity-1",
  recipient_type: "ALL_CONTACTS",
  recipient_segment_id: null,
  recipient_list_id: null,
  status: "DRAFT",
  scheduled_at: null,
  cancelled_at: null,
  idempotency_key: "idem-key-1",
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  sent_at: null,
};

function mockBaseFetches(permissions: string[]) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
    if (path === "/contacts/lists") return Promise.resolve([LIST]);
    if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
    if (path === "/templates") return Promise.resolve([TEMPLATE]);
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockPush.mockReset();
  mockBack.mockReset();
});

describe("CampaignFormPage", () => {
  it("shows an access-denied message for a user without campaigns.manage on create", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });

    expect(
      await screen.findByText("You don't have access to create campaigns."),
    ).toBeInTheDocument();
  });

  it("creates a campaign and navigates to its detail page", async () => {
    const user = userEvent.setup();
    mockBaseFetches(["campaigns.view", "campaigns.manage"]);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns" && init?.method === "POST") {
        return Promise.resolve({ ...DRAFT_CAMPAIGN, id: "new-campaign" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New campaign" });

    await user.type(screen.getByLabelText("Campaign name"), "Spring Sale");
    await user.type(screen.getByLabelText("Email subject"), "Spring is here");
    await user.selectOptions(screen.getByLabelText("Sender identity"), "identity-1");
    await user.type(screen.getByLabelText("HTML body"), "<p>Save 20%</p>");
    await user.click(screen.getByRole("button", { name: "Create campaign" }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/dashboard/campaigns/new-campaign"));
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/campaigns",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("loads content from a selected template", async () => {
    const user = userEvent.setup();
    mockBaseFetches(["campaigns.view", "campaigns.manage"]);

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New campaign" });

    await user.selectOptions(
      screen.getByLabelText("Load content from a template (optional)"),
      "template-1",
    );

    expect(screen.getByLabelText("Email subject")).toHaveValue("Welcome to Growixa");
    expect(screen.getByLabelText("HTML body")).toHaveValue("<p>Hello</p>");
  });

  it("requires a target list once Recipients is set to a specific list", async () => {
    const user = userEvent.setup();
    mockBaseFetches(["campaigns.view", "campaigns.manage"]);

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New campaign" });

    await user.selectOptions(screen.getByLabelText("Recipients"), "LIST");

    expect(screen.getByLabelText("List")).toBeRequired();
  });

  it("loads an existing draft campaign as editable", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });

    const nameInput = await screen.findByLabelText("Campaign name");
    expect(nameInput).toHaveValue("Spring Sale");
    expect(nameInput).not.toBeDisabled();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
  });

  it("shows a sent campaign as read-only with no Send now button", async () => {
    const sentCampaign: Campaign = { ...DRAFT_CAMPAIGN, status: "SENT" };
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(sentCampaign);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });

    const nameInput = await screen.findByLabelText("Campaign name");
    expect(nameInput).toBeDisabled();
    expect(
      screen.getByText("This campaign is no longer a draft and can't be edited."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save changes" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send now" })).not.toBeInTheDocument();
    // Test-send stays available regardless of status.
    expect(screen.getByRole("button", { name: "Send test" })).toBeInTheDocument();
  });

  it("shows the delivery report for a sent campaign", async () => {
    const sentCampaign: Campaign = { ...DRAFT_CAMPAIGN, status: "SENT" };
    const report: CampaignReport = {
      campaign_id: "campaign-1",
      sent: 200,
      delivered: 190,
      opened: 95,
      clicked: 38,
      bounced: 10,
      complained: 1,
    };
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(sentCampaign);
      if (path === "/campaigns/campaign-1/report") return Promise.resolve(report);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    expect(await screen.findByText("Delivery report")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("190 (95%)")).toBeInTheDocument();
    expect(screen.getByText("95 (50%)")).toBeInTheDocument();
    expect(screen.getByText("38 (20%)")).toBeInTheDocument();
    expect(screen.getByText("10 (5%)")).toBeInTheDocument();
    expect(screen.getByText("1 (1%)")).toBeInTheDocument();
  });

  it("does not show a delivery report for a draft campaign", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    expect(screen.queryByText("Delivery report")).not.toBeInTheDocument();
  });

  it("shows raw counts without a percentage when nothing was sent yet", async () => {
    const sendingCampaign: Campaign = { ...DRAFT_CAMPAIGN, status: "SENDING" };
    const report: CampaignReport = {
      campaign_id: "campaign-1",
      sent: 0,
      delivered: 0,
      opened: 0,
      clicked: 0,
      bounced: 0,
      complained: 0,
    };
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(sendingCampaign);
      if (path === "/campaigns/campaign-1/report") return Promise.resolve(report);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    expect(await screen.findByText("Delivery report")).toBeInTheDocument();
    expect(screen.getAllByText("0")).toHaveLength(6);
  });

  it("still renders the campaign when the report fetch fails", async () => {
    const sentCampaign: Campaign = { ...DRAFT_CAMPAIGN, status: "SENT" };
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(sentCampaign);
      if (path === "/campaigns/campaign-1/report") return Promise.reject(new Error("boom"));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });

    expect(await screen.findByLabelText("Campaign name")).toHaveValue("Spring Sale");
    expect(screen.queryByText("Delivery report")).not.toBeInTheDocument();
  });

  it("hides the test/send panel entirely for a user without campaigns.send", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1") return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    expect(screen.queryByRole("button", { name: "Send test" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Send now" })).not.toBeInTheDocument();
  });

  it("sends a test email", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      if (path === "/campaigns/campaign-1/test-send" && init?.method === "POST") {
        return Promise.resolve(undefined);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    await user.type(screen.getByLabelText("Send a test email"), "qa@example.com");
    await user.click(screen.getByRole("button", { name: "Send test" }));

    expect(await screen.findByText("Test email sent to qa@example.com.")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/campaigns/campaign-1/test-send",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ to_email: "qa@example.com" }),
      }),
    );
  });

  it("sends a draft campaign now after confirmation", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      if (path === "/campaigns/campaign-1/send" && init?.method === "POST") {
        return Promise.resolve({ job_id: "job-1" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    await user.click(screen.getByRole("button", { name: "Send now" }));

    expect(
      await screen.findByText("Campaign is sending — check back shortly for delivery status."),
    ).toBeInTheDocument();
    expect(screen.getByText("SENDING")).toBeInTheDocument();
  });

  it("does not send when the confirmation is declined", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    await user.click(screen.getByRole("button", { name: "Send now" }));

    expect(mockedApiFetch).not.toHaveBeenCalledWith(
      "/campaigns/campaign-1/send",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("renders Schedule for Later radio button for DRAFT campaigns with canManage", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    expect(screen.getByLabelText("Send Now")).toBeInTheDocument();
    expect(screen.getByLabelText("Schedule for Later")).toBeInTheDocument();
  });

  it("shows datetime picker when Schedule for Later is selected", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    await user.click(screen.getByLabelText("Schedule for Later"));

    expect(screen.getByLabelText("Send date & time")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirm schedule" })).toBeInTheDocument();
  });

  it("hides Send Mode selector when canManage is false", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.send"]));
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    expect(screen.queryByLabelText("Schedule for Later")).not.toBeInTheDocument();
  });

  it("calls POST /schedule with correct ISO timestamp on confirm", async () => {
    const user = userEvent.setup();
    const SCHEDULED_BACK: Campaign = {
      ...DRAFT_CAMPAIGN,
      status: "SCHEDULED",
      scheduled_at: "2026-11-01T09:00:00Z",
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["campaigns.view", "campaigns.manage", "campaigns.send"]),
        );
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/contacts/lists") return Promise.resolve([LIST]);
      if (path === "/contacts/segments") return Promise.resolve([SEGMENT]);
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/campaigns/campaign-1" && !init) return Promise.resolve(DRAFT_CAMPAIGN);
      if (path === "/campaigns/campaign-1/schedule" && init?.method === "POST")
        return Promise.resolve(SCHEDULED_BACK);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", campaignId: "campaign-1" });
    await screen.findByLabelText("Campaign name");

    await user.click(screen.getByLabelText("Schedule for Later"));
    const picker = screen.getByLabelText("Send date & time");
    await user.type(picker, "2026-11-01T09:00");
    await user.click(screen.getByRole("button", { name: "Confirm schedule" }));

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/campaigns/campaign-1/schedule",
      expect.objectContaining({ method: "POST" }),
    );
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/dashboard/campaigns"));
  });
});
