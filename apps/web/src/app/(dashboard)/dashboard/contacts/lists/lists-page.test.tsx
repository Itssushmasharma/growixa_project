import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { Contact, ContactList, MeResponse } from "../types";
import { ListsPage } from "./lists-page";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderListsPage() {
  return render(
    <ToastProvider>
      <ListsPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const VIP_LIST: ContactList = {
  id: "list-1",
  name: "VIP customers",
  description: "Top tier",
  member_count: 2,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
};

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
  is_suppressed: false,
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("ListsPage", () => {
  it("renders lists with member counts", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/lists") return Promise.resolve([VIP_LIST]);
      if (path === "/contacts") return Promise.resolve([ALICE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderListsPage();

    expect(await screen.findByText("VIP customers")).toBeInTheDocument();
    expect(screen.getByText("Top tier")).toBeInTheDocument();
    expect(screen.getByText("2 members")).toBeInTheDocument();
  });

  it("shows an access-denied message for a user without contacts.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/contacts/lists") return Promise.resolve([]);
      if (path === "/contacts") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderListsPage();

    expect(await screen.findByText("You don't have access to view lists.")).toBeInTheDocument();
  });

  it("hides write controls for a view-only user", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/contacts/lists") return Promise.resolve([VIP_LIST]);
      if (path === "/contacts") return Promise.resolve([ALICE]);
      throw new Error(`unexpected path: ${path}`);
    });

    const user = userEvent.setup();
    renderListsPage();

    await screen.findByText("VIP customers");
    expect(screen.queryByRole("button", { name: "+ Add list" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Manage" }));
    expect(screen.getByText("You have view-only access to lists.")).toBeInTheDocument();
  });

  it("creates a list via the add form", async () => {
    const created: ContactList = { ...VIP_LIST, id: "list-2", name: "Newsletter", member_count: 0 };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/lists" && (!init || init.method === undefined)) {
        return Promise.resolve([]);
      }
      if (path === "/contacts") return Promise.resolve([]);
      if (path === "/contacts/lists" && init?.method === "POST") {
        return Promise.resolve(created);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderListsPage();

    await screen.findByText("No lists yet.");
    await user.click(screen.getByRole("button", { name: "+ Add list" }));
    await user.type(screen.getByLabelText("Name"), "Newsletter");
    await user.click(screen.getByRole("button", { name: "Create list" }));

    await waitFor(() => expect(screen.getByText("Newsletter")).toBeInTheDocument());
  });

  it("adds a contact to a list", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/lists" && (!init || init.method === undefined)) {
        return Promise.resolve([{ ...VIP_LIST, member_count: 0 }]);
      }
      if (path === "/contacts") return Promise.resolve([ALICE]);
      if (path === "/contacts/lists/list-1/members" && (!init || init.method === undefined)) {
        return Promise.resolve([]);
      }
      if (path === "/contacts/lists/list-1/members" && init?.method === "POST") {
        return Promise.resolve({ ...VIP_LIST, member_count: 1 });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderListsPage();

    await screen.findByText("VIP customers");
    await user.click(screen.getByRole("button", { name: "Manage" }));
    await user.selectOptions(screen.getByLabelText("Contact to add"), "contact-1");
    await user.click(screen.getByRole("button", { name: "Add to list" }));

    await waitFor(() => expect(screen.getByText("1 members")).toBeInTheDocument());
  });

  it("fetches list members on modal open and filters with live search", async () => {
    const BOB: Contact = {
      ...ALICE,
      id: "contact-2",
      email: "bob@example.com",
      first_name: "Bob",
      last_name: "Jones",
    };

    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/lists") return Promise.resolve([VIP_LIST]);
      if (path === "/contacts") return Promise.resolve([ALICE, BOB]);
      if (path === "/contacts/lists/list-1/members") return Promise.resolve([ALICE, BOB]);
      throw new Error(`unexpected path: ${path}`);
    });

    const user = userEvent.setup();
    renderListsPage();

    await screen.findByText("VIP customers");
    await user.click(screen.getByRole("button", { name: "Manage" }));

    await waitFor(() => expect(screen.getByText("alice@example.com")).toBeInTheDocument());
    expect(screen.getByText("bob@example.com")).toBeInTheDocument();
    expect(screen.getByText("Current Members (2)")).toBeInTheDocument();

    const searchInput = screen.getByLabelText("Search current members");
    await user.type(searchInput, "Bob");

    expect(screen.queryByText("alice@example.com")).not.toBeInTheDocument();
    expect(screen.getByText("bob@example.com")).toBeInTheDocument();
    expect(screen.getByText("Current Members (1 of 2)")).toBeInTheDocument();

    await user.clear(searchInput);
    await user.type(searchInput, "nonexistent");

    expect(screen.getByText(/No members match/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Clear search" }));

    expect(screen.getByText("alice@example.com")).toBeInTheDocument();
    expect(screen.getByText("bob@example.com")).toBeInTheDocument();
  });
});
