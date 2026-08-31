"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import styles from "./sidebar.module.css";

interface NavItem {
  label: string;
  href: string;
  stage: "overview" | "find" | "qualify" | "create" | "send" | "manage";
  icon: ReactNode;
  requiresPermission?: string;
}

interface NavSection {
  label: string;
  stage: "overview" | "find" | "qualify" | "create" | "send" | "manage";
  items: NavItem[];
}

function IconDashboard() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2.5" y="2.5" width="6" height="6" rx="1.5" />
      <rect x="11.5" y="2.5" width="6" height="6" rx="1.5" />
      <rect x="2.5" y="11.5" width="6" height="6" rx="1.5" />
      <rect x="11.5" y="11.5" width="6" height="6" rx="1.5" />
    </svg>
  );
}

function IconContacts() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 16.5v-1.5a3.5 3.5 0 0 0-3.5-3.5h-5A3.5 3.5 0 0 0 2 15v1.5" />
      <circle cx="8" cy="5.5" r="3.5" />
      <path d="M18 16.5v-1.2a3.5 3.5 0 0 0-2.5-3.3" />
      <path d="M13.5 2.2a3.5 3.5 0 0 1 0 6.6" />
    </svg>
  );
}

function IconLists() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="7" y1="5" x2="16.5" y2="5" />
      <line x1="7" y1="10" x2="16.5" y2="10" />
      <line x1="7" y1="15" x2="16.5" y2="15" />
      <circle cx="3.5" cy="5" r="1" fill="currentColor" />
      <circle cx="3.5" cy="10" r="1" fill="currentColor" />
      <circle cx="3.5" cy="15" r="1" fill="currentColor" />
    </svg>
  );
}

function IconSegments() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="10" cy="10" r="7.5" />
      <circle cx="10" cy="10" r="4.5" />
      <circle cx="10" cy="10" r="1.5" fill="currentColor" />
    </svg>
  );
}

function IconImports() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 13.5v2.5a1.5 1.5 0 0 0 1.5 1.5h11a1.5 1.5 0 0 0 1.5-1.5v-2.5" />
      <polyline points="6 9 10 13 14 9" />
      <line x1="10" y1="2.5" x2="10" y2="13" />
    </svg>
  );
}

function IconSuppression() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="10" cy="10" r="7.5" />
      <line x1="4.5" y1="4.5" x2="15.5" y2="15.5" />
    </svg>
  );
}

function IconVerify() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M17 9.2A7.5 7.5 0 1 1 12.8 3" />
      <polyline points="17 3.5 9.5 11 7 8.5" />
    </svg>
  );
}

function IconCampaigns() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="17.5" y1="2.5" x2="8.5" y2="11.5" />
      <polygon points="17.5 2.5 12 17.5 8.5 11.5 2.5 8 17.5 2.5" />
    </svg>
  );
}

function IconTemplates() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2.5" y="2.5" width="15" height="15" rx="2" />
      <line x1="2.5" y1="7.5" x2="17.5" y2="7.5" />
      <line x1="7.5" y1="7.5" x2="7.5" y2="17.5" />
    </svg>
  );
}

function IconSocial() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2.5" y="2.5" width="15" height="15" rx="3.5" />
      <circle cx="10" cy="10" r="3.5" />
      <circle cx="14.5" cy="5.5" r="0.8" fill="currentColor" />
    </svg>
  );
}

function IconAi() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M10 2.5l1.8 4.2 4.2 1.8-4.2 1.8L10 14.5l-1.8-4.2-4.2-1.8 4.2-1.8L10 2.5z" />
      <path d="M15.5 13.5l0.8 1.8 1.8 0.8-1.8 0.8-0.8 1.8-0.8-1.8-1.8-0.8 1.8-0.8 0.8-1.8z" />
    </svg>
  );
}

function IconCompany() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="5" width="14" height="12.5" rx="2" />
      <path d="M7 5V3a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 13 3v2" />
      <line x1="3" y1="9.5" x2="17" y2="9.5" />
    </svg>
  );
}

function IconTeam() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="10" cy="6" r="3" />
      <path d="M4 16.5v-1a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v1" />
    </svg>
  );
}

function IconBilling() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="2.5" y="4" width="15" height="12" rx="2" />
      <line x1="2.5" y1="8" x2="17.5" y2="8" />
      <line x1="5.5" y1="12.5" x2="8.5" y2="12.5" />
    </svg>
  );
}

