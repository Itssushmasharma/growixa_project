import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

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
  it("renders Google OAuth button and links", () => {
    renderLoginPage();

    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
    expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute(
      "href",
      "/register",
    );
    expect(screen.getByRole("link", { name: "Continue with Google" })).toHaveAttribute(
      "href",
      "/api/auth/oauth/google",
    );
  });

  it("displays toast error when oauth_error parameter is present", () => {
    mockSearchParams = new URLSearchParams("oauth_error=OAuthStateInvalidError");
    renderLoginPage();

    expect(
      screen.getByText("Google sign-in was interrupted or failed. Please try again."),
    ).toBeInTheDocument();
  });
});
