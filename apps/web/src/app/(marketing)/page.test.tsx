import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import LandingPage from "./page";

vi.mock("@/lib/auth", () => ({
  getCurrentUser: vi.fn().mockResolvedValue(null),
}));

describe("LandingPage", () => {
  it("renders the hero title and branding sections", () => {
    render(<LandingPage />);
    expect(screen.getByText(/Grow Faster. Market Smarter./i)).toBeInTheDocument();
    expect(screen.getByText(/Meet Your AI Marketing Team/i)).toBeInTheDocument();
    expect(screen.getByText(/Automate Entire Marketing Pipelines/i)).toBeInTheDocument();
    expect(screen.getByText(/Simple Plans That Scale With Your Growth/i)).toBeInTheDocument();
  });

  it("renders plans with USD by default and switches to INR when toggled", () => {
    render(<LandingPage />);

    // Default USD
    expect(screen.getByText("$19")).toBeInTheDocument();
    expect(screen.getByText("$49")).toBeInTheDocument();
    expect(screen.getAllByText("Custom").length).toBeGreaterThan(0);

    // Switch to INR
    const inrButton = screen.getByRole("button", { name: /₹ INR/i });
    fireEvent.click(inrButton);

    expect(screen.getByText("₹1,499")).toBeInTheDocument();
    expect(screen.getByText("₹3,999")).toBeInTheDocument();
    expect(screen.getAllByText("Custom").length).toBeGreaterThan(0);
  });

  it("renders the Pay-As-You-Go Credit Packs section with accurate catalog packs", () => {
    render(<LandingPage />);

    expect(screen.getByText(/Pay-As-You-Go Top-Up Credit Packs/i)).toBeInTheDocument();
    expect(screen.getByText("250 AI Runs")).toBeInTheDocument();
    expect(screen.getByText("1,000 AI Runs")).toBeInTheDocument();
    expect(screen.getByText("10,000 Email Sends")).toBeInTheDocument();
    expect(screen.getByText("2,500 Contact Slots")).toBeInTheDocument();
    expect(screen.getByText("50 Social Posts")).toBeInTheDocument();
  });
});
