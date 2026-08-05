import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { CompanySettingsForm } from "./company-settings-form";
import type { BrandProfile, CompanyProfile, MeResponse } from "./types";

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
}));

const mockedApiFetch = vi.mocked(apiFetch);

function renderCompanySettingsForm() {
  return render(
    <ToastProvider>
      <CompanySettingsForm />
    </ToastProvider>,
  );
}

const COMPANY_PROFILE: CompanyProfile = {
  id: "company-1",
  name: "Acme Inc",
  logo_url: null,
  website: "https://acme.example",
  industry: "Software",
  timezone: "Asia/Kolkata",
  default_language: "en",
  legal_footer: "© Acme",
  contact_details: {},
};

const BRAND_PROFILE: BrandProfile = {
  id: "brand-1",
  company_id: "company-1",
  brand_voice: "Friendly and direct",
  forbidden_claims: ["guaranteed results"],
  required_facts: ["Founded in 2020"],
};

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "user@example.com", full_name: "Test User", permissions };
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("CompanySettingsForm", () => {
  it("renders the fetched company and brand values", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["company.settings.edit"]));
      if (path === "/company/profile") return Promise.resolve(COMPANY_PROFILE);
      if (path === "/brand/profile") return Promise.resolve(BRAND_PROFILE);
      throw new Error(`unexpected path: ${path}`);
    });

    renderCompanySettingsForm();

    expect(await screen.findByDisplayValue("Acme Inc")).toBeInTheDocument();
    expect(screen.getByDisplayValue("https://acme.example")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Friendly and direct")).toBeInTheDocument();
    expect(screen.getByDisplayValue("guaranteed results")).toBeInTheDocument();
  });

  it("disables every field and hides Save for a viewer without edit permission", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/company/profile") return Promise.resolve(COMPANY_PROFILE);
      if (path === "/brand/profile") return Promise.resolve(BRAND_PROFILE);
      throw new Error(`unexpected path: ${path}`);
    });

    renderCompanySettingsForm();

    expect(await screen.findByDisplayValue("Acme Inc")).toBeDisabled();
    expect(screen.getByText("You have view-only access to company settings.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save changes" })).not.toBeInTheDocument();
  });

  it("saves company then brand profile in order when an editor submits", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["company.settings.edit"]));
      if (path === "/company/profile" && !init) return Promise.resolve(COMPANY_PROFILE);
      if (path === "/brand/profile" && !init) return Promise.resolve(BRAND_PROFILE);
      if (path === "/company/profile" && init?.method === "PUT") {
        return Promise.resolve(COMPANY_PROFILE);
      }
      if (path === "/brand/profile" && init?.method === "PUT") {
        return Promise.resolve(BRAND_PROFILE);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderCompanySettingsForm();
    await screen.findByDisplayValue("Acme Inc");

    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(screen.getByText("Settings saved.")).toBeInTheDocument());

    const putCalls = mockedApiFetch.mock.calls.filter(([, init]) => init?.method === "PUT");
    expect(putCalls).toHaveLength(2);
    expect(putCalls[0]?.[0]).toBe("/company/profile");
    expect(putCalls[1]?.[0]).toBe("/brand/profile");
  });
});
