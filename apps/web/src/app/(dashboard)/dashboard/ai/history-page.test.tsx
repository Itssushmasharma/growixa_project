import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import { HistoryPage } from "./history-page";
import type { AIGeneration, MeResponse } from "./types";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
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
  approval_status: "PENDING_APPROVAL",
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
  approval_status: "PENDING_APPROVAL",
};

function mockLoad(permissions: string[], generations: AIGeneration[]) {
  mockedApiFetch.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(meWithPermissions(permissions));
    if (path === "/ai/generations") return Promise.resolve(generations);
    if (path === "/billing/subscription")
      return Promise.resolve({
        period_ai_used: 12,
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
});

describe("HistoryPage (AI Studio)", () => {
  it("shows an access-denied message for a user without ai.view", async () => {
    mockLoad([], []);

    renderHistoryPage();

    expect(
      await screen.findByText("You don't have access to the AI Studio."),
    ).toBeInTheDocument();
  });

  it("shows ready state when there are no past generations", async () => {
    mockLoad(["ai.view", "ai.manage"], []);

    renderHistoryPage();

    expect(await screen.findByText("Ready to create with AI")).toBeInTheDocument();
    expect(screen.getByText("Generate content")).toBeInTheDocument();
  });

  it("lists a completed generation with its output text and approval button", async () => {
    mockLoad(["ai.view", "ai.manage"], [SUBJECT_LINE_GENERATION]);

    renderHistoryPage();

    expect(await screen.findByText("20% Off Running Shoes!")).toBeInTheDocument();
    expect(screen.getByText("● Pending approval")).toBeInTheDocument();
    expect(screen.getAllByText("Email subject").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("button", { name: "✓ Approve & use" })).toBeInTheDocument();
  });

  it("approves a generation upon clicking Approve & use", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view", "ai.manage"], [SUBJECT_LINE_GENERATION]);

    renderHistoryPage();
    const approveBtn = await screen.findByRole("button", { name: "✓ Approve & use" });

    await user.click(approveBtn);

    expect(screen.getAllByText("✓ Approved").length).toBeGreaterThanOrEqual(1);
  });

  it("lists a failed generation with its error message", async () => {
    mockLoad(["ai.view", "ai.manage"], [FAILED_HASHTAGS_GENERATION]);

    renderHistoryPage();

    expect(await screen.findByText("Error: Provider returned HTTP 401")).toBeInTheDocument();
    expect(screen.getByText("✕ Failed")).toBeInTheDocument();
  });

  it("filters by capability tab", async () => {
    const user = userEvent.setup();
    mockLoad(["ai.view", "ai.manage"], [SUBJECT_LINE_GENERATION, FAILED_HASHTAGS_GENERATION]);

    renderHistoryPage();
    await screen.findByText("20% Off Running Shoes!");
    expect(screen.getByText("Error: Provider returned HTTP 401")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Hashtags" }));

    expect(screen.queryByText("20% Off Running Shoes!")).not.toBeInTheDocument();
    expect(screen.getByText("Error: Provider returned HTTP 401")).toBeInTheDocument();
  });

  it("generates variations when prompt is submitted", async () => {
    let callCount = 0;
    const user = userEvent.setup();
    mockedApiFetch.mockImplementation((path: string, options?: RequestInit) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["ai.view", "ai.manage"]));
      if (path === "/ai/generations") return Promise.resolve([]);
      if (path === "/billing/subscription")
        return Promise.resolve({
          period_ai_used: 5,
          plan: { max_monthly_ai_runs: 500, name: "Growth" },
        });
      if (path.startsWith("/ai/generate/") && options?.method === "POST") {
        callCount++;
        return Promise.resolve({
          id: `new-gen-${callCount}`,
          capability: "SUBJECT_LINE",
          output: { text: "Exclusive Early Access — 30% Off" },
          provider: "OPENAI",
          model: "gpt-4o",
          prompt_tokens: 50,
          completion_tokens: 15,
          estimated_cost_usd: 0.0005,
          status: "COMPLETE",
          error_message: null,
          created_at: new Date().toISOString(),
        });
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderHistoryPage();
    await screen.findByText("Ready to create with AI");

    const promptInput = screen.getByLabelText("Prompt");
    await user.type(promptInput, "Flash sale summer shoes");

    const generateBtn = screen.getByRole("button", { name: /Generate 5 variations/i });
    await user.click(generateBtn);

    await waitFor(() => {
      expect(screen.getAllByText("Exclusive Early Access — 30% Off").length).toBeGreaterThan(0);
    });
  });
});


