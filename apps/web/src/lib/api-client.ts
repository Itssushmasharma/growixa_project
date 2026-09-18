import { getApiUrl } from "./env";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Paths whose own 401 is a meaningful answer (bad credentials, no/invalid refresh token),
// never a signal to attempt a refresh-and-retry — retrying these would either recurse
// forever (refresh calling itself) or mask a real authentication failure as a transient one.
const NO_REFRESH_RETRY_PATHS = [
  "/auth/login",
  "/auth/password-reset/request",
  "/auth/password-reset/complete",
  "/auth/refresh",
  "/auth/logout",
  "/platform/auth/login",
  "/platform/auth/refresh",
  "/platform/auth/logout",
  "/platform/auth/me",
];

// Access tokens are short-lived (15 min, DEC-GRX-014) and nothing else on the frontend
// proactively renews them, so any request can hit a stale cookie mid-session. Shared across
// calls so concurrent 401s all await the same refresh instead of each firing their own —
// GRX-AUTH-003's refresh-token rotation treats a second use of the same refresh token as
// reuse and revokes the whole session, so a naive per-call refresh would log the user out.
let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${getApiUrl()}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then((response) => response.ok)
      .catch(() => false)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

/**
 * Fetch wrapper for the Growixa API. Sends cookies (auth is HttpOnly-cookie-based per
 * DEC-GRX-014) and throws ApiError on a non-2xx response instead of leaving callers to
 * check `response.ok` themselves. On a 401 from an already-authenticated route, silently
 * attempts one token refresh and retries the request once before giving up — access tokens
 * expire well within a normal editing session, and nothing else renews them proactively.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // A FormData body (e.g. CSV import upload) needs the browser to set its own
  // multipart/form-data Content-Type with the correct boundary — setting it manually
  // to application/json here would break the upload.
  const isFormData = init?.body instanceof FormData;

  const doFetch = () =>
    fetch(`${getApiUrl()}${path}`, {
      ...init,
      credentials: "include",
      headers: isFormData
        ? init?.headers
        : {
            "Content-Type": "application/json",
            ...init?.headers,
          },
    });

  let response = await doFetch();

  if (response.status === 401 && !NO_REFRESH_RETRY_PATHS.includes(path)) {
    const refreshed = await refreshSession();
    if (refreshed) {
      response = await doFetch();
    }
  }

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function apiFetchBlob(path: string, init?: RequestInit): Promise<Blob> {
  const isFormData = init?.body instanceof FormData;

  const doFetch = () =>
    fetch(`${getApiUrl()}${path}`, {
      ...init,
      credentials: "include",
      headers: isFormData
        ? init?.headers
        : {
            "Content-Type": "application/json",
            ...init?.headers,
          },
    });

  let response = await doFetch();

  if (response.status === 401 && !NO_REFRESH_RETRY_PATHS.includes(path)) {
    const refreshed = await refreshSession();
    if (refreshed) {
      response = await doFetch();
    }
  }

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(response.status, body || response.statusText);
  }

  return await response.blob();
}
