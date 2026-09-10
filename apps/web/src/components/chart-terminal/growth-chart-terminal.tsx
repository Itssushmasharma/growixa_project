"use client";

import React, { useState, useMemo, useRef, useCallback } from "react";
import styles from "./growth-chart-terminal.module.css";
import {
  Timeframe,
  ChartMode,
  MetricKey,
  IndicatorKey,
  CandleData,
  MetricConfig,
  TelemetryEvent,
  TickerMetric,
} from "./types";

// Live Ticker Data
const TICKER_ITEMS: TickerMetric[] = [
  {
    symbol: "GROWTH/USD",
    value: "$48.20K",
    change: "+24.8%",
    isPositive: true,
    note: "Bullish Breakout",
  },
  { symbol: "DELIVERY/SLO", value: "99.82%", change: "+0.14%", isPositive: true, note: "Optimal" },
  {
    symbol: "ENGAGE_RSI(14)",
    value: "68.40",
    change: "+5.2",
    isPositive: true,
    note: "Strong Momentum",
  },
  {
    symbol: "THROUGHPUT",
    value: "4,850/s",
    change: "+18.2%",
    isPositive: true,
    note: "Peak Sending",
  },
  {
    symbol: "CONV_VELOCITY",
    value: "4.82x",
    change: "+0.65x",
    isPositive: true,
    note: "Accelerating",
  },
  {
    symbol: "BOUNCE_INDEX",
    value: "0.14%",
    change: "-0.08%",
    isPositive: true,
    note: "Ultra Clean",
  },
  {
    symbol: "CAC/EFFICIENCY",
    value: "$12.40",
    change: "-18.5%",
    isPositive: true,
    note: "Max Margin",
  },
];

// Metric Configurations
const METRIC_CONFIGS: Record<MetricKey, MetricConfig> = {
  GROWTH_VELOCITY: {
    key: "GROWTH_VELOCITY",
    label: "Growth Velocity",
    symbol: "GRX/VEL",
    unit: "pts",
    currentValue: "2,845.60",
    change24h: "+28.4%",
    isPositive: true,
    high24h: "2,920.00",
    low24h: "2,180.40",
    volume24h: "1.42M",
    description: "Composite engine velocity tracking user acquisition & revenue velocity",
  },
  CONVERSION_DEPTH: {
    key: "CONVERSION_DEPTH",
    label: "Conversion Depth",
    symbol: "GRX/CVR",
    unit: "%",
    currentValue: "18.45%",
    change24h: "+4.12%",
    isPositive: true,
    high24h: "19.20%",
    low24h: "14.10%",
    volume24h: "850K",
    description: "Multi-stage funnel conversion rate from subscriber to paying customer",
  },
  DELIVERY_HEALTH: {
    key: "DELIVERY_HEALTH",
    label: "Delivery Telemetry",
    symbol: "GRX/DEL",
    unit: "%",
    currentValue: "99.85%",
    change24h: "+0.25%",
    isPositive: true,
    high24h: "99.98%",
    low24h: "99.20%",
    volume24h: "3.80M",
    description: "Strict SMTP inbox placement & DMARC/DKIM authentication health",
  },
  AUDIENCE_CAPITAL: {
    key: "AUDIENCE_CAPITAL",
    label: "Audience Capital",
    symbol: "GRX/AUD",
    unit: "subscribers",
    currentValue: "124,580",
    change24h: "+12.6%",
    isPositive: true,
    high24h: "125,100",
    low24h: "110,450",
    volume24h: "2.10M",
    description: "Compounded enterprise audience asset under management",
  },
};

