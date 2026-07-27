export function getApiUrl(): string {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return url;
}

/**
 * Server-only base URL for the API, for fetches made from Node (Server Components,
 * Route Handlers) rather than the browser. Inside Compose, the `web` container's own
 * "localhost" is itself, not the `api` container — NEXT_PUBLIC_API_URL is the
 * browser-facing, host-published address and cannot be reused for container-to-container
 * calls. Falls back to NEXT_PUBLIC_API_URL when API_INTERNAL_URL isn't set, which is
 * correct for running outside Docker (e.g. `next dev`), where both processes really do
 * share one "localhost".
 */
export function getServerApiUrl(): string {
  return process.env.API_INTERNAL_URL ?? getApiUrl();
}
