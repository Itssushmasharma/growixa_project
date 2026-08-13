"use client";

import { useState } from "react";

import { useToast } from "@/components/toast/toast-context";
import { ApiError, apiFetch } from "@/lib/api-client";

import styles from "./ai-generate-button.module.css";

export type AICapability =
  "SUBJECT_LINE" | "BODY_COPY" | "SOCIAL_CAPTION" | "REWRITE" | "HASHTAGS" | "POSTING_TIME";

interface AIGenerationResponse {
  id: string;
  capability: AICapability;
  output: { text: string } | null;
  status: "COMPLETE" | "FAILED";
  error_message: string | null;
}

interface AIGenerateButtonProps {
  capability: AICapability;
  triggerLabel: string;
  briefPlaceholder: string;
  onInsert: (text: string) => void;
  linkedEntityType?: "campaign" | "social_post";
  linkedEntityId?: string;
}

/**
 * A "Generate with AI" affordance reused across composers (campaign subject/body,
 * social caption/hashtags). Always shows a suggestion for the caller to review and
 * click "Insert" — never auto-applies anything (DEC-GRX-006).
 */
export function AIGenerateButton({
  capability,
  triggerLabel,
  briefPlaceholder,
  onInsert,
  linkedEntityType,
  linkedEntityId,
}: AIGenerateButtonProps) {
  const { showToast } = useToast();
  const [open, setOpen] = useState(false);
  const [brief, setBrief] = useState("");
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function handleGenerate() {
    setGenerating(true);
    setResult(null);
    try {
      const response = await apiFetch<AIGenerationResponse>(`/ai/generate/${capability}`, {
        method: "POST",
        body: JSON.stringify({
          brief,
          linked_entity_type: linkedEntityType,
          linked_entity_id: linkedEntityId,
        }),
      });
      if (response.output?.text) {
        setResult(response.output.text);
      } else {
        showToast("error", "AI did not return any text — please try again.");
      }
    } catch (error) {
      showToast("error", parseAIError(error));
    } finally {
      setGenerating(false);
    }
  }

  function handleInsert() {
    if (!result) return;
    onInsert(result);
    setOpen(false);
    setResult(null);
    setBrief("");
    showToast("success", "Inserted the AI suggestion — review before saving.");
  }

  return (
    <div className={styles.wrapper}>
      <button type="button" className={styles.trigger} onClick={() => setOpen((prev) => !prev)}>
        ✨ {triggerLabel}
      </button>
      {open && (
        <div className={styles.panel}>
          <label className={styles.panelLabel} htmlFor={`ai-brief-${capability}`}>
            What should this be about?
          </label>
          <textarea
            id={`ai-brief-${capability}`}
            className={styles.panelTextarea}
            placeholder={briefPlaceholder}
            value={brief}
            onChange={(event) => setBrief(event.target.value)}
          />
          <button
            type="button"
            className={styles.generateButton}
            disabled={generating || !brief.trim()}
            onClick={handleGenerate}
          >
            {generating ? "Generating…" : "Generate"}
          </button>

          {result && (
            <div className={styles.resultBox}>
              <p className={styles.resultText}>{result}</p>
              <div className={styles.resultActions}>
                <button type="button" className={styles.insertButton} onClick={handleInsert}>
                  Insert
                </button>
                <button
                  type="button"
                  className={styles.regenerateButton}
                  disabled={generating}
                  onClick={handleGenerate}
                >
                  Regenerate
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function parseAIError(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: string };
      if (parsed.detail?.includes("No AI provider is configured")) {
        return "AI isn't configured yet — connect a provider under Integrations, or ask your platform admin.";
      }
      if (parsed.detail) return parsed.detail;
    } catch {
      // Keep fallback
    }
  }
  return "Could not generate content right now. Please try again.";
}
