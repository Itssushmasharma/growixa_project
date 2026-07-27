import { render } from "@testing-library/react";
import { redirect } from "next/navigation";
import { describe, expect, it, vi } from "vitest";

import HomePage from "./page";

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

describe("HomePage", () => {
  it("redirects to the dashboard", () => {
    render(<HomePage />);
    expect(redirect).toHaveBeenCalledWith("/dashboard");
  });
});
