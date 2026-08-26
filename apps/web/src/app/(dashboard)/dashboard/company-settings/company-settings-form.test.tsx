import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { CompanySettingsForm } from "./company-settings-form";
import type { BrandProfile, CompanyProfile, MeResponse } from "./types";

vi.mock("@/lib/api-client", () => ({
  apiFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
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
  business_address: "1 Acme Way",
  description: "Acme makes things.",
  support_email: "support@acme.example",
  sender_name: "Acme Team",
  contact_details: {},
  updated_at: "2026-08-20T10:00:00Z",
};

const BRAND_PROFILE: BrandProfile = {
  id: "brand-1",
  company_id: "company-1",
  brand_voice: "Friendly and direct",
  forbidden_claims: ["guaranteed results"],
  required_facts: ["Founded in 2020"],
  persona_tags: ["Professional"],
  voice_settings: { formality: 60 },
  updated_at: "2026-08-20T10:00:00Z",
};

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "user@example.com", full_name: "Test User", permissions };
}

function mockLoad(permissions: string[]) {
  mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/company/profile" && !init) return Promise.resolve(COMPANY_PROFILE);
    if (path === "/brand/profile" && !init) return Promise.resolve(BRAND_PROFILE);
    if (path === "/company/profile" && init?.method === "PUT") {
      return Promise.resolve({ ...COMPANY_PROFILE, ...JSON.parse(String(init.body)) });
    }
    if (path === "/brand/profile" && init?.method === "PUT") {
      return Promise.resolve({ ...BRAND_PROFILE, ...JSON.parse(String(init.body)) });
    }
    throw new Error(`unexpected call: ${path} ${init?.method ?? "GET"}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("CompanySettingsForm", () => {
  it("renders the fetched company values on the default Company Profile tab", async () => {
    mockLoad(["company.settings.edit"]);

    renderCompanySettingsForm();

    expect(await screen.findByDisplayValue("Acme Inc")).toBeInTheDocument();
    expect(screen.getByDisplayValue("https://acme.example")).toBeInTheDocument();
    expect(screen.getByDisplayValue("1 Acme Way")).toBeInTheDocument();
    expect(screen.getByDisplayValue("support@acme.example")).toBeInTheDocument();
    expect(screen.getByText("90% Ready")).toBeInTheDocument();
  });

  it("shows the Brand Voice tab's persona and description after switching tabs", async () => {
    const user = userEvent.setup();
    mockLoad(["company.settings.edit"]);

    renderCompanySettingsForm();
    await screen.findByDisplayValue("Acme Inc");

    await user.click(screen.getByRole("tab", { name: "Brand Voice" }));

    expect(screen.getByDisplayValue("Friendly and direct")).toBeInTheDocument();
    const professionalChip = screen.getByRole("button", { name: "Professional" });
    expect(professionalChip).toHaveAttribute("aria-pressed", "true");
  });

  it("shows forbidden claims and required facts as structured rows on the AI Guardrails tab", async () => {
    const user = userEvent.setup();
    mockLoad(["company.settings.edit"]);

    renderCompanySettingsForm();
    await screen.findByDisplayValue("Acme Inc");

    await user.click(screen.getByRole("tab", { name: "AI Guardrails" }));

    expect(screen.getByDisplayValue("guaranteed results")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Founded in 2020")).toBeInTheDocument();
  });

  it("disables every field, hides the save bar, and shows a view-only note for a viewer", async () => {
    mockLoad([]);

    renderCompanySettingsForm();

    expect(await screen.findByDisplayValue("Acme Inc")).toBeDisabled();
    expect(screen.getByText("You have view-only access to company settings.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Save changes" })).not.toBeInTheDocument();
  });

  it("shows the sticky save bar only after an edit, and saves company then brand on Save", async () => {
    const user = userEvent.setup();
    mockLoad(["company.settings.edit"]);

    renderCompanySettingsForm();
    const nameInput = await screen.findByDisplayValue("Acme Inc");

    expect(screen.queryByText("You have unsaved changes")).not.toBeInTheDocument();

    await user.clear(nameInput);
    await user.type(nameInput, "Acme Corp");

    expect(await screen.findByText("You have unsaved changes")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => expect(screen.getByText("Settings saved.")).toBeInTheDocument());
    expect(screen.queryByText("You have unsaved changes")).not.toBeInTheDocument();

    const putCalls = mockedApiFetch.mock.calls.filter(([, init]) => init?.method === "PUT");
    expect(putCalls).toHaveLength(2);
    expect(putCalls[0]?.[0]).toBe("/company/profile");
    expect(putCalls[1]?.[0]).toBe("/brand/profile");
  });

  it("discards an edit back to the last-saved value", async () => {
    const user = userEvent.setup();
    mockLoad(["company.settings.edit"]);

    renderCompanySettingsForm();
    const nameInput = await screen.findByDisplayValue("Acme Inc");

    await user.clear(nameInput);
    await user.type(nameInput, "Something Else");
    await screen.findByText("You have unsaved changes");

    await user.click(screen.getByRole("button", { name: "Discard changes" }));

    expect(await screen.findByDisplayValue("Acme Inc")).toBeInTheDocument();
    expect(screen.queryByText("You have unsaved changes")).not.toBeInTheDocument();
  });

  it("adds and removes a guardrail row via the structured list", async () => {
    const user = userEvent.setup();
    mockLoad(["company.settings.edit"]);

    renderCompanySettingsForm();
    await screen.findByDisplayValue("Acme Inc");
    await user.click(screen.getByRole("tab", { name: "AI Guardrails" }));

    await user.click(screen.getByRole("button", { name: "+ Add claim" }));

    const newRow = screen.getByLabelText("Forbidden Claims 2");
    await user.type(newRow, "No spam ever");
    expect(newRow).toHaveValue("No spam ever");

    await user.click(screen.getByLabelText("Remove forbidden claims 2"));
    expect(screen.queryByLabelText("Forbidden Claims 2")).not.toBeInTheDocument();
  });
});
