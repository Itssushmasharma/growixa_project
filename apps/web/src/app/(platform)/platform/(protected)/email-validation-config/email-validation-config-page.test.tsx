import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { EmailValidationConfigPage } from "./email-validation-config-page";
import type { PlatformEmailValidationProviderConfig } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const CONFIG: PlatformEmailValidationProviderConfig = {
  id: "cfg-1",
  provider: "CLEAROUT",
  is_active: true,
  created_at: "2026-08-15T00:00:00Z",
  updated_at: "2026-08-15T00:00:00Z",
};

function renderPage() {
  return render(
    <ToastProvider>
      <EmailValidationConfigPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("EmailValidationConfigPage", () => {
  it("shows Not configured when no platform vendor exists", async () => {
    mockedApiFetch.mockResolvedValueOnce(null);

    renderPage();

    expect(await screen.findByText("Not configured")).toBeInTheDocument();
  });

  it("renders the current platform vendor", async () => {
    mockedApiFetch.mockResolvedValueOnce(CONFIG);

    renderPage();

    expect(await screen.findByText("Configured")).toBeInTheDocument();
    expect(screen.getAllByText("Clearout.io").length).toBeGreaterThan(0);
  });

  it("shows an access-denied message for an admin without platform.validation.manage", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(403, "Insufficient permission"));

    renderPage();

    expect(
      await screen.findByText("You don't have access to configure email validation."),
    ).toBeInTheDocument();
  });

  it("saves a new platform vendor and shows a success toast", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(null);
    mockedApiFetch.mockResolvedValueOnce(CONFIG);

    renderPage();
    await screen.findByText("Not configured");

    await user.type(screen.getByLabelText("API key"), "co-fake-key");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/email-validation-config", {
        method: "PUT",
        body: JSON.stringify({ provider: "CLEAROUT", api_key: "co-fake-key" }),
      });
    });
    expect(
      await screen.findByText("Platform email-validation provider saved."),
    ).toBeInTheDocument();
  });

  it("tests a connection without saving anything", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(null);
    mockedApiFetch.mockResolvedValueOnce(undefined);

    renderPage();
    await screen.findByText("Not configured");

    await user.type(screen.getByLabelText("API key"), "co-fake-key");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/email-validation-config/test", {
        method: "POST",
        body: JSON.stringify({ provider: "CLEAROUT", api_key: "co-fake-key" }),
      });
    });
    expect(
      await screen.findByText("Connection successful — credentials are valid."),
    ).toBeInTheDocument();
  });

  it("shows the test-connection failure detail from the API", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(null);
    mockedApiFetch.mockRejectedValueOnce(
      new ApiError(502, JSON.stringify({ detail: "invalid api key" })),
    );

    renderPage();
    await screen.findByText("Not configured");

    await user.type(screen.getByLabelText("API key"), "co-bad-key");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    expect(await screen.findByText("invalid api key")).toBeInTheDocument();
  });

  it("keeps Save disabled until an API key is entered", async () => {
    mockedApiFetch.mockResolvedValueOnce(null);

    renderPage();
    await screen.findByText("Not configured");

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });
});
