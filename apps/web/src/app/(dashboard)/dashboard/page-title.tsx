"use client";

import { usePathname } from "next/navigation";

import styles from "./topbar.module.css";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/contacts": "Contacts",
  "/dashboard/contacts/lists": "Lists",
  "/dashboard/contacts/segments": "Segments",
  "/dashboard/contacts/imports": "Imports",
  "/dashboard/contacts/suppression": "Suppression",
  "/dashboard/company-settings": "Company Settings",
  "/dashboard/team": "Team",
  "/dashboard/audit": "Audit Log",
  "/dashboard/integrations": "Integrations",
  "/dashboard/templates": "Email Templates",
};

export function PageTitle() {
  const pathname = usePathname();
  let title = PAGE_TITLES[pathname];
  if (!title && pathname === "/dashboard/templates/new") {
    title = "New Template";
  } else if (!title && /^\/dashboard\/templates\/[^/]+\/edit$/.test(pathname)) {
    title = "Edit Template";
  }
  return <h1 className={styles.title}>{title ?? "Growixa"}</h1>;
}
