import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { IntegrationsPage } from "./integrations-page";
import type { EmailProviderConnection, MeResponse, SenderIdentity } from "./types";

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}));

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

const CONNECTION: EmailProviderConnection = {
  id: "conn-1",
  provider: "POSTMARK",
  smtp_host: "smtp.postmarkapp.com",
  smtp_port: 587,
  smtp_username: "postmark-token",
  is_active: true,
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  webhook_username: "wh-user",
};

const IDENTITY: SenderIdentity = {
  id: "identity-1",
  email_provider_connection_id: "conn-1",
  from_email: "hello@growixa.local",
  from_name: "Growixa",
  reply_to_email: null,
  verification_status: "PENDING",
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("IntegrationsPage", () => {
  it("shows an access-denied message for a user without integrations.manage", async () => {
    // The connection/identity GETs are themselves gated by integrations.manage on the
    // real backend, so a user lacking it gets a 403 from both, not an empty/null
    // response — this test must reflect that, or it can't catch a regression where the
    // page's load effect lets those 403s mask the access-denied branch entirely.
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/integrations/email-provider")
        return Promise.reject(new ApiError(403, "Forbidden"));
      if (path === "/integrations/sender-identities")
        return Promise.reject(new ApiError(403, "Forbidden"));
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(
      await screen.findByText("You don't have access to configure integrations."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Email provider connection")).not.toBeInTheDocument();
  });

  it("renders the existing connection summary and sender identities", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-provider") return Promise.resolve(CONNECTION);
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("smtp.postmarkapp.com")).toBeInTheDocument();
    expect(screen.getByText("Growixa")).toBeInTheDocument();
    expect(screen.getByText("hello@growixa.local")).toBeInTheDocument();
  });

  it("creates a connection and reveals the one-time webhook credentials", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-provider" && !init) return Promise.resolve(null);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
      if (path === "/integrations/email-provider" && init?.method === "POST") {
        return Promise.resolve({
          ...CONNECTION,
          webhook_username: "wh-user",
          webhook_password: "wh-pass-shown-once",
        });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("Email provider connection");

    await user.click(screen.getByRole("button", { name: "+ Configure connection" }));
    await user.clear(screen.getByLabelText("SMTP username"));
    await user.type(screen.getByLabelText("SMTP username"), "postmark-token");
    await user.type(screen.getByLabelText("SMTP password / server token"), "server-token");
    await user.click(screen.getByRole("button", { name: "Save connection" }));

    await waitFor(() =>
      expect(screen.getByText(/Webhook credentials generated/)).toBeInTheDocument(),
    );
    expect(screen.getByText("wh-user:wh-pass-shown-once")).toBeInTheDocument();
  });

  it("adds a sender identity when a connection exists", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-provider") return Promise.resolve(CONNECTION);
      if (path === "/integrations/sender-identities" && !init) return Promise.resolve([]);
      if (path === "/integrations/sender-identities" && init?.method === "POST") {
        return Promise.resolve(IDENTITY);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
    await screen.findByText("smtp.postmarkapp.com");

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
      if (path === "/integrations/email-provider") return Promise.resolve(CONNECTION);
      if (path === "/integrations/sender-identities" && !init) return Promise.resolve([IDENTITY]);
      if (
        path === "/integrations/sender-identities/identity-1/status" &&
        init?.method === "PATCH"
      ) {
        return Promise.resolve({ ...IDENTITY, verification_status: "VERIFIED" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderIntegrationsPage();
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
});
