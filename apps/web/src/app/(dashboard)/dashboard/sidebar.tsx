"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import iconMark from "@/assets/icon/growixa-icon-mark.png";

import styles from "./sidebar.module.css";

interface NavItem {
  label: string;
  href: string;
  icon: string;
  requiresPermission?: string;
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: "OVERVIEW",
    items: [{ label: "Dashboard", href: "/dashboard", icon: "📊" }],
  },
  {
    label: "AUDIENCE",
    items: [
      {
        label: "Contacts",
        href: "/dashboard/contacts",
        icon: "👥",
        requiresPermission: "contacts.view",
      },
      {
        label: "Lists",
        href: "/dashboard/contacts/lists",
        icon: "📋",
        requiresPermission: "contacts.view",
      },
      {
        label: "Segments",
        href: "/dashboard/contacts/segments",
        icon: "🎯",
        requiresPermission: "contacts.view",
      },
      {
        label: "Imports",
        href: "/dashboard/contacts/imports",
        icon: "📥",
        requiresPermission: "contacts.view",
      },
      {
        label: "Suppression",
        href: "/dashboard/contacts/suppression",
        icon: "🚫",
        requiresPermission: "contacts.view",
      },
    ],
  },
  {
    label: "CAMPAIGNS",
    items: [
      {
        label: "Campaigns",
        href: "/dashboard/campaigns",
        icon: "📧",
        requiresPermission: "campaigns.view",
      },
      {
        label: "Templates",
        href: "/dashboard/templates",
        icon: "🎨",
        requiresPermission: "campaigns.view",
      },
      {
        label: "Social",
        href: "/dashboard/social",
        icon: "📸",
        requiresPermission: "social.view",
      },
      {
        label: "AI Assistant",
        href: "/dashboard/ai",
        icon: "✨",
        requiresPermission: "ai.view",
      },
    ],
  },
  {
    label: "SETTINGS",
    items: [
      { label: "Company", href: "/dashboard/company-settings", icon: "🏢" },
      { label: "Team", href: "/dashboard/team", icon: "👥", requiresPermission: "users.manage" },
      {
        label: "Billing",
        href: "/dashboard/billing",
        icon: "💳",
        requiresPermission: "billing.view",
      },
      {
        label: "Audit Log",
        href: "/dashboard/audit",
        icon: "📜",
        requiresPermission: "audit.view",
      },
      {
        label: "Integrations",
        href: "/dashboard/integrations",
        icon: "🔌",
        requiresPermission: "integrations.manage",
      },
      {
        label: "System Health",
        href: "/admin",
        icon: "🩺",
        requiresPermission: "admin.access",
      },
    ],
  },
];

interface SidebarProps {
  permissions: string[];
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ permissions, open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(NAV_SECTIONS.map((section) => [section.label, true])),
  );

  // Auto-expand the section containing the current active route
  useEffect(() => {
    for (const section of NAV_SECTIONS) {
      if (
        section.items.some((item) => pathname === item.href || pathname.startsWith(`${item.href}/`))
      ) {
        setExpandedSections((prev) => ({ ...prev, [section.label]: true }));
      }
    }
  }, [pathname]);

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
            <div key={section.label} style={{ marginBottom: 12 }}>
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
                items.map((item) => {
                  const isActive =
                    item.href === "/dashboard/contacts" || item.href === "/dashboard/campaigns"
                      ? pathname === item.href
                      : pathname === item.href ||
                        (item.href !== "/dashboard" && pathname.startsWith(`${item.href}/`));
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
            </div>
          );
        })}
      </nav>
    </>
  );
}
