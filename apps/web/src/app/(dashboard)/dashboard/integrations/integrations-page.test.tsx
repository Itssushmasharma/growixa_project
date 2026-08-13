import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";
import { ToastProvider } from "@/components/toast/toast-context";

import { IntegrationsPage } from "./integrations-page";
import type {
  AIProviderConnection,
  EmailProviderConnection,
  MeResponse,
  SenderIdentity,
  SocialConnection,
} from "./types";

const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
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

function renderIntegrationsPage() {
  return render(
    <ToastProvider>
      <IntegrationsPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const POSTMARK_CONNECTION: EmailProviderConnection = {
  id: "conn-postmark",
  provider: "POSTMARK",
  smtp_host: "smtp.postmarkapp.com",
  smtp_port: 587,
  smtp_username: "postmark-token",
  is_active: true,
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  webhook_username: "wh-user",
};

const CUSTOM_SMTP_CONNECTION: EmailProviderConnection = {
  id: "conn-custom-smtp",
  provider: "CUSTOM_SMTP",
  smtp_host: "smtp.example.com",
  smtp_port: 587,
  smtp_username: "custom-user",
  is_active: true,
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  webhook_username: "wh-user-2",
};

const SOCIAL_CONNECTION: SocialConnection = {
  id: "social-conn-1",
  provider: "INSTAGRAM_BUSINESS",
  ig_business_account_id: "ig-123",
  ig_username: "growixa_test",
  facebook_page_id: "page-123",
  is_active: true,
  last_connected_at: "2026-08-12T00:00:00Z",
  last_error: null,
};

const AI_CONNECTION: AIProviderConnection = {
  id: "ai-conn-1",
  provider: "ANTHROPIC",
  base_url: null,
  default_model: "claude-sonnet-4-5",
  is_active: true,
  created_at: "2026-08-12T00:00:00Z",
  updated_at: "2026-08-12T00:00:00Z",
};

const IDENTITY: SenderIdentity = {
  id: "identity-1",
  email_provider_connection_id: "conn-postmark",
  from_email: "hello@growixa.local",
  from_name: "Growixa",
  reply_to_email: null,
  verification_status: "PENDING",
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
};

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockReplace.mockReset();
  mockSearchParams = new URLSearchParams();
});

