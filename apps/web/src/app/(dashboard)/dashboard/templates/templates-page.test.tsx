import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { TemplatesPage } from "./templates-page";
import type { EmailTemplate, MeResponse } from "./types";

const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

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
  name: "Welcome Onboarding email",
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

const PLATFORM_TEMPLATE: EmailTemplate = {
  id: "platform-template-1",
  name: "Platform Welcome Default",
  is_platform_default: true,
  created_at: "2026-08-06T00:00:00Z",
  updated_at: "2026-08-06T00:00:00Z",
  current_version: {
    id: "platform-version-1",
    template_id: "platform-template-1",
    version_number: 1,
    subject: "Welcome to Growixa",
    body_html: "<p>Hello {{first_name}}</p>",
    body_text: "Hello {{first_name}}",
    created_at: "2026-08-06T00:00:00Z",
  },
};

const OTHER_TEMPLATE: EmailTemplate = {
  id: "template-2",
  name: "Monthly Newsletter digest",
  is_platform_default: false,
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
  mockPush.mockReset();
});

describe("TemplatesPage", () => {
  it("shows an access-denied message for a user without campaigns.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/templates") return Promise.reject(new ApiError(403, "Forbidden"));
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();

    expect(
      await screen.findByText("You don't have access to email templates."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Email Templates")).not.toBeInTheDocument();
  });

  it("shows the template list with PageHeader to a view-only user without manage links", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();

    expect(await screen.findByRole("heading", { name: "Email Templates" })).toBeInTheDocument();
    expect(screen.getByText("Welcome Onboarding email")).toBeInTheDocument();
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
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

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

  it("toggles a rendered HTML preview of the saved current version and switches device view", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

    expect(screen.queryByTitle("Template preview")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Preview" }));
    const frame = screen.getByTitle("Template preview") as HTMLIFrameElement;
    expect(frame).toBeInTheDocument();
    expect(frame.srcdoc).toBe(TEMPLATE.current_version!.body_html);

    // Switch to Mobile
    const mobileBtn = screen.getByRole("button", { name: "📱 Mobile" });
    await user.click(mobileBtn);

    // Switch back to Desktop
    const desktopBtn = screen.getByRole("button", { name: "🖥️ Desktop" });
    await user.click(desktopBtn);

    await user.click(screen.getByRole("button", { name: "Close preview" }));
    expect(screen.queryByTitle("Template preview")).not.toBeInTheDocument();
  });

  it("shows an empty state when there are no templates yet", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([]);
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
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
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");
    expect(screen.getByText("Monthly Newsletter digest")).toBeInTheDocument();

    await user.type(screen.getByLabelText("Search templates"), "newsletter");

    expect(screen.queryByText("Welcome Onboarding email")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly Newsletter digest")).toBeInTheDocument();
  });

  it("filters the list by category pills", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE, OTHER_TEMPLATE]);
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");
    expect(screen.getByText("Monthly Newsletter digest")).toBeInTheDocument();

    // Click Newsletter tab
    await user.click(screen.getByRole("tab", { name: /Newsletter/i }));
    expect(screen.queryByText("Welcome Onboarding email")).not.toBeInTheDocument();
    expect(screen.getByText("Monthly Newsletter digest")).toBeInTheDocument();

    // Click Onboarding tab
    await user.click(screen.getByRole("tab", { name: /Onboarding/i }));
    expect(screen.getByText("Welcome Onboarding email")).toBeInTheDocument();
    expect(screen.queryByText("Monthly Newsletter digest")).not.toBeInTheDocument();

    // Click All tab
    await user.click(screen.getByRole("tab", { name: /^All/i }));
    expect(screen.getByText("Welcome Onboarding email")).toBeInTheDocument();
    expect(screen.getByText("Monthly Newsletter digest")).toBeInTheDocument();
  });

  it("toggles between grid and list views", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

    const listBtn = screen.getByRole("button", { name: "List View" });
    await user.click(listBtn);
    expect(listBtn).toHaveAttribute("aria-pressed", "true");

    const gridBtn = screen.getByRole("button", { name: "Grid View" });
    await user.click(gridBtn);
    expect(gridBtn).toHaveAttribute("aria-pressed", "true");
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
      if (path === "/templates/platform-defaults" && !init) return Promise.resolve([]);
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() =>
      expect(screen.queryByText("Welcome Onboarding email")).not.toBeInTheDocument(),
    );
    expect(await screen.findByText("Template deleted.")).toBeInTheDocument();
  });

  it("does not delete when the confirmation is declined", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(false);
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates" && !init) return Promise.resolve([TEMPLATE]);
      if (path === "/templates/platform-defaults" && !init) return Promise.resolve([]);
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(screen.getByText("Welcome Onboarding email")).toBeInTheDocument();
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
      if (path === "/templates/platform-defaults" && !init) return Promise.resolve([]);
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(
      await screen.findByText(
        "This template is referenced by one or more campaigns and cannot be deleted",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Welcome Onboarding email")).toBeInTheDocument();
  });

  it("does not render the Default Templates section when there are none", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/templates/platform-defaults") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Welcome Onboarding email");

    expect(screen.queryByText("Default Templates")).not.toBeInTheDocument();
  });

  it("shows platform default templates in a separate read-only section", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates") return Promise.resolve([TEMPLATE]);
      if (path === "/templates/platform-defaults") return Promise.resolve([PLATFORM_TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Default Templates");

    expect(screen.getByText("Platform Welcome Default")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Use this template" })).toBeInTheDocument();
    // My Templates' own row is unaffected -- still just the account-owned template.
    expect(screen.getByText("Welcome Onboarding email")).toBeInTheDocument();
  });

  it("hides the 'Use this template' action for a view-only user", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["campaigns.view"]));
      if (path === "/templates") return Promise.resolve([]);
      if (path === "/templates/platform-defaults") return Promise.resolve([PLATFORM_TEMPLATE]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Platform Welcome Default");

    expect(screen.queryByRole("button", { name: "Use this template" })).not.toBeInTheDocument();
    // Preview stays available -- browse/preview only, per GRX-EMAIL-016.
    expect(screen.getByRole("button", { name: "Preview" })).toBeInTheDocument();
  });

  it("clones a platform default and navigates to the new copy's edit page", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["campaigns.view", "campaigns.manage"]));
      if (path === "/templates" && !init) return Promise.resolve([]);
      if (path === "/templates/platform-defaults") return Promise.resolve([PLATFORM_TEMPLATE]);
      if (path === "/templates/platform-template-1/clone" && init?.method === "POST") {
        return Promise.resolve({
          ...PLATFORM_TEMPLATE,
          id: "cloned-1",
          is_platform_default: false,
        });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderTemplatesPage();
    await screen.findByText("Platform Welcome Default");

    await user.click(screen.getByRole("button", { name: "Use this template" }));

    expect(
      await screen.findByText('"Platform Welcome Default" added to your templates.'),
    ).toBeInTheDocument();
    expect(mockPush).toHaveBeenCalledWith("/dashboard/templates/cloned-1/edit");
  });
});
