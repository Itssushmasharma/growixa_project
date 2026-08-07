import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";

import { UsagePage } from "./usage-page";
import type { UsageSummaryItem } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const ITEMS: UsageSummaryItem[] = [
  {
    account_id: "acc-1",
    account_name: "Acme Corp",
    operation_type: "email.sent",
    total_quantity: 42,
    unit: "email",
  },
];

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("UsagePage", () => {
  it("renders per-account usage totals", async () => {
    mockedApiFetch.mockResolvedValueOnce(ITEMS);

    render(<UsagePage />);

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("email.sent")).toBeInTheDocument();
    expect(screen.getByText("42 emails")).toBeInTheDocument();
  });

  it("shows an access-denied message for an admin without platform.usage.manage", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(403, "Insufficient permission"));

    render(<UsagePage />);

    expect(await screen.findByText("You don't have access to view usage.")).toBeInTheDocument();
  });
});
