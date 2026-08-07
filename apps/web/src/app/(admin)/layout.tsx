"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { ToastProvider } from "@/components/toast/toast-context";
import { apiFetch } from "@/lib/api-client";
import type { AuthUser } from "@/lib/client-auth";

import { AdminHeader } from "./admin-header";
import styles from "./admin-header.module.css";

export default function AdminLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<AuthUser>("/auth/me")
      .then((data) => {
        if (!data.permissions.includes("admin.access")) {
          router.replace("/dashboard");
          return;
        }
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        router.replace("/login");
      });
  }, [router]);

  if (loading || !user) {
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
    <ToastProvider>
      <div className={styles.shell}>
        <AdminHeader fullName={user.full_name} />
        <main className={styles.content}>{children}</main>
      </div>
    </ToastProvider>
  );
}
