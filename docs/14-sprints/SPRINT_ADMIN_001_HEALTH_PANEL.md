# GRX-ADMIN-001: System Health Panel

## Background

`MASTER_TASK_TRACKER.md`'s `GRX-ADMIN-001` row describes a broad "System Platform
Control Plane" — system providers, global user management, platform health metrics,
audit logs. Scoped down deliberately (confirmed with the user via `AskUserQuestion`
before writing this doc): three of those four already exist as Super-Admin/Admin-gated
pages under `(dashboard)` —

- System providers → `/dashboard/integrations` (`integrations.manage`)
- Global user management → `/dashboard/team` (`users.manage`)
- Audit logs → `/dashboard/audit` (`audit.view`)

Relocating them into a separate `(admin)` section would be pure churn (nav changes,
route moves, retests) with no functional gain — this codebase's own convention
(established throughout this project) is not to build or move things without a real
reason. **This task is scoped to the one piece that's genuinely missing: a system
health panel.**

Two backend pieces already exist and are unused by any frontend:

- `GET /health` (`apps/api/src/growixa_api/health.py`) — public, unauthenticated,
  returns `{"status": "ok" | "degraded", "checks": {"postgres": "ok"|"error: …",
  "redis": "ok"|"error: …", "rabbitmq": "ok"|"error: …"}}`.
- `POST /system/jobs/healthcheck` (`apps/api/src/growixa_api/jobs/api.py`) —
  `admin.access`-gated, enqueues a `SYSTEM_HEALTHCHECK_QUEUE` job via RabbitMQ and
  returns `202 {"job_id": "<uuid>"}`. Exists purely as an ops smoke-check that the
  publish→consume pipeline works end-to-end. The worker consumes and logs it; there is
  no per-job status row anywhere, so this is fire-and-forget — the API response is the
  only feedback, there is no way to poll for job completion.

`admin.access` is already seeded (Super Admin + Admin ✅, everyone else ❌ — see
`docs/08-security/RBAC.md`).

**No backend changes are needed for this task** — both endpoints already exist and do
exactly what the panel needs. This is a frontend-only task.

## What This Feature Delivers

1. A real `(admin)` route group: currently `apps/web/src/app/(admin)/layout.tsx` is a
   bare unauthenticated `<div>` wrapper with no auth check at all — anyone with the URL
   can currently reach anything placed under `(admin)/`. This task fixes that gap too.
2. `/admin` — a single System Health page:
   - Live Postgres/Redis/RabbitMQ status (from `GET /health`), each as a colored
     ok/error pill, with the raw error text shown for a failing check (the API already
     returns `"error: <exception message>"` — surface it, don't swallow it).
   - A "Run healthcheck job" button → `POST /system/jobs/healthcheck` → toast showing
     the returned `job_id` on success (`202`). No polling — be honest that this is
     fire-and-forget, matching what the endpoint actually does; don't imply a result
     will appear when nothing tracks one.
   - A manual refresh action for the `/health` checks (no auto-polling interval needed
     for a first cut — a refresh button is enough).
3. A link into `/admin` from the regular dashboard, visible only to users with
   `admin.access` (mirrors every other permission-gated `sidebar.tsx` entry) — without
   this, the page is unreachable through the UI. Suggested placement: a new
   `SETTINGS` section item, e.g. `{ label: "System Health", href: "/admin",
   icon: "🩺", requiresPermission: "admin.access" }`. **Do not create a new NAV_SECTIONS
   section for one item** — it belongs in the existing SETTINGS section alongside
   Company/Team/Audit Log/Integrations, which are all Admin/Super-Admin-tier links.

## Proposed Changes

### New Worktree

- Path: `.worktrees/grx-admin-health-panel`
- Branch: `feature/FRONTEND/GRX-ADMIN-001-HEALTH-PANEL`
- Preview: `http://localhost:3001`
- Works in isolation; merges into `main` when done, same pattern as every other
  worktree row in `WORKTREE_TRACKER.md`.
- **Learn from the GRX-SCHED-UI incident** (see that row in `WORKTREE_TRACKER.md`'s
  Completed section, commit `1463f1d`): commit only the files this task actually
  touches. A broad `git add -A`/`git add .` from the repo root will pick up **every**
  other active `.worktrees/*` entry as a stray gitlink and any other uncommitted litter
  sitting in the parent tree. Stage files explicitly by path.

### Component 1 — Admin Layout (real auth gate)

**[MODIFY] `apps/web/src/app/(admin)/layout.tsx`**

Currently:

```tsx
import type { ReactNode } from "react";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <div className="admin-wrapper">{children}</div>;
}
```

Replace with a server component matching `(dashboard)/dashboard/layout.tsx`'s existing
pattern (`getCurrentUser()` from `@/lib/auth`, `redirect("/login")` on no session) —
**plus** an `admin.access` permission check this dashboard layout doesn't need (the
dashboard shell filters nav per-permission but doesn't gate the whole layout; `/admin`
should, since everything under it is Super-Admin/Admin-tier by definition). A user
without `admin.access` who navigates to `/admin` directly should be redirected to
`/dashboard`, not shown a blank/broken page.

A minimal header for the admin shell: "Growixa Admin" branding + a "← Back to
Dashboard" link (`/dashboard`) + the existing `Log out` button pattern reused from
`DashboardShell`. Do not build a sidebar for a single page — add one only when a second
`/admin` page actually exists.

