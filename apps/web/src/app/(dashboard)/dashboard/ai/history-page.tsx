"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./history-page.module.css";
import type {
  AICapability,
  AIGeneration,
  MeResponse,
  StudioContentType,
  SubscriptionUsageInfo,
} from "./types";

const VIEW_PERMISSION = "ai.view";
const MANAGE_PERMISSION = "ai.manage";

interface ContentTypeConfig {
  value: StudioContentType;
  label: string;
  icon: string;
  capability: AICapability;
  placeholder: string;
  starters: string[];
}

const CONTENT_TYPES: ContentTypeConfig[] = [
  {
    value: "SUBJECT_LINE",
    label: "Email subject",
    icon: "✉️",
    capability: "SUBJECT_LINE",
    placeholder: "e.g. Subject lines for our Q3 product update, targeting existing customers",
    starters: [
      "Q3 product update announcement",
      "20% off flash sale ending Friday",
      "We miss you — VIP comeback offer",
      "Your weekly growth digest is here",
    ],
  },
  {
    value: "BODY_COPY",
    label: "Body copy",
    icon: "📝",
    capability: "BODY_COPY",
    placeholder: "e.g. Opening section for a re-engagement email with special discount code",
    starters: [
      "New feature release announcement",
      "Webinar invitation for marketers",
      "End of month product newsletter",
    ],
  },
  {
    value: "SOCIAL_CAPTION",
    label: "Social caption",
    icon: "📱",
    capability: "SOCIAL_CAPTION",
    placeholder: "e.g. Instagram post announcing our new AI automation tools with high energy",
    starters: [
      "Feature launch highlight",
      "Founder journey & behind the scenes",
      "3 tips to double email open rates",
    ],
  },
  {
    value: "HASHTAGS",
    label: "Hashtags",
    icon: "#️⃣",
    capability: "HASHTAGS",
    placeholder: "e.g. SaaS growth marketing tools for founders and digital agencies",
    starters: [
      "SaaS marketing & automation",
      "E-commerce holiday growth hacks",
      "AI productivity tools 2026",
    ],
  },
  {
    value: "CTA",
    label: "CTA",
    icon: "🎯",
    capability: "SUBJECT_LINE",
    placeholder: "e.g. High-converting button text and banner hook for booking a demo",
    starters: [
      "Book a live demo button",
      "Claim 20% discount hook",
      "Start free 14-day trial",
    ],
  },
  {
    value: "REWRITE",
    label: "Rewrite",
    icon: "✨",
    capability: "REWRITE",
    placeholder: "Paste the draft you want to refine or adjust tone for...",
    starters: [
      "Make this more punchy and concise",
      "Change tone to friendly and warm",
      "Make it bold and persuasive",
    ],
  },
];

const TONE_OPTIONS = [
  { value: "Friendly", label: "Tone: Friendly 😊" },
  { value: "Professional", label: "Tone: Professional 💼" },
  { value: "Urgent", label: "Tone: Urgent / FOMO ⚡" },
  { value: "Bold & Direct", label: "Tone: Bold & Direct 🔥" },
  { value: "Playful & Witty", label: "Tone: Playful & Witty 🎭" },
  { value: "Persuasive", label: "Tone: Persuasive 🎯" },
];

const LENGTH_OPTIONS = [
  { value: "Short", label: "Length: Short & Punchy" },
  { value: "Medium", label: "Length: Medium" },
  { value: "Detailed", label: "Length: In-Depth" },
];

type FilterTab = "ALL" | "PENDING" | "APPROVED" | StudioContentType;

const FILTER_TABS: { value: FilterTab; label: string }[] = [
  { value: "ALL", label: "All history" },
  { value: "PENDING", label: "Pending approval" },
  { value: "APPROVED", label: "Approved" },
  { value: "SUBJECT_LINE", label: "Subject lines" },
  { value: "BODY_COPY", label: "Body copy" },
  { value: "SOCIAL_CAPTION", label: "Captions" },
  { value: "HASHTAGS", label: "Hashtags" },
];

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function getCapabilityLabel(capability: AICapability, isCTA?: boolean): string {
  if (isCTA) return "CTA";
  switch (capability) {
    case "SUBJECT_LINE":
      return "Email subject";
    case "BODY_COPY":
      return "Body copy";
    case "SOCIAL_CAPTION":
      return "Social caption";
    case "HASHTAGS":
      return "Hashtags";
    case "REWRITE":
      return "Rewrite";
    case "POSTING_TIME":
      return "Posting time";
    default:
      return capability;
  }
}

