import styles from "./trend-chart.module.css";

export interface TrendChartPoint {
  label: string;
  value: number;
}

interface TrendChartProps {
  points: TrendChartPoint[];
  height?: number;
  valueFormatter?: (value: number) => string;
}

const GRIDLINE_COUNT = 4;

// Native SVG, no charting library dependency (OQ-DSH-001 in the dashboards plan defaulted
// to this option, to avoid adding an unconfirmed dependency for a fixed-length series).
export function TrendChart({ points, height = 240, valueFormatter }: TrendChartProps) {
  if (points.length === 0) {
    return null;
  }

  const width = 600;
  const paddingTop = 16;
  const paddingBottom = 8;
  const plotHeight = height - paddingTop - paddingBottom;

  const values = points.map((p) => p.value);
  const rawMax = Math.max(...values, 1);
  const max = rawMax === 0 ? 1 : rawMax;
  const min = 0;
  const range = max - min || 1;
  const stepX = points.length > 1 ? width / (points.length - 1) : 0;

  const yFor = (value: number) => paddingTop + plotHeight - ((value - min) / range) * plotHeight;

  const coords = points.map((point, i) => ({
    x: i * stepX,
    y: yFor(point.value),
    value: point.value,
    label: point.label,
  }));

  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"}${c.x},${c.y}`).join(" ");
  const lastCoord = coords[coords.length - 1];
  const firstCoord = coords[0];
  const areaPath =
    lastCoord && firstCoord
      ? `${linePath} L${lastCoord.x},${height - paddingBottom} L${firstCoord.x},${height - paddingBottom} Z`
      : "";

  const gridlines = Array.from({ length: GRIDLINE_COUNT + 1 }, (_, i) => {
    const fraction = i / GRIDLINE_COUNT;
    const value = min + range * (1 - fraction);
    const y = paddingTop + plotHeight * fraction;
    return { y, value };
  });

  const format = valueFormatter ?? ((value: number) => value.toLocaleString());
  const gradientId = "trend-chart-gradient";

  return (
    <div className={styles.wrap}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        className={styles.svg}
        role="img"
        aria-label="Trend over time"
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" className={styles.gradientStart} />
            <stop offset="100%" className={styles.gradientEnd} />
          </linearGradient>
        </defs>

        {gridlines.map((grid) => (
          <g key={grid.y}>
            <line
              x1={0}
              x2={width}
              y1={grid.y}
              y2={grid.y}
              className={styles.gridline}
              vectorEffect="non-scaling-stroke"
            />
            <text x={4} y={grid.y - 4} className={styles.gridLabel}>
              {format(Math.round(grid.value))}
            </text>
          </g>
        ))}

        <path d={areaPath} fill={`url(#${gradientId})`} className={styles.area} />
        <path d={linePath} className={styles.line} vectorEffect="non-scaling-stroke" />

        {coords.map((c) => (
          <circle
            key={c.label}
            cx={c.x}
            cy={c.y}
            r={4}
            className={styles.point}
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
      <div className={styles.labels}>
        {points.map((point) => (
          <span key={point.label}>{point.label}</span>
        ))}
      </div>
    </div>
  );
}
