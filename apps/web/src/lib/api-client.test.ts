import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "./api-client";

function mockFetchOnce(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  const fullResponse = {
    ok: true,
    status: 200,
    json: async () => ({}),
    text: async () => "",
    ...response,
  } as Response;
  vi.spyOn(global, "fetch").mockResolvedValueOnce(fullResponse);
  return fullResponse;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
});

describe("apiFetch", () => {
  it("sets Content-Type: application/json for a plain JSON body", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    mockFetchOnce({});

    await apiFetch("/contacts", { method: "POST", body: JSON.stringify({ email: "a@b.com" }) });

    const [, init] = vi.mocked(fetch).mock.calls[0] ?? [];
    const headers = init?.headers as Record<string, string>;
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("omits Content-Type for a FormData body so the browser sets the multipart boundary", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    mockFetchOnce({});

    const formData = new FormData();
    formData.append("file", new Blob(["a,b\n1,2"]), "contacts.csv");
    formData.append("column_mapping", JSON.stringify({ a: "email" }));

    await apiFetch("/contacts/imports", { method: "POST", body: formData });

    const [, init] = vi.mocked(fetch).mock.calls[0] ?? [];
    const headers = init?.headers as Record<string, string> | undefined;
    expect(headers?.["Content-Type"]).toBeUndefined();
  });
});
