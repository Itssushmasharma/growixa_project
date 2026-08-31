import { render, screen, within } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Footer from "./footer";

describe("Footer", () => {
  it("renders a contentinfo landmark", () => {
    render(<Footer />);
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("links all five engine stages", () => {
    render(<Footer />);
    const group = screen.getByRole("navigation", { name: /the engine/i });
    ["Find", "Qualify", "Create", "Send", "Manage"].forEach((name) => {
      expect(within(group).getByRole("link", { name })).toBeInTheDocument();
    });
  });

  it("links to login and get started free", () => {
    render(<Footer />);
    const group = screen.getByRole("navigation", { name: /product/i });
    expect(within(group).getByRole("link", { name: /log in/i })).toHaveAttribute("href", "/login");
    expect(within(group).getByRole("link", { name: /get started free/i })).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("states the honest build status in the base row", () => {
    render(<Footer />);
    expect(
      screen.getByText(
        "Campaigns and contacts are live. Find and Create are in beta. Qualify ships Q4.",
      ),
    ).toBeInTheDocument();
  });
});
