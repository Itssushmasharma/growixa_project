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

export function getWsUrl(): string {
  const apiUrl = getApiUrl();
  if (apiUrl.startsWith("http://")) {
    return apiUrl.replace("http://", "ws://");
  } else if (apiUrl.startsWith("https://")) {
    return apiUrl.replace("https://", "wss://");
  } else if (apiUrl.startsWith("/")) {
    // Relative path, construct absolute WS url
    if (typeof window !== "undefined") {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return `${protocol}//${window.location.host}${apiUrl}`;
    }
  }
  return "ws://localhost:8000";
}

export function getServerApiUrl(): string {
  return process.env.API_INTERNAL_URL ?? "http://api:8000";
}