// Deterministic candle data generator for each timeframe
function generateCandlesForTimeframe(timeframe: Timeframe, metric: MetricKey): CandleData[] {
  const count =
    timeframe === "1H"
      ? 24
      : timeframe === "24H"
        ? 24
        : timeframe === "7D"
          ? 28
          : timeframe === "30D"
            ? 30
            : 26;

  let basePrice = 2100;
  if (metric === "CONVERSION_DEPTH") basePrice = 14;
  if (metric === "DELIVERY_HEALTH") basePrice = 99.1;
  if (metric === "AUDIENCE_CAPITAL") basePrice = 98000;

  const volatility = basePrice * 0.035;
  const result: CandleData[] = [];
  let current = basePrice;

  for (let i = 0; i < count; i++) {
    const change = (Math.sin(i * 0.7) * 0.6 + (i / count) * 0.8) * volatility;
    const open = current;
    const close = open + change + Math.cos(i * 1.3) * volatility * 0.5;
    const high = Math.max(open, close) + Math.abs(Math.sin(i * 2.1)) * volatility * 0.6;
    const low = Math.min(open, close) - Math.abs(Math.cos(i * 2.1)) * volatility * 0.5;
    const volume = Math.round(15000 + Math.sin(i) * 8000 + i * 500);
    const rsi = Math.min(
      88,
      Math.max(28, Math.round(52 + Math.sin(i * 0.8) * 22 + (i / count) * 12)),
    );

    // Simple moving averages
    const ema9 = close * 0.98 + i * volatility * 0.05;
    const ema21 = close * 0.95 + i * volatility * 0.08;

    let label = `${i + 1}h`;
    if (timeframe === "7D") label = `Day ${(i % 7) + 1}`;
    if (timeframe === "30D") label = `D${i + 1}`;
    if (timeframe === "90D" || timeframe === "1Y") label = `W${i + 1}`;

    result.push({
      id: `candle-${i}`,
      timestamp: `T-${count - i}:00`,
      label,
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume,
      rsi,
      ema9: Number(ema9.toFixed(2)),
      ema21: Number(ema21.toFixed(2)),
    });

    current = close;
  }

  return result;
}

// Live simulated telemetry stream events
const INITIAL_TELEMETRY: TelemetryEvent[] = [
  {
    id: "t1",
    time: "14:02:18",
    tag: "CAMPAIGN_EXEC",
    label: "14,200 contacts dispatched",
    value: "200 OK (18ms)",
    status: "optimal",
  },
  {
    id: "t2",
    time: "14:02:14",
    tag: "AI_OPTIMIZER",
    label: "Subject line A/B uplift +22.4%",
    value: "Confidence 99.2%",
    status: "bullish",
  },
  {
    id: "t3",
    time: "14:02:09",
    tag: "DMARC_CHECK",
    label: "Postal Relay TLS 1.3 verified",
    value: "DKIM Validated",
    status: "optimal",
  },
  {
    id: "t4",
    time: "14:02:01",
    tag: "ENGAGEMENT_SPIKE",
    label: "Click rate anomaly on VIP Segment",
    value: "+14.8% spike",
    status: "bullish",
  },
  {
    id: "t5",
    time: "14:01:54",
    tag: "BOUNCE_GUARD",
    label: "0.04% soft bounce auto-retried",
    value: "Resolved",
    status: "optimal",
  },
  {
    id: "t6",
    time: "14:01:42",
    tag: "AUDIENCE_INGEST",
    label: "1,840 verified leads synced",
    value: "Postgres Scoped",
    status: "neutral",
  },
];

export interface GrowthChartTerminalProps {
  initialMetric?: MetricKey;
  initialTimeframe?: Timeframe;
  className?: string;
}

