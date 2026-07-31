"use client";

import { usePathname } from "next/navigation";

import styles from "./topbar.module.css";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/contacts": "Contacts",
  "/dashboard/contacts/lists": "Lists",
  "/dashboard/contacts/segments": "Segments",
  "/dashboard/company-settings": "Company Settings",
  "/dashboard/team": "Team",
};

export function PageTitle() {
  const pathname = usePathname();
  return <h1 className={styles.title}>{PAGE_TITLES[pathname] ?? "Growixa"}</h1>;
}
