import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { HistoryPage } from "./history-page";
import type { AIGeneration, MeResponse } from "./types";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function meWithPermissions(permissions: string[]): MeResponse {
  return {
    id: "user-1",
    email: "ravi@growixa.com",
    full_name: "Ravi Sharma",
    company_name: "Growixa",
    permissions,
  };
}

const SAMPLE_GENERATION: AIGeneration = {
  id: "gen-1",
  capability: "BODY_COPY",
  channel: "Email",
  output: { text: "We miss you! Here's 20% off\nHi there, claim your discount now!" },
  provider: "OPENAI",
  model: "gpt-4o-mini",
  prompt_tokens: 100,
  completion_tokens: 40,
  estimated_cost_usd: 0.0012,
  status: "COMPLETE",
  error_message: null,
  linked_entity_type: null,
  linked_entity_id: null,
  created_at: "2026-08-13T00:00:00Z",
  approval_status: "PENDING_APPROVAL",
  metrics: {
    brand_match_percent: 94,
    readability: "Excellent",
    spam_risk: "Low",
    is_best_match: true,
  },
};

function mockLoad(permissions: string[], generations: AIGeneration[] = []) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/ai/generations") return Promise.resolve(generations);
    if (path === "/campaigns")
      return Promise.resolve([{ id: "c-1", name: "Summer Sale 2025", status: "DRAFT" }]);
    if (path === "/contacts/segments")
      return Promise.resolve([{ id: "s-1", name: "Inactive Customers", contact_count: 1420 }]);
    if (path === "/billing/subscription")
      return Promise.resolve({
        period_ai_used: 245,
        plan: { max_monthly_ai_runs: 500, name: "Growth" },
      });
    throw new Error(`unexpected path: ${path}`);
  });
}

function renderHistoryPage() {
  return render(
    <ToastProvider>
      <HistoryPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockPush.mockReset();
});

describe("HistoryPage (Growixa AI Marketing Copilot)", () => {
  it("shows an access-denied message for a user without ai.view", async () => {
    mockLoad([]);

    renderHistoryPage();

    expect(await screen.findByText("You don't have access to the AI Studio.")).toBeInTheDocument();
  });

  it("renders the AI Marketing Copilot header and studio panel", async () => {
    mockLoad(["ai.view", "ai.manage"], []);

    renderHistoryPage();

    expect(await screen.findByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByText("Create with AI")).toBeInTheDocument();
    expect(screen.getByText("Suggested for you")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate 3 Variations/i })).toBeInTheDocument();
  });

  it("populates prompt and context when clicking a Suggested for you card", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view", "ai.manage"], []);

    renderHistoryPage();
    await screen.findByText("Suggested for you");

    const reEngageSuggestion = screen.getByText(/for inactive customers/i);
    await user.click(reEngageSuggestion);

    const textarea = screen.getByPlaceholderText(
      /Write a re-engagement email to win back inactive customers/i,
    ) as HTMLTextAreaElement;
    expect(textarea.value).toContain("re-engagement email with a 20% discount");
  });

  it("opens and closes the Brand Voice slide-over drawer", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view", "ai.manage"], []);

    renderHistoryPage();
    const brandVoiceBtn = await screen.findByRole("button", { name: /Brand Voice/i });

    await user.click(brandVoiceBtn);
    expect(screen.getByText("Active Brand Voice")).toBeInTheDocument();
    expect(screen.getByText(/Core Tone & Personality/i)).toBeInTheDocument();

    const closeBtn = screen.getByText("✕");
    await user.click(closeBtn);
    expect(screen.queryByText("Active Brand Voice")).not.toBeInTheDocument();
  });

  it("renders generated variation comparison cards with content and workflow actions", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view", "ai.manage"], [SAMPLE_GENERATION]);

    renderHistoryPage();

    expect(await screen.findByText("Variation 1")).toBeInTheDocument();
    expect(screen.getAllByText(/We miss you! Here's 20% off/i).length).toBeGreaterThanOrEqual(1);

    // Test Use button
    const useBtn = screen.getByRole("button", { name: "✓ Use" });
    await user.click(useBtn);

    // Test Add to Campaign button
    const campaignBtn = screen.getByTitle("Add to Campaign");
    await user.click(campaignBtn);
    expect(mockPush).toHaveBeenCalledWith("/dashboard/campaigns/new");
  });

  it("executes multi-variation generation with selected parameters", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view", "ai.manage"], []);

    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["ai.view", "ai.manage"]));
      if (path === "/ai/generations") return Promise.resolve([]);
      if (path === "/campaigns") return Promise.resolve([]);
      if (path === "/contacts/segments") return Promise.resolve([]);
      if (path === "/billing/subscription")
        return Promise.resolve({
          period_ai_used: 10,
          plan: { max_monthly_ai_runs: 500, name: "Growth" },
        });
      if (path.startsWith("/ai/generate/")) {
        return Promise.resolve({
          id: `gen-${Math.random()}`,
          capability: "BODY_COPY",
          output: { text: "Generated special discount offer for summer!" },
          status: "COMPLETE",
          error_message: null,
          created_at: new Date().toISOString(),
        } as AIGeneration);
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderHistoryPage();
    const promptInput = await screen.findByPlaceholderText(
      /Write a re-engagement email to win back inactive customers/i,
    );
    await user.type(promptInput, "Special holiday discount offer");

    const generateBtn = screen.getByRole("button", { name: /Generate 3 Variations/i });
    await user.click(generateBtn);

    await waitFor(() => {
      expect(
        screen.getAllByText(/Generated special discount offer/i).length,
      ).toBeGreaterThanOrEqual(1);
    });
  });
});
