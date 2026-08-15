import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DashboardShell } from "./dashboard-shell";

vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
}));

afterEach(() => {
  vi.restoreAllMocks();
});

describe("DashboardShell", () => {
  it("renders the sidebar open by default and toggles it via the hamburger button", async () => {
    const user = userEvent.setup();
    render(
      <DashboardShell permissions={["users.manage"]} fullName="Admin User">
        <p>Page content</p>
      </DashboardShell>,
    );

    expect(screen.getByText("Page content")).toBeInTheDocument();
    expect(screen.getByText("Admin User")).toBeInTheDocument();

    const toggle = screen.getByRole("button", { name: "Collapse sidebar" });
    expect(toggle).toHaveAttribute("aria-expanded", "true");

    await user.click(toggle);
    expect(screen.getByRole("button", { name: "Expand sidebar" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );

    await user.click(screen.getByRole("button", { name: "Expand sidebar" }));
    expect(screen.getByRole("button", { name: "Collapse sidebar" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("defaults to closed on a mobile viewport", async () => {
    vi.spyOn(window, "matchMedia").mockImplementation(
      (query: string) =>
        ({
          matches: true,
          media: query,
          addEventListener: () => {},
          removeEventListener: () => {},
        }) as unknown as MediaQueryList,
    );

    render(
      <DashboardShell permissions={[]} fullName="Mobile User">
        <p>Page content</p>
      </DashboardShell>,
    );

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Expand sidebar" })).toHaveAttribute(
        "aria-expanded",
        "false",
      ),
    );
  });

  it("filters sidebar nav items by permission", () => {
    const { rerender } = render(
      <DashboardShell permissions={[]} fullName="Viewer User">
        <p>Page content</p>
      </DashboardShell>,
    );

    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Team" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Audit Log" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "System Health" })).not.toBeInTheDocument();

    rerender(
      <DashboardShell permissions={["admin.access"]} fullName="Admin User">
        <p>Page content</p>
      </DashboardShell>,
    );

    expect(screen.getByRole("link", { name: "System Health" })).toBeInTheDocument();
  });

  it("collapses and expands an individual section independently of the others", async () => {
    const user = userEvent.setup();
    render(
      <DashboardShell permissions={["contacts.view", "users.manage"]} fullName="Admin User">
        <p>Page content</p>
      </DashboardShell>,
    );

    const audienceHeader = screen.getByRole("button", { name: "AUDIENCE" });
    expect(audienceHeader).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("link", { name: "Contacts" })).toBeInTheDocument();

    await user.click(audienceHeader);
    expect(audienceHeader).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("link", { name: "Contacts" })).not.toBeInTheDocument();
    // unrelated sections are unaffected
    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Team" })).toBeInTheDocument();

    await user.click(audienceHeader);
    expect(audienceHeader).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("link", { name: "Contacts" })).toBeInTheDocument();
  });

  it("renders the global search input, AI credits meter, and user company profile", () => {
    render(
      <DashboardShell
        permissions={[]}
        fullName="Ravi Sharma"
        companyName="TechCorp Global"
      >
        <p>Dashboard</p>
      </DashboardShell>
    );

    expect(screen.getByPlaceholderText(/Search dashboard\.\.\. \(⌘K\)/i)).toBeInTheDocument();
    expect(screen.getByText("AI Credits")).toBeInTheDocument();
    expect(screen.getByText("Ravi Sharma")).toBeInTheDocument();
    expect(screen.getByText("TechCorp Global")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Upgrade/i })).toBeInTheDocument();
  });
});

