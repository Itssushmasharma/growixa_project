import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { SocialPage } from "./social-page";
import type { MeResponse, SocialPost } from "./types";

function renderWithToast(ui: React.ReactElement) {
  return render(<ToastProvider>{ui}</ToastProvider>);
}

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const DRAFT_POST: SocialPost = {
  id: "post-1",
  social_connection_id: "conn-1",
  caption: "Check out our new launch!",
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

const SCHEDULED_POST: SocialPost = {
  id: "post-2",
  social_connection_id: "conn-1",
  caption: "Scheduled post",
  status: "SCHEDULED",
  scheduled_at: "2026-11-29T09:00:00Z",
  cancelled_at: null,
  published_at: null,
  ig_media_id: null,
  ig_permalink: null,
  last_error: null,
  created_at: "2026-08-12T00:00:00Z",
  updated_at: "2026-08-12T00:00:00Z",
  media: [],
};

const PUBLISHED_POST: SocialPost = {
  id: "post-3",
  social_connection_id: "conn-1",
  caption: "Already live",
  status: "PUBLISHED",
  scheduled_at: null,
  cancelled_at: null,
  published_at: "2026-08-01T00:00:00Z",
  ig_media_id: "ig-media-1",
  ig_permalink: "https://instagram.com/p/abc",
  last_error: null,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
  media: [],
};

function mockLoad(permissions: string[], posts: SocialPost[]) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/social/posts") return Promise.resolve(posts);
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("SocialPage", () => {
  it("shows an access-denied message for a user without social.view", async () => {
    mockLoad([], []);

    renderWithToast(<SocialPage />);

    expect(await screen.findByText("You don't have access to social posts.")).toBeInTheDocument();
  });

  it("shows the post list to a view-only user without a New post link", async () => {
    mockLoad(["social.view"], [DRAFT_POST]);

    renderWithToast(<SocialPage />);

    expect(await screen.findByText("Check out our new launch!")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "+ New post" })).not.toBeInTheDocument();
  });

  it("shows the New post link for a social.manage user", async () => {
    mockLoad(["social.view", "social.manage"], []);

    renderWithToast(<SocialPage />);
    await screen.findByText("No social posts yet.");

    expect(screen.getByRole("link", { name: "+ New post" })).toHaveAttribute(
      "href",
      "/dashboard/social/new",
    );
  });

  it("links each row to its detail page", async () => {
    mockLoad(["social.view"], [DRAFT_POST]);

    renderWithToast(<SocialPage />);
    const row = await screen.findByText("Check out our new launch!");

    expect(row.closest("a")).toHaveAttribute("href", "/dashboard/social/post-1");
  });

  it("filters by status tab", async () => {
    const user = userEvent.setup();
    mockLoad(["social.view"], [DRAFT_POST, PUBLISHED_POST]);

    renderWithToast(<SocialPage />);
    await screen.findByText("Check out our new launch!");
    expect(screen.getByText("Already live")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: /^Published/ }));

    expect(screen.queryByText("Check out our new launch!")).not.toBeInTheDocument();
    expect(screen.getByText("Already live")).toBeInTheDocument();
  });

  it("shows Cancel button only for DRAFT and SCHEDULED posts when canManage", async () => {
    mockLoad(["social.view", "social.manage"], [DRAFT_POST, SCHEDULED_POST, PUBLISHED_POST]);

    renderWithToast(<SocialPage />);
    await screen.findByText("Check out our new launch!");

    const cancelButtons = screen.getAllByRole("button", { name: "Cancel post" });
    expect(cancelButtons).toHaveLength(2);
  });

  it("hides Cancel button entirely when canManage is false", async () => {
    mockLoad(["social.view"], [DRAFT_POST, SCHEDULED_POST]);

    renderWithToast(<SocialPage />);
    await screen.findByText("Check out our new launch!");

    expect(screen.queryByRole("button", { name: "Cancel post" })).not.toBeInTheDocument();
  });

  it("links to the content calendar", async () => {
    mockLoad(["social.view"], []);

    renderWithToast(<SocialPage />);
    await screen.findByText("No social posts yet.");

    expect(screen.getByRole("link", { name: "Calendar" })).toHaveAttribute(
      "href",
      "/dashboard/social/calendar",
    );
  });
});
