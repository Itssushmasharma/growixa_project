import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api-client";

import { ProvidersPage } from "./providers-page";

const mockShowToast = vi.fn();
vi.mock("@/components/toast/toast-context", () => ({
  useToast: () => ({ showToast: mockShowToast }),
}));

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

const mockedApiFetch = vi.mocked(apiFetch);

const mockAIConfig = {
  provider: "OPENAI",
  base_url: null,
  default_model: "gpt-4o-mini",
  is_active: true,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
};

const mockEmailConfig = {
  provider: "POSTMARK",
  smtp_host: "smtp.postmarkapp.com",
  smtp_port: 587,
  smtp_username: "postmark-token",
  from_email: "marketing@growixa.local",
  from_name: "Growixa",
  is_active: true,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
};

const mockValidationConfig = {
  provider: "CLEAROUT",
  is_active: true,
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-01T00:00:00Z",
};

beforeEach(() => {
  mockedApiFetch.mockReset();
  mockShowToast.mockReset();
});

describe("ProvidersPage", () => {
  it("renders all 3 provider cards with operational status", async () => {
    mockedApiFetch.mockImplementation(async (url) => {
      if (url === "/platform/ai-config") return mockAIConfig;
      if (url === "/platform/email-config") return mockEmailConfig;
      if (url === "/platform/email-validation-config") return mockValidationConfig;
      return null;
    });

    render(<ProvidersPage />);

    expect(await screen.findByText("AI & LLM Engine")).toBeInTheDocument();
    expect(screen.getByText("Outbound Email Relay")).toBeInTheDocument();
    expect(screen.getByText("Email Validation")).toBeInTheDocument();

    expect(screen.getByText("3 / 3")).toBeInTheDocument();
    expect(screen.getByText("Operational")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o-mini")).toBeInTheDocument();
    expect(screen.getByText("smtp.postmarkapp.com:587")).toBeInTheDocument();
  });

  it("tests AI provider connection on click", async () => {
    mockedApiFetch.mockImplementation(async (url, init) => {
      if (url === "/platform/ai-config") return mockAIConfig;
      if (url === "/platform/email-config") return mockEmailConfig;
      if (url === "/platform/email-validation-config") return mockValidationConfig;
      if (url === "/platform/ai-config/test" && init?.method === "POST") return undefined;
      return null;
    });

    render(<ProvidersPage />);

    expect(await screen.findByText("AI & LLM Engine")).toBeInTheDocument();

    const testButtons = screen.getAllByRole("button", { name: "Test Connection" });
    fireEvent.click(testButtons[0]!);

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/platform/ai-config/test",
        expect.objectContaining({ method: "POST" }),
      );
    });

    expect(mockShowToast).toHaveBeenCalledWith("success", "AI connection verified successfully");
    expect(await screen.findByText(/AI API connection verified/)).toBeInTheDocument();
  });

  it("tests Email SMTP connection on click", async () => {
    mockedApiFetch.mockImplementation(async (url, init) => {
      if (url === "/platform/ai-config") return mockAIConfig;
      if (url === "/platform/email-config") return mockEmailConfig;
      if (url === "/platform/email-validation-config") return mockValidationConfig;
      if (url === "/platform/email-config/test" && init?.method === "POST") return undefined;
      return null;
    });

    render(<ProvidersPage />);

    expect(await screen.findByText("Outbound Email Relay")).toBeInTheDocument();

    const testButtons = screen.getAllByRole("button", { name: "Test Connection" });
    fireEvent.click(testButtons[1]!);

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/platform/email-config/test",
        expect.objectContaining({ method: "POST" }),
      );
    });

    expect(mockShowToast).toHaveBeenCalledWith(
      "success",
      "Email SMTP relay connection verified successfully",
    );
  });

  it("tests Validation provider connection on click", async () => {
    mockedApiFetch.mockImplementation(async (url, init) => {
      if (url === "/platform/ai-config") return mockAIConfig;
      if (url === "/platform/email-config") return mockEmailConfig;
      if (url === "/platform/email-validation-config") return mockValidationConfig;
      if (url === "/platform/email-validation-config/test" && init?.method === "POST")
        return undefined;
      return null;
    });

    render(<ProvidersPage />);

    expect(await screen.findByText("Email Validation")).toBeInTheDocument();

    const testButtons = screen.getAllByRole("button", { name: "Test Connection" });
    fireEvent.click(testButtons[2]!);

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/platform/email-validation-config/test",
        expect.objectContaining({ method: "POST" }),
      );
    });

    expect(mockShowToast).toHaveBeenCalledWith(
      "success",
      "Email validation service connection verified",
    );
  });

  it("tests all active connections sequentially on 'Test All Active' click", async () => {
    mockedApiFetch.mockImplementation(async (url, init) => {
      if (url === "/platform/ai-config") return mockAIConfig;
      if (url === "/platform/email-config") return mockEmailConfig;
      if (url === "/platform/email-validation-config") return mockValidationConfig;
      if (init?.method === "POST") return undefined;
      return null;
    });

    render(<ProvidersPage />);

    expect(await screen.findByText("3 / 3")).toBeInTheDocument();

    const testAllBtn = screen.getByRole("button", { name: "⚡ Test All Active" });
    fireEvent.click(testAllBtn);

    await waitFor(() => {
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/ai-config/test", expect.anything());
      expect(mockedApiFetch).toHaveBeenCalledWith("/platform/email-config/test", expect.anything());
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/platform/email-validation-config/test",
        expect.anything(),
      );
    });
  });

  it("renders unconfigured placeholders when providers are not set", async () => {
    mockedApiFetch.mockResolvedValue(null);

    render(<ProvidersPage />);

    expect(await screen.findByText("0 / 3")).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByText("No platform AI provider configured.")).toBeInTheDocument();
    expect(screen.getByText("No platform SMTP relay configured.")).toBeInTheDocument();
    expect(screen.getByText("No validation provider configured.")).toBeInTheDocument();
  });
});
