import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { AICopyPreview } from "./ai-copy-preview";

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

const mockedApiFetch = vi.mocked(apiFetch);

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("AICopyPreview", () => {
  it("calls the real /ai/generate endpoint and renders the returned text", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValue({
      output: { text: "Hi there, here is a preview." },
      status: "COMPLETE",
    });

    render(<AICopyPreview forbiddenClaims={["guaranteed results"]} />);

    await user.click(screen.getByRole("button", { name: "Generate preview" }));

    expect(await screen.findByText("Hi there, here is a preview.")).toBeInTheDocument();
    expect(screen.getByText("✓ No prohibited claims detected")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/ai/generate/BODY_COPY",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("flags a real forbidden claim found in the generated text", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValue({
      output: { text: "We offer guaranteed results for everyone." },
      status: "COMPLETE",
    });

    render(<AICopyPreview forbiddenClaims={["guaranteed results"]} />);
    await user.click(screen.getByRole("button", { name: "Generate preview" }));

    expect(
      await screen.findByText('⚠ Contains forbidden claim: "guaranteed results"'),
    ).toBeInTheDocument();
  });

  it("shows an honest not-connected state on a 409, never a fake preview", async () => {
    const user = userEvent.setup();
    const { ApiError } = await import("@/lib/api-client");
    mockedApiFetch.mockRejectedValue(new ApiError(409, "No AI provider is configured"));

    render(<AICopyPreview forbiddenClaims={[]} />);
    await user.click(screen.getByRole("button", { name: "Generate preview" }));

    expect(
      await screen.findByText("No AI provider is connected for this account yet."),
    ).toBeInTheDocument();
  });
});
