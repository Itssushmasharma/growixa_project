import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import MegaMenu from "./mega-menu";
import { STAGES } from "@/content/website/stages";

function setup() {
  return render(
    <div>
      <MegaMenu label="Platform" items={STAGES} />
      <button type="button">outside</button>
    </div>,
  );
}

describe("MegaMenu", () => {
  it("is collapsed initially", () => {
    setup();
    expect(screen.getByRole("button", { name: /platform/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("opens on click and reports expanded state", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /platform/i }));
    expect(screen.getByRole("button", { name: /platform/i })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByRole("link", { name: /find/i })).toBeVisible();
  });

  it("shows every stage with its status label", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /platform/i }));
    expect(screen.getAllByText("Live")).toHaveLength(2);
    expect(screen.getByText("Coming Q4 2026")).toBeInTheDocument();
    expect(screen.getAllByText("Beta")).toHaveLength(2);
  });

  it("closes on Escape", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /platform/i }));
    await userEvent.keyboard("{Escape}");
    expect(screen.getByRole("button", { name: /platform/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("closes when clicking outside", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /platform/i }));
    await userEvent.click(screen.getByRole("button", { name: "outside" }));
    expect(screen.getByRole("button", { name: /platform/i })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
  });

  it("links each stage to its route", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /platform/i }));
    expect(screen.getByRole("link", { name: /find/i })).toHaveAttribute("href", "/platform/find");
  });

  it("marks an unshipped stage as coming, not merely dated", async () => {
    setup();
    await userEvent.click(screen.getByRole("button", { name: /platform/i }));
    expect(screen.getByText(/^Coming /)).toBeInTheDocument();
    expect(screen.queryByText(/^Q4 2026$/)).not.toBeInTheDocument();
  });
});
