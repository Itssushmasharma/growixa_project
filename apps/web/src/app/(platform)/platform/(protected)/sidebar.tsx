"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import styles from "./sidebar.module.css";

interface NavItem {
  label: string;
  href: string;
  requiresPermission: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Accounts", href: "/platform/accounts", requiresPermission: "platform.accounts.manage" },
  { label: "Usage", href: "/platform/usage", requiresPermission: "platform.usage.manage" },
  { label: "Campaigns", href: "/platform/campaigns", requiresPermission: "platform.usage.manage" },
];

export function Sidebar({ permissions }: { permissions: string[] }) {
  const pathname = usePathname();
  const items = NAV_ITEMS.filter((item) => permissions.includes(item.requiresPermission));

  return (
    <nav className={styles.sidebar}>
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? styles.navItemActive : styles.navItem}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
