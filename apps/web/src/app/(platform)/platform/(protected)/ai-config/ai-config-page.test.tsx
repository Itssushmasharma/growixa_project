import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { AIConfigPage } from "./ai-config-page";
import type { PlatformAIProviderConfig } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const CONFIG: PlatformAIProviderConfig = {
  id: "cfg-1",
  provider: "ANTHROPIC",
  base_url: null,
  default_model: "claude-sonnet-4-5",
  is_active: true,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
};

function renderPage() {
  return render(
    <ToastProvider>
      <AIConfigPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("AIConfigPage", () => {
  it("shows Not configured when no platform default exists", async () => {
    mockedApiFetch.mockResolvedValueOnce(null);

    renderPage();

    expect(await screen.findByText("Not configured")).toBeInTheDocument();
  });

  it("renders the current platform default provider", async () => {
    mockedApiFetch.mockResolvedValueOnce(CONFIG);

    renderPage();

    expect(await screen.findByText("Configured")).toBeInTheDocument();
    expect(screen.getAllByText("Anthropic").length).toBeGreaterThan(0);
    expect(screen.getByText("claude-sonnet-4-5")).toBeInTheDocument();
  });

  it("shows an access-denied message for an admin without platform.ai.manage", async () => {
    mockedApiFetch.mockRejectedValueOnce(new ApiError(403, "Insufficient permission"));

    renderPage();

    expect(
      await screen.findByText("You don't have access to configure the AI provider."),
    ).toBeInTheDocument();
  });

  it("saves a new platform default and shows a success toast", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(null);
    mockedApiFetch.mockResolvedValueOnce(CONFIG);

    renderPage();
    await screen.findByText("Not configured");

    await user.selectOptions(screen.getByLabelText("Provider"), "ANTHROPIC");
    await user.type(screen.getByLabelText("API key"), "sk-fake");
    await user.type(screen.getByLabelText("Default model"), "claude-sonnet-4-5");
    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/ai-config", {
        method: "PUT",
        body: JSON.stringify({
          provider: "ANTHROPIC",
          api_key: "sk-fake",
          base_url: null,
          default_model: "claude-sonnet-4-5",
        }),
      });
    });
    expect(await screen.findByText("Platform default AI provider saved.")).toBeInTheDocument();
  });

  it("tests a connection without saving anything", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(null);
    mockedApiFetch.mockResolvedValueOnce(undefined);

    renderPage();
    await screen.findByText("Not configured");

    await user.type(screen.getByLabelText("API key"), "sk-fake");
    await user.type(screen.getByLabelText("Default model"), "gpt-4o-mini");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/ai-config/test", {
        method: "POST",
        body: JSON.stringify({
          provider: "OPENAI",
          api_key: "sk-fake",
          base_url: null,
          default_model: "gpt-4o-mini",
        }),
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

    await user.type(screen.getByLabelText("API key"), "sk-bad");
    await user.type(screen.getByLabelText("Default model"), "gpt-4o-mini");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    expect(await screen.findByText("invalid api key")).toBeInTheDocument();
  });

  it("requires a base URL for Azure OpenAI before enabling Save", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce(null);

    renderPage();
    await screen.findByText("Not configured");

    await user.selectOptions(screen.getByLabelText("Provider"), "AZURE_OPENAI");
    await user.type(screen.getByLabelText("API key"), "fake");
    await user.type(screen.getByLabelText("Default model"), "gpt4");

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });
});
