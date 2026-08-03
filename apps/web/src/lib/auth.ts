import { cookies } from "next/headers";

import { getServerApiUrl } from "./env";

export interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

/**
 * Server-only: resolves the current session by forwarding the incoming request's cookies
 * to the API's GET /auth/me. The access token is HttpOnly, so this is the only way a
 * Server Component can determine auth state — client-side JS can never read it directly.
 */
export async function getCurrentUser(): Promise<CurrentUser | null> {
  try {
    const cookieStore = await cookies();
    const cookieHeader = cookieStore
      .getAll()
      .map((cookie) => `${cookie.name}=${cookie.value}`)
      .join("; ");

    const response = await fetch(`${getServerApiUrl()}/auth/me`, {
      headers: { Cookie: cookieHeader },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as CurrentUser;
  } catch {
    return null;
  }
}
