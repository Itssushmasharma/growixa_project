"use client";

import { useState } from "react";

import type { AICapability } from "@/components/ai/ai-generate-button";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./components.module.css";

interface PreviewType {
  id: string;
  label: string;
  capability: AICapability;
  brief: string;
}

const PREVIEW_TYPES: PreviewType[] = [
  {
    id: "cold-outreach",
    label: "Cold Outreach Email",
    capability: "BODY_COPY",
    brief: "A cold outreach email introducing our company to a prospective customer.",
  },
  {
    id: "marketing-email",
    label: "Marketing Email",
    capability: "BODY_COPY",
    brief: "A marketing email announcing our latest offering to our existing audience.",
  },
  {
    id: "social-post",
    label: "Social Post",
    capability: "SOCIAL_CAPTION",
    brief: "A short social media caption promoting our product.",
  },
  {
    id: "product-copy",
    label: "Product Copy",
    capability: "BODY_COPY",
    brief: "Short marketing copy describing our product's core value.",
  },
];

interface AIGenerationResponse {
  output: { text: string } | null;
  status: "COMPLETE" | "FAILED";
}

interface AICopyPreviewProps {
  forbiddenClaims: string[];
}

/**
 * Uses the real POST /ai/generate/{capability} endpoint (the same one production
 * composers call) -- there is no separate "preview" API. Guardrail-compliance is a real
 * client-side check against the account's actual forbidden_claims; tone/readability
 * scores are deliberately NOT shown here since nothing in the API computes them
 * (GRX-QA-001 found fabricated AI scores shipped once before -- not repeating that).
 */
export function AICopyPreview({ forbiddenClaims }: AICopyPreviewProps) {
  const [selectedId, setSelectedId] = useState(PREVIEW_TYPES[0]!.id);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedType = PREVIEW_TYPES.find((type) => type.id === selectedId) ?? PREVIEW_TYPES[0]!;

  async function handleGenerate() {
    setGenerating(true);
    setResult(null);
    setError(null);
    setNotConfigured(false);
    try {
      const response = await apiFetch<AIGenerationResponse>(
        `/ai/generate/${selectedType.capability}`,
        { method: "POST", body: JSON.stringify({ brief: selectedType.brief }) },
      );
      if (response.output?.text) {
        setResult(response.output.text);
      } else {
        setError("AI did not return any text — please try again.");
      }
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 409) {
        setNotConfigured(true);
      } else {
        setError("Could not generate a preview right now. Please try again.");
      }
    } finally {
      setGenerating(false);
    }
  }

  const detectedClaims = result
    ? forbiddenClaims.filter(
        (claim) => claim.trim().length > 0 && result.toLowerCase().includes(claim.toLowerCase()),
      )
    : [];

  return (
    <div className={styles.field}>
      <div className={styles.previewToolbar}>
        <select
          className={styles.previewSelect}
          value={selectedId}
          onChange={(event) => {
            setSelectedId(event.target.value);
            setResult(null);
            setError(null);
            setNotConfigured(false);
          }}
          aria-label="Preview type"
        >
          {PREVIEW_TYPES.map((type) => (
            <option key={type.id} value={type.id}>
              {type.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className={styles.previewGenerate}
          disabled={generating}
          onClick={handleGenerate}
        >
          {generating ? "Generating…" : "Generate preview"}
        </button>
      </div>

      <div className={styles.previewBody}>
        {generating && <p className={styles.previewPlaceholder}>Generating with AI…</p>}
        {!generating && notConfigured && (
          <div className={styles.previewPlaceholder}>
            <span>No AI provider is connected for this account yet.</span>
            <span>Connect one under Integrations to generate a real preview.</span>
          </div>
        )}
        {!generating && error && <p className={styles.previewPlaceholder}>{error}</p>}
        {!generating && !notConfigured && !error && !result && (
          <p className={styles.previewPlaceholder}>
            Select a content type and generate a preview using your current brand settings.
          </p>
        )}
        {!generating && result && <p className={styles.previewText}>{result}</p>}
      </div>

      {result && (
        <div className={styles.previewMetaRow}>
          {detectedClaims.length === 0 ? (
            <span className={`${styles.previewMetaItem} ${styles.previewMetaOk}`}>
              ✓ No prohibited claims detected
            </span>
          ) : (
            <span className={`${styles.previewMetaItem} ${styles.previewMetaWarn}`}>
              ⚠ Contains forbidden claim: &quot;{detectedClaims[0]}&quot;
            </span>
          )}
        </div>
      )}
    </div>
  );
}
