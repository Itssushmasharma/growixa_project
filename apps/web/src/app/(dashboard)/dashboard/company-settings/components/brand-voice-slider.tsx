import styles from "./components.module.css";

interface BrandVoiceSliderProps {
  id: string;
  label: string;
  leftLabel: string;
  rightLabel: string;
  value: number;
  disabled: boolean;
  onChange: (value: number) => void;
}

export function BrandVoiceSlider({
  id,
  label,
  leftLabel,
  rightLabel,
  value,
  disabled,
  onChange,
}: BrandVoiceSliderProps) {
  return (
    <div className={styles.sliderRow}>
      <div className={styles.sliderHeader}>
        <label className={styles.sliderLabel} htmlFor={id}>
          {label}
        </label>
        <span className={styles.sliderValue}>{value}</span>
      </div>
      <input
        id={id}
        type="range"
        min={0}
        max={100}
        step={5}
        value={value}
        disabled={disabled}
        className={styles.sliderInput}
        aria-valuetext={`${value} out of 100, ${leftLabel} to ${rightLabel}`}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <div className={styles.sliderEnds}>
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
    </div>
  );
}
