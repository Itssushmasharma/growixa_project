import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "@/lib/api-client";
import { ToastProvider } from "@/components/toast/toast-context";

import { TemplatesPage } from "./templates-page";
import type { EmailTemplate, MeResponse } from "./types";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderTemplatesPage() {
  return render(
    <ToastProvider>
      <TemplatesPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const TEMPLATE: EmailTemplate = {
  id: "template-1",
  name: "Welcome email",
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

const OTHER_TEMPLATE: EmailTemplate = {
  id: "template-2",
  name: "Monthly digest",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
  current_version: {
    id: "version-2",
    template_id: "template-2",
    version_number: 1,
    subject: "Your monthly recap",
    body_html: "<p>Recap</p>",
    body_text: null,
    created_at: "2026-08-01T00:00:00Z",
  },
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("TemplatesPage", () => {
  it("shows an access-denied message for a user without campaigns.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/templates") return Promise.reject(new ApiError(403, "Forbidden"));
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();

    expect(
      await screen.findByText("You don't have access to email templates."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Email templates")).not.toBeInTheDocument();
  });

  it("shows the template list to a view-only user without manage links", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();

    expect(await screen.findByText("Welcome email")).toBeInTheDocument();
    expect(screen.getByText("Welcome to Growixa")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "+ New template" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Duplicate" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
    // Preview is a read-only action, available even without campaigns.manage.
    expect(screen.getByRole("button", { name: "Preview" })).toBeInTheDocument();
  });

  it("shows manage links pointing at the dedicated create/edit/duplicate pages", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome email");

    expect(screen.getByRole("link", { name: "+ New template" })).toHaveAttribute(
      "href",
      "/dashboard/templates/new",
    );
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href",
      "/dashboard/templates/template-1/edit",
    );
    expect(screen.getByRole("link", { name: "Duplicate" })).toHaveAttribute(
      "href",
      "/dashboard/templates/new?duplicateFrom=template-1",
    );
  });

  it("toggles a rendered HTML preview of the saved current version", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome email");

    expect(screen.queryByTitle("Template preview")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Preview" }));
    const frame = screen.getByTitle("Template preview") as HTMLIFrameElement;
    expect(frame).toBeInTheDocument();
    expect(frame.srcdoc).toBe(TEMPLATE.current_version!.body_html);

    await user.click(screen.getByRole("button", { name: "Hide preview" }));
    expect(screen.queryByTitle("Template preview")).not.toBeInTheDocument();
  });

  it("shows an empty state when there are no templates yet", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();

    expect(await screen.findByText("No email templates yet.")).toBeInTheDocument();
  });

  it("filters the list by search query", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE, OTHER_TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome email");
    expect(screen.getByText("Monthly digest")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Search templates"), "monthly");

    expect(screen.queryByText("Welcome email")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly digest")).toBeInTheDocument();
  });

  it("deletes a template after confirmation", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates" && !init) return Promise.resolve([TEMPLATE]);
      if (path === "/templates/template-1" && init?.method === "DELETE") {
        return Promise.resolve(undefined);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome email");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(screen.queryByText("Welcome email")).not.toBeInTheDocument());
    expect(await screen.findByText("Template deleted.")).toBeInTheDocument();
  });

  it("does not delete when the confirmation is declined", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates" && !init) return Promise.resolve([TEMPLATE]);
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome email");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(screen.getByText("Welcome email")).toBeInTheDocument();
    expect(mockedApiFetch).not.toHaveBeenCalledWith(
      "/templates/template-1",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("shows the backend's detail when deletion is blocked (e.g. in use by a campaign)", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates" && !init) return Promise.resolve([TEMPLATE]);
      if (path === "/templates/template-1" && init?.method === "DELETE") {
        return Promise.reject(
          new ApiError(
            409,
            JSON.stringify({
              detail: "This template is referenced by one or more campaigns and cannot be deleted",
            }),
          ),
        );
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome email");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(
      await screen.findByText(
        "This template is referenced by one or more campaigns and cannot be deleted",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Welcome email")).toBeInTheDocument();
  });
});
