import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { HistoryPage } from "./history-page";
import type { AIGeneration, MeResponse } from "./types";

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

const SUBJECT_LINE_GENERATION: AIGeneration = {
  id: "gen-1",
  capability: "SUBJECT_LINE",
  output: { text: "20% Off Running Shoes!" },
  provider: "OPENAI",
  model: "gpt-4o-mini",
  prompt_tokens: 100,
  completion_tokens: 20,
  estimated_cost_usd: 0.0012,
  status: "COMPLETE",
  error_message: null,
  linked_entity_type: null,
  linked_entity_id: null,
  created_at: "2026-08-13T00:00:00Z",
};

const FAILED_HASHTAGS_GENERATION: AIGeneration = {
  id: "gen-2",
  capability: "HASHTAGS",
  output: null,
  provider: "ANTHROPIC",
  model: "claude-sonnet-4-5",
  prompt_tokens: null,
  completion_tokens: null,
  estimated_cost_usd: null,
  status: "FAILED",
  error_message: "Provider returned HTTP 401",
  linked_entity_type: null,
  linked_entity_id: null,
  created_at: "2026-08-13T01:00:00Z",
};

function mockLoad(permissions: string[], generations: AIGeneration[]) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/ai/generations") return Promise.resolve(generations);
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("HistoryPage", () => {
  it("shows an access-denied message for a user without ai.view", async () => {
    mockLoad([], []);

    render(<HistoryPage />);

    expect(
      await screen.findByText("You don't have access to AI generation history."),
    ).toBeInTheDocument();
  });

  it("shows an empty state when there are no generations", async () => {
    mockLoad(["ai.view"], []);

    render(<HistoryPage />);

    expect(
      await screen.findByText(
        'No AI generations yet — use "Generate with AI" in a campaign or social post to get started.',
      ),
    ).toBeInTheDocument();
  });

  it("lists a completed generation with its output text", async () => {
    mockLoad(["ai.view"], [SUBJECT_LINE_GENERATION]);

    render(<HistoryPage />);

    expect(await screen.findByText("20% Off Running Shoes!")).toBeInTheDocument();
    expect(screen.getByText("Complete")).toBeInTheDocument();
    expect(screen.getByText("Subject line")).toBeInTheDocument();
  });

  it("lists a failed generation with its error message", async () => {
    mockLoad(["ai.view"], [FAILED_HASHTAGS_GENERATION]);

    render(<HistoryPage />);

    expect(await screen.findByText("Error: Provider returned HTTP 401")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("filters by capability tab", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view"], [SUBJECT_LINE_GENERATION, FAILED_HASHTAGS_GENERATION]);

    render(<HistoryPage />);
    await screen.findByText("20% Off Running Shoes!");
    expect(screen.getByText("Error: Provider returned HTTP 401")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Hashtags" }));

    expect(screen.queryByText("20% Off Running Shoes!")).not.toBeInTheDocument();
    expect(screen.getByText("Error: Provider returned HTTP 401")).toBeInTheDocument();
  });
});
