import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";

import { MonitoringPage } from "./monitoring-page";
import type { QueueDepths } from "./types";

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

describe("MonitoringPage", () => {
  it("renders queue depths, flagging a backlogged DLQ", async () => {
    const data: QueueDepths = {
      queues: {
        "grx.campaigns.dispatch": 0,
        "grx.campaigns.dispatch.retry.0": "not declared",
        "grx.campaigns.dlq": 3,
      },
    };
    mockedApiFetch.mockResolvedValueOnce(data);

    render(<MonitoringPage />);

    expect(await screen.findByText("grx.campaigns.dispatch")).toBeInTheDocument();
    expect(screen.getByText("not declared")).toBeInTheDocument();
    expect(screen.getByText("DLQ")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows an access-denied message for an admin without platform.monitoring.manage", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(403, "Insufficient permission"));

    render(<MonitoringPage />);

    expect(
      await screen.findByText("You don't have access to view infra monitoring."),
    ).toBeInTheDocument();
  });
});
