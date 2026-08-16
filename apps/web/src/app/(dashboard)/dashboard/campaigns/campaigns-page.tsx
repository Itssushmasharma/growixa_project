"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { StatCard } from "@/components/stat-card/stat-card";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./campaigns-page.module.css";
import type { Campaign, ContactListSummary, MeResponse, SegmentSummary } from "./types";

const VIEW_PERMISSION = "campaigns.view";
const MANAGE_PERMISSION = "campaigns.manage";

type FilterTab = "ALL" | Campaign["status"];

const FILTER_TABS: { value: FilterTab; label: string }[] = [
  { value: "ALL", label: "All Campaigns" },
  { value: "SENT", label: "Sent" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "SENDING", label: "Sending" },
  { value: "DRAFT", label: "Drafts" },
  { value: "CANCELLED", label: "Cancelled" },
  { value: "FAILED", label: "Failed" },
];

const STATUS_LABEL: Record<Campaign["status"], string> = {
  DRAFT: "Draft",
  SCHEDULED: "Scheduled",
  DISPATCHING: "Dispatching…",
  SENDING: "Sending…",
  SENT: "Sent",
  CANCELLED: "Cancelled",
  FAILED: "Failed",
};

const STATUS_CLASS: Record<Campaign["status"], string> = {
  DRAFT: "statusDraft",
  SCHEDULED: "statusScheduled",
  DISPATCHING: "statusDispatching",
  SENDING: "statusSending",
  SENT: "statusSent",
  CANCELLED: "statusCancelled",
  FAILED: "statusFailed",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatScheduledAt(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function parseApiErrorDetail(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail) return parsed.detail;
    } catch {
      // Keep fallback
    }
  }
  return fallback;
}

