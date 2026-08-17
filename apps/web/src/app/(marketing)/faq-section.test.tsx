import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { FaqSection } from "./faq-section";

describe("FaqSection Component", () => {
  it("renders the 5 FAQ questions and header", () => {
    render(<FaqSection />);

    expect(screen.getByText("Got Questions?")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Frequently Asked Questions" })).toBeInTheDocument();
    expect(screen.getByText("What exactly is Growixa?")).toBeInTheDocument();
    expect(
      screen.getByText("Can I connect my own Custom SMTP and AI provider keys?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("How is my account data isolated from other customers?"),
    ).toBeInTheDocument();
    expect(screen.getByText("How do one-time credit top-ups work?")).toBeInTheDocument();
    expect(
      screen.getByText("Are there any onboarding fees or lock-in contracts?"),
    ).toBeInTheDocument();
  });

  it("toggles accordion answers on click and expands aria-expanded", async () => {
    const user = userEvent.setup();
    render(<FaqSection />);

    const firstButton = screen.getByRole("button", { name: /What exactly is Growixa\?/i });
    expect(firstButton).toHaveAttribute("aria-expanded", "false");

    await user.click(firstButton);
    expect(firstButton).toHaveAttribute("aria-expanded", "true");

    const secondButton = screen.getByRole("button", {
      name: /Can I connect my own Custom SMTP and AI provider keys\?/i,
    });
    await user.click(secondButton);

    expect(firstButton).toHaveAttribute("aria-expanded", "false");
    expect(secondButton).toHaveAttribute("aria-expanded", "true");
  });

  it("contains verified product claims without false security or trial guarantees", () => {
    render(<FaqSection />);

    // Verified security copy
    expect(
      screen.getByText(
        /Every customer-data table is keyed to your account ID, and all queries enforce strict account-level isolation/i,
      ),
    ).toBeInTheDocument();

    // No unbacked 14-day free trial guarantee
    expect(screen.queryByText(/14-day free trial/i)).toBeNull();

    // No claims about in-panel cancellation
    expect(screen.queryByText(/cancel at any time directly from your billing panel/i)).toBeNull();
  });
});