describe("IntegrationsPage", () => {
  it("shows an access-denied message for a user without integrations.manage", async () => {
    // The connection/identity GETs are themselves gated by integrations.manage on the
    // real backend, so a user lacking it gets a 403 from both, not an empty response —
    // this test must reflect that, or it can't catch a regression where those 403s
    // mask the access-denied branch entirely.
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/integrations/email-providers")
        return Promise.reject(new ApiError(403, "Forbidden"));
      if (path === "/integrations/sender-identities")
        return Promise.reject(new ApiError(403, "Forbidden"));
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(
      await screen.findByText("You don't have access to configure integrations."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Postmark")).not.toBeInTheDocument();
  });

  it("shows both provider cards as Unconfigured when nothing is connected", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("Postmark")).toBeInTheDocument();
    expect(screen.getByText("Custom SMTP")).toBeInTheDocument();
    // 4, not 2 -- includes the Instagram card (GRX-SOCIAL-010) and the AI Model
    // Provider card (GRX-AI-010), also unconfigured here.
    expect(screen.getAllByText("Unconfigured")).toHaveLength(4);
  });

  it("configuring Postmark leaves Custom SMTP still Unconfigured", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers" && !init) return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      if (path === "/integrations/email-provider" && init?.method === "POST") {
        return Promise.resolve({
          ...POSTMARK_CONNECTION,
          webhook_password: "wh-pass-shown-once",
        });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Postmark");

    // Card order is Instagram, then AI Model Provider (GRX-AI-010), then the
    // PROVIDER_REGISTRY cards (Postmark, Custom SMTP) -- all four start Unconfigured,
    // so the "+ Configure connection" button at index 1 belongs to Postmark.
    const configureButtons = screen.getAllByRole("button", { name: "+ Configure connection" });
    await user.click(configureButtons[1]!);
    await user.type(screen.getByLabelText("SMTP username"), "postmark-token");
    await user.type(screen.getByLabelText("SMTP password / server token"), "server-token");
    await user.click(screen.getByRole("button", { name: "Save connection" }));

    await waitFor(() =>
      expect(screen.getByText(/Webhook credentials generated/)).toBeInTheDocument(),
    );
    const statuses = screen.getAllByText(/Connected|Unconfigured/);
    // Instagram and AI Model Provider render first (both unconfigured here), then
    // Postmark (now Connected), then Custom SMTP (still Unconfigured).
    expect(statuses.map((el) => el.textContent)).toEqual([
      "Unconfigured",
      "Unconfigured",
      "Connected",
      "Unconfigured",
    ]);
  });

  it("shows a success toast when the connection test passes", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      if (path === "/integrations/email-providers/test" && init?.method === "POST") {
        return Promise.resolve(undefined);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Postmark");

    // Index 1: the AI Model Provider card (GRX-AI-010) also renders a
    // "+ Configure connection" button ahead of Postmark's, at index 0.
    const configureButtons = screen.getAllByRole("button", { name: "+ Configure connection" });
    await user.click(configureButtons[1]!);
    await user.type(screen.getByLabelText("SMTP username"), "postmark-token");
    await user.type(screen.getByLabelText("SMTP password / server token"), "server-token");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    expect(
      await screen.findByText("Connection successful — credentials are valid."),
    ).toBeInTheDocument();
  });

  it("shows the backend's error detail when the connection test fails", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      if (path === "/integrations/email-providers/test" && init?.method === "POST") {
        return Promise.reject(
          new ApiError(
            502,
            JSON.stringify({ detail: "Connection test failed: certificate has expired" }),
          ),
        );
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Postmark");

    // Index 1: the AI Model Provider card (GRX-AI-010) also renders a
    // "+ Configure connection" button ahead of Postmark's, at index 0.
    const configureButtons = screen.getAllByRole("button", { name: "+ Configure connection" });
    await user.click(configureButtons[1]!);
    await user.type(screen.getByLabelText("SMTP username"), "postmark-token");
    await user.type(screen.getByLabelText("SMTP password / server token"), "server-token");
    await user.click(screen.getByRole("button", { name: "Test connection" }));

    expect(
      await screen.findByText("Connection test failed: certificate has expired"),
    ).toBeInTheDocument();
  });

  it("renders identities scoped to their own connection's card", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers")
        return Promise.resolve([POSTMARK_CONNECTION, CUSTOM_SMTP_CONNECTION]);
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Postmark");

    const manageButtons = screen.getAllByRole("button", { name: "Manage identities" });
    await user.click(manageButtons[0]!);

    expect(await screen.findByText("hello@growixa.local")).toBeInTheDocument();

    await user.click(manageButtons[1]!);
    expect(screen.getByText("No sender identities yet.")).toBeInTheDocument();
  });

  it("adds a sender identity to the connection it was opened from", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([POSTMARK_CONNECTION]);
      if (path === "/integrations/sender-identities" && !init) return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      if (path === "/integrations/sender-identities" && init?.method === "POST") {
        return Promise.resolve(IDENTITY);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Postmark");

    await user.click(screen.getAllByRole("button", { name: "Manage identities" })[0]!);
    await user.click(screen.getByRole("button", { name: "+ Add sender identity" }));
    await user.type(screen.getByLabelText("From email"), "hello@growixa.local");
    await user.type(screen.getByLabelText("From name"), "Growixa");
    await user.click(screen.getByRole("button", { name: "Add identity" }));

    await waitFor(() => expect(screen.getByText("hello@growixa.local")).toBeInTheDocument());
  });

  it("changes a sender identity's verification status", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([POSTMARK_CONNECTION]);
      if (path === "/integrations/sender-identities" && !init) return Promise.resolve([IDENTITY]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      if (
        path === "/integrations/sender-identities/identity-1/status" &&
        init?.method === "PATCH"
      ) {
        return Promise.resolve({ ...IDENTITY, verification_status: "VERIFIED" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Postmark");
    await user.click(screen.getAllByRole("button", { name: "Manage identities" })[0]!);
    await screen.findByText("Growixa");

    await user.selectOptions(screen.getByDisplayValue("PENDING"), "VERIFIED");

    await waitFor(() => {
      const [, statusCall] =
        mockedApiFetch.mock.calls.find(
          ([path]) => path === "/integrations/sender-identities/identity-1/status",
        ) ?? [];
      expect(statusCall).toBeDefined();
    });
  });

  it("shows the Instagram card as Unconfigured with no connection", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("Instagram Business")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "+ Connect Instagram" })).toBeInTheDocument();
  });

  it("shows the Instagram card as Connected with the account username", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([SOCIAL_CONNECTION]);
      if (path === "/ai/connections") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("growixa_test")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Reconnect Instagram" })).toBeInTheDocument();
  });

  it("shows a success toast and clears the query param after a successful Instagram connect", async () => {
    mockSearchParams = new URLSearchParams("instagram=connected");
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([SOCIAL_CONNECTION]);
      if (path === "/ai/connections") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("Instagram account connected.")).toBeInTheDocument();
    expect(mockReplace).toHaveBeenCalledWith("/dashboard/integrations");

    mockSearchParams = new URLSearchParams();
  });

  it("shows an error toast when the Instagram connect flow fails", async () => {
    mockSearchParams = new URLSearchParams("instagram=error&reason=graph_api_error");
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(
      await screen.findByText("Could not connect that Instagram account. Please try again."),
    ).toBeInTheDocument();

    mockSearchParams = new URLSearchParams();
  });

  it("shows the AI Model Provider card as Connected with its provider and model", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections") return Promise.resolve([AI_CONNECTION]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("AI Model Provider")).toBeInTheDocument();
    expect(screen.getByText("Anthropic")).toBeInTheDocument();
    expect(screen.getByText("claude-sonnet-4-5")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Replace connection" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Use platform default instead" }),
    ).toBeInTheDocument();
  });

  it("saves a new AI provider connection", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections" && !init) return Promise.resolve([]);
      if (path === "/ai/connections" && init?.method === "POST") {
        return Promise.resolve(AI_CONNECTION);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("AI Model Provider");

    await user.click(screen.getAllByRole("button", { name: "+ Configure connection" })[0]!);
    await user.selectOptions(screen.getByLabelText("Provider"), "ANTHROPIC");
    await user.type(screen.getByLabelText("API key"), "sk-fake");
    await user.type(screen.getByLabelText("Default model"), "claude-sonnet-4-5");
    await user.click(screen.getByRole("button", { name: "Save connection" }));

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/ai/connections", {
        method: "POST",
        body: JSON.stringify({
          provider: "ANTHROPIC",
          api_key: "sk-fake",
          base_url: null,
          default_model: "claude-sonnet-4-5",
        }),
      });
    });
    expect(await screen.findByText("AI provider connection saved.")).toBeInTheDocument();
  });

  it("removes the AI provider connection to fall back to the platform default", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers") return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/social/connections") return Promise.resolve([]);
      if (path === "/ai/connections" && !init) return Promise.resolve([AI_CONNECTION]);
      if (path === "/ai/connections/ai-conn-1/deactivate" && init?.method === "POST") {
        return Promise.resolve({ ...AI_CONNECTION, is_active: false });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("AI Model Provider");

    await user.click(screen.getByRole("button", { name: "Use platform default instead" }));

    expect(
      await screen.findByText(
        "AI provider connection removed — the platform default will be used.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No AI provider connected — the platform default is used."),
    ).toBeInTheDocument();
  });
});
