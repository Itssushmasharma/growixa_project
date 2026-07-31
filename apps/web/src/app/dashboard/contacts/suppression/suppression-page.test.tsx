import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { Contact, MeResponse, SuppressionEntry } from "../types";
import { SuppressionPage } from "./suppression-page";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderSuppressionPage() {
  return render(
    <ToastProvider>
      <SuppressionPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const ALICE: Contact = {
  id: "contact-1",
  email: "alice@example.com",
  first_name: "Alice",
  last_name: null,
  phone: null,
  status: "ACTIVE",
  source: null,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
  custom_fields: {},
  tags: [],
  is_suppressed: true,
};

const BOUNCED_ENTRY: SuppressionEntry = {
  id: "suppression-1",
  email: "bounced@example.com",
  reason: "BOUNCED",
  contact_id: null,
  suppressed_at: "2026-07-01T00:00:00Z",
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("SuppressionPage", () => {
  it("renders suppression entries", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/suppression") return Promise.resolve([BOUNCED_ENTRY]);
      if (path === "/contacts") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderSuppressionPage();

    expect(await screen.findByText("bounced@example.com")).toBeInTheDocument();
    expect(screen.getByText("BOUNCED")).toBeInTheDocument();
    expect(screen.getByText(/No matching contact/)).toBeInTheDocument();
  });

  it("shows an access-denied message for a user without contacts.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/contacts/suppression") return Promise.resolve([]);
      if (path === "/contacts") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderSuppressionPage();

    expect(
      await screen.findByText("You don't have access to view the suppression list."),
    ).toBeInTheDocument();
  });

  it("hides the suppress-email control for a view-only user", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/contacts/suppression") return Promise.resolve([BOUNCED_ENTRY]);
      if (path === "/contacts") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderSuppressionPage();

    await screen.findByText("bounced@example.com");
    expect(screen.queryByRole("button", { name: "+ Suppress an email" })).not.toBeInTheDocument();
  });

  it("suppresses an email via the add form", async () => {
    const created: SuppressionEntry = {
      id: "suppression-2",
      email: "new@example.com",
      reason: "MANUAL",
      contact_id: null,
      suppressed_at: "2026-07-01T00:00:00Z",
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/suppression" && (!init || init.method === undefined)) {
        return Promise.resolve([]);
      }
      if (path === "/contacts") return Promise.resolve([ALICE]);
      if (path === "/contacts/suppression" && init?.method === "POST") {
        return Promise.resolve(created);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderSuppressionPage();

    await screen.findByText("No suppressed emails yet.");
    await user.click(screen.getByRole("button", { name: "+ Suppress an email" }));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.selectOptions(screen.getByLabelText("Reason"), "MANUAL");
    await user.click(screen.getByRole("button", { name: "Suppress email" }));

    await waitFor(() => expect(screen.getByText("new@example.com")).toBeInTheDocument());
  });

  it("updates the same entry in place when re-suppressing an already-suppressed email", async () => {
    const updated: SuppressionEntry = { ...BOUNCED_ENTRY, reason: "COMPLAINED" };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/suppression" && (!init || init.method === undefined)) {
        return Promise.resolve([BOUNCED_ENTRY]);
      }
      if (path === "/contacts") return Promise.resolve([]);
      if (path === "/contacts/suppression" && init?.method === "POST") {
        return Promise.resolve(updated);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderSuppressionPage();

    await screen.findByText("bounced@example.com");
    await user.click(screen.getByRole("button", { name: "+ Suppress an email" }));
    await user.type(screen.getByLabelText("Email"), "bounced@example.com");
    await user.selectOptions(screen.getByLabelText("Reason"), "COMPLAINED");
    await user.click(screen.getByRole("button", { name: "Suppress email" }));

    await waitFor(() => expect(screen.getByText("COMPLAINED")).toBeInTheDocument());
    expect(screen.getAllByText("bounced@example.com")).toHaveLength(1);
  });
});
