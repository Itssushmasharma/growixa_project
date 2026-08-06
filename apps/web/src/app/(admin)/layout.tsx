import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { ToastProvider } from "@/components/toast/toast-context";
import { getCurrentUser } from "@/lib/auth";

import { AdminHeader } from "./admin-header";
import styles from "./admin-header.module.css";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  if (!user.permissions.includes("admin.access")) {
    redirect("/dashboard");
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