export const GrowthChartTerminal: React.FC<GrowthChartTerminalProps> = ({
  initialMetric = "GROWTH_VELOCITY",
  initialTimeframe = "24H",
  className = "",
}) => {
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>(initialMetric);
  const [selectedTimeframe, setSelectedTimeframe] = useState<Timeframe>(initialTimeframe);
  const [chartMode, setChartMode] = useState<ChartMode>("candlestick");
  const [indicators, setIndicators] = useState<Record<IndicatorKey, boolean>>({
    ema: true,
    rsi: true,
    volume: true,
  });
  const [hoveredCandle, setHoveredCandle] = useState<CandleData | null>(null);
  const [hoverCoords, setHoverCoords] = useState<{ x: number; y: number } | null>(null);

  const metricConfig = METRIC_CONFIGS[selectedMetric];

  // Candles memoized based on timeframe and metric
  const candles = useMemo(() => {
    return generateCandlesForTimeframe(selectedTimeframe, selectedMetric);
  }, [selectedTimeframe, selectedMetric]);

  // Coordinate math for SVG
  const svgRef = useRef<SVGSVGElement | null>(null);
  const stageWidth = 900;
  const stageHeight = 360;
  const padding = { top: 25, right: 65, bottom: 35, left: 15 };

  const chartArea = useMemo(
    () => ({
      width: stageWidth - padding.left - padding.right,
      height: stageHeight - padding.top - padding.bottom,
    }),
    [padding.left, padding.right, padding.top, padding.bottom],
  );

  const { minVal, priceRange } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    candles.forEach((c) => {
      if (c.low < min) min = c.low;
      if (c.high > max) max = c.high;
    });
    const pad = (max - min) * 0.08 || 1;
    return {
      minVal: min - pad,
      maxVal: max + pad,
      priceRange: max + pad - (min - pad),
    };
  }, [candles]);

  const getY = useCallback(
    (val: number) => {
      return padding.top + chartArea.height - ((val - minVal) / priceRange) * chartArea.height;
    },
    [padding.top, chartArea.height, minVal, priceRange],
  );

  const candleStep = chartArea.width / candles.length;

  const candleWidth = Math.max(4, candleStep * 0.65);

  // Path for Area Chart
  const areaPath = useMemo(() => {
    if (candles.length === 0) return "";
    let d = "";
    candles.forEach((c, idx) => {
      const x = padding.left + (idx + 0.5) * candleStep;
      const y = getY(c.close);
      if (idx === 0) d += `M ${x} ${y}`;
      else {
        const prevCandle = candles[idx - 1];
        if (prevCandle) {
          const prevX = padding.left + (idx - 0.5) * candleStep;
          const prevY = getY(prevCandle.close);
          const cp1x = prevX + (x - prevX) / 2;
          const cp2x = cp1x;
          d += ` C ${cp1x} ${prevY}, ${cp2x} ${y}, ${x} ${y}`;
        }
      }
    });
    return d;
  }, [candles, candleStep, getY, padding.left]);

  const areaClosedPath = useMemo(() => {
    if (!areaPath) return "";
    const lastX = padding.left + (candles.length - 0.5) * candleStep;
    const firstX = padding.left + 0.5 * candleStep;
    const bottomY = padding.top + chartArea.height;
    return `${areaPath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
  }, [areaPath, candles.length, candleStep, padding.left, padding.top, chartArea.height]);

  // Path for EMA 9 and EMA 21
  const ema9Path = useMemo(() => {
    if (!indicators.ema) return "";
    return candles.reduce((acc, c, idx) => {
      if (!c.ema9) return acc;
      const x = padding.left + (idx + 0.5) * candleStep;
      const y = getY(c.ema9);
      return acc === "" ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");
  }, [candles, candleStep, getY, indicators.ema, padding.left]);

  const ema21Path = useMemo(() => {
    if (!indicators.ema) return "";
    return candles.reduce((acc, c, idx) => {
      if (!c.ema21) return acc;
      const x = padding.left + (idx + 0.5) * candleStep;
      const y = getY(c.ema21);
      return acc === "" ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");
  }, [candles, candleStep, getY, indicators.ema, padding.left]);

  // Mouse move handler for interactive crosshair
  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    const scaleX = stageWidth / rect.width;
    const scaleY = stageHeight / rect.height;

    const svgX = clientX * scaleX;
    const svgY = clientY * scaleY;

    if (svgX < padding.left || svgX > stageWidth - padding.right) {
      setHoveredCandle(null);
      setHoverCoords(null);
      return;
    }

    const relX = svgX - padding.left;
    const candleIndex = Math.min(candles.length - 1, Math.max(0, Math.floor(relX / candleStep)));
    const candle = candles[candleIndex];

    if (candle) {
      setHoveredCandle(candle);
      setHoverCoords({
        x: padding.left + (candleIndex + 0.5) * candleStep,
        y: svgY,
      });
    } else {
      setHoveredCandle(null);
      setHoverCoords(null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredCandle(null);
    setHoverCoords(null);
  };

  const toggleIndicator = (ind: IndicatorKey) => {
    setIndicators((prev) => ({ ...prev, [ind]: !prev[ind] }));
  };

  return (
    <section
      className={`${styles.terminalContainer} ${className}`}
      aria-label="Growth Chart Terminal"
    >
      {/* 1. Live Ticker Ribbon */}
      <div className={styles.tickerRibbon}>
        <div className={styles.tickerPulseBadge}>
          <span className={styles.pulseDot} />
          <span>LIVE TELEMETRY</span>
        </div>
        {TICKER_ITEMS.map((item) => (
          <div key={item.symbol} className={styles.tickerItem}>
            <span className={styles.tickerSymbol}>{item.symbol}</span>
            <span className={styles.tickerVal}>{item.value}</span>
            <span className={item.isPositive ? styles.tickerUp : styles.tickerDown}>
              {item.change}
            </span>
          </div>
        ))}
      </div>

      {/* 2. Terminal Header & Controls */}
      <div className={styles.terminalHeader}>
        <div className={styles.assetInfoGroup}>
          <div className={styles.metricTabs} role="tablist">
            {(Object.keys(METRIC_CONFIGS) as MetricKey[]).map((key) => {
              const cfg = METRIC_CONFIGS[key];
              return (
                <button
                  key={key}
                  role="tab"
                  aria-selected={selectedMetric === key}
                  onClick={() => setSelectedMetric(key)}
                  className={`${styles.metricTabBtn} ${selectedMetric === key ? styles.metricTabBtnActive : ""}`}
                >
                  {cfg.label}
                </button>
              );
            })}
          </div>

          <div className={styles.statsRow}>
            <span className={styles.priceMain}>
              {hoveredCandle ? hoveredCandle.close.toLocaleString() : metricConfig.currentValue}
            </span>
            <span className={metricConfig.isPositive ? styles.priceBadgeUp : styles.priceBadgeDown}>
              {metricConfig.change24h}
            </span>
          </div>

          <div className={styles.statPills}>
            <span className={styles.statPillItem}>
              24h High: <strong>{metricConfig.high24h}</strong>
            </span>
            <span className={styles.statPillItem}>
              24h Low: <strong>{metricConfig.low24h}</strong>
            </span>
            <span className={styles.statPillItem}>
              Vol: <strong>{metricConfig.volume24h}</strong>
            </span>
          </div>
        </div>

        {/* Right Controls: Timeframe, Chart Mode, Indicators */}
        <div className={styles.controlCluster}>
          {/* Timeframe selector */}
          <div className={styles.timeframeGroup} role="group" aria-label="Timeframe">
            {(["1H", "24H", "7D", "30D", "90D", "1Y"] as Timeframe[]).map((tf) => (
              <button
                key={tf}
                onClick={() => setSelectedTimeframe(tf)}
                className={`${styles.timeframeBtn} ${selectedTimeframe === tf ? styles.timeframeBtnActive : ""}`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Mode Switcher */}
          <div className={styles.modeToggleGroup} role="group" aria-label="Chart Mode">
            <button
              onClick={() => setChartMode("candlestick")}
              className={`${styles.modeBtn} ${chartMode === "candlestick" ? styles.modeBtnActive : ""}`}
              title="Candlestick OHLC View"
            >
              Candle
            </button>
            <button
              onClick={() => setChartMode("area")}
              className={`${styles.modeBtn} ${chartMode === "area" ? styles.modeBtnActive : ""}`}
              title="Area Trend View"
            >
              Area
            </button>
          </div>

          {/* Indicator toggles */}
          <div className={styles.indicatorChips}>
            <button
              onClick={() => toggleIndicator("ema")}
              className={`${styles.indChip} ${indicators.ema ? styles.indChipActive : ""}`}
              title="Exponential Moving Averages (EMA 9/21)"
            >
              EMA 9/21
            </button>
            <button
              onClick={() => toggleIndicator("rsi")}
              className={`${styles.indChip} ${indicators.rsi ? styles.indChipActive : ""}`}
              title="RSI 14 Momentum"
            >
              RSI (14)
            </button>
            <button
              onClick={() => toggleIndicator("volume")}
              className={`${styles.indChip} ${indicators.volume ? styles.indChipActive : ""}`}
              title="Send Volume Histogram"
            >
              Volume
            </button>
          </div>
        </div>
      </div>

      {/* 3. Main Chart Canvas Stage */}
      <div className={styles.chartCanvasStage}>
        <svg
          ref={svgRef}
          viewBox={`0 0 ${stageWidth} ${stageHeight}`}
          preserveAspectRatio="none"
          className={styles.chartSvg}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          <defs>
            <linearGradient id="areaGlowGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
              <stop offset="60%" stopColor="#0284c7" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0.0" />
            </linearGradient>
            <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Horizontal Gridlines & Price Ticks */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct) => {
            const y = padding.top + chartArea.height * (1 - pct);
            const val = minVal + priceRange * pct;
            return (
              <g key={`grid-${pct}`}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={stageWidth - padding.right}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.07)"
                  strokeDasharray="4 4"
                />
                <text
                  x={stageWidth - padding.right + 8}
                  y={y + 4}
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="ui-monospace, monospace"
                  textAnchor="start"
                >
                  {val.toFixed(metricConfig.unit === "%" ? 2 : 0)}
                </text>
              </g>
            );
          })}

          {/* Volume Histogram Bars (at bottom of main stage) */}
          {indicators.volume && (
            <g opacity="0.35">
              {candles.map((c, idx) => {
                const x = padding.left + (idx + 0.5) * candleStep - candleWidth * 0.45;
                const maxVol = 30000;
                const barH = (c.volume / maxVol) * (chartArea.height * 0.22);
                const barY = padding.top + chartArea.height - barH;
                const isBullish = c.close >= c.open;
                return (
                  <rect
                    key={`vol-${c.id}`}
                    x={x}
                    y={barY}
                    width={candleWidth * 0.9}
                    height={barH}
                    fill={isBullish ? "#10b981" : "#f43f5e"}
                    rx="1"
                  />
                );
              })}
            </g>
          )}

          {/* Area Mode Rendering */}
          {chartMode === "area" && (
            <>
              <path d={areaClosedPath} fill="url(#areaGlowGrad)" />
              <path
                d={areaPath}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2.5"
                filter="url(#lineGlow)"
              />
            </>
          )}

          {/* Candlestick Mode Rendering */}
          {chartMode === "candlestick" && (
            <g>
              {candles.map((c, idx) => {
                const centerX = padding.left + (idx + 0.5) * candleStep;
                const highY = getY(c.high);
                const lowY = getY(c.low);
                const openY = getY(c.open);
                const closeY = getY(c.close);
                const isBullish = c.close >= c.open;
                const bodyTop = Math.min(openY, closeY);
                const bodyHeight = Math.max(2, Math.abs(closeY - openY));
                const color = isBullish ? "#10b981" : "#f43f5e";

                return (
                  <g key={c.id}>
                    {/* Wick Line */}
                    <line
                      x1={centerX}
                      y1={highY}
                      x2={centerX}
                      y2={lowY}
                      stroke={color}
                      strokeWidth="1.2"
                      opacity="0.85"
                    />
                    {/* Candle Body */}
                    <rect
                      x={centerX - candleWidth / 2}
                      y={bodyTop}
                      width={candleWidth}
                      height={bodyHeight}
                      fill={color}
                      stroke={color}
                      strokeWidth="0.5"
                      rx="1"
                    />
                  </g>
                );
              })}
            </g>
          )}

          {/* Moving Averages: EMA 9 & EMA 21 */}
          {indicators.ema && (
            <>
              <path
                d={ema9Path}
                fill="none"
                stroke="#38bdf8"
                strokeWidth="1.6"
                strokeDasharray="2 2"
                opacity="0.8"
              />
              <path d={ema21Path} fill="none" stroke="#f59e0b" strokeWidth="1.6" opacity="0.75" />
            </>
          )}

          {/* Interactive Crosshair & Hover Markers */}
          {hoverCoords && (
            <g>
              {/* Vertical tracking line */}
              <line
                x1={hoverCoords.x}
                y1={padding.top}
                x2={hoverCoords.x}
                y2={padding.top + chartArea.height}
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="3 3"
                opacity="0.8"
              />
              {/* Horizontal tracking line */}
              <line
                x1={padding.left}
                y1={hoverCoords.y}
                x2={stageWidth - padding.right}
                y2={hoverCoords.y}
                stroke="#38bdf8"
                strokeWidth="1"
                strokeDasharray="3 3"
                opacity="0.8"
              />
              {/* Target dot on candle close */}
              {hoveredCandle && (
                <circle
                  cx={hoverCoords.x}
                  cy={getY(hoveredCandle.close)}
                  r="4"
                  fill="#38bdf8"
                  stroke="#ffffff"
                  strokeWidth="2"
                  filter="url(#lineGlow)"
                />
              )}
            </g>
          )}

          {/* X-axis labels */}
          {candles
            .filter((_, idx) => idx % Math.ceil(candles.length / 7) === 0)
            .map((c, idx) => {
              const originalIndex = candles.findIndex((item) => item.id === c.id);
              const x = padding.left + (originalIndex + 0.5) * candleStep;
              return (
                <text
                  key={`label-${idx}`}
                  x={x}
                  y={stageHeight - 12}
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="ui-monospace, monospace"
                  textAnchor="middle"
                >
                  {c.label}
                </text>
              );
            })}
        </svg>

        {/* Floating Tooltip Card */}
        {hoveredCandle && hoverCoords && (
          <div
            className={styles.floatingTooltip}
            style={{
              left: `${(hoverCoords.x / stageWidth) * 100}%`,
              top: `${(getY(hoveredCandle.close) / stageHeight) * 100}%`,
            }}
          >
            <div className={styles.tooltipHeader}>
              <span>{hoveredCandle.timestamp}</span>
              <span>{metricConfig.symbol}</span>
            </div>
            <div className={styles.tooltipRow}>
              <span>Open:</span>
              <strong>{hoveredCandle.open}</strong>
            </div>
            <div className={styles.tooltipRow}>
              <span>High:</span>
              <strong>{hoveredCandle.high}</strong>
            </div>
            <div className={styles.tooltipRow}>
              <span>Low:</span>
              <strong>{hoveredCandle.low}</strong>
            </div>
            <div className={styles.tooltipRow}>
              <span>Close:</span>
              <strong
                style={{ color: hoveredCandle.close >= hoveredCandle.open ? "#34d399" : "#fb7185" }}
              >
                {hoveredCandle.close}
              </strong>
            </div>
            <div className={styles.tooltipRow}>
              <span>Volume:</span>
              <strong>{hoveredCandle.volume.toLocaleString()}</strong>
            </div>
            <div className={styles.tooltipRow}>
              <span>RSI(14):</span>
              <strong
                style={{
                  color:
                    hoveredCandle.rsi > 70
                      ? "#fb7185"
                      : hoveredCandle.rsi < 30
                        ? "#34d399"
                        : "#c084fc",
                }}
              >
                {hoveredCandle.rsi}
              </strong>
            </div>
          </div>
        )}
      </div>

      {/* 4. Lower Analytical Workstation: Sub-Panels + Live Telemetry Stream */}
      <div className={styles.analyticalWorkstation}>
        <div className={styles.subPanelsArea}>
          {/* RSI Sub-Panel */}
          {indicators.rsi && (
            <div className={styles.indicatorSubPanel}>
              <div className={styles.subPanelTitleBar}>
                <span>RSI(14) Momentum Oscillator</span>
                <span className={styles.rsiBadge}>
                  Current:{" "}
                  {hoveredCandle ? hoveredCandle.rsi : candles[candles.length - 1]?.rsi || 64}
                </span>
              </div>
              <svg viewBox="0 0 500 50" preserveAspectRatio="none" className={styles.rsiCanvas}>
                {/* Overbought 70 line */}
                <line
                  x1="0"
                  y1="15"
                  x2="500"
                  y2="15"
                  stroke="rgba(244, 63, 94, 0.4)"
                  strokeDasharray="3 3"
                />
                {/* Oversold 30 line */}
                <line
                  x1="0"
                  y1="35"
                  x2="500"
                  y2="35"
                  stroke="rgba(16, 185, 129, 0.4)"
                  strokeDasharray="3 3"
                />
                {/* RSI Line */}
                <path
                  d={candles.reduce((acc, c, idx) => {
                    const x = (idx / (candles.length - 1)) * 500;
                    const y = 50 - ((c.rsi - 20) / 70) * 50;
                    return acc === "" ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
                  }, "")}
                  fill="none"
                  stroke="#c084fc"
                  strokeWidth="2"
                />
              </svg>
            </div>
          )}
        </div>

        {/* Live Telemetry Execution Feed */}
        <div className={styles.telemetryDrawer}>
          <div className={styles.telemetryTitle}>
            <span>Event Telemetry Stream</span>
            <span className={styles.streamBadge}>ONLINE ●</span>
          </div>
          <div className={styles.telemetryStreamList}>
            {INITIAL_TELEMETRY.map((evt) => (
              <div key={evt.id} className={styles.telemetryItem} data-status={evt.status}>
                <div>
                  <span className={styles.telemetryTime}>{evt.time}</span>
                  <span className={styles.telemetryTag}>{evt.tag}:</span>
                  <span style={{ marginLeft: "0.3rem", color: "#94a3b8" }}>{evt.label}</span>
                </div>
                <span className={styles.telemetryVal}>{evt.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. Institutional Quant Cards Grid */}
      <div className={styles.quantCardsGrid}>
        <div className={styles.quantCard}>
          <div className={styles.quantLabel}>Sharpe Growth Ratio</div>
          <div className={styles.quantValue}>3.48x</div>
          <div className={styles.quantSub}>Tier-1 Top Decile</div>
        </div>
        <div className={styles.quantCard}>
          <div className={styles.quantLabel}>Delivery Alpha</div>
          <div className={styles.quantValue}>+18.4%</div>
          <div className={styles.quantSub}>vs Industry Baseline</div>
        </div>
        <div className={styles.quantCard}>
          <div className={styles.quantLabel}>CAC Velocity Delta</div>
          <div className={styles.quantValue}>-$14.80</div>
          <div className={styles.quantSub}>Margin Efficiency Up</div>
        </div>
        <div className={styles.quantCard}>
          <div className={styles.quantLabel}>Conversion Confidence</div>
          <div className={styles.quantValue}>94.2%</div>
          <div className={styles.quantSub}>Statistical Significance</div>
        </div>
      </div>
    </section>
  );
};
