import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { SupportSessionDetailPage } from "./support-session-detail-page";
import type { SupportSessionOverview } from "../types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const WRITE_OVERVIEW: SupportSessionOverview = {
  session: {
    id: "session-1",
    account_id: "acc-1",
    platform_admin_id: "admin-1",
    reason: "Fixing contact info",
    ticket_number: "SUP-1",
    access_level: "WRITE",
    started_at: "2026-08-07T00:00:00Z",
    expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    ended_at: null,
  },
  company: { name: "Acme Inc.", website: "https://acme.example.com", industry: "SaaS" },
  contacts: [
    {
      id: "contact-1",
      email: "alice@example.com",
      first_name: "Alice",
      last_name: "A",
      phone: null,
      status: "ACTIVE",
    },
  ],
  audit_events: [
    {
      id: "event-1",
      action: "support_session.started",
      entity_type: "support_session",
      actor_user_id: null,
      event_metadata: {},
      created_at: "2026-08-07T00:00:00Z",
    },
  ],
};

function renderPage() {
  return render(
    <ToastProvider>
      <SupportSessionDetailPage supportSessionId="session-1" />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("SupportSessionDetailPage", () => {
  it("renders company, contacts, and audit trail for a WRITE session with an Edit button", async () => {
    mockedApiFetch.mockResolvedValueOnce(WRITE_OVERVIEW);

    renderPage();

    expect(await screen.findByText("Fixing contact info")).toBeInTheDocument();
    expect(screen.getByText(/Acme Inc\./)).toBeInTheDocument();
    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("support_session.started")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
  });

  it("hides the Edit button for a READ-only session", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      ...WRITE_OVERVIEW,
      session: { ...WRITE_OVERVIEW.session, access_level: "READ" },
    });

    renderPage();

    await screen.findByText("alice@example.com");
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument();
  });

  it("edits a contact and reflects the saved value", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(WRITE_OVERVIEW);
    mockedApiFetch.mockResolvedValueOnce({ ...WRITE_OVERVIEW.contacts[0], first_name: "Alicia" });

    renderPage();
    await screen.findByText("alice@example.com");

    await user.click(screen.getByRole("button", { name: "Edit" }));
    const firstNameInput = screen.getByPlaceholderText("First name");
    await user.clear(firstNameInput);
    await user.type(firstNameInput, "Alicia");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/platform/support-sessions/session-1/contacts/contact-1",
        {
          method: "PATCH",
          body: JSON.stringify({
            email: "alice@example.com",
            first_name: "Alicia",
            last_name: "A",
            phone: "",
          }),
        },
      );
    });
    expect(await screen.findByText("Alicia A")).toBeInTheDocument();
  });

  it("shows a friendly message when the session has expired", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(410, "Support session has expired"));

    renderPage();

    expect(
      await screen.findByText("This support session has ended or expired."),
    ).toBeInTheDocument();
  });
});
