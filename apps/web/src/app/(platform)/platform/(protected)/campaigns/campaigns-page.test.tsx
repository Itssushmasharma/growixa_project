import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { CampaignsPage } from "./campaigns-page";
import type { CampaignOversightItem } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const SCHEDULED_CAMPAIGN: CampaignOversightItem = {
  id: "camp-1",
  account_id: "acc-1",
  account_name: "Acme Corp",
  name: "Suspicious Blast",
  status: "SCHEDULED",
  scheduled_at: "2026-08-08T00:00:00Z",
  created_at: "2026-08-07T00:00:00Z",
  updated_at: "2026-08-07T00:00:00Z",
};

const FAILED_CAMPAIGN: CampaignOversightItem = {
  id: "camp-2",
  account_id: "acc-2",
  account_name: "Other Co",
  name: "Failed Send",
  status: "FAILED",
  scheduled_at: null,
  created_at: "2026-08-07T00:00:00Z",
  updated_at: "2026-08-07T00:00:00Z",
};

function renderPage() {
  return render(
    <ToastProvider>
      <CampaignsPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("CampaignsPage", () => {
  it("renders queued and failed campaigns across accounts", async () => {
    mockedApiFetch.mockResolvedValueOnce([SCHEDULED_CAMPAIGN, FAILED_CAMPAIGN]);

    renderPage();

    expect(await screen.findByText("Suspicious Blast")).toBeInTheDocument();
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Failed Send")).toBeInTheDocument();
    expect(screen.getByText("Other Co")).toBeInTheDocument();
  });

  it("disables Pause for a campaign that isn't SCHEDULED", async () => {
    mockedApiFetch.mockResolvedValueOnce([FAILED_CAMPAIGN]);

    renderPage();
    await screen.findByText("Failed Send");

    expect(screen.getByRole("button", { name: "Pause" })).toBeDisabled();
  });

  it("pauses a scheduled campaign and shows a success toast", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce([SCHEDULED_CAMPAIGN]);
    mockedApiFetch.mockResolvedValueOnce({ ...SCHEDULED_CAMPAIGN, status: "SCHEDULED" });

    renderPage();
    await screen.findByText("Suspicious Blast");

    await user.click(screen.getByRole("button", { name: "Pause" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/campaigns/camp-1/pause", {
        method: "POST",
      });
    });
    expect(await screen.findByText("Campaign paused.")).toBeInTheDocument();
  });

  it("shows an error toast when the campaign can no longer be paused", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce([SCHEDULED_CAMPAIGN]);
    mockedApiFetch.mockRejectedValueOnce(new ApiError(409, "not cancellable"));

    renderPage();
    await screen.findByText("Suspicious Blast");

    await user.click(screen.getByRole("button", { name: "Pause" }));

    expect(await screen.findByText("This campaign can no longer be paused.")).toBeInTheDocument();
  });
});
