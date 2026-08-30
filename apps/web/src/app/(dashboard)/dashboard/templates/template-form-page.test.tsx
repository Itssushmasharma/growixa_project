import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";
import { ToastProvider } from "@/components/toast/toast-context";

import { TemplateFormPage } from "./template-form-page";
import type { EmailTemplate, MeResponse } from "./types";

const mockPush = vi.fn();
const mockBack = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
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

function renderFormPage(props: { mode: "create" | "edit"; templateId?: string }) {
  return render(
    <ToastProvider>
      <TemplateFormPage {...props} />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const TEMPLATE: EmailTemplate = {
  id: "template-1",
  name: "Welcome email",
  is_platform_default: false,
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  current_version: {
    id: "version-1",
    template_id: "template-1",
    version_number: 1,
    subject: "Welcome to Growixa",
    body_html: "<p>Hello</p>",
    body_text: "Hello",
    created_at: "2026-08-06T00:00:00Z",
  },
};

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockPush.mockReset();
  mockBack.mockReset();
  mockSearchParams = new URLSearchParams();
});

describe("TemplateFormPage", () => {
  it("shows an access-denied message for a user without campaigns.manage", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });

    expect(
      await screen.findByText("You don't have access to email templates."),
    ).toBeInTheDocument();
  });

  it("creates a template and navigates back to the list", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates" && init?.method === "POST") return Promise.resolve(TEMPLATE);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New template" });

    await user.type(screen.getByLabelText("Template name"), "Welcome email");
    await user.type(screen.getByLabelText("Email subject"), "Welcome to Growixa");
    await user.type(screen.getByLabelText("HTML body"), "<p>Hello</p>");
    await user.click(screen.getByRole("button", { name: "Create template" }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/dashboard/templates"));
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/templates",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows a live preview as the HTML body is typed", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New template" });

    expect(screen.queryByTitle("Template preview")).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("HTML body"), "<p>Hi</p>");

    const frame = screen.getByTitle("Template preview") as HTMLIFrameElement;
    expect(frame.srcdoc).toBe("<p>Hi</p>");
  });

  it("pre-fills the form from a source template when duplicating", async () => {
    mockSearchParams = new URLSearchParams("duplicateFrom=template-1");
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates/template-1") return Promise.resolve(TEMPLATE);
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });

    expect(await screen.findByLabelText("Template name")).toHaveValue("Welcome email (copy)");
    expect(screen.getByLabelText("Email subject")).toHaveValue("Welcome to Growixa");
    expect(screen.getByLabelText("HTML body")).toHaveValue("<p>Hello</p>");
  });

  it("loads and edits an existing template, saving a new version", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates/template-1" && !init) return Promise.resolve(TEMPLATE);
      if (path === "/templates/template-1/versions" && init?.method === "POST") {
        return Promise.resolve({
          ...TEMPLATE,
          current_version: { ...TEMPLATE.current_version!, version_number: 2 },
        });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", templateId: "template-1" });

    const nameInput = await screen.findByLabelText("Template name");
    expect(nameInput).toHaveValue("Welcome email");
    expect(nameInput).toBeDisabled();
    expect(screen.getByLabelText("Email subject")).toHaveValue("Welcome to Growixa");

    await user.click(screen.getByRole("button", { name: "Save new version" }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/dashboard/templates"));
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/templates/template-1/versions",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("inserts personalization tokens into the visual editor and preview", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New template" });

    await user.click(screen.getByRole("button", { name: "+ First Name" }));

    expect(screen.getByRole("textbox", { name: "Visual Editor" })).toHaveTextContent(
      "{{first_name}}",
    );

    const frame = screen.getByTitle("Template preview") as HTMLIFrameElement;
    expect(frame.srcdoc).toBe("{{first_name}}");
  });

  it("formats the HTML body when Format is clicked", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New template" });

    const textarea = screen.getByLabelText("HTML body");
    await user.type(textarea, "<div><p>Hi</p></div>");
    await user.click(screen.getByRole("button", { name: "Format" }));

    expect(textarea).toHaveValue("<div>\n  <p>\n    Hi\n  </p>\n</div>");
  });

  it("copies the HTML body to the clipboard when Copy is clicked", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New template" });

    await user.type(screen.getByLabelText("HTML body"), "<p>Hi</p>");
    await user.click(screen.getByRole("button", { name: "Copy" }));

    await waitFor(() => expect(writeText).toHaveBeenCalledWith("<p>Hi</p>"));
    expect(await screen.findByText("HTML body copied to clipboard.")).toBeInTheDocument();
  });

  it("navigates back when Cancel is clicked", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByRole("heading", { name: "New template" });

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(mockBack).toHaveBeenCalled();
  });
});
