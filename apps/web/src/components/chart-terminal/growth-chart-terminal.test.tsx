import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GrowthChartTerminal } from "./growth-chart-terminal";

describe("GrowthChartTerminal", () => {
  it("renders the terminal with ticker and initial metrics", () => {
    render(<GrowthChartTerminal />);

    expect(screen.getByText("LIVE TELEMETRY")).toBeInTheDocument();
    expect(screen.getByText("GROWTH/USD")).toBeInTheDocument();
    expect(screen.getByText("Growth Velocity")).toBeInTheDocument();
    expect(screen.getByText("Conversion Depth")).toBeInTheDocument();
    expect(screen.getByText("Delivery Telemetry")).toBeInTheDocument();
    expect(screen.getByText("Audience Capital")).toBeInTheDocument();
    expect(screen.getByText("Event Telemetry Stream")).toBeInTheDocument();
  });

  it("allows switching metric tabs", () => {
    render(<GrowthChartTerminal />);

    const conversionTab = screen.getByRole("tab", { name: "Conversion Depth" });
    fireEvent.click(conversionTab);

    expect(conversionTab).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("18.45%")).toBeInTheDocument();
  });

  it("allows switching timeframe", () => {
    render(<GrowthChartTerminal />);

    const tf7d = screen.getByRole("button", { name: "7D" });
    fireEvent.click(tf7d);

    expect(tf7d.className).toContain("timeframeBtnActive");
  });

  it("allows toggling chart mode between Candlestick and Area", () => {
    render(<GrowthChartTerminal />);

    const areaBtn = screen.getByTitle("Area Trend View");
    fireEvent.click(areaBtn);

    expect(areaBtn.className).toContain("modeBtnActive");

    const candleBtn = screen.getByTitle("Candlestick OHLC View");
    fireEvent.click(candleBtn);

    expect(candleBtn.className).toContain("modeBtnActive");
  });

  it("allows toggling indicators", () => {
    render(<GrowthChartTerminal />);

    const emaBtn = screen.getByTitle("Exponential Moving Averages (EMA 9/21)");
    expect(emaBtn.className).toContain("indChipActive");

    fireEvent.click(emaBtn);
    expect(emaBtn.className).not.toContain("indChipActive");
  });
});
