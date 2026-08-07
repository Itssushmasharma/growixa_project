"use client";

import { useEffect, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./campaigns-page.module.css";
import type { CampaignOversightItem, CampaignOversightStatus } from "./types";

function statusBadgeClass(status: CampaignOversightStatus): string {
  if (status === "SCHEDULED") return styles.statusScheduled ?? "";
  if (status === "FAILED") return styles.statusFailed ?? "";
  return styles.statusInFlight ?? "";
}

export function CampaignsPage() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [campaigns, setCampaigns] = useState<CampaignOversightItem[]>([]);
  const [pendingId, setPendingId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const list = await apiFetch<CampaignOversightItem[]>("/platform/campaigns");
        setCampaigns(list);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          setLoadError("You don't have access to campaign oversight.");
        } else {
          setLoadError("Could not load campaigns.");
        }
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  async function handlePause(campaignId: string) {
    setPendingId(campaignId);
    try {
      const updated = await apiFetch<CampaignOversightItem>(
        `/platform/campaigns/${campaignId}/pause`,
        { method: "POST" },
      );
      setCampaigns((current) =>
        current.map((campaign) => (campaign.id === campaignId ? updated : campaign)),
      );
      showToast("success", "Campaign paused.");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        showToast("error", "This campaign can no longer be paused.");
      } else {
        showToast("error", "Could not pause this campaign.");
      }
    } finally {
      setPendingId(null);
    }
  }

  if (loading) {
    return <div className={styles.card}>Loading…</div>;
  }

  if (loadError) {
    return <div className={styles.card}>{loadError}</div>;
  }

  return (
    <div className={styles.card}>
      <h2 className={styles.headerTitle}>
        Queued &amp; failed campaigns{" "}
        <span className={styles.headerCount}>· {campaigns.length} total</span>
      </h2>
      {campaigns.length === 0 && (
        <div className={styles.empty}>No queued or failed campaigns right now.</div>
      )}
      {campaigns.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Account</th>
              <th>Campaign</th>
              <th>Status</th>
              <th>Scheduled</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map((campaign) => (
              <tr key={campaign.id}>
                <td className={styles.accountCell}>{campaign.account_name}</td>
                <td className={styles.nameCell}>{campaign.name}</td>
                <td>
                  <span className={`${styles.statusBadge} ${statusBadgeClass(campaign.status)}`}>
                    {campaign.status}
                  </span>
                </td>
                <td>
                  {campaign.scheduled_at ? new Date(campaign.scheduled_at).toLocaleString() : "—"}
                </td>
                <td>
                  <button
                    type="button"
                    className={styles.pauseButton}
                    disabled={campaign.status !== "SCHEDULED" || pendingId === campaign.id}
                    onClick={() => handlePause(campaign.id)}
                  >
                    Pause
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
