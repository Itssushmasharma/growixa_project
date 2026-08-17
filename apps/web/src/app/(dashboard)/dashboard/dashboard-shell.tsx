"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import { HelpDrawer } from "@/components/help/help-drawer";
import layoutStyles from "./layout.module.css";
import { LogoutButton } from "./logout-button";
import { Sidebar } from "./sidebar";
import { SupportSessionBanner } from "./support-session-banner";
import topbarStyles from "./topbar.module.css";

const MOBILE_QUERY = "(max-width: 768px)";

interface SubscriptionSummary {
  period_ai_used: number;
  plan: {
    name: string;
    max_monthly_ai_runs: number;
  };
}

const QUICK_JUMP_ROUTES = [
  { label: "AI Assistant", path: "/dashboard/ai", icon: "✨" },
  { label: "Campaigns", path: "/dashboard/campaigns", icon: "📧" },
  { label: "Contacts", path: "/dashboard/contacts", icon: "👥" },
  { label: "Templates", path: "/dashboard/templates", icon: "📄" },
  { label: "Social Media", path: "/dashboard/social", icon: "📱" },
  { label: "Billing & Plans", path: "/dashboard/billing", icon: "💳" },
  { label: "Company Settings", path: "/dashboard/company-settings", icon: "⚙️" },
];

export function DashboardShell({
  permissions,
  fullName,
  companyName,
  children,
}: {
  permissions: string[];
  fullName: string;
  companyName?: string;
  children: ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [helpDrawerOpen, setHelpDrawerOpen] = useState(false);
  const [usage, setUsage] = useState<{ used: number; max: number; planName: string } | null>(null);
  const [usageLoading, setUsageLoading] = useState(true);

  const pathname = usePathname();
  const router = useRouter();

  // Desktop defaults to open; mobile defaults to closed
  useEffect(() => {
    if (window.matchMedia(MOBILE_QUERY).matches) {
      setSidebarOpen(false);
    }
  }, [pathname]);

  // Load live subscription / usage data once on mount
  useEffect(() => {
    let isMounted = true;
    apiFetch<SubscriptionSummary>("/billing/subscription")
      .then((data) => {
        if (isMounted && data?.plan) {
          setUsage({
            used: data.period_ai_used ?? 0,
            max: data.plan.max_monthly_ai_runs ?? 10,
            planName: data.plan.name ?? "Free",
          });
        }
      })
      .catch(() => {
        // Leave usage as null if unavailable
      })
      .finally(() => {
        if (isMounted) setUsageLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Keyboard shortcut listener (⌘K / Ctrl+K)
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        const searchInput = document.getElementById("global-topbar-search");
        if (searchInput) {
          searchInput.focus();
          setIsSearchOpen(true);
        }
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const initials = fullName
    ? fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  const isPaidPlan =
    usage &&
    (usage.planName.toLowerCase().includes("growth") ||
      usage.planName.toLowerCase().includes("pro") ||
      usage.planName.toLowerCase().includes("enterprise"));

  const usagePercent = usage
    ? Math.min(100, Math.round((usage.used / Math.max(1, usage.max)) * 100))
    : 0;

  const filteredJumpRoutes = QUICK_JUMP_ROUTES.filter((r) =>
    r.label.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className={layoutStyles.shell}>
      <Sidebar permissions={permissions} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className={layoutStyles.main}>
        {/* =========================================================================
            Global Topbar (Unified across all dashboard pages)
            ========================================================================= */}
        <header className={topbarStyles.topbar}>
          {/* Left: Sidebar Toggle + Global Search Command Bar */}
          <div className={topbarStyles.leftArea}>
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

            <div className={topbarStyles.searchWrapper}>
              <span className={topbarStyles.searchIcon}>🔍</span>
              <input
                id="global-topbar-search"
                type="text"
                className={topbarStyles.searchInput}
                placeholder="Search dashboard... (⌘K)"
                value={searchQuery}
                onFocus={() => setIsSearchOpen(true)}
                onBlur={() => setTimeout(() => setIsSearchOpen(false), 200)}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <kbd className={topbarStyles.kbdShortcut}>⌘K</kbd>

              {/* Quick Jump Dropdown Menu */}
              {isSearchOpen && (
                <div className={topbarStyles.quickJumpMenu}>
                  {filteredJumpRoutes.map((route) => (
                    <Link
                      key={route.path}
                      href={route.path}
                      className={topbarStyles.quickJumpItem}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        router.push(route.path);
                        setIsSearchOpen(false);
                      }}
                    >
                      <span>{route.icon}</span>
                      <span>{route.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right: AI Credits + Upgrade/Manage + Notifications + User Profile */}
          <div className={topbarStyles.rightArea}>
            {/* AI Credits Meter (Rendered when usage is resolved) */}
            {!usageLoading && usage && (
              <Link
                href="/dashboard/billing"
                className={topbarStyles.creditsPill}
                title="AI Credits Usage"
              >
                <span className={topbarStyles.creditsLabel}>
                  <span>⚡</span> AI Credits
                </span>
                <span className={topbarStyles.creditsCount}>
                  {usage.used} / {usage.max}
                </span>
                <div className={topbarStyles.creditsTrack}>
                  <div className={topbarStyles.creditsFill} style={{ width: `${usagePercent}%` }} />
                </div>
              </Link>
            )}

            {/* Subscription Action Button */}
            {!usageLoading &&
              (isPaidPlan ? (
                <Link href="/dashboard/billing" className={topbarStyles.managePlanBtn}>
                  Manage Plan
                </Link>
              ) : (
                <Link href="/dashboard/billing" className={topbarStyles.upgradeBtn}>
                  Upgrade
                </Link>
              ))}

            {/* Help Drawer Trigger Button */}
            <button
              type="button"
              className={topbarStyles.helpButton}
              onClick={() => setHelpDrawerOpen(true)}
              title="Help & Documentation"
              aria-label="Help & Documentation"
            >
              ❓ Help
            </button>

            {/* Notifications Bell */}
            <button
              type="button"
              className={topbarStyles.notificationButton}
              aria-label="Notifications"
              onClick={() => router.push("/dashboard/ai")}
            >
              🔔
              <span className={topbarStyles.notificationBadge}>3</span>
            </button>

            {/* User Profile Chip */}
            <div className={topbarStyles.userProfileChip}>
              <div className={topbarStyles.userAvatar}>{initials}</div>
              <div className={topbarStyles.userInfo}>
                <span className={topbarStyles.userName}>{fullName}</span>
                <span className={topbarStyles.userOrg}>{companyName || "Personal Workspace"}</span>
              </div>
              <LogoutButton />
            </div>
          </div>
        </header>

        <SupportSessionBanner />
        <div className={layoutStyles.content}>{children}</div>

        <HelpDrawer isOpen={helpDrawerOpen} onClose={() => setHelpDrawerOpen(false)} />
      </div>
    </div>
  );
}
