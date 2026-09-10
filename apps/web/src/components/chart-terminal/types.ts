export type Timeframe = "1H" | "24H" | "7D" | "30D" | "90D" | "1Y";

export type ChartMode = "candlestick" | "area" | "depth";

export type MetricKey =
  "GROWTH_VELOCITY" | "CONVERSION_DEPTH" | "DELIVERY_HEALTH" | "AUDIENCE_CAPITAL";

export type IndicatorKey = "ema" | "rsi" | "volume";

export interface CandleData {
  id: string;
  timestamp: string;
  label: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi: number;
  ema9?: number;
  ema21?: number;
}

export interface MetricConfig {
  key: MetricKey;
  label: string;
  symbol: string;
  unit: string;
  currentValue: string;
  change24h: string;
  isPositive: boolean;
  high24h: string;
  low24h: string;
  volume24h: string;
  description: string;
}

export interface TelemetryEvent {
  id: string;
  time: string;
  tag: string;
  label: string;
  value: string;
  status: "optimal" | "warning" | "bullish" | "neutral";
}

export interface TickerMetric {
  symbol: string;
  value: string;
  change: string;
  isPositive: boolean;
  note: string;
}
