"use client";

import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "@/lib/api-client";

import styles from "./history-page.module.css";
import type { AICapability, AIGeneration, MeResponse } from "./types";

const VIEW_PERMISSION = "ai.view";

type FilterTab = "ALL" | AICapability;

const FILTER_TABS: { value: FilterTab; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "SUBJECT_LINE", label: "Subject lines" },
  { value: "BODY_COPY", label: "Body copy" },
  { value: "SOCIAL_CAPTION", label: "Captions" },
  { value: "REWRITE", label: "Rewrites" },
  { value: "HASHTAGS", label: "Hashtags" },
  { value: "POSTING_TIME", label: "Posting time" },
];

const CAPABILITY_LABEL: Record<AICapability, string> = {
  SUBJECT_LINE: "Subject line",
  BODY_COPY: "Body copy",
  SOCIAL_CAPTION: "Social caption",
  REWRITE: "Rewrite",
  HASHTAGS: "Hashtags",
  POSTING_TIME: "Posting time",
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function HistoryPage() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [generations, setGenerations] = useState<AIGeneration[]>([]);
  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        setCanView(hasView);
        if (hasView) {
          const list = await apiFetch<AIGeneration[]>("/ai/generations");
          setGenerations(list);
        }
      } catch {
        setLoadError("Could not load generation history.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const visibleGenerations = useMemo(() => {
    return generations
      .filter((g) => activeTab === "ALL" || g.capability === activeTab)
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }, [generations, activeTab]);

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
        <div className={styles.card}>You don&apos;t have access to AI generation history.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h2 className={styles.heading}>AI generation history</h2>
      <div className={styles.tabs} role="tablist" aria-label="Filter by capability">
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
          </button>
        ))}
      </div>

      {generations.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>
            No AI generations yet — use &quot;Generate with AI&quot; in a campaign or social post to
            get started.
          </p>
        </div>
      )}
      {generations.length > 0 && visibleGenerations.length === 0 && (
        <div className={styles.emptyState}>
          <p className={styles.hint}>No generations match this filter.</p>
        </div>
      )}

      <div className={styles.list}>
        {visibleGenerations.map((generation) => (
          <div className={styles.row} key={generation.id}>
            <div className={styles.rowHeader}>
              <span className={styles.capabilityBadge}>
                {CAPABILITY_LABEL[generation.capability]}
              </span>
              <span
                className={
                  generation.status === "COMPLETE" ? styles.statusComplete : styles.statusFailed
                }
              >
                {generation.status === "COMPLETE" ? "Complete" : "Failed"}
              </span>
              <span className={styles.timestamp}>{formatDateTime(generation.created_at)}</span>
            </div>
            {generation.status === "COMPLETE" && generation.output && (
              <p className={styles.outputText}>{generation.output.text}</p>
            )}
            {generation.status === "FAILED" && generation.error_message && (
              <p className={styles.errorText}>Error: {generation.error_message}</p>
            )}
            <div className={styles.rowFooter}>
              <span>
                {generation.provider} / {generation.model}
              </span>
              {generation.prompt_tokens !== null && generation.completion_tokens !== null && (
                <span>{generation.prompt_tokens + generation.completion_tokens} tokens</span>
              )}
              {generation.estimated_cost_usd !== null && (
                <span>${generation.estimated_cost_usd.toFixed(4)} (est.)</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
