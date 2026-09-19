# Changelog

- Document ID: DOC-CHANGELOG
- Status: ACTIVE
- Version: 0.8.0
- Last updated: 2026-09-20
- Owner: Coding agent
- Related documents: [PROJECT_STATUS](PROJECT_STATUS.md), [DECISIONS](DECISIONS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md)

Reverse-chronological log of material changes to the Growixa repository (documentation and,
from Sprint 1 onward, code). Each entry names what changed and the commit(s) it landed in.

## 2026-09-20 — v0.8.0 production release

- **`feat(website)`** — **Omnichannel AI Landing Page (All 5 Design Template Concepts Integrated)**:
  - **Hero AI Agent Platform (Image 1)**: Added `#1 Product of the Day` pill, *"The Ultimate All-In-One AI Growth Engine"* title, floating interactive hero cards (Voice Assistant, Magic AI, Gartner `#1 trend in 2025` badge), and 4.9⭐ rating badge.
  - **"Current Way We Work Is Chaotic" (Image 4)**: Added chaotic notification app icons (`Slack 1M+`, `Calendar 99+`, `Drive Offline`, `Messages 420`) connected with SVG curved paths and 3 key impact stats (2x task-switching errors, multitasking burnout, 1.2 months/year wasted).
  - **Central Glowing 3D Integration Hub & Search Orb (Image 2 & 5)**: Built central glowing purple orb surrounded by floating ribbon app badges (Postmark, OpenAI, Razorpay, Google Workspace, Slack, Zapier) and a mock search input card with *"Book Demo"* button.
  - **Omnichannel Social Deep Link Arch (Image 3)**: Built a rainbow arch of social platform icons (Instagram, LinkedIn, YouTube, WhatsApp, Discord) converging into a live Instagram & LinkedIn direct deep-link preview card.
  - **Ecosystem & Enterprise Security Sections**: Integrated native tech stack cards (Postmark, OpenAI, Claude AI, Stripe, Razorpay, Google Workspace, Meta Ads, LinkedIn, Slack, Zapier) and Bank-Grade Security cards (SOC2 Ready Architecture, GDPR & Opt-Out Handling, Fernet & Argon2id Encryption).
  - **Build & Test Verification**: `npm run typecheck` passed (0 errors) and Vitest suite passed (5/5 clean).

## 2026-09-19 — v0.7.4 production release

- **`fix(website)`** — **UI Polish & Mobile Optimization**: Removed old hardcoded HEX colors from the Premium Homepage that clashed with the new Dark Green / Light Beige theme. Ensured testimonials, graphs, and CTA buttons use the correct semantic CSS variables (`var(--paper)`, `var(--brand-gold)`, `var(--ink)`). Verified 4-column pricing grid successfully collapses into 1-column layout on mobile devices.

## 2026-09-19 — v0.7.3 production release

- **`feat(website)`** — **Theme Overhaul (Dark Green/Beige)**: Applied a new 2-color premium theme requested by the user, replacing the previous colors with Deep Green (`#1C352D`) and Light Beige (`#F8F0E5`) across the website's tokens, globals, and glass-icon utilities.

## 2026-09-19 — v0.7.2 production release

- **`feat(website)`** — **Ecosystem Section & Pricing Grid Fixes**: Injected the "Connects With Your Tech Stack" Ecosystem section to the premium home and fixed the 4-column pricing layout for `Simple Plans That Scale With Your Growth`.

## 2026-09-19 — v0.7.1 production release

- **`feat(website)`** — **Pricing Grid & Footer**: Added Free plan card and expanded grid layout for a seamless 4-column pricing layout. Updated footer copyright attribution to IITDEVELOPER.