export function HistoryPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [generations, setGenerations] = useState<AIGeneration[]>([]);
  const [activeTab, setActiveTab] = useState<FilterTab>("ALL");

  // Studio State
  const [selectedType, setSelectedType] = useState<StudioContentType>("SUBJECT_LINE");
  const [promptText, setPromptText] = useState("");
  const [rewriteInstruction, setRewriteInstruction] = useState("");
  const [selectedTone, setSelectedTone] = useState("Friendly");
  const [selectedLength, setSelectedLength] = useState("Short");
  const [variationsCount, setVariationsCount] = useState<number>(5);
  const [isGenerating, setIsGenerating] = useState(false);

  // Quota usage
  const [usage, setUsage] = useState<SubscriptionUsageInfo>({
    period_ai_used: 12,
    max_monthly_ai_runs: 500,
    plan_name: "Pro",
  });

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        const hasManage = me.permissions.includes(MANAGE_PERMISSION);
        setCanView(hasView);
        setCanManage(hasManage);

        if (hasView) {
          const list = await apiFetch<AIGeneration[]>("/ai/generations");
          // Initialize approval status if not preset
          const enriched = list.map((item) => ({
            ...item,
            approval_status: item.approval_status || "PENDING_APPROVAL",
          }));
          setGenerations(enriched);
        }

        // Try loading usage quota from subscription
        try {
          const sub = await apiFetch<{
            period_ai_used: number;
            plan: { max_monthly_ai_runs: number; name: string };
          }>("/billing/subscription");
          if (sub?.plan) {
            setUsage({
              period_ai_used: sub.period_ai_used,
              max_monthly_ai_runs: sub.plan.max_monthly_ai_runs,
              plan_name: sub.plan.name,
            });
          }
        } catch {
          // Fallback gracefully if subscription endpoint isn't accessible
        }
      } catch {
        setLoadError("Could not load generation history.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const currentTypeConfig: ContentTypeConfig = useMemo(() => {
    return CONTENT_TYPES.find((t) => t.value === selectedType) ?? CONTENT_TYPES[0]!;
  }, [selectedType]);

  // Handle Multi-Variation Generation
  async function handleGenerate() {
    if (!promptText.trim()) return;
    setIsGenerating(true);

    const capability = currentTypeConfig.capability;
    const isRewrite = selectedType === "REWRITE";

    // Build enriched prompt incorporating parameters
    let enrichedPrompt = promptText.trim();
    if (selectedType === "CTA") {
      enrichedPrompt = `[Call to Action Copy] ${enrichedPrompt}`;
    }
    if (!isRewrite) {
      enrichedPrompt += ` (Tone: ${selectedTone}, Length: ${selectedLength})`;
    }

    const payload = isRewrite
      ? {
          brief: "",
          existing_text: promptText.trim(),
          instruction: rewriteInstruction.trim() || `Rewrite with ${selectedTone} tone (${selectedLength} length)`,
        }
      : {
          brief: enrichedPrompt,
        };

    const countToGenerate = Math.max(1, variationsCount);
    const requests = Array.from({ length: countToGenerate }).map(() =>
      apiFetch<AIGeneration>(`/ai/generate/${capability}`, {
        method: "POST",
        body: JSON.stringify(payload),
      })
    );

    try {
      const results = await Promise.allSettled(requests);
      const successfulGenerations: AIGeneration[] = [];

      for (const res of results) {
        if (res.status === "fulfilled" && res.value) {
          successfulGenerations.push({
            ...res.value,
            approval_status: "PENDING_APPROVAL",
          });
        }
      }

      if (successfulGenerations.length > 0) {
        setGenerations((prev) => [...successfulGenerations, ...prev]);
        setUsage((prev) => ({
          ...prev,
          period_ai_used: prev.period_ai_used + successfulGenerations.length,
        }));
        showToast("success", `Generated ${successfulGenerations.length} new variation(s)!`);
      } else {
        const firstFailure = results.find((r) => r.status === "rejected") as
          | PromiseRejectedResult
          | undefined;
        showToast("error", parseAIError(firstFailure?.reason));
      }
    } catch (error) {
      showToast("error", parseAIError(error));
    } finally {
      setIsGenerating(false);
    }
  }

  // Card Action Handlers
  function handleApprove(generationId: string, text: string) {
    setGenerations((prev) =>
      prev.map((g) => (g.id === generationId ? { ...g, approval_status: "APPROVED" } : g))
    );
    if (navigator.clipboard) {
      void navigator.clipboard.writeText(text);
    }
    showToast("success", "Approved & copied to clipboard!");
  }

  function handleRewrite(text: string) {
    setSelectedType("REWRITE");
    setPromptText(text);
    setRewriteInstruction("Make this more concise and punchy");
    showToast("info", "Loaded into studio for rewrite.");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleAddToCampaign(text: string, capability: AICapability) {
    if (typeof window !== "undefined") {
      if (capability === "SUBJECT_LINE") {
        sessionStorage.setItem("growixa_draft_subject", text);
      } else {
        sessionStorage.setItem("growixa_draft_body", text);
      }
    }
    showToast("success", "Opening campaign composer with AI draft...");
    router.push("/dashboard/campaigns/new");
  }

  function handleAddToSocial(text: string) {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("growixa_draft_caption", text);
    }
    showToast("success", "Opening social composer with AI draft...");
    router.push("/dashboard/social/new");
  }

  function handleDiscard(generationId: string) {
    setGenerations((prev) =>
      prev.map((g) => (g.id === generationId ? { ...g, approval_status: "DISCARDED" } : g))
    );
    showToast("info", "Variation discarded.");
  }

  // Filtered Generations Stream
  const visibleGenerations = useMemo(() => {
    return generations
      .filter((g) => {
        if (g.approval_status === "DISCARDED") return false;
        if (activeTab === "ALL") return true;
        if (activeTab === "PENDING") return g.approval_status === "PENDING_APPROVAL";
        if (activeTab === "APPROVED") return g.approval_status === "APPROVED";
        if (activeTab === "CTA") return g.input_context?.brief?.toString().includes("[Call to Action");
        return g.capability === activeTab;
      })
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }, [generations, activeTab]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <div className={styles.emptyTitle}>Loading AI Studio…</div>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <div className={styles.emptyTitle}>{loadError}</div>
        </div>
      </div>
    );
  }

  if (!canView) {
    return (
      <div className={styles.page}>
        <div className={styles.emptyState}>
          <div className={styles.emptyTitle}>Access Denied</div>
          <p className={styles.emptyHint}>You don&apos;t have access to the AI Studio.</p>
        </div>
      </div>
    );
  }

  const quotaPercent = Math.min(
    100,
    Math.round((usage.period_ai_used / Math.max(1, usage.max_monthly_ai_runs)) * 100)
  );

  return (
    <div className={styles.page}>
      <div className={styles.studioLayout}>
        {/* =========================================================================
            LEFT PANEL: AI Studio Creation Engine (Dark Glassmorphic)
            ========================================================================= */}
        <section className={styles.studioCard} aria-label="AI Creation Controls">
          <div className={styles.studioHeader}>
            <div className={styles.studioTitleRow}>
              <h2 className={styles.studioTitle}>
                <span>✨</span> Generate content
              </h2>
              <span className={styles.brandVoiceBadge} title="Brand Voice is automatically injected">
                🛡️ Brand Voice
              </span>
            </div>
            <p className={styles.studioSubtitle}>
              Applies your saved brand voice · human approval always required before send/publish
            </p>
          </div>

          {/* Content Type Selector Pills */}
          <div className={styles.typeSection}>
            <span className={styles.sectionLabel}>Content type</span>
            <div className={styles.typePillsGrid} role="tablist" aria-label="Select content type">
              {CONTENT_TYPES.map((type) => (
                <button
                  key={type.value}
                  type="button"
                  role="tab"
                  aria-selected={selectedType === type.value}
                  className={selectedType === type.value ? styles.typePillActive : styles.typePill}
                  onClick={() => {
                    setSelectedType(type.value);
                    if (type.value === "REWRITE" && !rewriteInstruction) {
                      setRewriteInstruction("Make this punchy and concise");
                    }
                  }}
                >
                  <span>{type.icon}</span>
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Prompt / Input Group */}
          <div className={styles.inputGroup}>
            <label htmlFor="ai-studio-prompt" className={styles.sectionLabel}>
              {selectedType === "REWRITE" ? "Draft text to rewrite" : "Prompt"}
            </label>
            <textarea
              id="ai-studio-prompt"
              className={styles.promptTextarea}
              placeholder={currentTypeConfig.placeholder}
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
            />

            {/* Quick Starters */}
            {currentTypeConfig.starters.length > 0 && selectedType !== "REWRITE" && (
              <div className={styles.quickStarters} aria-label="Prompt starters">
                {currentTypeConfig.starters.map((starter) => (
                  <button
                    key={starter}
                    type="button"
                    className={styles.starterPill}
                    onClick={() => setPromptText(starter)}
                  >
                    + {starter}
                  </button>
                ))}
              </div>
            )}

            {/* Extra Instruction for Rewrite */}
            {selectedType === "REWRITE" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "6px" }}>
                <label htmlFor="ai-rewrite-instruction" className={styles.sectionLabel}>
                  Rewrite instruction
                </label>
                <input
                  id="ai-rewrite-instruction"
                  type="text"
                  className={styles.paramSelect}
                  placeholder="e.g. Make it more casual and add a strong hook"
                  value={rewriteInstruction}
                  onChange={(e) => setRewriteInstruction(e.target.value)}
                />
              </div>
            )}
          </div>

          {/* Tone & Length Parameter Selectors */}
          <div className={styles.parameterGrid}>
            <div>
              <label htmlFor="ai-tone-select" className={styles.sectionLabel}>
                Tone
              </label>
              <select
                id="ai-tone-select"
                className={styles.paramSelect}
                value={selectedTone}
                onChange={(e) => setSelectedTone(e.target.value)}
              >
                {TONE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="ai-length-select" className={styles.sectionLabel}>
                Length
              </label>
              <select
                id="ai-length-select"
                className={styles.paramSelect}
                value={selectedLength}
                onChange={(e) => setSelectedLength(e.target.value)}
              >
                {LENGTH_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Variations Count Selector */}
          <div className={styles.variationsRow}>
            <span className={styles.sectionLabel}>Variations</span>
            <div className={styles.variationButtons}>
              {[1, 3, 5].map((count) => (
                <button
                  key={count}
                  type="button"
                  className={variationsCount === count ? styles.varBtnActive : styles.varBtn}
                  onClick={() => setVariationsCount(count)}
                >
                  {count} {count === 1 ? "var" : "vars"}
                </button>
              ))}
            </div>
          </div>

          {/* Primary Action Button */}
          <button
            type="button"
            className={styles.generateButton}
            disabled={isGenerating || !promptText.trim() || !canManage}
            onClick={handleGenerate}
          >
            {isGenerating ? (
              <>⏳ Generating {variationsCount} variation(s)…</>
            ) : (
              <>✨ Generate {variationsCount} {variationsCount === 1 ? "variation" : "variations"}</>
            )}
          </button>

          {/* Quota & Token Meter */}
          <div className={styles.quotaFooter}>
            <div className={styles.quotaTextRow}>
              <span>AI Runs this month</span>
              <strong>
                {usage.period_ai_used.toLocaleString()} / {usage.max_monthly_ai_runs.toLocaleString()}
              </strong>
            </div>
            <div className={styles.quotaBarTrack}>
              <div className={styles.quotaBarFill} style={{ width: `${quotaPercent}%` }} />
            </div>
          </div>
        </section>

        {/* =========================================================================
            RIGHT PANEL: Generation History & Live Variations Feed
            ========================================================================= */}
        <section className={styles.feedColumn} aria-label="Generation History and Feed">
          <div className={styles.feedHeader}>
            <div className={styles.feedHeadingRow}>
              <h3 className={styles.feedTitle}>Generation History</h3>
              <span className={styles.feedCounter}>
                {visibleGenerations.length} {visibleGenerations.length === 1 ? "item" : "items"}
              </span>
            </div>

            {/* Filter Tabs */}
            <div className={styles.tabs} role="tablist" aria-label="Filter by capability or status">
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
          </div>

          {/* Empty States */}
          {generations.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>✨</div>
              <h4 className={styles.emptyTitle}>Ready to create with AI</h4>
              <p className={styles.emptyHint}>
                Select a content type on the left, type a quick prompt, and click &quot;Generate
                variations&quot; to begin.
              </p>
            </div>
          )}

          {generations.length > 0 && visibleGenerations.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>🔍</div>
              <h4 className={styles.emptyTitle}>No matching variations</h4>
              <p className={styles.emptyHint}>No generations match the selected filter tab.</p>
            </div>
          )}

          {/* List of Generation Cards */}
          <div className={styles.list}>
            {visibleGenerations.map((generation, index) => {
              const isApproved = generation.approval_status === "APPROVED";
              const outputText = generation.output?.text || "";
              const isCTA = generation.input_context?.brief?.toString().includes("[Call to Action");

              return (
                <article
                  key={`${generation.id}-${index}`}
                  className={`${styles.card} ${
                    isApproved ? styles.cardApproved : styles.cardPending
                  }`}
                >
                  {/* Card Header Badges */}
                  <div className={styles.cardHeader}>
                    <span className={styles.capabilityBadge}>
                      {getCapabilityLabel(generation.capability, isCTA)}
                    </span>
                    <span className={styles.aiBadge}>AI_GENERATED</span>
                    {generation.status === "COMPLETE" ? (
                      isApproved ? (
                        <span className={styles.statusApproved}>✓ Approved</span>
                      ) : (
                        <span className={styles.statusPending}>● Pending approval</span>
                      )
                    ) : (
                      <span className={styles.statusFailed}>✕ Failed</span>
                    )}
                    <span className={styles.timestamp}>
                      {formatDateTime(generation.created_at)}
                    </span>
                  </div>

                  {/* Card Content Text */}
                  {generation.status === "COMPLETE" && outputText && (
                    <div className={styles.cardContent}>
                      <p className={styles.outputText}>{outputText}</p>
                    </div>
                  )}

                  {generation.status === "FAILED" && generation.error_message && (
                    <div className={styles.cardContent}>
                      <p className={styles.errorText}>Error: {generation.error_message}</p>
                    </div>
                  )}

                  {/* Interactive Action Toolbar */}
                  {generation.status === "COMPLETE" && outputText && (
                    <div className={styles.cardActions}>
                      {!isApproved ? (
                        <button
                          type="button"
                          className={styles.approveBtn}
                          onClick={() => handleApprove(generation.id, outputText)}
                        >
                          ✓ Approve &amp; use
                        </button>
                      ) : (
                        <span className={styles.approvedDoneBtn}>✓ Approved</span>
                      )}

                      <button
                        type="button"
                        className={styles.secondaryActionBtn}
                        onClick={() => handleRewrite(outputText)}
                      >
                        ✨ Rewrite
                      </button>

                      {/* Channel-Specific Export Handlers */}
                      {(generation.capability === "SUBJECT_LINE" ||
                        generation.capability === "BODY_COPY") && (
                        <button
                          type="button"
                          className={styles.secondaryActionBtn}
                          onClick={() =>
                            handleAddToCampaign(outputText, generation.capability)
                          }
                        >
                          ✉️ Add to campaign
                        </button>
                      )}

                      {(generation.capability === "SOCIAL_CAPTION" ||
                        generation.capability === "HASHTAGS") && (
                        <button
                          type="button"
                          className={styles.secondaryActionBtn}
                          onClick={() => handleAddToSocial(outputText)}
                        >
                          📱 Add to social
                        </button>
                      )}

                      <button
                        type="button"
                        className={styles.discardBtn}
                        onClick={() => handleDiscard(generation.id)}
                      >
                        Discard
                      </button>
                    </div>
                  )}

                  {/* Card Metadata Footer */}
                  <div className={styles.cardFooter}>
                    <span>
                      {generation.provider} / {generation.model}
                    </span>
                    {generation.prompt_tokens !== null &&
                      generation.completion_tokens !== null && (
                        <span>
                          {generation.prompt_tokens + generation.completion_tokens} tokens
                        </span>
                      )}
                    {generation.estimated_cost_usd !== null && (
                      <span>${generation.estimated_cost_usd.toFixed(4)} (est.)</span>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

function parseAIError(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string; message?: string };
      if (parsed.detail?.includes("No AI provider is configured")) {
        return "AI isn't configured yet — connect a provider under Integrations, or ask your platform admin.";
      }
      if (parsed.detail) return parsed.detail;
      if (parsed.message) return parsed.message;
    } catch {
      // Keep fallback
    }
  }
  return "Could not generate content right now. Please try again.";
}

