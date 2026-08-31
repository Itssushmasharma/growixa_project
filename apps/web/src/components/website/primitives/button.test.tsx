import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import Button from "./button";

describe("Button", () => {
  it("renders as a button element by default", () => {
    render(<Button>Start free</Button>);
    expect(screen.getByRole("button", { name: "Start free" })).toBeInTheDocument();
  });

  it("calls onClick when pressed", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Go" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders as another element when given `as`", () => {
    render(
      <Button as="a" href="/pricing">
        Pricing
      </Button>,
    );
    expect(screen.getByRole("link", { name: "Pricing" })).toHaveAttribute("href", "/pricing");
  });

  it("applies the variant class", () => {
    render(<Button variant="glass">Demo</Button>);
    expect(screen.getByRole("button", { name: "Demo" }).className).toMatch(/glass/);
  });

  it('defaults to type="button" so it never submits a form by accident', () => {
    render(<Button>Save</Button>);
    expect(screen.getByRole("button", { name: "Save" })).toHaveAttribute("type", "button");
  });
});
