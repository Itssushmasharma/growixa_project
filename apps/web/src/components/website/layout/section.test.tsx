import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Section, { hueVars } from "./section";

describe("Section", () => {
  it("renders children inside a section landmark", () => {
    render(
      <Section id="engine">
        <h2>The Engine</h2>
      </Section>,
    );
    expect(screen.getByRole("heading", { name: "The Engine" })).toBeInTheDocument();
    expect(document.getElementById("engine")).not.toBeNull();
  });

  it("sets hue custom properties when given a hue", () => {
    const { container } = render(<Section hue="send">x</Section>);
    const el = container.firstChild as HTMLElement;
    expect(el.style.getPropertyValue("--hue")).toBe("var(--send)");
    expect(el.style.getPropertyValue("--hue-l")).toBe("var(--send-l)");
    expect(el.style.getPropertyValue("--hue-d")).toBe("var(--send-d)");
  });

  it("does not set hue properties when no hue is given", () => {
    const { container } = render(<Section>x</Section>);
    const el = container.firstChild as HTMLElement;
    expect(el.style.getPropertyValue("--hue")).toBe("");
    expect(el.hasAttribute("style")).toBe(false);
  });

  it("applies the tint modifier class", () => {
    const { container } = render(<Section tint>x</Section>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toMatch(/tint/);
  });

  it("hueVars returns undefined for a falsy hue so React omits the style attribute", () => {
    expect(hueVars(undefined)).toBeUndefined();
    expect(hueVars("")).toBeUndefined();
  });

  it("hueVars maps a bare hue name to the full custom property triple", () => {
    expect(hueVars("send")).toEqual({
      "--hue": "var(--send)",
      "--hue-l": "var(--send-l)",
      "--hue-d": "var(--send-d)",
    });
  });
});
