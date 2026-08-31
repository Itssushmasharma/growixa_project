import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Header from "./header";

describe("Header", () => {
  it("renders a banner landmark", () => {
    render(<Header />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });

  it("links the brand to home", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: /growixa/i })).toHaveAttribute("href", "/");
  });

  it("renders both disclosure menus collapsed", () => {
    render(<Header />);
    expect(screen.getByRole("button", { name: /platform/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.getByRole("button", { name: /solutions/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("renders the direct nav links", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: "Pricing" })).toHaveAttribute("href", "/pricing");
    expect(screen.getByRole("link", { name: "Roadmap" })).toHaveAttribute("href", "/roadmap");
    expect(screen.getByRole("link", { name: "Docs" })).toHaveAttribute("href", "/docs");
  });

  it("renders the primary call to action linking to register", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: /start free/i })).toHaveAttribute("href", "/register");
  });

  it("renders the log in button linking to login", () => {
    render(<Header />);
    expect(screen.getByRole("link", { name: /log in/i })).toHaveAttribute("href", "/login");
  });
});
