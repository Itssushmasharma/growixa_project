import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("presents Growixa as a clear growth execution platform", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      /Turn marketing goals into approved growth campaigns/i,
    );
    expect(screen.getByText(/audience data, brand-aware content/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /three clear steps/i })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /Everything your marketing team needs/i }),
    ).toBeInTheDocument();
  });

  it("shows implemented capabilities without fake customer endorsements", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { name: "Email campaigns" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Human approvals" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Actionable analytics" })).toBeInTheDocument();
    expect(screen.queryByText(/trusted by/i)).not.toBeInTheDocument();
  });

  it("uses working registration, pricing and contact links", () => {
    render(<HomePage />);
    expect(screen.getAllByRole("link", { name: /Start free/i })[0]).toHaveAttribute(
      "href",
      "/register",
    );
    expect(screen.getAllByRole("link", { name: /View current pricing/i })[0]).toHaveAttribute(
      "href",
      "/pricing",
    );
    expect(screen.getByRole("link", { name: /See how it works/i })).toHaveAttribute(
      "href",
      "#how-it-works",
    );
    expect(screen.getByRole("link", { name: /Talk to a Growixa specialist/i })).toHaveAttribute(
      "href",
      "/contact",
    );
    expect(screen.getAllByRole("link", { name: /Create campaign/i })[0]).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("answers key safety and onboarding questions", () => {
    render(<HomePage />);
    expect(screen.getByText("Can I start without a credit card?")).toBeInTheDocument();
    expect(screen.getByText("Does AI publish automatically?")).toBeInTheDocument();
    expect(screen.getByText(/human review and approval step/i)).toBeInTheDocument();
  });
});
