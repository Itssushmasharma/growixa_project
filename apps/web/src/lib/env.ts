export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    // In the browser: use relative /api path for same-origin HTTPS proxying unless explicitly overridden
    return process.env.NEXT_PUBLIC_API_URL ?? "/api";
  }
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

export function getServerApiUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://api:8000";
}
