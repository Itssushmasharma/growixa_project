import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import LoginPage from "./page";

const mockPush = vi.fn();
const mockRefresh = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, refresh: mockRefresh }),
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

function renderLoginPage() {
  return render(
    <ToastProvider>
      <LoginPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockPush.mockReset();
  mockRefresh.mockReset();
  mockSearchParams = new URLSearchParams();
});

describe("LoginPage", () => {
  it("renders Google OAuth button, showcase, and navigation links", () => {
    renderLoginPage();

    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
    expect(screen.getByRole("link", { name: "Continue with Google" })).toHaveAttribute(
      "href",
      "http://localhost:8000/auth/oauth/google",
    );
    expect(screen.getByText("AI-Powered Growth")).toBeInTheDocument();
    expect(screen.getByText("4.82x")).toBeInTheDocument();
    expect(screen.getByText("99.4%")).toBeInTheDocument();
  });

  it("submits the login form and redirects safely", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce({ status: "ok" });
    mockSearchParams = new URLSearchParams("next=/dashboard/campaigns");

    renderLoginPage();

    await user.type(screen.getByLabelText("Work email"), "alex@growixa.example");
    await user.type(screen.getByLabelText("Password"), "Secret123!");
    await user.click(screen.getByRole("button", { name: /Login to Growixa/ }));

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/dashboard/campaigns");
    });
  });

  it("displays toast error on invalid credentials (401)", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockRejectedValueOnce(new ApiError(401, "Unauthorized"));

    renderLoginPage();

    await user.type(screen.getByLabelText("Work email"), "alex@growixa.example");
    await user.type(screen.getByLabelText("Password"), "WrongPassword");
    await user.click(screen.getByRole("button", { name: /Login to Growixa/ }));

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
  });

  it("displays toast error when oauth_error parameter is present", () => {
    mockSearchParams = new URLSearchParams("oauth_error=OAuthStateInvalidError");
    renderLoginPage();

    expect(
      screen.getByText("Google sign-in was interrupted or failed. Please try again."),
    ).toBeInTheDocument();
  });
});
