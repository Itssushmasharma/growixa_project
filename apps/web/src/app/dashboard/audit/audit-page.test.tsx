import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { AuditPage } from "./audit-page";
import type { AuditLogEntry, MeResponse, UserSummary } from "./types";

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}));

const mockedApiFetch = vi.mocked(apiFetch);

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const ADMIN: UserSummary = { id: "user-1", email: "admin@example.com", full_name: "Admin User" };

const LOGIN_EVENT: AuditLogEntry = {
  id: "event-1",
  actor_user_id: "user-1",
  action: "user.login",
  entity_type: "user",
  entity_id: "user-1",
  event_metadata: {},
  ip_address: "127.0.0.1",
  user_agent: "vitest",
  created_at: "2026-07-31T00:00:00Z",
};

const CONTACT_EVENT: AuditLogEntry = {
  id: "event-2",
  actor_user_id: "user-1",
  action: "contact.created",
  entity_type: "contact",
  entity_id: "contact-1",
  event_metadata: { email: "someone@example.com" },
  ip_address: null,
  user_agent: null,
  created_at: "2026-07-31T01:00:00Z",
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("AuditPage", () => {
  it("renders audit events with resolved actor emails", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["audit.view"]));
      if (path === "/audit") return Promise.resolve([LOGIN_EVENT, CONTACT_EVENT]);
      if (path === "/users") return Promise.resolve([ADMIN]);
      throw new Error(`unexpected path: ${path}`);
    });

    render(<AuditPage />);

    expect(await screen.findByText("user.login")).toBeInTheDocument();
    expect(screen.getByText("contact.created")).toBeInTheDocument();
    expect(screen.getAllByText(/admin@example.com/)).toHaveLength(2);
  });

  it("shows an access-denied message for a user without audit.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      throw new Error(`unexpected call: ${path}`);
    });

    render(<AuditPage />);

    expect(
      await screen.findByText("You don't have access to view the audit log."),
    ).toBeInTheDocument();
  });

  it("filters events by entity type", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["audit.view"]));
      if (path === "/audit") return Promise.resolve([LOGIN_EVENT, CONTACT_EVENT]);
      if (path === "/users") return Promise.resolve([ADMIN]);
      throw new Error(`unexpected path: ${path}`);
    });

    const user = userEvent.setup();
    render(<AuditPage />);

    await screen.findByText("user.login");
    await user.selectOptions(screen.getByLabelText("Filter by entity type"), "contact");

    expect(screen.queryByText("user.login")).not.toBeInTheDocument();
    expect(screen.getByText("contact.created")).toBeInTheDocument();
  });

  it("shows an empty state when there are no audit events", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["audit.view"]));
      if (path === "/audit") return Promise.resolve([]);
      if (path === "/users") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    render(<AuditPage />);

    expect(await screen.findByText("No audit events yet.")).toBeInTheDocument();
  });
});
