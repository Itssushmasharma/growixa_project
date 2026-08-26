import { useEffect, useRef } from "react";

import styles from "./components.module.css";

interface GuardrailListProps {
  title: string;
  addLabel: string;
  icon: "forbidden" | "required";
  items: string[];
  disabled: boolean;
  emptyHint: string;
  onChange: (items: string[]) => void;
}

/**
 * Structured editable rule list backing a `string[]` field (forbidden_claims /
 * required_facts) that is already stored as a real JSONB list on the API side — this
 * only changes how it's edited, not the wire format (GRX-COMPANY-003).
 */
export function GuardrailList({
  title,
  addLabel,
  icon,
  items,
  disabled,
  emptyHint,
  onChange,
}: GuardrailListProps) {
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const justAddedIndex = useRef<number | null>(null);

  // A freshly added row starts empty, so typing has to land in it immediately —
  // otherwise "+ Add claim" silently does nothing from the user's perspective
  // (reported: keystrokes went nowhere because focus never moved into the new row).
  useEffect(() => {
    if (justAddedIndex.current === null) return;
    inputRefs.current[justAddedIndex.current]?.focus();
    justAddedIndex.current = null;
  }, [items.length]);

  function updateItem(index: number, value: string) {
    const next = [...items];
    next[index] = value;
    onChange(next);
  }

  function removeItem(index: number) {
    onChange(items.filter((_, i) => i !== index));
  }

  function addItem() {
    justAddedIndex.current = items.length;
    onChange([...items, ""]);
  }

  const iconGlyph = icon === "forbidden" ? "⊘" : "✓";
  const iconClass =
    icon === "forbidden" ? styles.guardrailIconForbidden : styles.guardrailIconRequired;

  return (
    <div className={styles.field}>
      <div className={styles.guardrailHeader}>
        <span className={styles.label}>{title}</span>
        <button type="button" className={styles.guardrailAdd} disabled={disabled} onClick={addItem}>
          + {addLabel}
        </button>
      </div>

      {items.length === 0 ? (
        <p className={styles.guardrailEmpty}>{emptyHint}</p>
      ) : (
        <ul className={styles.guardrailList}>
          {items.map((item, index) => (
            // Index-keyed is safe here: rows are only ever appended/removed by this
            // same list, never reordered independently of their position.
            <li key={index} className={styles.guardrailItem}>
              <span className={iconClass} aria-hidden="true">
                {iconGlyph}
              </span>
              <input
                ref={(element) => {
                  inputRefs.current[index] = element;
                }}
                type="text"
                className={styles.guardrailInput}
                value={item}
                disabled={disabled}
                aria-label={`${title} ${index + 1}`}
                onChange={(event) => updateItem(index, event.target.value)}
              />
              {!disabled && (
                <button
                  type="button"
                  className={styles.guardrailRemove}
                  aria-label={`Remove ${title.toLowerCase()} ${index + 1}`}
                  onClick={() => removeItem(index)}
                >
                  ×
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
