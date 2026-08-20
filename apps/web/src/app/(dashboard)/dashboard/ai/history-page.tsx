"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header/page-header";
import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./history-page.module.css";
import type {
  AICapability,
  AIGeneration,
  BrandProfile,
  CampaignSummary,
  MeResponse,
  SegmentSummary,
  StudioChannel,
  SuggestedPrompt,
} from "./types";

const VIEW_PERMISSION = "ai.view";
const MANAGE_PERMISSION = "ai.manage";

const CHANNELS: { value: StudioChannel; label: string; icon: string; capability: AICapability }[] =
  [
    { value: "Email", label: "Email", icon: "✉️", capability: "BODY_COPY" },
    { value: "Social Post", label: "Social Post", icon: "📱", capability: "SOCIAL_CAPTION" },
    { value: "SMS", label: "SMS", icon: "💬", capability: "BODY_COPY" },
    { value: "Ad Copy", label: "Ad Copy", icon: "📢", capability: "SUBJECT_LINE" },
    { value: "Blog", label: "Blog", icon: "📝", capability: "BODY_COPY" },
  ];

const TONE_OPTIONS = [
  { value: "Friendly", label: "Friendly 😊" },
  { value: "Professional", label: "Professional 💼" },
  { value: "Bold", label: "Bold 🔥" },
  { value: "Conversational", label: "Conversational 💬" },
  { value: "Persuasive", label: "Persuasive 🎯" },
];

const LENGTH_OPTIONS = [
  { value: "Short & Punchy", label: "Short & Punchy" },
  { value: "Medium", label: "Medium" },
  { value: "Detailed", label: "Detailed" },
];

const DEFAULT_SUGGESTIONS: SuggestedPrompt[] = [
  {
    id: "sug-1",
    title: "Re-engagement email",
    subtitle: "for inactive customers",
    channel: "Email",
    tag: "High Impact",
    tagColor: "purple",
    prompt:
      "Write a high-converting re-engagement email with a 20% discount offer to win back inactive leads.",
    tone: "Friendly",
    length: "Short & Punchy",
  },
  {
    id: "sug-2",
    title: "LinkedIn post",
    subtitle: "for Summer Sale 2025",
    channel: "Social Post",
    tag: "Engagement Booster",
    tagColor: "blue",
    prompt:
      "Announce our Summer Sale with high-engagement founder storytelling and 3 key benefits.",
    tone: "Bold",
    length: "Medium",
  },
  {
    id: "sug-3",
    title: "Subject lines",
    subtitle: "for upcoming campaign",
    channel: "Email",
    tag: "Improve Open Rate",
    tagColor: "green",
    prompt: "5 curiosity-driven subject lines for announcing our biggest feature release.",
    tone: "Persuasive",
    length: "Short & Punchy",
  },
  {
    id: "sug-4",
    title: "Improve your lowest",
    subtitle: "performing email",
    channel: "Email",
    tag: "AI Analysis",
    tagColor: "orange",
    prompt: "Rewrite our welcome email with clearer value props and high urgency.",
    tone: "Conversational",
    length: "Short & Punchy",
  },
];

const EXAMPLE_CHIPS = [
  "Re-engagement email",
  "Product launch email",
  "Flash sale email",
  "VIP customer thank you",
];

