export function getApiUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000";
    }
    // In production / VPS: use relative /api path for same-origin HTTPS proxying via Caddy
    return "/api";
  }
  return "http://localhost:8000";
}

export function getServerApiUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://api:8000";
}
