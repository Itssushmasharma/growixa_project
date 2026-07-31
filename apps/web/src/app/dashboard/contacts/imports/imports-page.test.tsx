import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";

import type { ContactImport, ContactImportRow, MeResponse } from "../types";
import { ImportsPage } from "./imports-page";

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, apiFetch: vi.fn() };
});

const mockedApiFetch = vi.mocked(apiFetch);

function renderImportsPage() {
  return render(
    <ToastProvider>
      <ImportsPage />
    </ToastProvider>,
  );
}

function meWithPermissions(permissions: string[]): MeResponse {
  return { id: "user-1", email: "admin@example.com", full_name: "Admin User", permissions };
}

const PAST_IMPORT: ContactImport = {
  id: "import-1",
  filename: "contacts.csv",
  status: "COMPLETED",
  column_mapping: { Email: "email" },
  total_rows: 3,
  imported_count: 2,
  updated_count: 1,
  skipped_count: 0,
  error_count: 0,
  created_at: "2026-07-01T00:00:00Z",
  completed_at: "2026-07-01T00:00:05Z",
};

const IMPORT_ROWS: ContactImportRow[] = [
  {
    id: "row-1",
    row_number: 1,
    email: "alice@example.com",
    status: "IMPORTED",
    error_message: null,
  },
];

function makeCsvFile(content: string): File {
  return new File([content], "contacts.csv", { type: "text/csv" });
}

beforeEach(() => {
  mockedApiFetch.mockReset();
});

describe("ImportsPage", () => {
  it("renders import history", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/imports") return Promise.resolve([PAST_IMPORT]);
      if (path === "/contacts/custom-fields") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderImportsPage();

    expect(await screen.findByText("contacts.csv")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText(/Imported 2, updated 1, skipped 0, errors 0/)).toBeInTheDocument();
  });

  it("shows an access-denied message for a user without contacts.view", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions([]));
      if (path === "/contacts/imports") return Promise.resolve([]);
      if (path === "/contacts/custom-fields") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderImportsPage();

    expect(await screen.findByText("You don't have access to view imports.")).toBeInTheDocument();
  });

  it("hides the upload form for a view-only user", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(meWithPermissions(["contacts.view"]));
      if (path === "/contacts/imports") return Promise.resolve([PAST_IMPORT]);
      if (path === "/contacts/custom-fields") return Promise.resolve([]);
      throw new Error(`unexpected path: ${path}`);
    });

    renderImportsPage();

    await screen.findByText("contacts.csv");
    expect(screen.queryByLabelText("CSV file")).not.toBeInTheDocument();
  });

  it("parses CSV headers, maps columns, and uploads via multipart form data", async () => {
    const created: ContactImport = { ...PAST_IMPORT, id: "import-2" };
    mockedApiFetch.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/imports" && (!init || init.method === undefined)) {
        return Promise.resolve([]);
      }
      if (path === "/contacts/custom-fields") return Promise.resolve([]);
      if (path === "/contacts/imports" && init?.method === "POST") {
        return Promise.resolve(created);
      }
      throw new Error(`unexpected call: ${path}`);
    });

    const user = userEvent.setup();
    renderImportsPage();

    await screen.findByText("No imports yet.");

    const file = makeCsvFile("Email,First Name\nalice@example.com,Alice\n");
    const fileInput = screen.getByLabelText("CSV file");
    await user.upload(fileInput, file);

    await screen.findByLabelText("Map column Email");
    expect(screen.getByLabelText("Map column Email")).toHaveValue("email");

    await user.click(screen.getByRole("button", { name: "Import contacts" }));

    await waitFor(() => {
      const [, postCall] =
        mockedApiFetch.mock.calls.find(
          ([path, callInit]) => path === "/contacts/imports" && callInit?.method === "POST",
        ) ?? [];
      expect(postCall).toBeDefined();
      expect(postCall?.body).toBeInstanceOf(FormData);
    });

    await waitFor(() => expect(screen.getByText(/\(of 3 rows\)/)).toBeInTheDocument());
  });

  it("views an import's row detail", async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve(meWithPermissions(["contacts.view", "contacts.manage"]));
      }
      if (path === "/contacts/imports") return Promise.resolve([PAST_IMPORT]);
      if (path === "/contacts/custom-fields") return Promise.resolve([]);
      if (path === "/contacts/imports/import-1/rows") return Promise.resolve(IMPORT_ROWS);
      throw new Error(`unexpected path: ${path}`);
    });

    const user = userEvent.setup();
    renderImportsPage();

    await screen.findByText("contacts.csv");
    await user.click(screen.getByRole("button", { name: "View rows" }));

    await waitFor(() =>
      expect(screen.getByText(/Row 1: alice@example.com — IMPORTED/)).toBeInTheDocument(),
    );
  });
});
