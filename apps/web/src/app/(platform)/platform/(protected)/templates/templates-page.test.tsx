import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { PlatformTemplatesPage } from "./templates-page";
import type { EmailTemplate } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const TEMPLATE: EmailTemplate = {
  id: "platform-template-1",
  name: "Welcome Series Kickoff",
  is_platform_default: true,
  created_at: "2026-08-30T00:00:00Z",
  updated_at: "2026-08-30T00:00:00Z",
  current_version: {
    id: "version-1",
    template_id: "platform-template-1",
    version_number: 1,
    subject: "Welcome to Growixa",
    body_html: "<p>Hello {{first_name}}</p>",
    body_text: "Hello {{first_name}}",
    created_at: "2026-08-30T00:00:00Z",
  },
};

function renderPage() {
  return render(
    <ToastProvider>
      <PlatformTemplatesPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("PlatformTemplatesPage", () => {
  it("shows an access-denied message on a 403", async () => {
    mockedApiFetch.mockRejectedValue(new ApiError(403, "Forbidden"));

    renderPage();

    expect(
      await screen.findByText("You don't have access to manage platform default templates."),
    ).toBeInTheDocument();
  });

  it("lists existing default templates", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/platform/templates") return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("Welcome Series Kickoff")).toBeInTheDocument();
    expect(screen.getByText("Welcome to Growixa")).toBeInTheDocument();
    expect(screen.getByText("v1")).toBeInTheDocument();
  });

  it("shows an empty state when there are none yet", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/platform/templates") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("No default templates published yet.")).toBeInTheDocument();
  });

  it("publishes a new default template", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/platform/templates" && !init) return Promise.resolve([]);
      if (path === "/platform/templates" && init?.method === "POST") {
        return Promise.resolve(TEMPLATE);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderPage();
    await screen.findByText("No default templates published yet.");

    await user.click(screen.getByRole("button", { name: "+ New default template" }));
    await user.type(screen.getByLabelText("Name"), "Welcome Series Kickoff");
    await user.type(screen.getByLabelText("Subject"), "Welcome to Growixa");
    await user.type(screen.getByLabelText("Body (HTML)"), "<p>Hello {{first_name}}</p>");
    await user.click(screen.getByRole("button", { name: "Publish" }));

    expect(
      await screen.findByText('"Welcome Series Kickoff" published as a default template.'),
    ).toBeInTheDocument();
  });

  it("edits a template by appending a new version", async () => {
    const user = userEvent.setup();
    const updated: EmailTemplate = {
      ...TEMPLATE,
      current_version: {
        ...TEMPLATE.current_version!,
        version_number: 2,
        subject: "Updated subject",
      },
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/platform/templates" && !init) return Promise.resolve([TEMPLATE]);
      if (path === "/platform/templates/platform-template-1/versions" && init?.method === "POST") {
        return Promise.resolve(updated);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderPage();
    await screen.findByText("Welcome Series Kickoff");

    await user.click(screen.getByRole("button", { name: "Edit" }));
    const subjectInput = screen.getByLabelText("Subject");
    await user.clear(subjectInput);
    await user.type(subjectInput, "Updated subject");
    await user.click(screen.getByRole("button", { name: "Save new version" }));

    expect(await screen.findByText('"Welcome Series Kickoff" updated to v2.')).toBeInTheDocument();
  });

  it("retires a template after confirmation", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/platform/templates" && !init) return Promise.resolve([TEMPLATE]);
      if (path === "/platform/templates/platform-template-1" && init?.method === "DELETE") {
        return Promise.resolve(undefined);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderPage();
    await screen.findByText("Welcome Series Kickoff");

    await user.click(screen.getByRole("button", { name: "Retire" }));

    expect(await screen.findByText('"Welcome Series Kickoff" retired.')).toBeInTheDocument();
    expect(screen.queryByText("Welcome Series Kickoff")).not.toBeInTheDocument();
  });

  it("does not retire when the confirmation is declined", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/platform/templates" && !init) return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected call: ${path}`);
    });

    renderPage();
    await screen.findByText("Welcome Series Kickoff");

    await user.click(screen.getByRole("button", { name: "Retire" }));

    expect(screen.getByText("Welcome Series Kickoff")).toBeInTheDocument();
    expect(mockedApiFetch).not.toHaveBeenCalledWith(
      "/platform/templates/platform-template-1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("opens a preview modal when clicking the Preview button", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/platform/templates") return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    await screen.findByText("Welcome Series Kickoff");

    await user.click(screen.getByRole("button", { name: "Preview" }));

    // The shared TemplatePreviewModal renders the template name and subject
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Subject: Welcome to Growixa")).toBeInTheDocument();
    // An iframe renders the HTML body
    const iframe = screen.getByTitle("Template preview");
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute("srcdoc", "<p>Hello {{first_name}}</p>");
  });

  it("shows a live preview iframe in the create form when HTML is typed", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/platform/templates") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    await screen.findByText("No default templates published yet.");

    await user.click(screen.getByRole("button", { name: "+ New default template" }));

    // Before typing, no live preview iframe should exist
    expect(screen.queryByTitle("Create template live preview")).not.toBeInTheDocument();

    await user.type(screen.getByLabelText("Body (HTML)"), "<h1>Hello</h1>");

    // After typing, the live preview iframe should appear
    const previewIframe = screen.getByTitle("Create template live preview");
    expect(previewIframe).toBeInTheDocument();
    expect(previewIframe).toHaveAttribute("srcdoc", "<h1>Hello</h1>");
  });
});
