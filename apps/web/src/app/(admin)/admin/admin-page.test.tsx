import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import AdminHealthPage from "./page";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderPage() {
  return render(
    <ToastProvider>
      <AdminHealthPage />
    </ToastProvider>,
  );
}

const OK_HEALTH = {
  status: "ok",
  checks: {
    postgres: "ok",
    redis: "ok",
    rabbitmq: "ok",
  },
};

const DEGRADED_HEALTH = {
  status: "degraded",
  checks: {
    postgres: "ok",
    redis: "error: Connection refused on port 6379",
    rabbitmq: "ok",
  },
};

describe("AdminHealthPage", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
  });

  it("renders all three health checks as OK when GET /health returns all-ok", async () => {
    mockedApiFetch.mockResolvedValue(OK_HEALTH);

    renderPage();

    expect(await screen.findByText(/System Operational/)).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL Database")).toBeInTheDocument();
    expect(screen.getByText("Redis Cache & Locks")).toBeInTheDocument();
    expect(screen.getByText("RabbitMQ Message Broker")).toBeInTheDocument();

    const okPills = screen.getAllByText("OK");
    expect(okPills).toHaveLength(3);
  });

  it("renders an ERROR pill and the raw error text for a failing check", async () => {
    mockedApiFetch.mockResolvedValue(DEGRADED_HEALTH);

    renderPage();

    expect(await screen.findByText(/System Degraded/)).toBeInTheDocument();
    expect(screen.getByText("ERROR")).toBeInTheDocument();
    expect(screen.getByText("error: Connection refused on port 6379")).toBeInTheDocument();
  });

  it("renders the degraded banner when overall status is 'degraded'", async () => {
    mockedApiFetch.mockResolvedValue(DEGRADED_HEALTH);

    renderPage();

    expect(await screen.findByText(/System Degraded/)).toBeInTheDocument();
  });

  it("refresh button re-fetches GET /health", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValue(OK_HEALTH);

    renderPage();
    await screen.findByText(/System Operational/);

    await user.click(screen.getByRole("button", { name: "Refresh" }));

    expect(mockedApiFetch).toHaveBeenCalledTimes(2);
    expect(mockedApiFetch).toHaveBeenLastCalledWith("/health");
  });

  it("clicking 'Run healthcheck job' posts to /system/jobs/healthcheck and shows a success toast with the job_id", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/health") return Promise.resolve(OK_HEALTH);
      if (path === "/system/jobs/healthcheck" && init?.method === "POST") {
        return Promise.resolve({ job_id: "test-job-uuid-1234" });
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    await screen.findByText(/System Operational/);

    await user.click(screen.getByRole("button", { name: "Run healthcheck job" }));

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/system/jobs/healthcheck",
      expect.objectContaining({ method: "POST" }),
    );
    expect(
      await screen.findByText("Healthcheck job enqueued (job_id: test-job-uuid-1234)"),
    ).toBeInTheDocument();
  });

  it("shows an error toast when the healthcheck trigger fails", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/health") return Promise.resolve(OK_HEALTH);
      if (path === "/system/jobs/healthcheck" && init?.method === "POST") {
        return Promise.reject(new ApiError(500, JSON.stringify({ detail: "Broker unreachable" })));
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    await screen.findByText(/System Operational/);

    await user.click(screen.getByRole("button", { name: "Run healthcheck job" }));

    expect(await screen.findByText("Broker unreachable")).toBeInTheDocument();
  });
});
