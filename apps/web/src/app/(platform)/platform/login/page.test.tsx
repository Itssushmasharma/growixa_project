import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import PlatformLoginPage from "./page";

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

function renderPage() {
  return render(
    <ToastProvider>
      <PlatformLoginPage />
    </ToastProvider>,
  );
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockPush.mockReset();
  mockRefresh.mockReset();
});

describe("PlatformLoginPage", () => {
  it("logs in and redirects to the accounts list", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockResolvedValueOnce({
      id: "admin-1",
      email: "owner@iitdeveloper.com",
      full_name: "Owner Admin",
      role: "platform.owner",
    });

    renderPage();

    await user.type(screen.getByLabelText("Email"), "owner@iitdeveloper.com");
    await user.type(screen.getByLabelText("Password"), "Platform-Owner-1!");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(mockedApiFetch).toHaveBeenCalledWith("/platform/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: "owner@iitdeveloper.com", password: "Platform-Owner-1!" }),
    });
    expect(mockPush).toHaveBeenCalledWith("/platform/accounts");
  });

  it("shows an error toast on invalid credentials", async () => {
    const user = userEvent.setup();
    mockedApiFetch.mockRejectedValueOnce(new ApiError(401, "Invalid email or password"));

    renderPage();

    await user.type(screen.getByLabelText("Email"), "owner@iitdeveloper.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });
});
