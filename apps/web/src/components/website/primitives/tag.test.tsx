import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Tag from "./tag";
import { STATUS } from "@/content/website/stages";

describe("Tag", () => {
  it("renders the label", () => {
    render(<Tag status={STATUS.LIVE} label="Live" />);
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("applies a distinct class per status", () => {
    const { rerender } = render(<Tag status={STATUS.LIVE} label="Live" />);
    const live = screen.getByText("Live").className;
    rerender(<Tag status={STATUS.BETA} label="Beta" />);
    const beta = screen.getByText("Beta").className;
    rerender(<Tag status={STATUS.SOON} label="Q4 2026" />);
    const soon = screen.getByText("Q4 2026").className;
    expect(new Set([live, beta, soon]).size).toBe(3);
  });
});
