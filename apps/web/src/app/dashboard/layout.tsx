import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { getCurrentUser } from "@/lib/auth";

import layoutStyles from "./layout.module.css";
import { LogoutButton } from "./logout-button";
import { PageTitle } from "./page-title";
import { Sidebar } from "./sidebar";
import topbarStyles from "./topbar.module.css";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <div className={layoutStyles.shell}>
      <Sidebar permissions={user.permissions} />
      <div className={layoutStyles.main}>
        <header className={topbarStyles.topbar}>
          <PageTitle />
          <div className={topbarStyles.userArea}>
            <span className={topbarStyles.userName}>{user.full_name}</span>
            <LogoutButton />
          </div>
        </header>
        <div className={layoutStyles.content}>{children}</div>
      </div>
    </div>
  );
}
