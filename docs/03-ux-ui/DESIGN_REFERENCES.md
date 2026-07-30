# Design References

- Document ID: DOC-UX-DESIGN-REFS
- Status: ACTIVE (reference material — not an implementation task, not itself gated by Sprint 1 scope)
- Version: 1.0
- Last updated: 2026-07-25
- Owner: Product owner (Ravi), captured by coding agent
- Related documents: [MVP_SCOPE](../01-product/MVP_SCOPE.md), [ROADMAP](../01-product/ROADMAP.md), [SPRINT_01_FOUNDATION](../14-sprints/SPRINT_01_FOUNDATION.md), [MASTER_TASK_TRACKER](../00-project-control/MASTER_TASK_TRACKER.md), [DESIGN_REFERENCE_REVSPOT](DESIGN_REFERENCE_REVSPOT.md)

## What this is

Visual/UX reference material for the Growixa frontend, supplied by the product owner: brand
assets, an HTML/CSS mockup (login screen + full dashboard concept), and a written design
brief. This document exists so a future session building actual frontend UI (`GRX-AUTH-002`'s
login page, `GRX-FOUND-008`'s dashboard shell, and later feature UIs) has a single place to
find the intended look and feel, instead of that context living only in chat history.

**This is reference material, not an approved Sprint 1 implementation spec.** See
[§Scope caveat](#scope-caveat-read-before-building-anything-from-this) before building
anything from it.

## Scope caveat — read before building anything from this

The mockup and brief below describe the **full eventual product** — Contacts, Segments,
Leads, Campaigns, Social & Calendar, Content Library, Workflows, AI Assistant, Analytics,
Reports, Integrations, Team, Billing. Per
[SPRINT_01_FOUNDATION.md §Explicitly excluded from Sprint 1](../14-sprints/SPRINT_01_FOUNDATION.md#explicitly-excluded-from-sprint-1),
almost all of that is **out of scope right now**: no email campaigns, no social integrations,
no AI generation, no billing, no advanced automation — regardless of how fully the mockup
depicts them.

What *is* near-term relevant to already-tracked Sprint 1 work:

- The **login screen** (dark navy gradient, glass card, role-based entry) — relevant to
  `GRX-AUTH-002` (password hashing + login/logout) once its frontend piece is built.
- The **visual system** (color tokens, card style, gradient buttons, typography) — relevant
  to any Sprint 1 UI, including `GRX-FOUND-008`'s dashboard shell.
- The **sidebar navigation shell and active/inactive nav-item styling** — `GRX-FOUND-008`
  should follow this pattern, but Sprint 1 only wires up the handful of nav items that
  actually have a Sprint 1 feature behind them (Dashboard placeholder, Team, Settings,
  Audit); every other nav item in the brief (Contacts, Campaigns, Social, AI, Billing, ...)
  is a **future-slice placeholder in the design only** — do not build its content, and do
  not add a real, clickable route for it until its own feature task exists in
  [MASTER_TASK_TRACKER.md](../00-project-control/MASTER_TASK_TRACKER.md).
- The **onboarding flow** (8-step, first-login-only) is not currently a tracked Sprint 1
  task at all — flag it if a future session thinks it's needed for "an admin can log in"
  (Sprint 1's actual acceptance criterion doesn't require onboarding, just login).

If implementing a Sprint 1 UI task and this brief implies something beyond that task's own
acceptance criteria, build only what the task asks for and leave the rest for its own future
task — the same scope discipline already applied to the backend (see
[AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md)).

## Related reference: token architecture (colors unchanged)

[DESIGN_REFERENCE_REVSPOT.md](DESIGN_REFERENCE_REVSPOT.md) captures real extracted design
tokens from a reference product (revspot.ai) and proposes adopting its *token
architecture* (radius scale, spacing, motion easing, a reusable status-chip color
formula) into `globals.css` — explicitly **not** its color palette. Growixa's approved
brand colors (navy/blue/teal/mint, per the brief below) are unchanged.

## Reference files

| File | Location | Status |
|---|---|---|
| `growixa-login-and-dashboard-mockup.html` | [`mockups/growixa-login-and-dashboard-mockup.html`](mockups/growixa-login-and-dashboard-mockup.html) | Present — self-contained, open directly in a browser |
| Live login-screen artifact | https://claude.ai/code/artifact/45781d5f-005b-4a43-90f4-81ebbf989428 | External link (claude.ai-hosted); may require sign-in, may change or expire — the local HTML copy is the durable reference |
| `Growixa Dashboard v2.dc.html` (main app + all pages) | *not present in the repo* | Referenced in the design brief below; add to `mockups/` if/when available |
| `Growixa Onboarding.dc.html` (onboarding flow) | *not present in the repo* | Referenced in the design brief below; add to `mockups/` if/when available |
| `Growixa Style Options.dc.html` (style explorations) | *not present in the repo* | Referenced in the design brief below; add to `mockups/` if/when available |

## Brand assets

Logo files live in [`apps/web/src/assets/`](../../apps/web/src/assets/README.md) (primary,
stacked, icon mark, wordmark, monochrome light/dark variants) — see that folder's own
`README.md` for the full file list.

## Design brief (as given, verbatim)

> Build a marketing/CRM SaaS dashboard web app called "Growixa" with the following pages,
> features, and visual design.
>
> TECH: Use your standard stack (React or similar) — this spec describes behavior and
> visuals only, not literal markup to copy.
>
> ### Auth / Entry
> - Dark navy login screen (gradient background #0B1E3F → #081428 → #052A2E), centered glass
>   card (blur, rounded 24px, deep shadow), Growixa logo/name, two entry buttons: "Sign in as
>   Super Admin" and "Sign in as Team Member" (each sets a role that gates permissions across
>   the app).
> - On first login only, route to a multi-step Onboarding flow (8 steps, progress indicator,
>   Back/Next, gradient "Finish" button on last step). Persist a flag once onboarding
>   completes (localStorage or user profile) so returning users skip straight to the
>   Dashboard.
>
> ### Shell / Navigation
> - Left sidebar, dark navy-to-teal gradient (150deg, #0B1E3F → #0A2A2C), containing: brand
>   mark, nav items (Dashboard, Contacts, Segments, Leads, Campaigns, Social & Calendar,
>   Content Library, Workflows, AI, Analytics, Reports, Integrations, Team, Billing,
>   Settings). Active item: teal/mint tint background (rgba(18,184,176,.16)) with mint text
>   (#5EEAD4); inactive: muted slate (#9CA9C7).
> - Top area shows page title, and a contact-limit banner when relevant.
> - Main content area is a single scrollable panel; each nav item swaps the content shown
>   there (no separate page reloads).
>
> ### Visual system (apply everywhere)
> - Background: light gray/white app canvas, cards on white.
> - Cards: no hard borders — white fill, 16-20px radius, soft shadow
>   (0 4px 24px rgba(15,42,86,.07)).
> - Primary buttons: gradient pill, 135deg #1457E6 → #12B8B0, white bold text, 13-14px
>   radius.
> - Accent colors: primary blue #1457E6, teal/mint #12B8B0 / #5EEAD4, success green #22A06B,
>   muted slate text #64748B / #94A3B8, dark text #0B1B33.
> - Typography: system sans, bold numerics (800 weight) for stats, 12-15px labels.
>
> ### Dashboard page
> - KPI row: "Total Contacts" as a hero card — dark navy/teal gradient, white text, soft
>   radial mint glow in corner, big stat (24,850), pill-style delta badge ("▲ 8.2% this
>   month" on translucent mint chip). Other KPI cards (Active Campaigns, etc.) stay on white
>   cards.
> - Campaign performance: rounded gradient bar chart, 6 bars, percentage label above each
>   bar, the peak bar highlighted in mint/teal gradient with a glow shadow and a filled pill
>   label; other bars in a lighter blue gradient.
> - Social performance card: connected-platform row (LinkedIn icon + connection status +
>   green online dot), a radial/donut gauge (SVG arc, mint-to-teal gradient stroke) showing
>   engagement rate % in the center, a delta line below it, then a divider and an
>   impressions stat with a green delta chip.
> - Recent campaigns: list of rows, each with a small circular gradient avatar swatch,
>   campaign name, status pill (color-coded by status), recipient count, open rate.
> - Recent activity / Approval queue sections below, simple list rows.
>
> ### Contacts / Segments / Leads / Campaigns / Content Library / Workflows / Analytics /
> ### Reports / Integrations / Team / Billing / Settings pages
> - Each is its own content block scoped strictly to its own nav selection (no shared/leaking
>   widgets between pages — verify each page only renders its own content and no other
>   page's widgets ever appear elsewhere).
> - Follow the same card style, color system and table/list row patterns described above;
>   consult the attached HTML files for exact per-page layouts, copy, and data shapes.
>
> ### Social & Calendar page (special — do not show this content on any other page)
> - Weekly calendar grid of scheduled posts, plus two widgets specific to this page only:
>   "Platform comparison (30d)" and "Recent posts" — these must render exclusively here.
>
> ### Reference files
> Recreate pixel-for-pixel from the attached: Growixa Dashboard v2.dc.html (main app + all
> pages), Growixa Onboarding.dc.html (onboarding flow), Growixa Style Options.dc.html (style
> explorations, if relevant). These are HTML/CSS design references, not production code —
> reimplement them idiomatically in your codebase's framework and component patterns.
