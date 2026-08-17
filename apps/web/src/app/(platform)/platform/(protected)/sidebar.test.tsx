import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Sidebar } from "./sidebar";

vi.mock("next/navigation", () => ({
  usePathname: () => "/platform/accounts",
}));

describe("Sidebar", () => {
  it("shows only the nav items the admin has permission for", () => {
    render(<Sidebar permissions={["platform.accounts.manage"]} />);

    expect(screen.getByRole("link", { name: "Accounts" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usage" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Campaigns" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Providers Hub" })).not.toBeInTheDocument();
  });

  it("shows every nav item for an admin with every permission", () => {
    render(<Sidebar permissions={["platform.accounts.manage", "platform.usage.manage"]} />);

    expect(screen.getByRole("link", { name: "Accounts" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Usage" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Campaigns" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Providers Hub" })).toBeInTheDocument();
  });
});