export function CampaignsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [lists, setLists] = useState<ContactListSummary[]>([]);
  const [segments, setSegments] = useState<SegmentSummary[]>([]);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        setCanManage(me.permissions.includes(MANAGE_PERMISSION));

        if (hasView) {
          const [campaignList, listList, segmentList] = await Promise.all([
            apiFetch<Campaign[]>("/campaigns"),
            apiFetch<ContactListSummary[]>("/contacts/lists"),
            apiFetch<SegmentSummary[]>("/contacts/segments"),
          ]);
          setCampaigns(campaignList);
          setLists(listList);
          setSegments(segmentList);
        }
      } catch {
        setLoadError("Could not load campaigns.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const listNameById = useMemo(() => new Map(lists.map((l) => [l.id, l.name])), [lists]);
  const segmentNameById = useMemo(() => new Map(segments.map((s) => [s.id, s.name])), [segments]);

  function recipientLabel(campaign: Campaign): string {
    if (campaign.recipient_type === "ALL_CONTACTS") return "All contacts";
    if (campaign.recipient_type === "LIST") {
      return `List: ${listNameById.get(campaign.recipient_list_id ?? "") ?? "Unknown list"}`;
    }
    return `Segment: ${segmentNameById.get(campaign.recipient_segment_id ?? "") ?? "Unknown segment"}`;
  }

  async function handleCancel(campaign: Campaign, event: React.MouseEvent) {
    event.preventDefault();
    event.stopPropagation();
    if (!window.confirm(`Cancel "${campaign.name}"? This cannot be undone.`)) return;
    setCancellingId(campaign.id);
    try {
      await apiFetch<Campaign>(`/campaigns/${campaign.id}/cancel`, { method: "POST" });
      setCampaigns((prev) =>
        prev.map((c) => (c.id === campaign.id ? { ...c, status: "CANCELLED" as const } : c)),
      );
      showToast("success", "Campaign cancelled successfully.");
    } catch (error) {
      showToast("error", parseApiErrorDetail(error, "Could not cancel this campaign."));
    } finally {
      setCancellingId(null);
    }
  }

  const tabCounts = useMemo(() => {
    const counts: Record<FilterTab, number> = {
      ALL: campaigns.length,
      DRAFT: 0,
      SCHEDULED: 0,
      DISPATCHING: 0,
      SENDING: 0,
      SENT: 0,
      CANCELLED: 0,
      FAILED: 0,
    };
    for (const campaign of campaigns) {
      if (campaign.status in counts) counts[campaign.status] += 1;
    }
    return counts;
  }, [campaigns]);

  const filteredCampaigns = useMemo(() => {
    return campaigns.filter((c) => {
      if (activeTab !== "ALL" && c.status !== activeTab) return false;
      if (search.trim()) {
        const query = search.toLowerCase();
        const matchesName = c.name.toLowerCase().includes(query);
        const matchesSubject = (c.subject ?? "").toLowerCase().includes(query);
        if (!matchesName && !matchesSubject) return false;
      }
      return true;
    });
  }, [campaigns, activeTab, search]);

  const totalCampaigns = campaigns.length;
  const sentCampaigns = campaigns.filter((c) => c.status === "SENT").length;
  const scheduledCampaigns = campaigns.filter(
    (c) => c.status === "SCHEDULED" || c.status === "DISPATCHING" || c.status === "SENDING",
  ).length;
  const draftCampaigns = campaigns.filter((c) => c.status === "DRAFT").length;

  if (loading) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          Loading campaigns…
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          {loadError}
        </div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          <h2>Access Denied</h2>
          <p>You don&apos;t have permission to view campaigns.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Page Header */}
      <PageHeader
        icon="📧"
        title="Campaigns"
        description="Create, schedule and track your marketing campaigns."
        actions={
          canManage ? (
            <Link href="/dashboard/campaigns/new" className={styles.actionButton}>
              + Create Campaign
            </Link>
          ) : null
        }
      />

      {/* KPI Stats Deck (Real Derived Counts) */}
      <section className={styles.statsDeck} aria-label="Campaigns Overview KPIs">
        <StatCard label="Total Campaigns" value={totalCampaigns} subtext="All time" />
        <StatCard label="Sent Campaigns" value={sentCampaigns} subtext="Delivered" />
        <StatCard label="Scheduled" value={scheduledCampaigns} subtext="Upcoming" />
        <StatCard label="Drafts" value={draftCampaigns} subtext="In progress" />
      </section>

      {/* Toolbar: Category Tabs + Search */}
      <div className={styles.toolbarRow}>
        <div className={styles.tabsGroup} role="tablist">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.value}
              className={activeTab === tab.value ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab(tab.value)}
            >
              <span>{tab.label === "All Campaigns" ? "All" : tab.label}</span>
              <span className={styles.tabCount}>{tabCounts[tab.value]}</span>
            </button>
          ))}
        </div>

        <div className={styles.toolbarActions}>
          <div className={styles.searchWrapper}>
            <span className={styles.searchIcon}>🔍</span>
            <input
              type="text"
              placeholder="Search campaigns..."
              aria-label="Search campaigns"
              className={styles.searchInput}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Empty State */}
      {filteredCampaigns.length === 0 && (
        <div className={styles.emptyState}>
          <div style={{ fontSize: "36px", marginBottom: "8px" }}>📧</div>
          <h3 className={styles.emptyStateTitle}>No campaigns found</h3>
          <p className={styles.emptyStateHint}>
            {search.trim()
              ? `No campaigns match "${search}". Try clearing your search.`
              : activeTab === "ALL"
                ? "You haven't created any campaigns yet. Click '+ Create Campaign' to get started."
                : `No campaigns in "${STATUS_LABEL[activeTab as Campaign["status"]]}" state.`}
          </p>
          {canManage && activeTab === "ALL" && !search.trim() && (
            <Link href="/dashboard/campaigns/new" className={styles.actionButton}>
              + Create your first campaign
            </Link>
          )}
        </div>
      )}

      {/* Table Data Grid */}
      {filteredCampaigns.length > 0 && (
        <div className={styles.tableCard}>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Campaign Name</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Recipients</th>
                  <th>Created / Scheduled</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredCampaigns.map((campaign) => {
                  const statusClass = styles[STATUS_CLASS[campaign.status]] ?? "";
                  const canCancel =
                    canManage &&
                    (campaign.status === "DRAFT" ||
                      campaign.status === "SCHEDULED" ||
                      campaign.status === "DISPATCHING");

                  return (
                    <tr key={campaign.id}>
                      <td>
                        <div className={styles.campaignTitleCell}>
                          <div className={styles.campaignIcon}>✉️</div>
                          <div>
                            <Link
                              href={`/dashboard/campaigns/${campaign.id}`}
                              className={styles.campaignName}
                            >
                              {campaign.name}
                            </Link>
                            {campaign.subject && (
                              <div className={styles.campaignSubject}>{campaign.subject}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={styles.typeBadge}>Email</span>
                      </td>
                      <td>
                        <span className={`${styles.statusBadge} ${statusClass}`}>
                          ● {STATUS_LABEL[campaign.status]}
                        </span>
                      </td>
                      <td>{recipientLabel(campaign)}</td>
                      <td>
                        {campaign.status === "SCHEDULED" && campaign.scheduled_at
                          ? `Scheduled: ${formatScheduledAt(campaign.scheduled_at)}`
                          : formatDate(campaign.created_at)}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "flex-end",
                            gap: "8px",
                          }}
                        >
                          {canCancel && (
                            <button
                              type="button"
                              className={styles.cancelButton}
                              aria-label={`Cancel campaign ${campaign.name}`}
                              disabled={cancellingId === campaign.id}
                              onClick={(e) => handleCancel(campaign, e)}
                            >
                              {cancellingId === campaign.id ? "Cancelling…" : "Cancel"}
                            </button>
                          )}
                          <Link
                            href={`/dashboard/campaigns/${campaign.id}`}
                            style={{
                              fontSize: "12.5px",
                              fontWeight: 700,
                              color: "var(--color-primary-blue, #1457e6)",
                              textDecoration: "none",
                              padding: "4px 8px",
                            }}
                          >
                            View →
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className={styles.tableFooter}>
            <span>
              Showing 1 to {filteredCampaigns.length} of {campaigns.length} campaigns
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
