import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import ResetPasswordPage from "./page";

let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderResetPasswordPage() {
  return render(
    <ToastProvider>
      <ResetPasswordPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockSearchParams = new URLSearchParams();
});

describe("ResetPasswordPage", () => {
  it("shows link expired when no token is present", async () => {
    renderResetPasswordPage();

    expect(await screen.findByText("Link expired")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Request a new reset link" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
    expect(mockedApiFetch).not.toHaveBeenCalled();
  });

  it("submits a matching new password and shows success", async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams("token=raw-token");
    mockedApiFetch.mockResolvedValueOnce(undefined);

    renderResetPasswordPage();

    await user.type(screen.getByLabelText("New password"), "New-Password-456!");
    await user.type(screen.getByLabelText("Confirm password"), "New-Password-456!");
    await user.click(screen.getByRole("button", { name: "Reset password" }));

    expect(await screen.findByText("Password updated")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith("/auth/password-reset/complete", {
      method: "POST",
      body: JSON.stringify({ token: "raw-token", new_password: "New-Password-456!" }),
    });
  });

  it("shows a toast and does not submit when passwords do not match", async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams("token=raw-token");

    renderResetPasswordPage();

    await user.type(screen.getByLabelText("New password"), "New-Password-456!");
    await user.type(screen.getByLabelText("Confirm password"), "Different-Password-456!");
    await user.click(screen.getByRole("button", { name: "Reset password" }));

    await waitFor(() => expect(screen.getByText("Passwords do not match.")).toBeInTheDocument());
    expect(mockedApiFetch).not.toHaveBeenCalled();
  });

  it("shows link expired when the API rejects the token", async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams("token=bad-token");
    mockedApiFetch.mockRejectedValueOnce(new Error("expired"));

    renderResetPasswordPage();

    await user.type(screen.getByLabelText("New password"), "New-Password-456!");
    await user.type(screen.getByLabelText("Confirm password"), "New-Password-456!");
    await user.click(screen.getByRole("button", { name: "Reset password" }));

    expect(await screen.findByText("Link expired")).toBeInTheDocument();
  });
});
