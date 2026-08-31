import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import PricingPage from "./page";

describe("PricingPage", () => {
  it("renders all four tier cards and FAQs", () => {
    render(<PricingPage />);
    expect(screen.getByRole("heading", { name: "Free" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Starter" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Growth" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Scale" })).toBeInTheDocument();
    expect(screen.getByText(/The ones worth asking before you pay/i)).toBeInTheDocument();
  });

  it("renders prices in USD by default and switches to INR when toggled", () => {
    render(<PricingPage />);

    // Default USD
    expect(screen.getByText("$29")).toBeInTheDocument();
    expect(screen.getByText("$89")).toBeInTheDocument();

    // Toggle to INR
    const inrButton = screen.getByRole("button", { name: /INR ₹/i });
    fireEvent.click(inrButton);

    expect(screen.getByText("₹2,400")).toBeInTheDocument();
    expect(screen.getByText("₹7,400")).toBeInTheDocument();
  });

  it("adjusts prices when toggling annual billing with 2 months free", () => {
    render(<PricingPage />);

    // Monthly USD
    expect(screen.getByText("$29")).toBeInTheDocument();

    // Toggle to Yearly
    const yearlyButton = screen.getByRole("button", { name: /Yearly/i });
    fireEvent.click(yearlyButton);

    expect(screen.getByText("$24")).toBeInTheDocument();
    expect(screen.getByText("$74")).toBeInTheDocument();
  });
});
