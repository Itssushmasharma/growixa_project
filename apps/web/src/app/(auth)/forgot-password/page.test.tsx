import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import ForgotPasswordPage from "./page";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderForgotPasswordPage() {
  return render(
    <ToastProvider>
      <ForgotPasswordPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("ForgotPasswordPage", () => {
  it("requests a reset link and shows the check-email state", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce({
      message: "If an account with that email exists, a password reset link has been sent.",
      token: null,
    });

    renderForgotPasswordPage();

    await user.type(screen.getByLabelText("Email"), "ada@acme.example");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));

    expect(await screen.findByText("Check your email")).toBeInTheDocument();
    expect(screen.getByText("ada@acme.example")).toBeInTheDocument();
    expect(screen.getByText(/expires in 30 minutes/i)).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/auth/password-reset/request",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "ada@acme.example" }),
      }),
    );
  });

  it("shows a rate-limit toast", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockRejectedValueOnce(new ApiError(429, "Too many attempts"));

    renderForgotPasswordPage();

    await user.type(screen.getByLabelText("Email"), "ada@acme.example");
    await user.click(screen.getByRole("button", { name: "Send reset link" }));

    await waitFor(() =>
      expect(screen.getByText("Too many attempts. Please try again later.")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Check your email")).not.toBeInTheDocument();
  });
});
