# Growixa Parallel Worktree & Feature Tracker

This document maintains a real-time record of all parallel Git worktrees, active feature branches, preview ports, and merge statuses.

---

## 🟢 Active Worktrees & Preview Servers

| Worktree Path | Branch Name | Feature / Task | Preview URL | Status | Created |
|---|---|---|---|---|---|
| `.worktrees/grx-templates-page-redesign` | `feature/FRONTEND/GRX-TEMPLATES-PAGE-REDESIGN` | Email Templates Page Redesign (Hero Showcase, Visual Card Grid, Metric Summary Cards, View Switcher & Live Preview Drawer) | `http://localhost:3001` | 🟡 `IN_PROGRESS` | 2026-08-06 |

---

## 📜 Completed & Merged Worktrees

| Worktree Directory | Branch | Feature Delivered | Merged Commit | Merged Date |
|---|---|---|---|---|
| `.worktrees/grx-contacts-page-redesign` | `feature/FRONTEND/GRX-CONTACTS-PAGE-REDESIGN` | Contacts Page Redesign (Metric Cards, Search & Filter Toolbar, Table Grid Header, CSV Export, Frosted Glass Modal View) | `a11d261` | 2026-08-06 |
| `.worktrees/grx-sidebar-redesign` | `feature/FRONTEND/GRX-SIDEBAR-REDESIGN` | Sidebar Nav Redesign (Icons for all items, AUDIENCE/CAMPAIGNS/SETTINGS hierarchy, auto-expand active parent section) | `eda4dba` | 2026-08-06 |
| `.worktrees/grx-frontend-imports-redesign` | `feature/FRONTEND/GRX-CONTACTS-IMPORTS-REDESIGN` | Drag & Drop CSV dropzone, 3-step progress, column mapping, metrics, status pills, CSV export downloader | `635f434` | 2026-08-06 |
| `.worktrees/grx-sprint4-scheduler` | `feature/BACKEND/GRX-SCHED-001` | Campaign schedule/cancel schema (`scheduled_at`, `cancelled_at`, `idempotency_key`), migration `4a92b8107c12`, schedule/cancel API endpoints + 8 unit tests | `1757538` | 2026-08-06 |

---

## ⚙️ Worktree Execution Rules

1. **Isolation**: Every parallel feature must be built inside `.worktrees/<feature-name>` on a branch named `feature/FRONTEND/...` or `feature/BACKEND/...`.
2. **Preview Server**: Frontend features run a secondary preview dev server on **`http://localhost:3001`**.
3. **Commit Attribution**: Every commit includes `Co-Authored-By: Ravi Kant Yadav <ravikantyadav1918@gmail.com>`.
4. **Merge Protocol**: Once user reviews `http://localhost:3001` and confirms *"Looks good"*, merge to `main`, run build/tests, and remove the worktree.
