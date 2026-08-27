import styles from "./components.module.css";

export const PERSONA_OPTIONS = [
  "Professional",
  "Confident",
  "Innovative",
  "Friendly",
  "Technical",
  "Authoritative",
  "Casual",
] as const;

interface BrandPersonaSelectorProps {
  selected: string[];
  disabled: boolean;
  onToggle: (persona: string) => void;
}

export function BrandPersonaSelector({ selected, disabled, onToggle }: BrandPersonaSelectorProps) {
  return (
    <div className={styles.personaGrid} role="group" aria-label="Brand persona">
      {PERSONA_OPTIONS.map((persona) => {
        const isSelected = selected.includes(persona);
        return (
          <button
            key={persona}
            type="button"
            disabled={disabled}
            aria-pressed={isSelected}
            className={`${styles.personaCard} ${isSelected ? styles.personaCardSelected : ""}`}
            onClick={() => onToggle(persona)}
          >
            {isSelected && (
              <span className={styles.personaCheck} aria-hidden="true">
                ✓
              </span>
            )}
            {persona}
          </button>
        );
      })}
    </div>
  );
}
