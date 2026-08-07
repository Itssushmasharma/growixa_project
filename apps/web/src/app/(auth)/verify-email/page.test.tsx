import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import VerifyEmailPage from "./page";

let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

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
  mockSearchParams = new URLSearchParams();
});

describe("VerifyEmailPage", () => {
  it("shows an error immediately when no token is present in the URL", async () => {
    render(<VerifyEmailPage />);

    expect(await screen.findByText("Verification failed")).toBeInTheDocument();
    expect(mockedApiFetch).not.toHaveBeenCalled();
  });

  it("calls verify-email with the token and shows success", async () => {
    mockSearchParams = new URLSearchParams("token=raw-token");
    mockedApiFetch.mockResolvedValueOnce(undefined);

    render(<VerifyEmailPage />);

    expect(await screen.findByText("Email verified")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith("/accounts/verify-email", {
      method: "POST",
      body: JSON.stringify({ token: "raw-token" }),
    });
  });

  it("shows an error state when the token is rejected", async () => {
    mockSearchParams = new URLSearchParams("token=bad-token");
    mockedApiFetch.mockRejectedValueOnce(new Error("invalid"));

    render(<VerifyEmailPage />);

    expect(await screen.findByText("Verification failed")).toBeInTheDocument();
  });
});
