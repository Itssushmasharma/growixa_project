"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import styles from "./sidebar.module.css";

interface NavItem {
  label: string;
  href: string;
  requiresPermission?: string;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

// Only nav items that have a real page behind them are wired up (per
// DESIGN_REFERENCES.md's scope caveat) — every other section from the design brief
// (Marketing, Automation, Insights, Billing, ...) has no page yet and is omitted
// entirely rather than shipped as a dead link.
const NAV_SECTIONS: NavSection[] = [
  { label: "OVERVIEW", items: [{ label: "Dashboard", href: "/dashboard" }] },
  {
    label: "AUDIENCE",
    items: [
      { label: "Contacts", href: "/dashboard/contacts", requiresPermission: "contacts.view" },
      { label: "Lists", href: "/dashboard/contacts/lists", requiresPermission: "contacts.view" },
      {
        label: "Segments",
        href: "/dashboard/contacts/segments",
        requiresPermission: "contacts.view",
      },
      {
        label: "Imports",
        href: "/dashboard/contacts/imports",
        requiresPermission: "contacts.view",
      },
      {
        label: "Suppression",
        href: "/dashboard/contacts/suppression",
        requiresPermission: "contacts.view",
      },
    ],
  },
  {
    label: "CAMPAIGNS",
    items: [
      { label: "Campaigns", href: "/dashboard/campaigns", requiresPermission: "campaigns.view" },
      { label: "Templates", href: "/dashboard/templates", requiresPermission: "campaigns.view" },
    ],
  },
  {
    label: "SETTINGS",
    items: [
      { label: "Company", href: "/dashboard/company-settings" },
      { label: "Team", href: "/dashboard/team", requiresPermission: "users.manage" },
      { label: "Audit Log", href: "/dashboard/audit", requiresPermission: "audit.view" },
      {
        label: "Integrations",
        href: "/dashboard/integrations",
        requiresPermission: "integrations.manage",
      },
    ],
  },
];

interface SidebarProps {
  permissions: string[];
  // Single boolean drives both breakpoints: on desktop it toggles a full-width vs.
  // zero-width sidebar (content reflows); on mobile it toggles an off-canvas drawer
  // sliding in over content (see sidebar.module.css's media query for the split).
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ permissions, open, onClose }: SidebarProps) {
  const pathname = usePathname();
  // Each section (OVERVIEW/AUDIENCE/SETTINGS) is its own independent accordion,
  // starting expanded — matches the reference pattern of per-heading expand/collapse
  // rather than one all-or-nothing toggle for the whole nav.
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(NAV_SECTIONS.map((section) => [section.label, true])),
  );

  function toggleSection(label: string) {
    setExpandedSections((current) => ({ ...current, [label]: !current[label] }));
  }

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="Close sidebar"
          className={styles.backdrop}
          onClick={onClose}
        />
      )}
      <nav
        className={`${styles.sidebar} ${open ? styles.mobileOpen : styles.collapsed}`}
        aria-hidden={!open}
      >
        <div className={styles.brand}>
          <Image src={iconMark} alt="" width={28} height={28} />
          <div>
            <div className={styles.brandName}>Growixa</div>
            <div className={styles.brandCaption}>BY IITDEVELOPER</div>
          </div>
        </div>

        {NAV_SECTIONS.map((section) => {
          const items = section.items.filter(
            (item) => !item.requiresPermission || permissions.includes(item.requiresPermission),
          );
          if (items.length === 0) {
            return null;
          }
          const expanded = expandedSections[section.label] ?? true;
          return (
            <div key={section.label}>
              <button
                type="button"
                className={styles.sectionHeader}
                onClick={() => toggleSection(section.label)}
                aria-expanded={expanded}
              >
                <span className={styles.sectionLabel}>{section.label}</span>
                <svg
                  className={expanded ? styles.chevronExpanded : styles.chevron}
                  width="10"
                  height="10"
                  viewBox="0 0 10 10"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M2.5 3.5 5 6.5l2.5-3"
                    stroke="currentColor"
                    strokeWidth="1.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
              {expanded &&
                items.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={pathname === item.href ? styles.navItemActive : styles.navItem}
                  >
                    {item.label}
                  </Link>
                ))}
            </div>
          );
        })}
      </nav>
    </>
  );
}
