# GRX-SCHED-FRONTEND: Scheduled Campaigns UI

## Background

Sprint 4 backend is fully done and committed on `main` (see `SPRINT_04_SCHEDULED_CAMPAIGN.md`
and `MASTER_TASK_TRACKER.md`'s `GRX-SCHED-001` through `006` rows):

- `POST /campaigns/{id}/schedule` — accepts `{ scheduled_at: ISO datetime }`, moves a `DRAFT`
  campaign to `SCHEDULED`. Rejects (409) any campaign not currently `DRAFT`. Rejects (422) a
  `scheduled_at` that isn't strictly in the future.
- `POST /campaigns/{id}/cancel` — moves a `DRAFT` or `SCHEDULED` campaign to `CANCELLED`.
  **Rejects (409) `DISPATCHING`, `SENDING`, `SENT`, and `FAILED`** — cancellation only works
  before dispatch has started.
- A background scheduler ticker polls every 5s and dispatches due campaigns to RabbitMQ
  automatically; the worker then sends via the existing pipeline, with Redis idempotency and
  retry/DLQ handling. None of that is this task's concern — it already works end to end.

Open gap (flagged in `AGENT_HANDOFF.md`): no frontend UI exists to schedule or cancel a
campaign. `campaign-form-page.tsx` has no fields or buttons calling these endpoints.

**This document was reviewed against the actual backend code before being handed off** — the
corrections below aren't stylistic, they reflect what the API actually does.

## What This Feature Delivers

Complete the campaign lifecycle from the frontend, so users can:

1. Schedule a `DRAFT` campaign to be sent at a future date and time (`Schedule for Later`
   date-time picker)
2. Send Now immediately (existing flow, unchanged)
3. Cancel a `DRAFT` or `SCHEDULED` campaign from the campaign detail/list page — **not**
   `SENDING` or `DISPATCHING`, both of which the backend rejects

## Proposed Changes

### New Worktree

- Path: `.worktrees/grx-sched-frontend`
- Branch: `feature/FRONTEND/GRX-SCHED-UI`
- Preview: `http://localhost:3001`
- Works in isolation; merges into `main` when done, same pattern as the other active
  worktrees tracked in `WORKTREE_TRACKER.md`.

### Component 1 — Campaign Form Page (Create / Edit)

**[MODIFY] `campaign-form-page.tsx`**

Add a Send Mode selector below the recipient section, visible only when the campaign is
editable (i.e. `mode === "create"` or `campaign.status === "DRAFT"` — reuse the existing
`editable` flag already computed in this file):

```
( ) Send Now
( ) Schedule for Later   [date-time picker]   e.g. 2026-08-10 09:00 AM IST
```

- On `Send Now` → existing `POST /campaigns/{id}/send` (no change).
- On `Schedule for Later` → new call to `POST /campaigns/{id}/schedule` with
  `{ scheduled_at }` as an ISO 8601 UTC string.
- **Gate the entire Send Mode selector (both options, but especially Schedule) behind
  `canManage`, not `canSend`.** The backend requires `campaigns.manage` for `/schedule` and
  `/cancel` (see `_require_manage` in `campaigns/api.py`) — `campaigns.send` only gates
  `/send` and `/test-send`. A user with `campaigns.send` but not `campaigns.manage` should
  not see a Schedule option that will 403.

UI details:

- Native `<input type="datetime-local">` scoped to the user's local timezone, converted to
  UTC before submission.
- Client-side minimum = now + 10 minutes. This is a UX safeguard, not a backend requirement
  (the backend only rejects `scheduled_at <= now`) — it exists so the chosen time hasn't
  already passed by the time the request reaches the server.
- Show a human-readable confirmation: `"This campaign will be sent on Aug 10, 2026 at 9:00
  AM IST"`.
- Handle the 409 case (campaign is no longer `DRAFT` by the time of submission — e.g. two
  tabs open) with `parseApiErrorDetail` + `showToast("error", ...)`, matching the existing
  `handleSendNow` error-handling pattern in this file.

**[MODIFY] `campaign-form-page.module.css`**

Add styles for:

- `.sendModeGroup` — segmented radio toggle (Send Now / Schedule)
- `.schedulePicker` — date-time input using the existing design tokens
- `.scheduleConfirmText` — humanized preview text

### Component 2 — Campaign List Page (Cancel button)

**[MODIFY] `campaigns-page.tsx`**

Add a Cancel action in the campaign row actions, **shown only for `status === "DRAFT" ||
status === "SCHEDULED"`** — not `SENDING`, not `DISPATCHING` (the backend 409s on both; do
not show a button that always fails).

- Gate visibility behind the existing `canManage` state in this file (same permission as the
  `+ New Campaign` button) — not a new permission check.
- Row action: `[Edit] [Cancel]`
- Cancel → `POST /campaigns/{id}/cancel` (no request body) → optimistic status update to
  `CANCELLED` in local state.
- Success: `showToast("success", "Campaign cancelled successfully.")`
- Error: `showToast("error", parseApiErrorDetail(error, "Could not cancel this campaign."))`
  — reuse the existing `parseApiErrorDetail` helper so a real 409 message surfaces instead of
  a generic one.

### Component 3 — Status badges

**[MODIFY] `campaigns-page.tsx`**

`STATUS_LABEL` and `STATUS_CLASS` are `Record<Campaign["status"], string>` — exhaustive
records keyed by the status union. Once `CampaignStatus` is widened (Component 4), these
**must** get an entry for every new status or the build fails to type-check. Add all four,
not just three:

- `SCHEDULED` → `"Scheduled"` (plus a `scheduledAtLabel` helper for the humanized
  `scheduled_at` time shown alongside it, e.g. "Scheduled for Aug 10, 9:00 AM" — the raw
  label stays plain text, matching the existing no-emoji style of `"Sending…"` /
  `"Draft"` / etc.)
- `DISPATCHING` → `"Dispatching…"` — a real, reachable status (the scheduler has claimed the
  campaign but the worker hasn't started sending yet). Missing this one is the most likely
  way this task ships with a build error or a blank badge.
- `CANCELLED` → `"Cancelled"`
- `FAILED` → `"Failed"` (unchanged — **do not** add "(DLQ exhausted)" or any other reason
  text; `status` alone doesn't tell you why a campaign failed, since a campaign can also
  fail for having no resolvable sender identity, with nothing to do with the dispatch retry
  path. Don't claim a cause the API doesn't expose.)

Keep styling consistent with the existing plain-text pill badges — no emoji, matching every
current status label in this file.

**[MODIFY] `FILTER_TABS`**

Currently:

```ts
// Only the statuses this app's data model actually has today (DRAFT/SENDING/SENT/FAILED).
// Scheduled/paused campaigns aren't a real status yet — that's separate, not-yet-built
// scheduled-send work — so no tab for them here rather than a filter that's always empty.
const FILTER_TABS: { value: FilterTab; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "DRAFT", label: "Draft" },
  { value: "SENDING", label: "Sending" },
  { value: "SENT", label: "Sent" },
  { value: "FAILED", label: "Failed" },
];
```

That comment is now stale — scheduling is built. Add a `Scheduled` tab (`value: "SCHEDULED"`)
and remove the comment (or update it to reflect the current state). Without this, a user can
create a scheduled campaign with no way to find it again except scrolling "All".

### Component 4 — Types Update

**[MODIFY] `types.ts`**

```ts
export type CampaignStatus =
  | "DRAFT"
  | "SCHEDULED"
  | "DISPATCHING"
  | "SENDING"
  | "SENT"
  | "CANCELLED"
  | "FAILED";
```

```ts
interface Campaign {
  // ...existing fields unchanged...
  scheduled_at: string | null;
  cancelled_at: string | null;
  idempotency_key: string; // NOT nullable — API always returns a UUID (DB column is
                            // NOT NULL UNIQUE with a server-generated default)
}
```

### Component 5 — Tests

**[MODIFY] `campaign-form-page.test.tsx`**

- `renders Schedule for Later radio button`
- `hides the Send Mode selector when canManage is false`
- `shows datetime picker when Schedule for Later is selected`
- `calls POST /schedule with correct ISO timestamp on submit`
- `disables past datetime selection`
- `shows an error toast on a 409 (campaign no longer DRAFT)`

**[MODIFY] `campaigns-page.test.tsx`**

- `shows Cancel button only for DRAFT and SCHEDULED campaigns` (assert it's absent for
  `SENDING` and `DISPATCHING` rows, not just present for the two valid ones)
- `hides Cancel button entirely when canManage is false`
- `calls POST /cancel and shows success toast`
- `renders SCHEDULED status badge with humanized scheduled_at time`
- `renders DISPATCHING status badge`
- `Scheduled filter tab shows only SCHEDULED campaigns`

Toast usage: `useToast()` from `@/components/toast/toast-context`, then
`showToast("success" | "error", message)` — matches the pattern already used throughout
`campaign-form-page.tsx`.

## Verification Plan

### Automated Tests

```bash
cd apps/web && npx vitest run
```

All existing tests must still pass, plus the new ones above.

```bash
cd apps/web && npm run lint && npm run typecheck
```

Note: widening `CampaignStatus` will surface any other exhaustive switch/record over
`Campaign["status"]` elsewhere in the codebase (grep for `Campaign\["status"\]` and
`CampaignStatus` before considering this done) — fix every one `tsc` flags, don't just patch
the two called out above if there turn out to be more.

### Manual Verification (on `http://localhost:3001`)

1. Open Create Campaign → select `Schedule for Later` → pick a future datetime → submit.
2. Verify the campaign appears in the list with a `SCHEDULED` badge and humanized
   `scheduled_at` time, and that the new `Scheduled` filter tab shows it.
3. Click `Cancel` on that `SCHEDULED` campaign → verify it moves to `CANCELLED` and the
   Cancel button disappears (since `CANCELLED` isn't cancellable).
4. Confirm no Cancel button appears on any `SENDING`/`DISPATCHING` row (create one via the
   existing Send Now flow to check, or via a real scheduled campaign whose time has passed
   and been claimed by the ticker).
5. Confirm the Send Mode selector (and Cancel button) don't render at all for a user without
   `campaigns.manage`.
6. Verify `Send Now` flow still works as before (regression test).
7. Clean up any smoke-test campaigns created during manual verification.

## Open Questions

None. Backend contract is stable and fully documented in `AGENT_HANDOFF.md` and
`campaigns/services.py`. All new UI calls existing, already-tested API endpoints only.
