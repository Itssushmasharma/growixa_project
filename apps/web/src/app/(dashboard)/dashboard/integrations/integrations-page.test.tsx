import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";
import { ToastProvider } from "@/components/toast/toast-context";

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
      throw new Error(`unexpected path: ${path}`);
    });

    renderIntegrationsPage();

    expect(await screen.findByText("Postmark")).toBeInTheDocument();
    expect(screen.getByText("Custom SMTP")).toBeInTheDocument();
    expect(screen.getAllByText("Unconfigured")).toHaveLength(2);
  });

  it("configuring Postmark leaves Custom SMTP still Unconfigured", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers" && !init) return Promise.resolve([]);
      if (path === "/integrations/sender-identities") return Promise.resolve([]);
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

    // Registry order is Postmark first, Custom SMTP second — both cards start
    // Unconfigured, so the first "+ Configure connection" button belongs to Postmark.
    const configureButtons = screen.getAllByRole("button", { name: "+ Configure connection" });
    await user.click(configureButtons[0]!);
    await user.type(screen.getByLabelText("SMTP username"), "postmark-token");
    await user.type(screen.getByLabelText("SMTP password / server token"), "server-token");
    await user.click(screen.getByRole("button", { name: "Save connection" }));

    await waitFor(() =>
      expect(screen.getByText(/Webhook credentials generated/)).toBeInTheDocument(),
    );
    const statuses = screen.getAllByText(/Connected|Unconfigured/);
    expect(statuses.map((el) => el.textContent)).toEqual(["Connected", "Unconfigured"]);
  });

  it("renders identities scoped to their own connection's card", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["integrations.manage"]));
      if (path === "/integrations/email-providers")
        return Promise.resolve([POSTMARK_CONNECTION, CUSTOM_SMTP_CONNECTION]);
      if (path === "/integrations/sender-identities") return Promise.resolve([IDENTITY]);
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
});
