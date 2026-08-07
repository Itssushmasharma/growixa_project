import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";

import { AccountsPage } from "./accounts-page";
import type { AccountListItem } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const ACCOUNTS: AccountListItem[] = [
  {
    id: "acc-1",
    name: "Acme Corp",
    status: "ACTIVE",
    selected_plan_slug: "starter",
    created_at: "2026-08-01T00:00:00Z",
    user_count: 3,
  },
  {
    id: "acc-2",
    name: "Suspended Co",
    status: "SUSPENDED",
    selected_plan_slug: "growth",
    created_at: "2026-08-02T00:00:00Z",
    user_count: 1,
  },
];

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("AccountsPage", () => {
  it("renders every account with its status and user count", async () => {
    mockedApiFetch.mockResolvedValueOnce(ACCOUNTS);

    render(<AccountsPage />);

    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Suspended Co")).toBeInTheDocument();
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("SUSPENDED")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows an access-denied message for a platform admin without platform.accounts.manage", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(403, "Insufficient permission"));

    render(<AccountsPage />);

    expect(
      await screen.findByText("You don't have access to manage accounts."),
    ).toBeInTheDocument();
  });
});
