import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatCard } from "./stat-card";

describe("StatCard", () => {
  it("renders the label, value, and subtext", () => {
    render(<StatCard label="Total Contacts" value={150} subtext="All audience" />);

    expect(screen.getByText("Total Contacts")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();
    expect(screen.getByText("All audience")).toBeInTheDocument();
  });

  it("renders trend percentage and direction when provided", () => {
    render(
      <StatCard
        label="Active Contacts"
        value={120}
        trend="15%"
        trendDirection="up"
        subtext="vs last month"
      />,
    );

    expect(screen.getByText("Active Contacts")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText(/↑.*15%/)).toBeInTheDocument();
    expect(screen.getByText("vs last month")).toBeInTheDocument();
  });

  it("renders downward trend indicator correctly", () => {
    render(
      <StatCard
        label="Bounced"
        value={5}
        trend="2%"
        trendDirection="down"
        subtext="vs last month"
      />,
    );

    expect(screen.getByText(/↓.*2%/)).toBeInTheDocument();
  });
});
