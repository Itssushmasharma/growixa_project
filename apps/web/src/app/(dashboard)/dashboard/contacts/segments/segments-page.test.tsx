import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { Contact, MeResponse, Segment } from "../types";
import { SegmentsPage } from "./segments-page";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderSegmentsPage() {
  return render(
    <ToastProvider>
      <SegmentsPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const ACTIVE_SEGMENT: Segment = {
  id: "segment-1",
  name: "Active customers",
  type: "DYNAMIC",
  member_count: 3,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
  rules: [{ id: "rule-1", field: "status", operator: "equals", value: "ACTIVE" }],
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

describe("SegmentsPage", () => {
  it("renders segments with type badge, member count, and rule summary", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/segments") return Promise.resolve([ACTIVE_SEGMENT]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderSegmentsPage();

    expect(await screen.findByText("Active customers")).toBeInTheDocument();
    expect(screen.getByText("Dynamic")).toBeInTheDocument();
    expect(screen.getByText("3 members")).toBeInTheDocument();
    expect(screen.getByText('Status equals "ACTIVE"')).toBeInTheDocument();
  });

  it("shows an access-denied message for a user without contacts.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/contacts/segments") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderSegmentsPage();

    expect(await screen.findByText("You don't have access to view segments.")).toBeInTheDocument();
  });

  it("hides the add-segment control for a view-only user", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/contacts/segments") return Promise.resolve([ACTIVE_SEGMENT]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderSegmentsPage();

    await screen.findByText("Active customers");
    expect(screen.queryByRole("button", { name: "+ Add segment" })).not.toBeInTheDocument();
  });

  it("creates a segment with a rule via the builder form", async () => {
    const created: Segment = { ...ACTIVE_SEGMENT, id: "segment-2", name: "VIP tag" };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/segments" && (!init || init.method === undefined)) {
        return Promise.resolve([]);
      }
      if (path === "/contacts/segments" && init?.method === "POST") {
        return Promise.resolve(created);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderSegmentsPage();

    await screen.findByText("No segments yet.");
    await user.click(screen.getByRole("button", { name: "+ Add segment" }));
    await user.type(screen.getByLabelText("Name"), "VIP tag");
    await user.selectOptions(screen.getByLabelText("Rule 1 field"), "tag");
    await user.type(screen.getByLabelText("Rule 1 value"), "VIP");
    await user.click(screen.getByRole("button", { name: "Create segment" }));

    await waitFor(() => {
      const [, postCall] =
        mockedApiFetch.mock.calls.find(
          ([path, callInit]) => path === "/contacts/segments" && callInit?.method === "POST",
        ) ?? [];
      expect(postCall).toBeDefined();
      const body = JSON.parse((postCall as RequestInit).body as string) as {
        rules: { field: string; operator: string; value: string }[];
      };
      expect(body.rules).toEqual([{ field: "tag", operator: "equals", value: "VIP" }]);
    });
  });

  it("views a segment's members", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/segments") return Promise.resolve([ACTIVE_SEGMENT]);
      if (path === "/contacts/segments/segment-1/members") return Promise.resolve([ALICE]);
      throw new Error(`unexpected path: ${path}`);
    });

    const user = userEvent.setup();
    renderSegmentsPage();

    await screen.findByText("Active customers");
    await user.click(screen.getByRole("button", { name: "View members" }));

    await waitFor(() => expect(screen.getByText("alice@example.com")).toBeInTheDocument());
  });
});
