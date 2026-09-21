"use client";

import React, { useState } from "react";
import { Sparkles, Palette, Download, Image as ImageIcon, Layout, Layers, Check } from "lucide-react";
import styles from "./creative-studio.module.css";

const PRESETS = [
  { id: "instagram_post", name: "Instagram Post", size: "1080 x 1080", aspect: "1:1" },
  { id: "story_reel", name: "Story / Reel", size: "1080 x 1920", aspect: "9:16" },
  { id: "facebook_ad", name: "Facebook Ad", size: "1200 x 628", aspect: "1.91:1" },
  { id: "linkedin_banner", name: "LinkedIn Banner", size: "1584 x 396", aspect: "4:1" },
  { id: "flyer_poster", name: "Flyer / Poster", size: "1200 x 1600", aspect: "3:4" },
  { id: "business_card", name: "Business Card", size: "1050 x 600", aspect: "1.75:1" },
];

export default function CreativeStudioPage() {
  const [selectedPreset, setSelectedPreset] = useState("instagram_post");
  const [prompt, setPrompt] = useState("Modern tech software product launch banner with glowing burgundy accents");
  const [headline, setHeadline] = useState("Accelerate Your GTM Execution");
  const [ctaText, setCtaText] = useState("Start Free Trial →");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedResult, setGeneratedResult] = useState<{
    headline: string;
    cta_text: string;
    captions: string[];
  } | null>(null);

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setGeneratedResult({
        headline: headline || "Accelerate Your GTM Execution",
        cta_text: ctaText || "Start Free Trial →",
        captions: [
          `🔥 ${headline} — Transform your GTM campaign with Growixa AI studio. Click link in bio!`,
          `✨ Ready to scale? ${headline} Learn how our automated workflow delivers results.`,
          `🚀 ${headline}. Built for modern growth teams. #growwithgrowixa #digitalmarketing`
        ],
      });
      setIsGenerating(false);
    }, 1200);
  };

  const currentPresetObj = PRESETS.find((p) => p.id === selectedPreset) || PRESETS[0];

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}><Sparkles className="w-3.5 h-3.5" /> AI Creative Studio</span>
          <h1 className={styles.title}>Social &amp; Ad Creative Generator</h1>
          <p className={styles.subtitle}>
            Design AI social posts, banners, flyers, ad creatives, reels, and business cards tuned to your brand kit.
          </p>
        </div>

        <div className={styles.brandKitBadge}>
          <Palette className="w-4 h-4 text-rose-700" />
          <span>Brand Kit: <strong>Growixa Burgundy (#6D0626)</strong></span>
        </div>
      </header>

      {/* Main Studio Workspace */}
      <div className={styles.workspaceGrid}>
        {/* Left Config Panel */}
        <div className={styles.configCard}>
          <h2 className={styles.panelTitle}><Layout className="w-4 h-4" /> 1. Select Dimension Preset</h2>
          <div className={styles.presetGrid}>
            {PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`${styles.presetBtn} ${selectedPreset === p.id ? styles.presetBtnActive : ""}`}
                onClick={() => setSelectedPreset(p.id)}
              >
                <div className={styles.presetName}>{p.name}</div>
                <div className={styles.presetSize}>{p.size} ({p.aspect})</div>
              </button>
            ))}
          </div>

          <h2 className={styles.panelTitle} style={{ marginTop: 24 }}>
            <Sparkles className="w-4 h-4" /> 2. AI Creative Prompt &amp; Copy
          </h2>
          
          <div className={styles.inputGroup}>
            <label className={styles.label}>Creative Prompt</label>
            <textarea
              className={styles.textarea}
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your desired creative background & mood..."
            />
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>Main Headline Text</label>
            <input
              type="text"
              className={styles.input}
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="e.g. Accelerate Your GTM Execution"
            />
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.label}>CTA Button Label</label>
            <input
              type="text"
              className={styles.input}
              value={ctaText}
              onChange={(e) => setCtaText(e.target.value)}
              placeholder="e.g. Start Free Trial →"
            />
          </div>

          <button
            type="button"
            className={styles.generateBtn}
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating Creative..." : "✦ Generate AI Creative Canvas"}
          </button>
        </div>

        {/* Right Canvas Preview Panel */}
        <div className={styles.canvasCard}>
          <div className={styles.canvasHeader}>
            <div className={styles.canvasTitleRow}>
              <ImageIcon className="w-4 h-4 text-rose-700" />
              <span>Canvas Preview — <strong>{currentPresetObj?.name ?? "Preset"}</strong></span>
            </div>
            <button type="button" className={styles.exportBtn}>
              <Download className="w-4 h-4" /> Export Preset ({currentPresetObj?.size ?? "1080x1080"})
            </button>
          </div>

          {/* Interactive Visual Canvas Box */}
          <div className={styles.canvasBox} style={{ aspectRatio: currentPresetObj?.aspect === "1:1" ? "1/1" : currentPresetObj?.aspect === "9:16" ? "9/16" : "1.91/1" }}>
            <div className={styles.canvasGlow} aria-hidden="true" />
            <span className={styles.canvasBadge}>GROWIXA AI CANVAS</span>

            <div className={styles.canvasContent}>
              <span className={styles.canvasEyebrow}>BRAND POWERED</span>
              <h2 className={styles.canvasHeadline}>
                {headline || "Your Creative Headline Here"}
              </h2>
              <p className={styles.canvasDesc}>
                {prompt ? prompt.slice(0, 90) + "..." : "AI generated visual background asset preview."}
              </p>
              <div className={styles.canvasCtaBtn}>
                {ctaText || "Click Here →"}
              </div>
            </div>
          </div>

          {/* Suggested Social Captions */}
          {generatedResult && (
            <div className={styles.captionBox}>
              <h3 className={styles.captionTitle}><Layers className="w-4 h-4 text-rose-700" /> Suggested AI Social Captions</h3>
              <div className={styles.captionList}>
                {generatedResult.captions.map((cap, i) => (
                  <div key={i} className={styles.captionItem}>
                    <span>{cap}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