export function HistoryPage() {
  const router = useRouter();
  const { showToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [canView, setCanView] = useState(false);
  const [canManage, setCanManage] = useState(false);

  // Authenticated user & Account
  const [currentUser, setCurrentUser] = useState<MeResponse>({
    id: "u-1",
    email: "admin@growixa.com",
    full_name: "Ravi Sharma",
    company_name: "Growixa",
    permissions: [],
  });

  // Data Collections
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([
    { id: "c-1", name: "Summer Sale 2025", status: "DRAFT" },
    { id: "c-2", name: "Product Launch Q3", status: "SCHEDULED" },
  ]);
  const [segments, setSegments] = useState<SegmentSummary[]>([
    { id: "s-1", name: "Inactive Customers", contact_count: 1420 },
    { id: "s-2", name: "VIP Customers", contact_count: 580 },
    { id: "s-3", name: "All Contacts", contact_count: 4200 },
  ]);

  // Studio Creation Controls
  const [selectedChannel, setSelectedChannel] = useState<StudioChannel>("Email");
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>("c-1");
  const [selectedAudienceId, setSelectedAudienceId] = useState<string>("s-1");
  const [promptText, setPromptText] = useState("");
  const [selectedTone, setSelectedTone] = useState("Friendly");
  const [selectedLength, setSelectedLength] = useState("Short & Punchy");
  const [variationsCount, setVariationsCount] = useState<number>(3);
  const [isGenerating, setIsGenerating] = useState(false);

  // Brand Voice Drawer State
  const [isBrandDrawerOpen, setIsBrandDrawerOpen] = useState(false);
  const [brandProfile, setBrandProfile] = useState<BrandProfile | null>(null);
  const [brandProfileLoading, setBrandProfileLoading] = useState(true);

  // Generations History
  const [generations, setGenerations] = useState<AIGeneration[]>([]);
  const [historyFilter, setHistoryFilter] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [timeFilter, setTimeFilter] = useState("All Time");

  useEffect(() => {
    async function load() {
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        const hasView = me.permissions.includes(VIEW_PERMISSION);
        const hasManage = me.permissions.includes(MANAGE_PERMISSION);
        setCanView(hasView);
        setCanManage(hasManage);
        setCurrentUser(me);

        if (hasView) {
          try {
            const list = await apiFetch<AIGeneration[]>("/ai/generations");
            const enriched = list.map((item) => ({
              ...item,
              approval_status: item.approval_status || "PENDING_APPROVAL",
            }));
            setGenerations(enriched);
          } catch {
            // Keep empty list if no generations yet
          }

          // Fetch active campaigns if available
          try {
            const campList = await apiFetch<CampaignSummary[]>("/campaigns");
            if (campList && campList.length > 0) {
              setCampaigns(campList);
              setSelectedCampaignId(campList[0]?.id || "");
            }
          } catch {
            // Fallback to default campaigns list
          }

          // Fetch segments if available
          try {
            const segList = await apiFetch<SegmentSummary[]>("/contacts/segments");
            if (segList && segList.length > 0) {
              setSegments(segList);
              setSelectedAudienceId(segList[0]?.id || "");
            }
          } catch {
            // Fallback to default segments list
          }

          // Fetch the account's real brand profile for the Brand Voice drawer
          try {
            const profile = await apiFetch<BrandProfile | null>("/brand/profile");
            setBrandProfile(profile);
          } catch {
            // Leave brandProfile null -- drawer shows its own empty state
          } finally {
            setBrandProfileLoading(false);
          }
        }
      } catch {
        setLoadError("Could not load AI Assistant workspace.");
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, []);

  const activeCampaign = campaigns.find((c) => c.id === selectedCampaignId);
  const activeSegment = segments.find((s) => s.id === selectedAudienceId);

  // Handle Generating Variations
  async function handleGenerate() {
    if (!promptText.trim()) return;
    setIsGenerating(true);

    const activeConfig = CHANNELS.find((c) => c.value === selectedChannel) || CHANNELS[0]!;
    const capability = activeConfig.capability;

    const campaignLabel = activeCampaign ? activeCampaign.name : "General";
    const audienceLabel = activeSegment ? activeSegment.name : "All Contacts";

    const enrichedBrief = `${promptText.trim()} (Channel: ${selectedChannel}, Campaign: ${campaignLabel}, Audience: ${audienceLabel}, Tone: ${selectedTone}, Length: ${selectedLength})`;

    const payload: {
      brief: string;
      linked_entity_type?: string;
      linked_entity_id?: string;
    } = {
      brief: enrichedBrief,
    };

    if (selectedCampaignId && selectedCampaignId !== "general") {
      payload.linked_entity_type = "campaign";
      payload.linked_entity_id = selectedCampaignId;
    }

    const countToGenerate = Math.max(1, variationsCount);
    const requests = Array.from({ length: countToGenerate }).map(() =>
      apiFetch<AIGeneration>(`/ai/generate/${capability}`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );

    try {
      const results = await Promise.allSettled(requests);
      const newItems: AIGeneration[] = [];

      results.forEach((res) => {
        if (res.status === "fulfilled" && res.value) {
          newItems.push({
            ...res.value,
            channel: selectedChannel,
            approval_status: "PENDING_APPROVAL",
            input_context: {
              brief: promptText,
              campaign: campaignLabel,
              audience: audienceLabel,
            },
          });
        }
      });

      if (newItems.length > 0) {
        setGenerations((prev) => [...newItems, ...prev]);
        showToast("success", `Generated ${newItems.length} variation(s) for ${selectedChannel}!`);
      } else {
        const firstError = results.find((r) => r.status === "rejected") as
          PromiseRejectedResult | undefined;
        showToast("error", parseAIError(firstError?.reason));
      }
    } catch (error) {
      showToast("error", parseAIError(error));
    } finally {
      setIsGenerating(false);
    }
  }

  // Handle Suggestion Click
  function handleSelectSuggestion(sug: SuggestedPrompt) {
    // Only apply fields this starter template can genuinely set (channel, prompt text,
    // tone, length). It deliberately does not touch campaign/audience selection: these
    // are example templates, not tied to this account's real campaigns/segments, and
    // matching by name against them was silently doing nothing whenever no name
    // happened to match (GRX-BUG-003) -- leaving the current selection untouched is
    // honest instead of silently failing.
    setSelectedChannel(sug.channel);
    setPromptText(sug.prompt);
    setSelectedTone(sug.tone);
    setSelectedLength(sug.length);
    showToast("info", `Loaded template for ${sug.title}`);
  }

  // Workflow Handlers
  function handleUse(text: string, genId: string) {
    setGenerations((prev) =>
      prev.map((g) => (g.id === genId ? { ...g, approval_status: "APPROVED" } : g)),
    );
    if (navigator.clipboard) {
      void navigator.clipboard.writeText(text);
    }
    showToast("success", "Approved & copied to clipboard!");
  }

  function handleEdit(text: string) {
    setPromptText(text);
    showToast("info", "Loaded into prompt editor for tweaking.");
    window.scrollTo({ top: 120, behavior: "smooth" });
  }

  function handleAddToCampaign(text: string) {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("growixa_draft_body", text);
    }
    showToast("success", "Opening campaign builder with AI copy...");
    router.push("/dashboard/campaigns/new");
  }

  function handleScheduleSocial(text: string) {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("growixa_draft_caption", text);
    }
    showToast("success", "Opening social composer with AI caption...");
    router.push("/dashboard/social/new");
  }

  function handleSaveTemplate(text: string) {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("growixa_template_html", `<p>${text.replace(/\n/g, "<br/>")}</p>`);
    }
    showToast("success", "Opening template builder with AI copy...");
    router.push("/dashboard/templates/new");
  }

  // Filtered Generations
  const visibleGenerations = useMemo(() => {
    return generations.filter((g) => {
      if (g.approval_status === "DISCARDED") return false;
      if (historyFilter !== "All" && g.channel !== historyFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const text = g.output?.text?.toLowerCase() || "";
        const campaign = g.input_context?.campaign?.toLowerCase() || "";
        if (!text.includes(q) && !campaign.includes(q)) return false;
      }
      return true;
    });
  }, [generations, historyFilter, searchQuery]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div
          style={{ background: "#fff", padding: "40px", borderRadius: "18px", textAlign: "center" }}
        >
          Loading AI Assistant…
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
          <p>You don&apos;t have access to the AI Studio.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      {/* Reusable Page Header */}
      <PageHeader
        icon="✨"
        title="AI Assistant"
        description="Your AI marketing copilot to create high-performing content in seconds."
      />

      {/* =========================================================================
          Two-Column Main Studio Layout
          ========================================================================= */}
      <div className={styles.studioLayout}>
        {/* =========================================================================
            LEFT COLUMN: "Create with AI" Panel (~30%)
            ========================================================================= */}
        <section className={styles.leftPanelCard} aria-label="Create with AI Panel">
          <div className={styles.panelHeaderRow}>
            <div>
              <h2 className={styles.panelTitle}>Create with AI</h2>
              <p className={styles.panelSubtitle}>Generate content that converts.</p>
            </div>
            <button
              type="button"
              className={styles.brandVoicePill}
              onClick={() => setIsBrandDrawerOpen(true)}
              title="Click to view active Brand Voice parameters"
            >
              🛡️ Brand Voice
            </button>
          </div>

          {/* 1. Content Type */}
          <div className={styles.formSection}>
            <span className={styles.stepLabel}>1. Content Type</span>
            <div className={styles.channelPills}>
              {CHANNELS.map((ch) => (
                <button
                  key={ch.value}
                  type="button"
                  className={
                    selectedChannel === ch.value ? styles.channelBtnActive : styles.channelBtn
                  }
                  onClick={() => setSelectedChannel(ch.value)}
                >
                  <span>{ch.icon}</span>
                  {ch.label}
                </button>
              ))}
            </div>
          </div>

          {/* 2. Marketing Context (Optional) */}
          <div className={styles.formSection}>
            <span className={styles.stepLabel}>2. Context (Optional)</span>
            <p className={styles.stepSubhint}>
              AI will use this context to create more relevant content.
            </p>

            <div className={styles.contextGrid}>
              <div className={styles.contextCol}>
                <label htmlFor="ai-context-campaign" className={styles.contextLabel}>
                  Campaign
                </label>
                <select
                  id="ai-context-campaign"
                  className={styles.selectInput}
                  value={selectedCampaignId}
                  onChange={(e) => setSelectedCampaignId(e.target.value)}
                >
                  {campaigns.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                  <option value="general">General / Ad-hoc</option>
                </select>
              </div>

              <div className={styles.contextCol}>
                <label htmlFor="ai-context-audience" className={styles.contextLabel}>
                  Audience
                </label>
                <select
                  id="ai-context-audience"
                  className={styles.selectInput}
                  value={selectedAudienceId}
                  onChange={(e) => setSelectedAudienceId(e.target.value)}
                >
                  {segments.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                  <option value="all">All Contacts</option>
                </select>
              </div>
            </div>

            {/* Context Informational Callout */}
            <div className={styles.contextCallout}>
              <span className={styles.calloutIcon}>✨</span>
              <span>
                AI will tailor the content based on your brand voice, audience and campaign goal.
              </span>
            </div>
          </div>

          {/* 3. What do you want to create? */}
          <div className={styles.formSection}>
            <label htmlFor="ai-copilot-prompt" className={styles.stepLabel}>
              3. What do you want to create?
            </label>
            <textarea
              id="ai-copilot-prompt"
              className={styles.promptTextarea}
              placeholder="e.g. Write a re-engagement email to win back inactive customers with a 20% discount offer."
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
            />

            {/* Quick Starter Chips */}
            <div className={styles.quickChipsRow}>
              {EXAMPLE_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  className={styles.chipBtn}
                  onClick={() =>
                    setPromptText(
                      `Write a high-impact ${chip.toLowerCase()} for ${
                        activeCampaign ? activeCampaign.name : "our campaign"
                      }`,
                    )
                  }
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Tone & Length Controls */}
            <div className={styles.paramsGrid}>
              <div className={styles.contextCol}>
                <label htmlFor="ai-tone-select" className={styles.contextLabel}>
                  Tone of Voice
                </label>
                <select
                  id="ai-tone-select"
                  className={styles.selectInput}
                  value={selectedTone}
                  onChange={(e) => setSelectedTone(e.target.value)}
                >
                  {TONE_OPTIONS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className={styles.contextCol}>
                <label htmlFor="ai-length-select" className={styles.contextLabel}>
                  Length
                </label>
                <select
                  id="ai-length-select"
                  className={styles.selectInput}
                  value={selectedLength}
                  onChange={(e) => setSelectedLength(e.target.value)}
                >
                  {LENGTH_OPTIONS.map((l) => (
                    <option key={l.value} value={l.value}>
                      {l.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 4. Variations Count */}
          <div className={styles.formSection}>
            <span className={styles.stepLabel}>4. Variations</span>
            <div className={styles.variationsButtonGroup}>
              {[1, 3, 5, 7].map((num) => (
                <button
                  key={num}
                  type="button"
                  className={
                    variationsCount === num ? styles.varNumberBtnActive : styles.varNumberBtn
                  }
                  onClick={() => setVariationsCount(num)}
                >
                  {num}
                </button>
              ))}
            </div>
          </div>

          {/* Primary Action Button */}
          <button
            type="button"
            className={styles.mainGenerateBtn}
            disabled={isGenerating || !promptText.trim() || !canManage}
            onClick={handleGenerate}
          >
            {isGenerating ? (
              <>⏳ Generating {variationsCount} variation(s)…</>
            ) : (
              <>✨ Generate {variationsCount} Variations</>
            )}
          </button>
          <div className={styles.btnCostFooter}>AI Credits: {variationsCount} ⓘ</div>
        </section>

        {/* =========================================================================
            RIGHT COLUMN: Top "Suggested for you" + Bottom "Generation History" (~70%)
            ========================================================================= */}
        <div className={styles.rightArea}>
          {/* =====================================================================
              Top: "Suggested for you" Card
              ===================================================================== */}
          <section className={styles.suggestedCard} aria-label="Quick starters">
            <div className={styles.suggestedHeader}>
              <div className={styles.suggestedTitleRow}>
                <span>✨</span>
                <h3 className={styles.suggestedTitle}>Quick Starters</h3>
                <span className={styles.suggestedSub}>
                  Ready-to-use prompt templates to get you started
                </span>
              </div>
            </div>

            {/* 4 Suggestions Grid */}
            <div className={styles.suggestedGrid}>
              {DEFAULT_SUGGESTIONS.map((sug) => {
                const tagClass =
                  sug.tagColor === "purple"
                    ? styles.tagPurple
                    : sug.tagColor === "blue"
                      ? styles.tagBlue
                      : sug.tagColor === "green"
                        ? styles.tagGreen
                        : styles.tagOrange;

                return (
                  <div
                    key={sug.id}
                    className={styles.suggestionItem}
                    onClick={() => handleSelectSuggestion(sug)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className={styles.suggestionItemHeader}>
                      <span className={styles.suggestionIcon}>
                        {sug.channel === "Social Post" ? "💼" : sug.channel === "SMS" ? "💬" : "✉️"}
                      </span>
                      <span className={styles.suggestionText}>
                        {sug.title} {sug.subtitle}
                      </span>
                    </div>
                    <span className={tagClass}>{sug.tag}</span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* =====================================================================
              Bottom: "Generation History" Section
              ===================================================================== */}
          <section className={styles.historySection} aria-label="Generation History">
            <div className={styles.historyToolbar}>
              {/* Filter Tabs */}
              <div className={styles.historyFilterTabs}>
                {["All", "Email", "Social", "SMS", "Ads", "Blog"].map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    className={
                      historyFilter === filter
                        ? styles.historyFilterTabActive
                        : styles.historyFilterTab
                    }
                    onClick={() => setHistoryFilter(filter)}
                  >
                    {filter}
                  </button>
                ))}
              </div>

              {/* Search & Time Filter */}
              <div className={styles.historyControlsRight}>
                <input
                  type="text"
                  placeholder="🔍 Search generations..."
                  className={styles.searchInput}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <select
                  className={styles.timeFilterSelect}
                  value={timeFilter}
                  onChange={(e) => setTimeFilter(e.target.value)}
                >
                  <option value="All Time">All Time</option>
                  <option value="Today">Today</option>
                  <option value="This Week">This Week</option>
                  <option value="This Month">This Month</option>
                </select>
              </div>
            </div>

            {/* Empty State */}
            {generations.length === 0 && (
              <div
                style={{
                  background: "#fff",
                  padding: "48px 24px",
                  borderRadius: "18px",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>✨</div>
                <h4
                  style={{
                    margin: 0,
                    fontSize: "16px",
                    fontWeight: 800,
                    color: "var(--color-dark-text, #0b1b33)",
                  }}
                >
                  Ready to create with AI
                </h4>
                <p
                  style={{
                    margin: "6px 0 0",
                    fontSize: "13px",
                    color: "var(--color-slate, #64748b)",
                  }}
                >
                  Select a suggestion above or enter a prompt on the left to generate content in
                  seconds.
                </p>
              </div>
            )}

            {/* Generated Items Group */}
            {visibleGenerations.length > 0 && (
              <div className={styles.generationGroup}>
                <div className={styles.groupHeaderRow}>
                  <div className={styles.groupHeaderLeft}>
                    <div className={styles.groupIconBadge}>
                      {selectedChannel === "Social Post" ? "💼" : "✉️"}
                    </div>
                    <div>
                      <h4 className={styles.groupTitle}>
                        {activeCampaign
                          ? `${selectedChannel} copy for ${activeCampaign.name}`
                          : "AI Generated Content"}
                      </h4>
                      <div style={{ display: "flex", gap: "10px", marginTop: "2px" }}>
                        <span className={styles.groupMetaTag}>@{selectedChannel}</span>
                        <span className={styles.groupMetaTag}>
                          🏷️ {activeCampaign ? activeCampaign.name : "General"}
                        </span>
                        <span className={styles.groupMetaTag}>
                          👥 {activeSegment ? activeSegment.name : "All Contacts"}
                        </span>
                      </div>
                    </div>
                  </div>
                  <span className={styles.groupTime}>
                    {formatRelativeTime(visibleGenerations[0]?.created_at)}
                  </span>
                </div>

                {/* Side-by-Side Variations Grid */}
                <div className={styles.variationsGrid}>
                  {visibleGenerations.map((item, idx) => {
                    const outputText = item.output?.text || "";

                    return (
                      <div key={`${item.id}-${idx}`} className={styles.variationCard}>
                        <div>
                          <div className={styles.variationCardHeader}>
                            <span className={styles.varNumberLabel}>Variation {idx + 1}</span>
                          </div>
                          <h5 className={styles.variationHeadline}>
                            {outputText.split("\n")[0] || `Variation ${idx + 1}`}
                          </h5>
                          <p className={styles.variationBody}>
                            {outputText.length > 220
                              ? `${outputText.substring(0, 220)}…`
                              : outputText}
                          </p>
                        </div>

                        <div>
                          {/* Action Toolbar */}
                          <div className={styles.cardActionsRow} style={{ marginTop: "12px" }}>
                            <button
                              type="button"
                              className={styles.useBtn}
                              onClick={() => handleUse(outputText, item.id)}
                            >
                              ✓ Use
                            </button>
                            <button
                              type="button"
                              className={styles.iconActionBtn}
                              title="Edit in prompt"
                              onClick={() => handleEdit(outputText)}
                            >
                              ✏️
                            </button>
                            <button
                              type="button"
                              className={styles.iconActionBtn}
                              title="Copy text"
                              onClick={() => handleUse(outputText, item.id)}
                            >
                              📋
                            </button>
                            {selectedChannel === "Email" && (
                              <button
                                type="button"
                                className={styles.iconActionBtn}
                                title="Add to Campaign"
                                onClick={() => handleAddToCampaign(outputText)}
                              >
                                ✉️
                              </button>
                            )}
                            {selectedChannel === "Social Post" && (
                              <button
                                type="button"
                                className={styles.iconActionBtn}
                                title="Schedule Social Post"
                                onClick={() => handleScheduleSocial(outputText)}
                              >
                                📱
                              </button>
                            )}
                            <button
                              type="button"
                              className={styles.iconActionBtn}
                              title="Save as Template"
                              onClick={() => handleSaveTemplate(outputText)}
                            >
                              💾
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>

      {/* =========================================================================
          3. Brand Voice Slide-Over Drawer
          ========================================================================= */}
      {isBrandDrawerOpen && (
        <div className={styles.drawerOverlay} onClick={() => setIsBrandDrawerOpen(false)}>
          <div className={styles.drawerPanel} onClick={(e) => e.stopPropagation()}>
            <div className={styles.drawerHeader}>
              <h3 className={styles.drawerTitle}>
                <span>🛡️</span> Active Brand Voice
              </h3>
              <button
                type="button"
                className={styles.closeDrawerBtn}
                onClick={() => setIsBrandDrawerOpen(false)}
              >
                ✕
              </button>
            </div>

            <div className={styles.brandVoiceField}>
              <span className={styles.brandFieldLabel}>Brand Name</span>
              <span className={styles.brandFieldValue}>
                {currentUser.company_name || "Growixa"}
              </span>
            </div>

            {brandProfileLoading ? (
              <div className={styles.brandVoiceField}>
                <span className={styles.brandFieldValue}>Loading brand profile…</span>
              </div>
            ) : (
              <>
                <div className={styles.brandVoiceField}>
                  <span className={styles.brandFieldLabel}>Brand Voice</span>
                  <span className={styles.brandFieldValue}>
                    {brandProfile?.brand_voice ||
                      "Not set yet — add your brand voice in Settings so every generation uses it automatically."}
                  </span>
                </div>

                <div className={styles.brandVoiceField}>
                  <span className={styles.brandFieldLabel}>Required Facts</span>
                  <span className={styles.brandFieldValue}>
                    {brandProfile?.required_facts?.length
                      ? brandProfile.required_facts.join(" • ")
                      : "None set."}
                  </span>
                </div>

                <div className={styles.brandVoiceField}>
                  <span className={styles.brandFieldLabel}>Forbidden Claims</span>
                  <span className={styles.brandFieldValue}>
                    {brandProfile?.forbidden_claims?.length
                      ? brandProfile.forbidden_claims.join(" • ")
                      : "None set."}
                  </span>
                </div>
              </>
            )}

            <Link
              href="/dashboard/company-settings"
              className={styles.editBrandLink}
              onClick={() => setIsBrandDrawerOpen(false)}
            >
              ⚙️ Edit Brand Profile in Settings →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function formatRelativeTime(isoTimestamp: string | undefined): string {
  if (!isoTimestamp) return "";
  const then = new Date(isoTimestamp).getTime();
  if (Number.isNaN(then)) return "";
  const diffSeconds = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (diffSeconds < 60) return "Just now";
  const diffMinutes = Math.round(diffSeconds / 60);
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  return new Date(isoTimestamp).toLocaleDateString();
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
