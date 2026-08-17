import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import LoginPage from "./page";

const mockPush = vi.fn();
const mockRefresh = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, refresh: mockRefresh }),
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
});

describe("LoginPage", () => {
  it("links to the forgot-password flow", () => {
    renderLoginPage();

    expect(screen.getByRole("link", { name: "Forgot password?" })).toHaveAttribute(
      "href",
      "/forgot-password",
    );
  });
});
