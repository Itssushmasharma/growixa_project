import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("renders the AI Agent platform hero and rating badge (Image 1)", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      /The Ultimate All-In-One AI Growth Engine/i,
    );
    expect(screen.getByText(/Rated 4.9\/5 by 12.5K\+ Growth Teams/i)).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Get Started Free/i })[0]).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("renders the Chaotic Work problem section (Image 4)", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /The Current Way Growth Teams Work Is Chaotic/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("2x More Errors")).toBeInTheDocument();
    expect(screen.getByText("Constant Multitasking")).toBeInTheDocument();
    expect(screen.getByText("1.2 Months/Year Wasted")).toBeInTheDocument();
  });

  it("renders the Integration Hub Orb section (Image 2 & 5)", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /A Data & Growth Solution That Works For Your Ecosystem/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Search 10\+ native integrations/i)).toBeInTheDocument();
  });

  it("renders the Social Deep Link Arch section (Image 3)", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /Drive Audience To The Right Channel, Every Time/i }),
    ).toBeInTheDocument();
  });

  it("renders the Ecosystem tech stack section and security section", () => {
    render(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /Ecosystem — Connects With Your Tech Stack/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Postmark")[0]).toBeInTheDocument();
    expect(screen.getAllByText("OpenAI")[0]).toBeInTheDocument();
    expect(screen.getByText("SOC2 Ready Architecture")).toBeInTheDocument();
    expect(screen.getByText("GDPR & Opt-Out Handling")).toBeInTheDocument();
  });
});