**[NEW] `apps/web/src/app/(admin)/admin-header.module.css`** (or reuse/extend an
existing shared module if one already fits — check `shared.module.css` first before
adding a new file).

### Component 2 — Health Page

**[NEW] `apps/web/src/app/(admin)/admin/page.tsx`** (route: `/admin`)

- `"use client"` component, matches this codebase's established data-fetching pattern
  (`useEffect` + `apiFetch` on mount, loading/error states) rather than introducing a
  new pattern.
- `GET /health` is unauthenticated at the API layer but call it via `apiFetch` anyway
  for consistent base-URL handling — do not add cookies/auth headers it doesn't need.
- Three status cards (Postgres / Redis / RabbitMQ), each: label, an "OK"/"ERROR" pill
  (green/red, reuse existing pill styling conventions from `campaigns-page.module.css`'s
  status badges rather than inventing new colors), and the raw check string shown
  beneath when not `"ok"`.
- An overall banner reflecting the top-level `status` field (`"ok"` vs `"degraded"`).
- "Refresh" button re-fetches `GET /health`.
- "Run healthcheck job" button → `POST /system/jobs/healthcheck` (no request body) →
  `showToast("success", \`Healthcheck job enqueued (job_id: ${job_id})\`)` on `202`, or
  `showToast("error", parseApiErrorDetail(error, "Could not trigger healthcheck job."))`
  on failure — reuse the existing `useToast()`/`parseApiErrorDetail` helpers already
  used throughout `campaign-form-page.tsx`/`campaigns-page.tsx`.
- No new types file needed for two fields — inline the `HealthResponse` shape in this
  file (`{ status: string; checks: { postgres: string; redis: string; rabbitmq: string } }`).

**[NEW] `apps/web/src/app/(admin)/admin/admin-page.module.css`**

Card grid + pill styles, consistent with the existing design tokens used throughout
`(dashboard)` (don't invent new colors/spacing scale).

### Component 3 — Sidebar Link

**[MODIFY] `apps/web/src/app/(dashboard)/dashboard/sidebar.tsx`**

Add to the existing `SETTINGS` section's `items` array (after `Integrations`):

```ts
{
  label: "System Health",
  href: "/admin",
  icon: "🩺",
  requiresPermission: "admin.access",
},
```

This is an intentional cross-route-group link (`/admin`, not `/dashboard/...`) — the
existing `NavItem`/`Link` machinery doesn't care, `href` is just a string.

### Component 4 — Tests

**[NEW] `apps/web/src/app/(admin)/admin/admin-page.test.tsx`**

- `renders all three health checks as OK when GET /health returns all-ok`
- `renders an ERROR pill and the raw error text for a failing check`
- `renders the degraded banner when overall status is "degraded"`
- `refresh button re-fetches GET /health`
- `clicking "Run healthcheck job" posts to /system/jobs/healthcheck and shows a success toast with the job_id`
- `shows an error toast when the healthcheck trigger fails`

**[MODIFY] `apps/web/src/app/(dashboard)/dashboard/sidebar.test.tsx`** (or wherever
sidebar permission-filtering is already tested — check for an existing file before
assuming one needs to be created)

- `shows the System Health link only when admin.access is present`

No backend test changes — no backend code changed.

## Verification Plan

### Automated Tests

```bash
cd apps/web && npx vitest run
```

All existing tests must still pass, plus the new ones above.

```bash
cd apps/web && npm run lint && npm run typecheck
```

### Manual Verification (on `http://localhost:3001`)

1. Log in as Super Admin, navigate to `/admin` directly — page loads, all three checks
   show OK (Compose's Postgres/Redis/RabbitMQ are all up in local dev).
2. Click "Run healthcheck job" — success toast appears with a `job_id`; confirm via
   `docker compose logs worker` that the job was actually consumed (matches this
   session's established pattern of verifying against real logs, not just the toast).
3. Stop one dependency (e.g. `docker compose stop redis`) and click Refresh — confirm
   the Redis card flips to ERROR with the real exception text, the banner flips to
   "degraded", and the other two checks are unaffected. **Restart it afterward**
   (`docker compose start redis`) — don't leave the environment in a broken state.
4. Log in as a role without `admin.access` (e.g. Analyst) — confirm no "System Health"
   sidebar link appears, and a direct navigation to `/admin` redirects to `/dashboard`
   rather than showing the page or erroring.
5. Confirm `/dashboard/integrations`, `/dashboard/team`, and `/dashboard/audit` are
   completely untouched by this change (no accidental edits from exploring their
   existing patterns while building this).

## Docs

- Tracker row `GRX-ADMIN-001`: flip `BACKLOG` → `DONE`, update the acceptance
  criterion to reflect the actual scoped deliverable (health panel, not the full
  original description) — note in the evidence column that system
  providers/users/audit were deliberately excluded as pre-existing, not missed.
- `WORKTREE_TRACKER.md`: move this worktree's row from Active to Completed & Merged
  once merged, same as every prior entry.
- `docs/08-security/RBAC.md`: no change needed — `admin.access` already exists and
  already has the correct grant matrix.
- Standard four-control-doc update (tracker/PROJECT_STATUS/CHANGELOG/AGENT_HANDOFF) at
  completion.

## Open Questions

None. Both endpoints this page calls already exist, are already tested, and their
exact response shapes are given above verbatim from the current source
(`apps/api/src/growixa_api/health.py`, `apps/api/src/growixa_api/jobs/api.py`) — no
guessing required.
