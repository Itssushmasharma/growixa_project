import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { AccountDetailPage } from "./account-detail-page";
import type { AccountDetail } from "../types";

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

function renderPage() {
  return render(
    <ToastProvider>
      <AccountDetailPage accountId="acc-1" />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("AccountDetailPage", () => {
  it("renders the account's users and security activity", async () => {
    mockedApiFetch.mockResolvedValueOnce(ACTIVE_ACCOUNT);
    mockedApiFetch.mockResolvedValueOnce([]); // support-session history
    mockedApiFetch.mockResolvedValueOnce({ permissions: [] }); // /platform/auth/me

    renderPage();

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Acme Owner")).toBeInTheDocument();
    expect(screen.getByText("owner@acme.example.com")).toBeInTheDocument();
    expect(screen.getByText("user.login")).toBeInTheDocument();
  });

  it("suspends the account via the Suspend button and refetches", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(ACTIVE_ACCOUNT);
    mockedApiFetch.mockResolvedValueOnce([]); // support-session history
    mockedApiFetch.mockResolvedValueOnce({ permissions: [] }); // /platform/auth/me
    mockedApiFetch.mockResolvedValueOnce({ ...ACTIVE_ACCOUNT, status: "SUSPENDED" });
    mockedApiFetch.mockResolvedValueOnce({ ...ACTIVE_ACCOUNT, status: "SUSPENDED" });

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
});
