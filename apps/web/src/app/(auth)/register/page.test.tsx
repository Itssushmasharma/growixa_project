import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import RegisterPage from "./page";

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

function renderRegisterPage() {
  return render(
    <ToastProvider>
      <RegisterPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockSearchParams = new URLSearchParams();
});

describe("RegisterPage", () => {
  it("renders Google OAuth button, showcase, and form inputs", () => {
    renderRegisterPage();

    expect(screen.getByRole("link", { name: "Continue with Google" })).toHaveAttribute(
      "href",
      "http://localhost:8000/auth/oauth/iitd?kc_idp_hint=google",
    );
    expect(screen.getByText("AI-Powered Growth")).toBeInTheDocument();
    expect(screen.getByLabelText("Company name")).toBeInTheDocument();
    expect(screen.getByLabelText("Your name")).toBeInTheDocument();
    expect(screen.getByLabelText("Work email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("submits the form and shows the check-your-email confirmation", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce({
      account_id: "acc-1",
      user_id: "user-1",
      email: "ada@acme.example",
      message: "ok",
      token: "raw-token",
    });

    renderRegisterPage();

    await user.type(screen.getByLabelText("Company name"), "Acme Inc");
    await user.type(screen.getByLabelText("Your name"), "Ada Owner");
    await user.type(screen.getByLabelText("Work email"), "ada@acme.example");
    await user.type(screen.getByLabelText("Password"), "Test-Password-123!");
    await user.click(screen.getByRole("button", { name: /Create your account/ }));

    expect(await screen.findByText("Check your email")).toBeInTheDocument();
    expect(screen.getByText("ada@acme.example")).toBeInTheDocument();

    expect(mockedApiFetch).toHaveBeenCalledWith(
      "/accounts/register",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          account_name: "Acme Inc",
          full_name: "Ada Owner",
          email: "ada@acme.example",
          password: "Test-Password-123!",
          plan_slug: "free",
        }),
      }),
    );
  });

  it("shows a toast on duplicate-email (409) instead of the success state", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockRejectedValueOnce(new ApiError(409, "already exists"));

    renderRegisterPage();

    await user.type(screen.getByLabelText("Company name"), "Acme Inc");
    await user.type(screen.getByLabelText("Your name"), "Ada Owner");
    await user.type(screen.getByLabelText("Work email"), "ada@acme.example");
    await user.type(screen.getByLabelText("Password"), "Test-Password-123!");
    await user.click(screen.getByRole("button", { name: /Create your account/ }));

    await waitFor(() =>
      expect(screen.getByText("An account with this email already exists.")).toBeInTheDocument(),
    );
    expect(screen.queryByText("Check your email")).not.toBeInTheDocument();
  });
});
