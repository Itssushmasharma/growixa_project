import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { CalendarPage } from "./calendar-page";
import type { MeResponse, SocialPost } from "./types";

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

const SCHEDULED_POST: SocialPost = {
  id: "post-1",
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
  id: "post-2",
  social_connection_id: "conn-1",
  caption: "Already live",
  status: "PUBLISHED",
  scheduled_at: null,
  cancelled_at: null,
  published_at: "2026-08-01T12:00:00Z",
  ig_media_id: "ig-media-1",
  ig_permalink: "https://instagram.com/p/abc",
  last_error: null,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
  media: [],
};

const DRAFT_POST: SocialPost = {
  id: "post-3",
  social_connection_id: "conn-1",
  caption: "Still a draft",
  status: "DRAFT",
  scheduled_at: null,
  cancelled_at: null,
  published_at: null,
  ig_media_id: null,
  ig_permalink: null,
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

describe("CalendarPage", () => {
  it("shows an access-denied message for a user without social.view", async () => {
    mockLoad([], []);

    render(<CalendarPage />);

    expect(
      await screen.findByText("You don't have access to the content calendar."),
    ).toBeInTheDocument();
  });

  it("shows an empty state when there are no scheduled or published posts", async () => {
    mockLoad(["social.view"], [DRAFT_POST]);

    render(<CalendarPage />);

    expect(await screen.findByText("No scheduled or published posts yet.")).toBeInTheDocument();
  });

  it("groups scheduled and published posts by date", async () => {
    mockLoad(["social.view"], [SCHEDULED_POST, PUBLISHED_POST, DRAFT_POST]);

    render(<CalendarPage />);

    expect(await screen.findByText("Scheduled post")).toBeInTheDocument();
    expect(screen.getByText("Already live")).toBeInTheDocument();
    expect(screen.queryByText("Still a draft")).not.toBeInTheDocument();
  });

  it("links each entry to its post detail page", async () => {
    mockLoad(["social.view"], [PUBLISHED_POST]);

    render(<CalendarPage />);
    const item = await screen.findByText("Already live");

    expect(item.closest("a")).toHaveAttribute("href", "/dashboard/social/post-2");
  });

  it("links back to the social post list", async () => {
    mockLoad(["social.view"], []);

    render(<CalendarPage />);
    await screen.findByText("No scheduled or published posts yet.");

    expect(screen.getByRole("link", { name: "Social" })).toHaveAttribute(
      "href",
      "/dashboard/social",
    );
  });
});
