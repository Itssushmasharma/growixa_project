import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { SupportSessionBanner } from "./support-session-banner";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("SupportSessionBanner", () => {
  it("renders nothing when no session is active", async () => {
    mockedApiFetch.mockResolvedValueOnce({ active: false, started_at: null, reason: null });

    const { container } = render(<SupportSessionBanner />);

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the reason when a session is active", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      active: true,
      started_at: "2026-08-07T00:00:00Z",
      reason: "Investigating a delivery issue",
    });

    render(<SupportSessionBanner />);

    expect(await screen.findByText(/Investigating a delivery issue/)).toBeInTheDocument();
  });
});
