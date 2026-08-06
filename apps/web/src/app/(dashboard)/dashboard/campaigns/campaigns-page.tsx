"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./campaigns-page.module.css";
import type { Campaign, ContactListSummary, MeResponse, SegmentSummary } from "./types";

const VIEW_PERMISSION = "campaigns.view";
const MANAGE_PERMISSION = "campaigns.manage";

type FilterTab = "ALL" | Campaign["status"];

const FILTER_TABS: { value: FilterTab; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "DRAFT", label: "Draft" },
  { value: "SCHEDULED", label: "Scheduled" },
  { value: "SENDING", label: "Sending" },
  { value: "SENT", label: "Sent" },
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
    event.preventDefault(); // prevent Link navigation
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

  const visibleCampaigns = useMemo(() => {
    const query = search.trim().toLowerCase();
    return campaigns
      .filter((c) => activeTab === "ALL" || c.status === activeTab)
      .filter(
        (c) =>
          !query || c.name.toLowerCase().includes(query) || c.subject.toLowerCase().includes(query),
      )
      .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  }, [campaigns, search, activeTab]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>Loading…</div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>{loadError}</div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>You don&apos;t have access to campaigns.</div>
      </div>
    );
  }

  const cancellableStatuses: Campaign["status"][] = ["DRAFT", "SCHEDULED"];

  return (
    <div className={styles.page}>
      <div className={styles.topRow}>
        <div className={styles.tabs} role="tablist" aria-label="Filter campaigns by status">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.value}
              className={activeTab === tab.value ? styles.tabActive : styles.tab}
              onClick={() => setActiveTab(tab.value)}
            >
              {tab.label}
              {tab.value !== "ALL" && tabCounts[tab.value] > 0 && (
                <span className={styles.tabCount}>{tabCounts[tab.value]}</span>
              )}
            </button>
          ))}
        </div>
        <div className={styles.topActions}>
          {campaigns.length > 0 && (
            <input
              type="search"
              className={styles.searchInput}
              placeholder="Search by name or subject…"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search campaigns"
            />
          )}
          {canManage && (
            <Link href="/dashboard/campaigns/new" className={styles.actionButton}>
              + New campaign
            </Link>
          )}
        </div>
      </div>

      {campaigns.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>No campaigns yet.</p>
        </div>
      )}
      {campaigns.length > 0 && visibleCampaigns.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>No campaigns match this filter.</p>
        </div>
      )}

      <div className={styles.grid}>
        {visibleCampaigns.map((campaign) => (
          <Link
            href={`/dashboard/campaigns/${campaign.id}`}
            className={styles.campaignCard}
            key={campaign.id}
          >
            <span className={`${styles.statusBadge} ${styles[STATUS_CLASS[campaign.status]]}`}>
              {STATUS_LABEL[campaign.status]}
            </span>
            <div className={styles.campaignName}>{campaign.name}</div>
            <div className={styles.campaignSubject}>{campaign.subject}</div>
            {campaign.status === "SCHEDULED" && campaign.scheduled_at && (
              <div className={styles.scheduledAtLabel}>
                Scheduled for {formatScheduledAt(campaign.scheduled_at)}
              </div>
            )}
            <div className={styles.cardFooter}>
              <span className={styles.hint}>{recipientLabel(campaign)}</span>
              <div className={styles.cardActions}>
                <span className={styles.hint}>Updated {formatDate(campaign.updated_at)}</span>
                {canManage && cancellableStatuses.includes(campaign.status) && (
                  <button
                    type="button"
                    className={styles.cancelButton}
                    disabled={cancellingId === campaign.id}
                    onClick={(e) => handleCancel(campaign, e)}
                    aria-label={`Cancel campaign ${campaign.name}`}
                  >
                    {cancellingId === campaign.id ? "Cancelling…" : "Cancel"}
                  </button>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
