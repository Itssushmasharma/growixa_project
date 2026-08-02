import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { getCurrentUser } from "@/lib/auth";

import { DashboardShell } from "./dashboard-shell";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <DashboardShell permissions={user.permissions} fullName={user.full_name}>
      {children}
    </DashboardShell>
  );
}
