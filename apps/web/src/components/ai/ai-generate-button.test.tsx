import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import { AIGenerateButton } from "./ai-generate-button";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

beforeEach(() => {
  mockedApiFetch.mockReset();
});

function renderButton(onInsert = vi.fn()) {
  render(
    <ToastProvider>
      <AIGenerateButton
        capability="SUBJECT_LINE"
        triggerLabel="Generate with AI"
        briefPlaceholder="e.g. a sale"
        onInsert={onInsert}
      />
    </ToastProvider>,
  );
  return { onInsert };
}

describe("AIGenerateButton", () => {
  it("opens the panel on click and generates a suggestion", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValue({
      id: "gen-1",
      capability: "SUBJECT_LINE",
      output: { text: "20% Off Running Shoes!" },
      status: "COMPLETE",
      error_message: null,
    });

    renderButton();
    await user.click(screen.getByRole("button", { name: "✨ Generate with AI" }));

    const brief = screen.getByLabelText("What should this be about?");
    await user.type(brief, "a running shoe sale");
    await user.click(screen.getByRole("button", { name: "Generate" }));

    expect(await screen.findByText("20% Off Running Shoes!")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/ai/generate/SUBJECT_LINE",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("calls onInsert with the generated text and closes the panel", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValue({
      id: "gen-1",
      capability: "SUBJECT_LINE",
      output: { text: "20% Off Running Shoes!" },
      status: "COMPLETE",
      error_message: null,
    });

    const { onInsert } = renderButton();
    await user.click(screen.getByRole("button", { name: "✨ Generate with AI" }));
    await user.type(screen.getByLabelText("What should this be about?"), "a sale");
    await user.click(screen.getByRole("button", { name: "Generate" }));
    await screen.findByText("20% Off Running Shoes!");

    await user.click(screen.getByRole("button", { name: "Insert" }));

    expect(onInsert).toHaveBeenCalledWith("20% Off Running Shoes!");
    await waitFor(() =>
      expect(screen.queryByText("20% Off Running Shoes!")).not.toBeInTheDocument(),
    );
  });

  it("shows a friendly message when no AI provider is configured", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockRejectedValue(
      new ApiError(
        409,
        JSON.stringify({ detail: "No AI provider is configured for this account" }),
      ),
    );

    renderButton();
    await user.click(screen.getByRole("button", { name: "✨ Generate with AI" }));
    await user.type(screen.getByLabelText("What should this be about?"), "a sale");
    await user.click(screen.getByRole("button", { name: "Generate" }));

    expect(
      await screen.findByText(
        "AI isn't configured yet — connect a provider under Integrations, or ask your platform admin.",
      ),
    ).toBeInTheDocument();
  });

  it("disables Generate until a brief is typed", async () => {
    renderButton();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "✨ Generate with AI" }));

    expect(screen.getByRole("button", { name: "Generate" })).toBeDisabled();
  });
});
