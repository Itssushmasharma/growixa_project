import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import HomePage from "./page";

describe("HomePage", () => {
  it("renders the hero headline and subtitle", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/Your AI/i);
    expect(screen.getByText(/Working while you sleep/i)).toBeInTheDocument();
    expect(screen.getByText(/The alternative/i)).toBeInTheDocument();
    expect(screen.getByText(/The Growixa Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/What the AI actually does/i)).toBeInTheDocument();
  });

  it("renders the 5 engine stage cards in the bento grid", () => {
    render(<HomePage />);
    expect(screen.getByRole("heading", { name: /^find$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^qualify$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^create$/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /^send$/i })).toBeInTheDocument();
    expect(screen.getByText(/01 — Find/i)).toBeInTheDocument();
    expect(screen.getByText(/02 — Qualify/i)).toBeInTheDocument();
    expect(screen.getByText(/05 — Manage/i)).toBeInTheDocument();
  });

  it("renders primary CTAs linking to register", () => {
    render(<HomePage />);
    const startFreeLinks = screen.getAllByRole("link", { name: /start free/i });
    expect(startFreeLinks.length).toBeGreaterThan(0);
    expect(startFreeLinks[0]).toHaveAttribute("href", "/register");
  });
});
