"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import styles from "./sidebar.module.css";

interface NavItem {
  label: string;
  href: string;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

// Sprint 1 wires up only the nav items that have a real page behind them (per
// DESIGN_REFERENCES.md's scope caveat) — every other section from the design brief
// (Audience, Marketing, Automation, Insights, Team, Billing, ...) has no page yet and is
// omitted entirely rather than shipped as a dead link.
const NAV_SECTIONS: NavSection[] = [
  { label: "OVERVIEW", items: [{ label: "Dashboard", href: "/dashboard" }] },
  {
    label: "SETTINGS",
    items: [{ label: "Company", href: "/dashboard/company-settings" }],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className={styles.sidebar}>
      <div className={styles.brand}>
        <Image src={iconMark} alt="" width={28} height={28} />
        <div>
          <div className={styles.brandName}>Growixa</div>
          <div className={styles.brandCaption}>BY IITDEVELOPER</div>
        </div>
      </div>

      {NAV_SECTIONS.map((section) => (
        <div key={section.label}>
          <span className={styles.sectionLabel}>{section.label}</span>
          {section.items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? styles.navItemActive : styles.navItem}
            >
              {item.label}
            </Link>
          ))}
        </div>
      ))}
    </nav>
  );
}
