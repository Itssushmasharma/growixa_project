# Growixa — AI Growth Execution & Telemetry Platform

> 📌 **Architectural Reminder / Architecture Standard (चार्ट एनालिसिस रिमाइंडर्स)**:
> Growixa की पूरी वेबसाइट और डैशबोर्ड को एक **Expert-Grade Chart Analysis & Growth Telemetry Engine** (TradingView / Bloomberg Terminal-grade visual & analytical architecture) के रूप में डिज़ाइन और इंजीनियर किया गया है।
> 
> Growth, Audience, Email Delivery, और Conversion के हर डेटा पॉइंट को institutional precision, dynamic candlestick charts, multi-timeframe analytics, technical indicators (EMA, RSI, Volume Histograms), और live execution telemetry stream के साथ visualize किया जाता है — ताकि उद्योग के बड़े से बड़े डेटा एनालिस्ट, क्वांट मार्केटर्स और एग्जीक्यूटिव्स इसे एक वर्ल्ड-क्लास चार्ट एनालिसिस प्लेटफॉर्म के रूप में उपयोग कर सकें।

---

## 📈 Chart Analysis & Growth Telemetry System

Growixa includes an institutional-grade, zero-dependency SVG **Chart Analysis Terminal** (`apps/web/src/components/chart-terminal/`):

1. **Interactive Candlestick (OHLC) & Area Spline Engine**:
   - **Candlestick Mode**: Sprint cycle modeling with Open, High, Low, and Close values. Emerald (`#10b981`) bullish lift candles and Crimson (`#f43f5e`) correction candles with precise wick geometry.
   - **Area Mode**: Smooth cubic Bézier curves with layered gradient illumination and glow filters.
   - **Interactive Crosshairs & Dynamic Coordinate Tooltip**: Real-time cursor tracking displaying timestamp, OHLC data, volume, conversion rates, and RSI values.
2. **Multi-Timeframe Analysis**:
   - Seamlessly toggle across `1H`, `24H`, `7D`, `30D`, `90D`, and `1Y` analytical horizons.
3. **Technical Overlays & Indicators**:
   - **Moving Averages**: Fast EMA 9 (cyan) and Trend EMA 21 (gold) overlays.
   - **RSI (14) Momentum Oscillator**: Sub-panel with overbought (70) and oversold (30) threshold bands.
   - **Send Volume Histogram**: Real-time campaign dispatch throughput bars aligned with time buckets.
4. **Live Telemetry & Execution Stream**:
   - High-throughput streaming event log tracking campaign dispatches, AI subject line uplifts, DMARC/DKIM handshakes, and audience sync events.
5. **Institutional Quant Metrics**:
   - **Sharpe Growth Ratio**: Multi-channel efficiency benchmark (Top Decile).
   - **Delivery Alpha**: Inbox placement outperformance vs. industry baseline.
   - **CAC Velocity Delta**: Acquisition margin efficiency gain.
   - **Conversion Confidence**: Statistical significance metric for campaign lift.

---

## 🎨 Visual Design Architecture

- **Liquid Glass Aesthetic**: Frosted pill capsules, chromatic refractive borders, caustic glow backdrops, and floating tactile 3D elements (`apps/web/src/styles/liquid-glass.css`).
- **3D Tactile Automation**: Dynamic 3D fluid knot core and isometric automation workflows (`apps/web/public/assets/3d/`).
- **Trading Terminal Theme**: Deep dark slate canvas (`#070a12`), subtle coordinate grid lines, tabular monospace readouts, and high-contrast telemetry signals.

---

## 🚀 Quick Start & Local Development

### 1. Prerequisites
- Node.js 20+ & npm
- Python 3.11+ & Poetry / virtualenv
- Docker & Docker Compose (for PostgreSQL and Redis)

### 2. Frontend Development Server
```bash
cd apps/web
npm install
npm run dev
```
Open **`http://localhost:3000`** in your browser:
- **Homepage & Chart Showcase**: `http://localhost:3000/`
- **Growth Command Center & Chart Terminal**: `http://localhost:3000/dashboard`
- **Pricing & Subscription**: `http://localhost:3000/pricing`
- **Auth & Onboarding**: `http://localhost:3000/login`

### 3. Backend API Server
```bash
cd apps/api
python -m uvicorn growixa_api.app:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation available at: `http://localhost:8000/docs`

---

## 🧪 Verification & Test Commands

CI validation commands must be 100% green before every merge:

```bash
# Frontend (apps/web)
npm run test          # Vitest suite (63+ suites, 370+ tests)
npm run lint          # ESLint checks
npm run typecheck     # TypeScript strict verification
npm run build         # Next.js production compilation

# Backend (apps/api)
pytest                # Pytest integration & unit suite
ruff check .          # Python linter
mypy .                # Python static typing
```

---

## 📚 Documentation Index

- [`docs/01-product/PRD.md`](docs/01-product/PRD.md) — Product requirements document
- [`docs/00-project-control/MASTER_TASK_TRACKER.md`](docs/00-project-control/MASTER_TASK_TRACKER.md) — Master project tracker
- [`docs/12-development/AGENT_EXECUTION_RULES.md`](docs/12-development/AGENT_EXECUTION_RULES.md) — Repository execution rules
- [`AGENTS.md`](AGENTS.md) — Workspace rules, git branch conventions, and security gates
