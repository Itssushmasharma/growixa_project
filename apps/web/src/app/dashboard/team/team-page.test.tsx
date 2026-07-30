import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { TeamPage } from "./team-page";
import type { MeResponse, Role, TeamMember } from "./types";

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}));

const mockedApiFetch = vi.mocked(apiFetch);

function renderTeamPage() {
  return render(
    <ToastProvider>
      <TeamPage />
    </ToastProvider>,
  );
}

const ROLES: Role[] = [
  { id: "role-analyst", name: "Analyst" },
  { id: "role-viewer", name: "Viewer" },
];

const ADMIN_MEMBER: TeamMember = {
  id: "user-1",
  email: "admin@example.com",
  full_name: "Admin User",
  status: "ACTIVE",
  last_login_at: null,
  roles: ["Admin"],
};

const VIEWER_MEMBER: TeamMember = {
  id: "user-2",
  email: "viewer@example.com",
  full_name: "Viewer User",
  status: "ACTIVE",
  last_login_at: null,
  roles: ["Viewer"],
};

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("TeamPage", () => {
  it("renders the member list with roles and status", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["users.manage"]));
      if (path === "/users") return Promise.resolve([ADMIN_MEMBER, VIEWER_MEMBER]);
      if (path === "/roles") return Promise.resolve(ROLES);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTeamPage();

    expect(await screen.findByText(/Admin User/)).toBeInTheDocument();
    expect(screen.getByText("Viewer User")).toBeInTheDocument();
    expect(screen.getAllByText("Active")).toHaveLength(2);
  });

  it("shows an access-denied message for a user without users.manage", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/users") return Promise.resolve([ADMIN_MEMBER, VIEWER_MEMBER]);
      if (path === "/roles") return Promise.resolve(ROLES);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTeamPage();

    expect(
      await screen.findByText("You don't have access to manage the team."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Admin User")).not.toBeInTheDocument();
  });

  it("sends an invitation and shows the returned token", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["users.manage"]));
      if (path === "/users") return Promise.resolve([ADMIN_MEMBER]);
      if (path === "/roles") return Promise.resolve(ROLES);
      if (path === "/users/invitations" && init?.method === "POST") {
        return Promise.resolve({
          id: "invite-1",
          email: "new@example.com",
          expires_at: "2026-08-05T00:00:00Z",
          token: "raw-invite-token",
        });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderTeamPage();
    await screen.findByText(/Admin User/);

    await user.click(screen.getByRole("button", { name: "+ Invite user" }));
    await user.type(screen.getByLabelText("Email"), "new@example.com");
    await user.click(screen.getByRole("button", { name: "Send invite" }));

    await waitFor(() =>
      expect(screen.getByText(/Invitation sent to new@example.com/)).toBeInTheDocument(),
    );
    expect(screen.getByText("raw-invite-token")).toBeInTheDocument();
  });

  it("changes a member's role via the role select", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["users.manage"]));
      if (path === "/users") return Promise.resolve([VIEWER_MEMBER]);
      if (path === "/roles") return Promise.resolve(ROLES);
      if (path === "/users/user-2/role" && init?.method === "PATCH") {
        return Promise.resolve({ ...VIEWER_MEMBER, roles: ["Analyst"] });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderTeamPage();
    await screen.findByText("Viewer User");

    await user.selectOptions(screen.getByDisplayValue("Viewer"), "Analyst");

    await waitFor(() => {
      const [, roleChangeCall] =
        mockedApiFetch.mock.calls.find(([path]) => path === "/users/user-2/role") ?? [];
      expect(roleChangeCall).toBeDefined();
    });
  });

  it("disables a member via the toggle button", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["users.manage"]));
      if (path === "/users") return Promise.resolve([VIEWER_MEMBER]);
      if (path === "/roles") return Promise.resolve(ROLES);
      if (path === "/users/user-2/status" && init?.method === "PATCH") {
        return Promise.resolve({ ...VIEWER_MEMBER, status: "DISABLED" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderTeamPage();
    await screen.findByText("Viewer User");

    await user.click(screen.getByRole("button", { name: "Disable" }));

    await waitFor(() => expect(screen.getByText("Disabled")).toBeInTheDocument());
  });
});
