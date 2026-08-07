import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { getCurrentPlatformAdmin } from "@/lib/auth";

import { PlatformShell } from "./platform-shell";

export default async function PlatformProtectedLayout({ children }: { children: ReactNode }) {
  const admin = await getCurrentPlatformAdmin();
  if (!admin) {
    redirect("/platform/login");
  }

  return (
    <PlatformShell fullName={admin.full_name} permissions={admin.permissions}>
      {children}
    </PlatformShell>
  );
}
