"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import styles from "./sidebar.module.css";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  requiresPermission: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Accounts",
    href: "/platform/accounts",
    icon: "🏢",
    requiresPermission: "platform.accounts.manage",
  },
  {
    label: "Usage",
    href: "/platform/usage",
    icon: "📈",
    requiresPermission: "platform.usage.manage",
  },
  {
    label: "Campaigns",
    href: "/platform/campaigns",
    icon: "📧",
    requiresPermission: "platform.usage.manage",
  },
  {
    label: "AI & LLM Config",
    href: "/platform/ai-config",
    icon: "⚙️",
    requiresPermission: "platform.ai.manage",
  },
  {
    label: "Email Provider",
    href: "/platform/email-config",
    icon: "✉️",
    requiresPermission: "platform.email.manage",
  },
  {
    label: "Subscriptions",
    href: "/platform/subscriptions",
    icon: "💳",
    requiresPermission: "platform.billing.manage",
  },
  {
    label: "Coupons",
    href: "/platform/coupons",
    icon: "🏷️",
    requiresPermission: "platform.billing.manage",
  },
];

export function Sidebar({ permissions }: { permissions: string[] }) {
  const pathname = usePathname();
  const items = NAV_ITEMS.filter((item) => permissions.includes(item.requiresPermission));

  return (
    <nav className={styles.sidebar}>
      <div className={styles.brand}>
        <Image src={iconMark} alt="" width={28} height={28} />
        <div>
          <div className={styles.brandName}>Growixa</div>
          <div className={styles.brandCaption}>PLATFORM ADMIN</div>
        </div>
      </div>

      <div className={styles.sectionLabel}>OVERSIGHT</div>
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? styles.navItemActive : styles.navItem}
          >
            <span className={styles.navIcon} aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
