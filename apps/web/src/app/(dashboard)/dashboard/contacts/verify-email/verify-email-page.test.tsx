import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { EmailValidationResult, MeResponse } from "../types";
import { VerifyEmailPage } from "./verify-email-page";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderPage() {
  return render(
    <ToastProvider>
      <VerifyEmailPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("VerifyEmailPage", () => {
  it("shows an access-denied message for a user without contacts.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("You don't have access to verify emails.")).toBeInTheDocument();
  });

  it("checks a single email and shows the basic-check result", async () => {
    const result: EmailValidationResult = {
      email: "test@mailinator.com",
      status: "DISPOSABLE",
      reasons: ["Domain is a known disposable/throwaway provider"],
      verification_level: "BASIC",
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/email-validation/availability") {
        return Promise.resolve({ realtime_available: false });
      }
      if (path === "/email-validation/check" && init?.method === "POST") {
        return Promise.resolve(result);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderPage();

    await screen.findByLabelText("Email");
    await user.type(screen.getByLabelText("Email"), "test@mailinator.com");
    await user.click(screen.getByRole("button", { name: "Verify email" }));

    expect(await screen.findByText("Disposable")).toBeInTheDocument();
    expect(screen.getByText("Domain is a known disposable/throwaway provider")).toBeInTheDocument();
    expect(screen.getByText("Basic check")).toBeInTheDocument();
    expect(
      screen.getByText("Real-time mailbox verification is available on paid plans."),
    ).toBeInTheDocument();
  });

  it("shows the real-time checkbox and sends use_realtime when available", async () => {
    const result: EmailValidationResult = {
      email: "test@example.org",
      status: "VALID",
      reasons: [],
      verification_level: "REALTIME",
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/email-validation/availability") {
        return Promise.resolve({ realtime_available: true });
      }
      if (path === "/email-validation/check" && init?.method === "POST") {
        expect(JSON.parse(init.body as string)).toMatchObject({ use_realtime: true });
        return Promise.resolve(result);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderPage();

    await screen.findByLabelText("Email");
    expect(
      screen.getByText("Use real-time mailbox verification (uses one verification credit)"),
    ).toBeInTheDocument();
    await user.type(screen.getByLabelText("Email"), "test@example.org");
    await user.click(screen.getByRole("button", { name: "Verify email" }));

    expect(await screen.findByText("Real-time")).toBeInTheDocument();
  });

  it("shows the bulk CSV drop zone on the Bulk Upload tab", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/email-validation/availability") {
        return Promise.resolve({ realtime_available: false });
      }
      throw new Error(`unexpected path: ${path}`);
    });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Bulk Upload" })).toBeInTheDocument(),
    );
    await user.click(screen.getByRole("button", { name: "Bulk Upload" }));

    expect(screen.getByRole("button", { name: "Choose file" })).toBeInTheDocument();
    expect(screen.getByText(/Upload or drop a CSV file here/)).toBeInTheDocument();
  });
});
