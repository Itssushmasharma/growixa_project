# Growixa Parallel Worktree & Feature Tracker

This document maintains a real-time record of all parallel Git worktrees, active feature branches, preview ports, and merge statuses.

---

## 🟢 Active Worktrees & Preview Servers

| Worktree Path | Branch Name | Feature / Task | Preview URL | Status | Created |
| `.worktrees/grx-contact-016-restore` | `feature/BACKEND/GRX-CONTACT-016` | `GRX-CONTACT-016` — Deleted Contacts View & Contact Restoration (UI & Backend) | `http://localhost:3000` | 🟢 Active Dev | 2026-08-17 |

---

## 📜 Completed & Merged Worktrees

| Worktree Directory | Branch | Feature Delivered | Merged Commit | Merged Date |
|---|---|---|---|---|
| `.worktrees/grx-saas-007-providers` | `feature/BACKEND/GRX-SAAS-007` | Platform Admin Provider Management Hub (`/platform/providers`) | `main` | 2026-08-17 |
| `.worktrees/grx-infra-ovh-deployment` | `feature/BACKEND/GRX-INFRA-001` | `GRX-INFRA-001` — OVH VPS Production Deployment Guide & Automated Scripts | `79e7b8c` | 2026-08-17 |
| `.worktrees/grx-contact-015-ui` | `feature/FRONTEND/GRX-CONTACT-015` | `GRX-CONTACT-015` — Contacts Table Bulk Actions, Multi-Select & Delete/Suppress UI | `a97bef2` | 2026-08-17 |
| `.worktrees/grx-contact-010-deletion` | `feature/BACKEND/GRX-CONTACT-010` | `GRX-CONTACT-010` — Contact Soft Deletion & Bulk Operations API | `a8419ff` | 2026-08-17 |
| `.worktrees/test-folder-organization` | `feature/BACKEND/test-folder-organization` | `GRX-TEST-ORG-001` — API and worker pytest suites reorganized into domain/job folders (rename-only, 62 files) | `f4d2b13` | 2026-08-17 |
| `.worktrees/grx-saas-009-monitoring` | `feature/BACKEND/GRX-SAAS-009` | Platform Admin Infrastructure Monitoring (`/platform/monitoring`) & Financial Overview (`/platform/finance`) | `af733c4` | 2026-08-16 |
| — | `feature/FRONTEND/GRX-SIDEBAR-CLEANUP` | Removed legacy single-tenant System Health link from customer dashboard sidebar | `c078602` | 2026-08-16 |
| `.worktrees/grx-marketing-redesign` | `feature/FRONTEND/GRX-MARKETING-REDESIGN` | Marketing pricing section redesign & credit pack catalog matching DEC-GRX-030 | `01962ad` | 2026-08-16 |
| `.worktrees/grx-templates-gallery` | `feature/FRONTEND/GRX-TEMPLATES-GALLERY` | Email Templates gallery visual redesign & interactive live HTML preview modal | `35bda06` | 2026-08-16 |
| `.worktrees/grx-dev-seed` | `feature/BACKEND/GRX-DEV-SEED-001` | Safe and idempotent dev demo-data seed CLI (`python -m growixa_api.cli.seed_demo_data`) + integration tests | `f1b7744` | 2026-08-15 |
| `.worktrees/grx-dashboard-suite` | `feature/FRONTEND/GRX-DASHBOARD-SUITE-003` | Dashboard Suite redesign — PageHeader + StatCard across Dashboard, Social, Calendar, Templates, Company Settings | `335b0ae` | 2026-08-15 |
| `.worktrees/grx-ai-studio-redesign` | `feature/FRONTEND/GRX-AI-STUDIO-001` | Global Header + AI Marketing Copilot redesign (`/dashboard/ai`) — first task run through the independent-review workflow end to end (developer: Antigravity, reviewer: Claude Code, human sign-off confirmed) | `2b6888f` | 2026-08-15 |
| `.worktrees/grx-settings-team-redesign` | `feature/FRONTEND/GRX-SETTINGS-TEAM-REDESIGN` | Card-Based Redesign for Company Settings, Team & Roles, and Integrations Pages | `dfd1cc1` | 2026-08-07 |
| `.worktrees/grx-templates-page-redesign` | `feature/FRONTEND/GRX-TEMPLATES-PAGE-REDESIGN` | Email Templates Page Redesign (Hero Showcase Spotlight, Visual Card Grid, Metric Summary Cards, Category Pills, View Switcher & Live Preview Drawer) | `954eab2` | 2026-08-07 |
| `.worktrees/grx-cicd-deployment` | `feature/BACKEND/GRX-CICD-DEPLOYMENT` | Deployment CI/CD Workflows (Hugging Face Spaces API+Worker, Netlify Web Frontend, Release Orchestration) | `f146b98` | 2026-08-07 |
| `.worktrees/grx-admin-health-panel` | `feature/FRONTEND/GRX-ADMIN-001-HEALTH-PANEL` | System Health Panel (`/admin`, real auth gate, live Postgres/Redis/RabbitMQ status, healthcheck-job trigger) | `c93af62` | 2026-08-06 |
| `.worktrees/grx-sched-frontend` | `feature/FRONTEND/GRX-SCHED-UI` | Scheduled Campaigns UI (Send Mode selector, datetime picker, Cancel button, status badges, Scheduled tab) | `211e81d` | 2026-08-06 |
| `.worktrees/grx-contacts-page-redesign` | `feature/FRONTEND/GRX-CONTACTS-PAGE-REDESIGN` | Contacts Page Redesign (Metric Cards, Search & Filter Toolbar, Table Grid Header, CSV Export, Frosted Glass Modal View) | `a11d261` | 2026-08-06 |
| `.worktrees/grx-sidebar-redesign` | `feature/FRONTEND/GRX-SIDEBAR-REDESIGN` | Sidebar Nav Redesign (Icons for all items, AUDIENCE/CAMPAIGNS/SETTINGS hierarchy, auto-expand active parent section) | `eda4dba` | 2026-08-06 |
| `.worktrees/grx-frontend-imports-redesign` | `feature/FRONTEND/GRX-CONTACTS-IMPORTS-REDESIGN` | Drag & Drop CSV dropzone, 3-step progress, column mapping, metrics, status pills, CSV export downloader | `635f434` | 2026-08-06 |
| `.worktrees/grx-sprint4-scheduler` | `feature/BACKEND/GRX-SCHED-001` | Campaign schedule/cancel schema (`scheduled_at`, `cancelled_at`, `idempotency_key`), migration `4a92b8107c12`, schedule/cancel API endpoints + 8 unit tests | `1757538` | 2026-08-06 |

---

## ⚙️ Worktree Execution Rules

1. **Isolation**: Every parallel feature must be built inside `.worktrees/<feature-name>` on a branch named `feature/FRONTEND/...` or `feature/BACKEND/...`.
2. **Preview Server**: Frontend features run a secondary preview dev server on **`http://localhost:3001`**.
3. **Commit Attribution**: Every commit includes `Co-Authored-By: Ravi Kant Yadav <ravikantyadav1918@gmail.com>`.
4. **Merge Protocol**: A `pr_reviews/<branch>.md` handoff file must exist with
   `Review Decision: APPROVED` from a different agent/tool, and nothing outside
   `pr_reviews/**` may have changed between `Reviewed Code Commit` and the branch's
   current HEAD (see [AGENT_EXECUTION_RULES.md §Independent
   review](../12-development/AGENT_EXECUTION_RULES.md#independent-review-mandatory-before-merge)).
   For UI/UX or customer-facing work, the user must also review `http://localhost:3001`
   and confirm *"Looks good"*. Once both are satisfied, merge to `main`, run build/tests,
   and remove the worktree.
