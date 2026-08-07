import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { SupportSessionPanel } from "./support-session-panel";
import type { SupportSession } from "../types";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const ACTIVE_SESSION: SupportSession = {
  id: "session-1",
  account_id: "acc-1",
  platform_admin_id: "admin-1",
  reason: "Investigating a delivery issue",
  ticket_number: "SUP-1",
  access_level: "READ",
  started_at: "2026-08-07T00:00:00Z",
  expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
  ended_at: null,
};

function renderPanel() {
  return render(
    <ToastProvider>
      <SupportSessionPanel accountId="acc-1" />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockPush.mockReset();
});

describe("SupportSessionPanel", () => {
  it("renders session history and hides the write option without the write permission", async () => {
    mockedApiFetch.mockResolvedValueOnce([ACTIVE_SESSION]);
    mockedApiFetch.mockResolvedValueOnce({ permissions: ["platform.support_session.create"] });

    renderPanel();

    expect(await screen.findByText("Investigating a delivery issue")).toBeInTheDocument();
    expect(screen.getByText("#SUP-1")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByLabelText("Read-only")).toBeInTheDocument();
    expect(screen.queryByLabelText("Read & write")).not.toBeInTheDocument();
  });

  it("shows the write option when the admin holds platform.support_session.write", async () => {
    mockedApiFetch.mockResolvedValueOnce([]);
    mockedApiFetch.mockResolvedValueOnce({
      permissions: ["platform.support_session.create", "platform.support_session.write"],
    });

    renderPanel();

    expect(await screen.findByText("No support sessions yet.")).toBeInTheDocument();
    expect(screen.getByLabelText("Read & write")).toBeInTheDocument();
  });

  it("starts a session and navigates to its detail page", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce([]);
    mockedApiFetch.mockResolvedValueOnce({ permissions: ["platform.support_session.create"] });
    mockedApiFetch.mockResolvedValueOnce({ ...ACTIVE_SESSION, id: "session-2" });

    renderPanel();
    await screen.findByText("No support sessions yet.");

    await user.type(screen.getByLabelText("Reason"), "Customer reported an issue");
    await user.type(screen.getByLabelText("Ticket number"), "SUP-99");
    await user.click(screen.getByRole("button", { name: "Start support session" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/accounts/acc-1/support-sessions", {
        method: "POST",
        body: JSON.stringify({
          reason: "Customer reported an issue",
          ticket_number: "SUP-99",
          access_level: "READ",
        }),
      });
    });
    expect(mockPush).toHaveBeenCalledWith("/platform/support-sessions/session-2");
  });
});
