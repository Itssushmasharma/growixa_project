import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { PostFormPage } from "./post-form-page";
import type { MeResponse, SocialConnection, SocialPost } from "./types";

const mockPush = vi.fn();
const mockBack = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, back: mockBack }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderFormPage(props: { mode: "create" | "edit"; postId?: string }) {
  return render(
    <ToastProvider>
      <PostFormPage {...props} />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const CONNECTION: SocialConnection = {
  id: "conn-1",
  provider: "INSTAGRAM_BUSINESS",
  ig_business_account_id: "ig-123",
  ig_username: "growixa_test",
  facebook_page_id: "page-123",
  is_active: true,
  last_connected_at: "2026-08-12T00:00:00Z",
  last_error: null,
};

const DRAFT_POST: SocialPost = {
  id: "post-1",
  social_connection_id: "conn-1",
  caption: "Hello world",
  status: "DRAFT",
  scheduled_at: null,
  cancelled_at: null,
  published_at: null,
  ig_media_id: null,
  ig_permalink: null,
  last_error: null,
  created_at: "2026-08-12T00:00:00Z",
  updated_at: "2026-08-12T00:00:00Z",
  media: [],
};

const DRAFT_POST_WITH_MEDIA: SocialPost = {
  ...DRAFT_POST,
  media: [
    { id: "media-1", media_type: "IMAGE", public_url: "https://x.test/img.jpg", position: 0 },
  ],
};

beforeEach(() => {
  mockedApiFetch.mockReset();
});

function jpegFile(): File {
  return new File([new Uint8Array([0xff, 0xd8, 0xff])], "test.jpg", { type: "image/jpeg" });
}

describe("PostFormPage", () => {
  it("shows an access-denied message when creating without social.manage", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["social.view"]));
      throw new Error(`unexpected path: ${path}`);
    });

    renderFormPage({ mode: "create" });

    expect(await screen.findByText("You don't have access to create posts.")).toBeInTheDocument();
  });

  it("creates a draft and redirects to its detail page", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["social.view", "social.manage"]));
      if (path === "/social/connections") return Promise.resolve([CONNECTION]);
      if (path === "/social/posts" && init?.method === "POST") {
        return Promise.resolve(DRAFT_POST);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "create" });
    await screen.findByLabelText("Instagram connection");

    await user.selectOptions(screen.getByLabelText("Instagram connection"), "conn-1");
    await user.type(screen.getByLabelText("Caption"), "Hello world");
    await user.click(screen.getByRole("button", { name: "Create draft" }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/dashboard/social/post-1"));
  });

  it("uploads an image and shows it once added", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["social.view", "social.manage"]));
      if (path === "/social/posts/post-1" && !init) return Promise.resolve(DRAFT_POST);
      if (path === "/social/posts/post-1/media" && init?.method === "POST") {
        return Promise.resolve(DRAFT_POST_WITH_MEDIA.media[0]);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", postId: "post-1" });
    const fileInput = await screen.findByLabelText("Upload image");

    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["social.view", "social.manage"]));
      if (path === "/social/posts/post-1" && !init) return Promise.resolve(DRAFT_POST_WITH_MEDIA);
      if (path === "/social/posts/post-1/media" && init?.method === "POST") {
        return Promise.resolve(DRAFT_POST_WITH_MEDIA.media[0]);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    await user.upload(fileInput, jpegFile());

    expect(await screen.findByText("Image added.")).toBeInTheDocument();
  });

  it("publishes now when social.publish is held and media exists", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(
          meWithPermissions(["social.view", "social.manage", "social.publish"]),
        );
      if (path === "/social/posts/post-1" && !init) return Promise.resolve(DRAFT_POST_WITH_MEDIA);
      if (path === "/social/posts/post-1/publish" && init?.method === "POST") {
        return Promise.resolve({ job_id: "job-1" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    vi.spyOn(window, "confirm").mockReturnValue(true);

    renderFormPage({ mode: "edit", postId: "post-1" });
    await screen.findByText("Publish");

    await user.click(screen.getByRole("button", { name: "Publish now" }));

    expect(
      await screen.findByText("Publishing — check back shortly for status."),
    ).toBeInTheDocument();
  });

  it("does not show publish controls without social.publish", async () => {
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["social.view", "social.manage"]));
      if (path === "/social/posts/post-1" && !init) return Promise.resolve(DRAFT_POST_WITH_MEDIA);
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", postId: "post-1" });
    await screen.findByDisplayValue("Hello world");

    expect(screen.queryByRole("button", { name: "Publish now" })).not.toBeInTheDocument();
  });

  it("shows a Retry button for a FAILED post", async () => {
    const user = userEvent.setup();
    const failedPost: SocialPost = {
      ...DRAFT_POST_WITH_MEDIA,
      status: "FAILED",
      last_error: "boom",
    };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me")
        return Promise.resolve(meWithPermissions(["social.view", "social.publish"]));
      if (path === "/social/posts/post-1" && !init) return Promise.resolve(failedPost);
      if (path === "/social/posts/post-1/retry" && init?.method === "POST") {
        return Promise.resolve({ job_id: "job-2" });
      }
      throw new Error(`unexpected call: ${path}`);
    });

    renderFormPage({ mode: "edit", postId: "post-1" });
    expect(await screen.findByText("Error: boom")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() =>
      expect(
        mockedApiFetch.mock.calls.some(([path]) => path === "/social/posts/post-1/retry"),
      ).toBe(true),
    );
  });
});
