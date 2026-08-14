import styles from "./trend-chart.module.css";

export interface TrendChartPoint {
  label: string;
  value: number;
}

interface TrendChartProps {
  points: TrendChartPoint[];
  height?: number;
}

// Native SVG, no charting library dependency (OQ-DSH-001 in the dashboards plan defaulted
// to this option, to avoid adding an unconfirmed dependency for a fixed-length series).
export function TrendChart({ points, height = 120 }: TrendChartProps) {
  if (points.length === 0) {
    return null;
  }

  const width = 100;
  const values = points.map((p) => p.value);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const stepX = points.length > 1 ? width / (points.length - 1) : 0;

  const coords = points.map((point, i) => ({
    x: i * stepX,
    y: height - ((point.value - min) / range) * height,
  }));

  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x},${c.y}`).join(" ");
  const lastCoord = coords[coords.length - 1];
  const firstCoord = coords[0];
  const areaPath =
    lastCoord && firstCoord
      ? `${linePath} L${lastCoord.x},${height} L${firstCoord.x},${height} Z`
      : "";

  return (
    <div className={styles.wrap}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className={styles.svg}
        role="img"
        aria-label="Trend over time"
      >
        <path d={areaPath} className={styles.area} />
        <path d={linePath} className={styles.line} />
      </svg>
      <div className={styles.labels}>
        {points.map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
    </div>
  );
}
