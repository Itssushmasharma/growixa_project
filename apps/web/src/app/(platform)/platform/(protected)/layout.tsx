"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import { PlatformShell } from "./platform-shell";

interface PlatformAdmin {
  id: string;
  email: string;
  full_name: string;
  role: string;
  permissions: string[];
}

export default function PlatformProtectedLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [admin, setAdmin] = useState<PlatformAdmin | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<PlatformAdmin>("/platform/auth/me")
      .then((data) => {
        setAdmin(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        router.replace("/platform/login");
      });
  }, [router]);

  if (loading || !admin) {
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

  return (
    <PlatformShell fullName={admin.full_name} permissions={admin.permissions}>
      {children}
    </PlatformShell>
  );
}
