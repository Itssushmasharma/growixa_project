# Growixa Parallel Worktree & Feature Tracker

This document maintains a real-time record of all parallel Git worktrees, active feature branches, preview ports, and merge statuses.

---

## 🟢 Active Worktrees & Preview Servers

| Worktree Path | Branch Name | Feature / Task | Preview URL | Status | Created |
|---|---|---|---|---|---|
| `.worktrees/grx-dashboard-006` | `feature/FRONTEND/GRX-DASHBOARD-006` | `GRX-DASHBOARD-006` — Growth Command Center UX | `http://localhost:3003` | READY_FOR_REVIEW — tests/build pass, product-owner direction applied | 2026-09-09 |
| — | `main` | Production & Integration Baseline | `http://localhost:3000` | ACTIVE | 2026-08-24 |

---

## 📜 Completed & Merged Worktrees

| Worktree Directory | Branch | Feature Delivered | Merged Commit | Merged Date |
|---|---|---|---|---|
| `.worktrees/grx-dashboard-redesign` | `feature/FRONTEND/GRX-DASHBOARD-REDESIGN` | `GRX-DASHBOARD-005` — Unified 5-Stage Dashboard Redesign (SVG Sidebar, Trend Charts, Quota Meters, Platform Login) | `c7e0425` | 2026-09-01 |
| `.worktrees/grx-dashboard-analytics-overview` | `feature/FRONTEND/GRX-DASHBOARD-004` | `GRX-DASHBOARD-004` — Executive Analytics Overview (CTOR StatCard, Live Activity Stream Feed) | `f769b5c` | 2026-08-25 |
| `.worktrees/grx-campaign-total-metrics` | `feature/SHARED/GRX-CAMP-010` | `GRX-CAMP-010` — Total vs Unique Email Engagement Metrics (Total Opens, Total Clicks, CTOR) | `8876bcf` | 2026-08-25 |
| `.worktrees/grx-campaign-list-metrics` | `feature/SHARED/GRX-CAMP-009` | `GRX-CAMP-009` — Campaign List Inline Performance & Engagement Metrics | `c9ef0ad` | 2026-08-24 |
| `.worktrees/grx-template-token-validation` | `feature/BACKEND/GRX-CONTENT-002` | `GRX-CONTENT-002` — Upfront Personalization Token Validation & `{{unsubscribe_url}}` First-Class Support | `930f7b3` | 2026-08-24 |
| `.worktrees/grx-personalization-renderer` | `feature/BACKEND/GRX-CONTENT-001` | `GRX-CONTENT-001` — Dynamic Email Personalization Engine & Merge Tags (DEC-GRX-036) | (pending merge) | 2026-08-24 |
| `.worktrees/grx-postal-webhook-analytics` | `feature/BACKEND/GRX-POSTAL-WEBHOOK-ANALYTICS` | `GRX-EMAIL-012` — Postal Webhook Receiver & Live Delivery Analytics | `aaf51b3` | 2026-08-23 |
| `.worktrees/grx-auth-split-screen-redesign` | `feature/FRONTEND/GRX-AUTH-SPLIT-SCREEN-REDESIGN` | `GRX-AUTH-007` — Unified Split-Screen Auth Redesign (Login & Register) | `02bf444` | 2026-08-23 |
| `.worktrees/grx-campaign-emergency-stop` | `feature/SHARED/GRX-CAMPAIGN-EMERGENCY-STOP` | `GRX-CAMP-008` — Live Campaign Emergency Stop & In-Flight Cancellation | `30f10c6` | 2026-08-23 |
| `.worktrees/grx-sender-identity-reassign` | `feature/SHARED/GRX-EMAIL-SENDER-REASSIGN` | `GRX-EMAIL-017` — Sender identity auto-reassignment on connection update | `f3cde3c` | 2026-08-23 |
| `.worktrees/grx-sender-identity-delete` | `feature/SHARED/GRX-SENDER-IDENTITY-DELETE` | `GRX-EMAIL-016` — Guarded Delete Sender Identity (Backend API & Frontend Integrations UI) | `4ff2e65` | 2026-08-23 |
| `.worktrees/grx-email-provider-name-fix` | `feature/FRONTEND/GRX-EMAIL-PROVIDER-NAME` | `GRX-EMAIL-015` — Add required name field to email provider payload and form | `2d775f6` | 2026-08-23 |
| `.worktrees/grx-web-favicon` | `feature/FRONTEND/add-web-favicon` | Site Favicon & Apple Touch Icon (512x512 PNG) | `b7e7584` | 2026-08-20 |
| `.worktrees/password-forgot-reset-flow` | `feature/FRONTEND/password-forgot-reset-flow` | Customer Forgot-Password & Reset Flow with transactional SMTP email delivery | `e970a4a` | 2026-08-20 |
| `.worktrees/campaign-schedule-redirect` | `feature/FRONTEND/campaign-schedule-redirect` | Campaign Scheduling Redirect to all-campaigns overview | `e970a4a` | 2026-08-20 |
| `.worktrees/grx-sec-002` | `feature/BACKEND/GRX-SEC-002` | `GRX-SEC-002` — Dependabot 7 CVE Vulnerability Triage, Package Overrides & CI Security Audit | `c84b61d` | 2026-08-18 |
| `.worktrees/grx-docs-help-center` | `feature/FRONTEND/GRX-DOCS-001` | `GRX-DOCS-001` — Customer Help Center (`/docs`) & In-App Contextual Help (`/dashboard`) | `89624bd` | 2026-08-17 |
| `.worktrees/grx-contact-016-restore` | `feature/BACKEND/GRX-CONTACT-016` | `GRX-CONTACT-016` — Deleted Contacts View & Contact Restoration (UI & Backend) | `95189af` | 2026-08-17 |
| `.worktrees/grx-infra-cicd-uat-prod` | `feature/BACKEND/GRX-INFRA-002` | `GRX-INFRA-002` — Unified Multi-Environment CI/CD (GitHub Actions, GHCR, Production & UAT on OVH VPS) | `a12c8c1` | 2026-08-17 |
| `.worktrees/grx-saas-007-providers` | `feature/BACKEND/GRX-SAAS-007` | Platform Admin Provider Management Hub (`/platform/providers`) | `434a464` | 2026-08-17 |
| `.worktrees/grx-infra-ovh-deployment` | `feature/BACKEND/GRX-INFRA-001` | `GRX-INFRA-001` — OVH VPS Production Deployment Guide & Automated Scripts | `79e7b8c` | 2026-08-17 |
| `.worktrees/grx-contact-015-ui` | `feature/FRONTEND/GRX-CONTACT-015` | `GRX-CONTACT-015` — Contacts Table Bulk Actions, Multi-Select & Delete/Suppress UI | `a97bef2` | 2026-08-17 |
