import { render, screen } from "@testing-library/react";
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
    expect(screen.getByText(/Simple Plans for Every Stage/i)).toBeInTheDocument();
  });
});
