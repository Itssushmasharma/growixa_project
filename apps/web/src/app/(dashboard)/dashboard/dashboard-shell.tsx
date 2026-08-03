"use client";

import { usePathname } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import layoutStyles from "./layout.module.css";
import { LogoutButton } from "./logout-button";
import { PageTitle } from "./page-title";
import { Sidebar } from "./sidebar";
import topbarStyles from "./topbar.module.css";

const MOBILE_QUERY = "(max-width: 768px)";

export function DashboardShell({
  permissions,
  fullName,
  children,
}: {
  permissions: string[];
  fullName: string;
  children: ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const pathname = usePathname();

  // Desktop defaults to the sidebar open (matches the pre-collapse behavior); mobile
  // defaults to closed since there it's an overlay drawer, not a reflowed column. Also
  // closes the drawer after navigating on mobile — it would otherwise cover the new
  // page until manually dismissed.
  useEffect(() => {
    if (window.matchMedia(MOBILE_QUERY).matches) {
      setSidebarOpen(false);
    }
  }, [pathname]);

  return (
    <div className={layoutStyles.shell}>
      <Sidebar permissions={permissions} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className={layoutStyles.main}>
        <header className={topbarStyles.topbar}>
          <div className={topbarStyles.titleArea}>
            <button
              type="button"
              className={topbarStyles.menuButton}
              aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen((open) => !open)}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path
                  d="M2.5 5.5h15M2.5 10h15M2.5 14.5h15"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                />
              </svg>
            </button>
            <PageTitle />
          </div>
          <div className={topbarStyles.userArea}>
            <span className={topbarStyles.userName}>{fullName}</span>
            <LogoutButton />
          </div>
        </header>
        <div className={layoutStyles.content}>{children}</div>
      </div>
    </div>
  );
}
