"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  permissions: string[];
}

/**
 * Client-side auth guard. In cross-origin deployments (Netlify frontend → Render API)
 * HttpOnly cookies live on the API domain, so the Next.js server (on the Netlify domain)
 * never sees them in `cookies()`. This component performs a client-side `/auth/me` fetch
 * with `credentials: "include"` — the browser attaches the API-domain cookie correctly.
 */
export function useClientAuth(): { user: AuthUser | null; loading: boolean } {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<AuthUser>("/auth/me")
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        router.replace("/login");
      });
  }, [router]);

  return { user, loading };
}

export function ClientAuthGuard({
  children,
  renderShell,
}: {
  children: ReactNode;
  renderShell: (user: AuthUser, children: ReactNode) => ReactNode;
}) {
  const { user, loading } = useClientAuth();

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          background: "#0a0e1a",
          color: "#8b95b0",
          fontFamily: "Inter, sans-serif",
          fontSize: "14px",
        }}
      >
        Loading…
      </div>
    );
  }

  if (!user) {
    return null; // redirect handled in useClientAuth
  }

  return <>{renderShell(user, children)}</>;
}
