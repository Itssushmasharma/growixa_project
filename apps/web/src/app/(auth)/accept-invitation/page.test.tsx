import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import AcceptInvitationPage from "./page";

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

function renderAcceptInvitationPage() {
  return render(
    <ToastProvider>
      <AcceptInvitationPage />
    </ToastProvider>,
  );
}

async function fillForm(user: ReturnType<typeof userEvent.setup>, password: string) {
  await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
  await user.type(screen.getByLabelText("Password"), password);
  await user.type(screen.getByLabelText("Confirm password"), password);
}

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockSearchParams = new URLSearchParams();
});

describe("AcceptInvitationPage", () => {
  it("shows the unavailable state when no token is present", async () => {
    renderAcceptInvitationPage();

    expect(await screen.findByText("Invitation unavailable")).toBeInTheDocument();
    expect(mockedApiFetch).not.toHaveBeenCalled();
  });

  it("creates the account from a valid invitation token", async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams("token=raw-invite-token");
    mockedApiFetch.mockResolvedValueOnce(undefined);

    renderAcceptInvitationPage();
    await fillForm(user, "New-Password-456!");
    await user.click(screen.getByRole("button", { name: "Accept invitation" }));

    expect(await screen.findByText("Account ready")).toBeInTheDocument();
    expect(mockedApiFetch).toHaveBeenCalledWith("/users/invitations/accept", {
      method: "POST",
      body: JSON.stringify({
        token: "raw-invite-token",
        password: "New-Password-456!",
        full_name: "Ada Lovelace",
      }),
    });
  });

  it("shows a toast and does not submit when passwords do not match", async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams("token=raw-invite-token");

    renderAcceptInvitationPage();
    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.type(screen.getByLabelText("Password"), "New-Password-456!");
    await user.type(screen.getByLabelText("Confirm password"), "Different-Password-456!");
    await user.click(screen.getByRole("button", { name: "Accept invitation" }));

    await waitFor(() => expect(screen.getByText("Passwords do not match.")).toBeInTheDocument());
    expect(mockedApiFetch).not.toHaveBeenCalled();
  });

  it("shows the unavailable state when the API rejects the token", async () => {
    const user = userEvent.setup();
    mockSearchParams = new URLSearchParams("token=bad-token");
    mockedApiFetch.mockRejectedValueOnce(new Error("invalid"));

    renderAcceptInvitationPage();
    await fillForm(user, "New-Password-456!");
    await user.click(screen.getByRole("button", { name: "Accept invitation" }));

    expect(await screen.findByText("Invitation unavailable")).toBeInTheDocument();
  });
});