function IconAudit() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2.5H5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7.5L12 2.5z" />
      <polyline points="12 2.5 12 7.5 17 7.5" />
      <line x1="7" y1="11" x2="13" y2="11" />
      <line x1="7" y1="14" x2="11" y2="14" />
    </svg>
  );
}

function IconIntegrations() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M8 2.5v3M12 2.5v3M5 6.5h10a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z" />
      <circle cx="10" cy="12.5" r="1.5" />
    </svg>
  );
}

function IconDocs() {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M2.5 4.5A2.5 2.5 0 0 1 5 2h11a1.5 1.5 0 0 1 1.5 1.5v12A1.5 1.5 0 0 1 16 17H5a2.5 2.5 0 0 0-2.5 2.5V4.5z" />
      <path d="M5 2v15" />
    </svg>
  );
}

const NAV_SECTIONS: NavSection[] = [
  {
    label: "OVERVIEW",
    stage: "overview",
    items: [{ label: "Dashboard", href: "/dashboard", stage: "overview", icon: <IconDashboard /> }],
  },
  {
    label: "AUDIENCE",
    stage: "find",
    items: [
      {
        label: "Contacts",
        href: "/dashboard/contacts",
        stage: "find",
        icon: <IconContacts />,
        requiresPermission: "contacts.view",
      },
      {
        label: "Lists",
        href: "/dashboard/contacts/lists",
        stage: "find",
        icon: <IconLists />,
        requiresPermission: "contacts.view",
      },
      {
        label: "Segments",
        href: "/dashboard/contacts/segments",
        stage: "qualify",
        icon: <IconSegments />,
        requiresPermission: "contacts.view",
      },
      {
        label: "Imports",
        href: "/dashboard/contacts/imports",
        stage: "find",
        icon: <IconImports />,
        requiresPermission: "contacts.view",
      },
      {
        label: "Suppression",
        href: "/dashboard/contacts/suppression",
        stage: "qualify",
        icon: <IconSuppression />,
        requiresPermission: "contacts.view",
      },
      {
        label: "Verify Emails",
        href: "/dashboard/contacts/verify-email",
        stage: "qualify",
        icon: <IconVerify />,
        requiresPermission: "contacts.view",
      },
    ],
  },
  {
    label: "CAMPAIGNS",
    stage: "send",
    items: [
      {
        label: "Campaigns",
        href: "/dashboard/campaigns",
        stage: "send",
        icon: <IconCampaigns />,
        requiresPermission: "campaigns.view",
      },
      {
        label: "Templates",
        href: "/dashboard/templates",
        stage: "create",
        icon: <IconTemplates />,
        requiresPermission: "campaigns.view",
      },
      {
        label: "Social",
        href: "/dashboard/social",
        stage: "send",
        icon: <IconSocial />,
        requiresPermission: "social.view",
      },
      {
        label: "AI Assistant",
        href: "/dashboard/ai",
        stage: "create",
        icon: <IconAi />,
        requiresPermission: "ai.view",
      },
    ],
  },
  {
    label: "SETTINGS",
    stage: "manage",
    items: [
      {
        label: "Company",
        href: "/dashboard/company-settings",
        stage: "manage",
        icon: <IconCompany />,
      },
      {
        label: "Team",
        href: "/dashboard/team",
        stage: "manage",
        icon: <IconTeam />,
        requiresPermission: "users.manage",
      },
      {
        label: "Billing",
        href: "/dashboard/billing",
        stage: "manage",
        icon: <IconBilling />,
        requiresPermission: "billing.view",
      },
      {
        label: "Audit Log",
        href: "/dashboard/audit",
        stage: "manage",
        icon: <IconAudit />,
        requiresPermission: "audit.view",
      },
      {
        label: "Integrations",
        href: "/dashboard/integrations",
        stage: "manage",
        icon: <IconIntegrations />,
        requiresPermission: "integrations.manage",
      },
      {
        label: "Documentation",
        href: "/docs",
        stage: "manage",
        icon: <IconDocs />,
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
          <div className={styles.brandMark} aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
            </svg>
          </div>
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
            <div key={section.label} style={{ marginBottom: 10 }}>
              <button
                type="button"
                className={styles.sectionHeader}
                onClick={() => toggleSection(section.label)}
                aria-expanded={expanded}
              >
                <span
                  className={`${styles.sectionLabel} ${styles[`stage_${section.stage}`] ?? ""}`}
                >
                  {section.label}
                </span>
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
                      className={`${isActive ? styles.navItemActive : styles.navItem} ${styles[`navStage_${item.stage}`] ?? ""}`}
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
