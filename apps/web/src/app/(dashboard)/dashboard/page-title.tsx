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
  "/dashboard/campaigns": "Campaigns",
  "/dashboard/social": "Social",
  "/dashboard/social/calendar": "Content Calendar",
  "/dashboard/ai": "AI Assistant",
};

export function PageTitle() {
  const pathname = usePathname();
  let title = PAGE_TITLES[pathname];
  if (!title && pathname === "/dashboard/templates/new") {
    title = "New Template";
  } else if (!title && /^\/dashboard\/templates\/[^/]+\/edit$/.test(pathname)) {
    title = "Edit Template";
  } else if (!title && pathname === "/dashboard/campaigns/new") {
    title = "New Campaign";
  } else if (!title && /^\/dashboard\/campaigns\/[^/]+$/.test(pathname)) {
    title = "Campaign";
  } else if (!title && pathname === "/dashboard/social/new") {
    title = "New Post";
  } else if (!title && /^\/dashboard\/social\/[^/]+$/.test(pathname)) {
    title = "Post";
  }
  return <h1 className={styles.title}>{title ?? "Growixa"}</h1>;
}
