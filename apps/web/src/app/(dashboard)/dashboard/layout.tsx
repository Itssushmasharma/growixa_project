"use client";

import type { ReactNode } from "react";

import { ClientAuthGuard } from "@/lib/client-auth";

import { DashboardShell } from "./dashboard-shell";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <ClientAuthGuard
      renderShell={(user, inner) => (
        <DashboardShell
          permissions={user.permissions}
          fullName={user.full_name}
          companyName={(user as { company_name?: string }).company_name}
        >
          {inner}
        </DashboardShell>
      )}
    >
      {children}
    </ClientAuthGuard>
  );
}
