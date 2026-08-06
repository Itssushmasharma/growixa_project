import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, ApiError } from "./api-client";

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

  it("silently refreshes and retries once after a 401", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    const fetchSpy = vi.spyOn(global, "fetch");
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => "Not authenticated",
    } as Response);
    fetchSpy.mockResolvedValueOnce({ ok: true, status: 200 } as Response); // /auth/refresh
    fetchSpy.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "1" }),
    } as Response);

    const result = await apiFetch("/campaigns/1");

    expect(result).toEqual({ id: "1" });
    expect(fetchSpy).toHaveBeenCalledTimes(3);
    expect(fetchSpy.mock.calls[1]?.[0]).toBe("http://localhost:8000/auth/refresh");
  });

  it("throws the original 401 when the refresh attempt also fails", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    const fetchSpy = vi.spyOn(global, "fetch");
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => "Not authenticated",
    } as Response);
    fetchSpy.mockResolvedValueOnce({ ok: false, status: 401 } as Response); // /auth/refresh

    await expect(apiFetch("/campaigns/1")).rejects.toMatchObject(
      new ApiError(401, "Not authenticated"),
    );
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it("does not attempt a refresh for /auth/login's own 401", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    const fetchSpy = vi.spyOn(global, "fetch");
    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => "Invalid email or password",
    } as Response);

    await expect(
      apiFetch("/auth/login", { method: "POST", body: JSON.stringify({}) }),
    ).rejects.toMatchObject(new ApiError(401, "Invalid email or password"));
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it("shares one in-flight refresh across concurrent 401s", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
    const fetchSpy = vi.spyOn(global, "fetch");
    fetchSpy.mockResolvedValueOnce({ ok: false, status: 401, text: async () => "" } as Response);
    fetchSpy.mockResolvedValueOnce({ ok: false, status: 401, text: async () => "" } as Response);
    fetchSpy.mockResolvedValueOnce({ ok: true, status: 200 } as Response); // shared /auth/refresh
    fetchSpy.mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({}) } as Response);
    fetchSpy.mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({}) } as Response);

    await Promise.all([apiFetch("/campaigns/1"), apiFetch("/campaigns/2")]);

    const refreshCalls = fetchSpy.mock.calls.filter(
      (call) => call[0] === "http://localhost:8000/auth/refresh",
    );
    expect(refreshCalls).toHaveLength(1);
  });
});
