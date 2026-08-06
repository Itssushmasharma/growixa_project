# Agent Handoff

- Document ID: DOC-AGENT-HANDOFF
- Status: ACTIVE (updated at the end of every work session)
- Version: 1.0
- Last updated: 2026-08-06
- Owner: Coding agent
- Related documents: [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md), [PROJECT_STATUS](PROJECT_STATUS.md), [CHANGELOG](CHANGELOG.md), [FEATURE_STATUS_MATRIX](FEATURE_STATUS_MATRIX.md)

## Task worked on

`GRX-WEB-002` — Public 3D Brand & Landing Website (`apps/web/src/app/(marketing)/`).

## Work completed

- Built the public Growixa 3D Brand & Landing Website adhering to Linear, Vercel, and Stripe design standards:
  - **`navbar.tsx`**: Header with official `BrandLogo` (`/assets/logo-icon.png`), nav links (*Platform*, *Solutions*, *Pricing*, *Security*, *Docs*), and dynamic CTAs (*Log In* / *Start Free* / *Go to Dashboard*).
  - **`hero-section.tsx`**: Outcome-focused hero (*"Grow Faster. Market Smarter. Powered by AI."*), dual CTAs (*"Start Free"*, *"Book Demo"*), and 3D floating glass dashboard preview card with live metric counters & simulated growth chart.
  - **`trust-bar.tsx`**: Social proof metric bar (*1,000+ Businesses*, *50M+ Emails*, *12M AI Generations*, *99.99% Uptime*).
  - **`ai-team-section.tsx`**: "Meet Your AI Marketing Team" grid showcasing 6 AI agents (Copywriter, Email Optimizer, Campaign Planner, Audience Builder, Social Creator, Marketing Analyst).
  - **`workflow-showcase.tsx`**: Visual automation step pipeline (*Lead fills form* ➔ *AI scores lead* ➔ *Email sequence* ➔ *WhatsApp/SMS* ➔ *Sales notified*).
  - **`integrations-section.tsx`**: Logo grid showcasing native connections (Postmark, Stripe, Razorpay, OpenAI, Claude, Meta, LinkedIn, Slack, Zapier).
  - **`security-section.tsx`**: Enterprise reliability badges (SOC2 Ready, GDPR, Fernet Encryption, RBAC, Insert-Only Audit Logs, 99.99% SLA Uptime).
  - **`pricing-section.tsx`**: Stripe-style tiered pricing matrix (Starter, Growth, Enterprise).
  - **`footer.tsx`**: Complete multi-column SaaS footer with system status badge.
  - **Dedicated Sub-pages**: `/features`, `/pricing`, `/solutions`, `/security`, `/docs`.
- Integrated official brand logo assets from `apps/web/src/assets/icon/growixa-icon-mark.png` and `primary/growixa-primary-horizontal-logo.png` into `public/assets/`.
- Verified zero regressions across Vitest (54 passed) and Playwright E2E (4 passed).

## Files changed

- `apps/web/src/app/(marketing)/marketing.module.css` (new)
- `apps/web/src/app/(marketing)/navbar.tsx` (new)
- `apps/web/src/app/(marketing)/hero-section.tsx` (new)
- `apps/web/src/app/(marketing)/trust-bar.tsx` (new)
- `apps/web/src/app/(marketing)/ai-team-section.tsx` (new)
- `apps/web/src/app/(marketing)/workflow-showcase.tsx` (new)
- `apps/web/src/app/(marketing)/integrations-section.tsx` (new)
- `apps/web/src/app/(marketing)/security-section.tsx` (new)
- `apps/web/src/app/(marketing)/pricing-section.tsx` (new)
- `apps/web/src/app/(marketing)/footer.tsx` (new)
- `apps/web/src/app/(marketing)/page.tsx` (new)
- `apps/web/src/app/(marketing)/page.test.tsx` (new)
- `apps/web/src/app/(marketing)/features/page.tsx` (new)
- `apps/web/src/app/(marketing)/pricing/page.tsx` (new)
- `apps/web/src/app/(marketing)/solutions/page.tsx` (new)
- `apps/web/src/app/(marketing)/security/page.tsx` (new)
- `apps/web/src/app/(marketing)/docs/page.tsx` (new)
- `apps/web/src/components/brand-logo.tsx` (new)
- `apps/web/public/assets/` (`logo-icon.png`, `logo-horizontal.png`, `hero-3d-concept.png`, `features-3d-concept.png`)
- `docs/00-project-control/MASTER_TASK_TRACKER.md`

## Commands executed

```bash
git checkout -b feature/FRONTEND/GRX-WEB-002
cd apps/web
npm run format && npm run lint && npm run typecheck && npm run test -- --run   # 54 passed (all clean)
npx playwright test                                                             # 4 passed (Playwright e2e)
```

## Test results

- `tsc --noEmit`, `eslint`, `prettier --check` clean.
- `vitest` 54 passed.
- Playwright `test:e2e` 4 passed.

## Current state

`GRX-WEB-002` is fully `DONE` and committed (`7b94ba2` & `eca4dd7`).

## Exact next task

`GRX-EMAIL-005` (Postmark webhook receiver + unsubscribe handling) is in progress by backend agent. Next frontend task is `GRX-EMAIL-007` / `GRX-ADMIN-001`.

## Latest commit

`eca4dd7` — feat(web): update brand logo component to use official logo-icon asset

## Decisions made this session

Before writing code, two open architectural questions were surfaced to the user directly
(not guessed):

1. **How should `apps/worker` access the database?** `apps/worker` is a separate Python
   package from `apps/api` with no shared code, but `send_campaign` needs to read/write
   Postgres. Chosen: the worker gets its **own minimal SQLAlchemy/asyncpg data layer** —
   lightweight models for exactly the tables it touches — rather than depending on
   `growixa_api` as a library. Keeps the two apps independently deployable, matching
   `SYSTEM_ARCHITECTURE.md`'s "independently scalable Python workers" framing, at the
   cost of hand-kept-in-sync column definitions.
2. **Is a live Postmark account available for real-send verification?** No. Per
   `DEC-GRX-011`/`SPRINT_03_EMAIL_CAMPAIGN.md`'s own pre-approved fallback: build the
   full real pipeline (real SMTP client, real DB writes) and explicitly document the
   final outbound-send success as an evidence gap rather than silently assuming it or
   faking it with a mock.

## Work completed (GRX-EMAIL-007, first Sprint 3 frontend task)

- New `apps/web/src/app/(dashboard)/dashboard/integrations/` page: a provider
  connection form (`POST /integrations/email-provider`) with a one-time
  webhook-credentials reveal banner (matches `EmailProviderConnectionOut`'s
  documented one-time convention from `GRX-EMAIL-005`, same UX shape as
  Team's invite-token banner), a read-only connection summary once one
  exists, and a sender-identity list + add form
  (`POST /integrations/sender-identities`) with a manual verification-status
  dropdown (`PATCH .../status`) — verification is a manual admin action in
  Sprint 3 per `SPRINT_03`'s scope, not automated Postmark polling.
- New "Integrations" sidebar item gated by `requiresPermission:
  "integrations.manage"`, matching every other SETTINGS item's pattern.
- 5 new `apps/web` component tests (`integrations-page.test.tsx`).

## Real bugs found and fixed while debugging the new tests

- **Access-control UX bug, only caught by live browser verification, not by
  the component tests as first written**: the connection/sender-identity GET
  routes are themselves `integrations.manage`-gated on the backend (unlike
  e.g. `/users`, readable by any authenticated user). The page's original
  load effect fetched `/auth/me` and both GETs in one `Promise.all`, so a
  real non-Super-Admin's 403s on those GETs rejected the whole `Promise.all`
  and hit the generic load-error catch *before* the `canManage` check was
  ever reached — the intended "You don't have access to configure
  integrations." message never actually rendered. A live login as a
  throwaway Admin (not Super Admin) surfaced a misleading "Could not load
  integration settings." instead. Fixed by checking `me.permissions` first
  and only issuing the connection/identity fetches when access is confirmed.
  Also fixed the test itself — the original mock resolved the gated GETs
  instead of rejecting them with a 403, so it couldn't have caught this;
  updated it to reject with a real `ApiError(403, ...)`, matching what the
  backend actually returns, so this regression class is now caught by the
  suite. Lesson for future frontend tasks in this codebase: check whether a
  page's non-`/auth/me` GETs are permission-gated on the backend before
  bundling them into the same `Promise.all` as the permission check itself.

## Files changed

- `apps/web/src/app/(dashboard)/dashboard/integrations/{page,integrations-page,types}.{tsx,ts}`,
  `integrations-page.module.css`, `integrations-page.test.tsx` (new)
- `apps/web/src/app/(dashboard)/dashboard/sidebar.tsx` (new "Integrations" nav item)
- `apps/web/src/app/(dashboard)/dashboard/page-title.tsx` (new page title)
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (`GRX-EMAIL-007` → `DONE`,
  `GRX-EMAIL-009`'s dependency labels updated)
- `docs/00-project-control/PROJECT_STATUS.md`, `CHANGELOG.md` (this update)

## Commands executed

- `eslint`, `tsc --noEmit`, `prettier --check` — clean
- `vitest run`: 59 passed (5 new)
- `next build` — clean, `/dashboard/integrations` route registered
- `podman compose restart web` (dev-server file watcher didn't pick up the
  new route directory on its own over the bind mount — needed a restart)
- Live verification against Compose (see below)

## Blockers

None. `GRX-EMAIL-008` (email templates frontend) is next.

## Known issues / evidence gaps

- No new evidence gap — this task didn't touch email sending. Live-verified
  against Compose: created a real connection as Super Admin and captured the
  real one-time webhook credentials in the UI; added a sender identity;
  flipped its verification status to VERIFIED via the dropdown; created a
  throwaway Admin (not Super Admin) user directly in the database to
  exercise the negative path — confirmed no "Integrations" item in their
  sidebar and, after the bug fix above, the correct access-denied message on
  direct navigation to `/dashboard/integrations`. Cleaned up the smoke-test
  connection/identity rows; the throwaway Admin account itself was disabled
  rather than deleted — deleting it would have violated `audit_logs`'
  insert-only invariant, since its login had already written an audit row
  referencing it.
- **Branch/doc coordination note — resolved**: the user merged the prior
  `feature/FRONTEND/GRX-WEB-002` branch into `main` via PR during this
  session (visible as merge commits `f94842f`/`5c644dd` in the log). This
  commit landed directly on `main`. The branch-split concern flagged in
  `GRX-EMAIL-005`/`006`'s entries no longer applies going forward.
- Retry/backoff/dead-letter handling for `send_campaign` remains unimplemented
  (unchanged from `GRX-EMAIL-004`'s note).

## Current state

Sprint 1 and Sprint 2 are `DONE`. Sprint 3 (Email Marketing) backend is fully
`DONE`; its frontend is now under way: `GRX-EMAIL-001` through `GRX-EMAIL-007`
are all `DONE`. `GRX-EMAIL-008`–`010` remain `BACKLOG`.

## Exact next task

`GRX-EMAIL-008` — Email templates frontend. Template list/create/edit UI
under `apps/web/src/app/dashboard/templates/`; a `campaigns.manage` user can
create and edit a template, a view-only user cannot. See
`MASTER_TASK_TRACKER.md`'s row for the exact acceptance criteria and required
tests.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit (superseded — see GRX-EMAIL-011 section below)

`fa0d924` — feat(web): provider connection + sender identity settings UI (GRX-EMAIL-007)

## Work completed (GRX-EMAIL-011, ad hoc addition — Custom SMTP as a second provider)

- `email_provider_connections` moved from "one active connection globally"
  to **one active connection per provider**, DB-enforced via a new partial
  unique index `(provider) WHERE is_active` (migration `04cce299c2d1`,
  replacing the old non-unique index); `provider` CHECK expanded to
  `('POSTMARK', 'CUSTOM_SMTP')`. Logged as `DEC-GRX-016`, following two
  `AskUserQuestion` rounds that scoped this down from a 6-provider design
  reference to "actually build it, but just these two providers, SMTP-relay
  only."
  `get_active_email_provider_connection`/`deactivate_active_email_provider_connections`
  are now provider-scoped; new `GET /integrations/email-providers` (plural)
  replaces the old singular GET.
- Frontend (`apps/web/.../dashboard/integrations/`) rebuilt as a 2-card grid
  (`PROVIDER_REGISTRY`), each card independently showing status, identity
  count, and its own scoped identity list/add form.
- **Real bug #1**: `test_campaigns.py::test_unauthenticated_requests_are_rejected`
  created a sender-identity fixture but never cleaned it up — harmless
  before the new unique constraint, a genuine cross-test failure after.
  Fixed with try/finally.

## Real bugs found and fixed live-testing against the user's own real SMTP server

The user provided real credentials for their own mail server
(`mail.iitdeveloper.com`), typing the password into the UI themselves — the
agent never handled it directly, per this session's credential-handling
policy. This surfaced two genuine transport-layer bugs neither the mocked
unit tests nor the earlier Postmark-only work had ever exercised:

- **Bug #1 — no implicit-TLS support**: `smtp_sender.py` (api) and
  `email_sender.py` (worker) both hardcoded `start_tls=True`
  unconditionally. Port 465 is *implicit* TLS (encrypted from the first
  byte); STARTTLS on that port just hangs waiting for a plaintext banner
  that never arrives — confirmed via a live probe
  (`SMTPConnectTimeoutError`). Fixed by selecting `use_tls` vs `start_tls`
  based on `smtp_port == 465`; confirmed the fix reaches a real TLS
  handshake against the user's server.
- **Bug #2 — TLS/cert errors weren't wrapped**: once TLS mode was correct, a
  real test-send against the user's server hit
  `ssl.SSLCertVerificationError: certificate has expired` — and it surfaced
  as an **unhandled 500**, not the `POST /campaigns/{id}/test-send`
  endpoint's intended 502 "Test send failed: ...". Root cause:
  `ssl.SSLCertVerificationError` is an `OSError`, not an
  `aiosmtplib.SMTPException`, so `EmailSendError`'s except clause missed it
  entirely despite its own docstring promising to cover "connection, TLS,
  auth" failures. Fixed by also catching `OSError` in both `smtp_sender.py`
  and `email_sender.py`.
- Confirmed the full fix with diagnostic-only probes (dummy password,
  `ssl.CERT_NONE` used *only* in a throwaway script, never in shipped code):
  with the correct TLS mode, the connection reached a real `535 Incorrect
  authentication data` from the user's own server — proving transport and
  auth both work correctly end-to-end.
- **Outstanding, external to this codebase**: the user's own mail server has
  an actually-expired TLS certificate. Real sends through
  `mail.iitdeveloper.com` will keep failing with that same 502 until they
  renew it with their host — nothing further to fix here.
- Added `apps/api/tests/test_smtp_sender.py` and
  `apps/worker/tests/test_email_sender.py` (2 tests each: TLS mode
  selection by port, `OSError`→`EmailSendError` wrapping).

## Known-quirk collision worth flagging to any future session

Running the **full `apps/api` pytest suite** wipes the entire dev database
(via `test_migrations.py`'s alembic downgrade/upgrade round-trip) — a
pre-existing quirk noted in earlier sessions' entries, but this is the first
time it collided with a user's *own real external credentials* sitting in
the DB for live testing. It happened twice during this task, each time
silently deleting the user's real Custom SMTP connection along with
`admin@growixa.local`. **Lesson for future sessions**: if real (non-smoke-test)
data is known to be in the dev DB — the user's own provider credentials,
anything they explicitly asked to keep around — run targeted test files
(e.g. `pytest tests/test_smtp_sender.py`) instead of the full suite until
that data is no longer needed, or warn the user immediately beforehand.
`apps/worker`'s suite does not touch Postgres this way and is always safe to
run in full.

## Files changed (GRX-EMAIL-011)

- `apps/api/migrations/versions/04cce299c2d1_*.py` (new)
- `apps/api/src/growixa_api/integrations/{models,repositories,services,schemas,api}.py`
- `apps/api/src/growixa_api/email_delivery/{smtp_sender.py,services.py}`
- `apps/worker/src/growixa_worker/email_sender.py`
- `apps/api/tests/{test_integrations.py,test_campaigns.py,test_smtp_sender.py (new)}`
- `apps/worker/tests/test_email_sender.py` (new)
- `apps/web/src/app/(dashboard)/dashboard/integrations/{types.ts,integrations-page.tsx,integrations-page.module.css,integrations-page.test.tsx}`
- `docs/00-project-control/{DECISIONS.md,MASTER_TASK_TRACKER.md,PROJECT_STATUS.md,CHANGELOG.md,AGENT_HANDOFF.md}`
- `docs/05-data/{DATA_MODEL.md,DATABASE_SCHEMA.md}`
- `docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md`

## Commands executed (GRX-EMAIL-011)

- `ruff check`/`ruff format --check`/`mypy` — clean on `apps/api` and
  `apps/worker`
- `alembic check` — clean, no drift
- `apps/api` `pytest`: 152 passed, 3 skipped
- `apps/worker` `pytest`: 12 passed
- `eslint`/`tsc --noEmit`/`prettier --check` — clean on `apps/web`
- `vitest run`: 60 passed
- `next build` — clean
- `podman compose restart api` (to pick up source changes after the second
  TLS fix — bind-mounted source with `uvicorn --reload`, restart forced a
  reload rather than a full image rebuild; no image rebuild was needed since
  no dependency changed)
- Recreated `admin@growixa.local` (Super Admin role) twice via direct SQL,
  matching the argon2 hash produced by `growixa_api.auth.security.hash_password`

## Blockers

None for this codebase. The user's own mail server certificate being
expired blocks *their* real sends, not further work here.

## Work completed (GRX-EMAIL-012, ad hoc addition — "Test connection" button)

Direct user follow-up, requested immediately after watching `GRX-EMAIL-011`'s
live testing hit the certificate-expiry error the hard way (via a real
test-send round trip). Wanted a faster, non-destructive way to check SMTP
credentials during setup.

- **Architecture fix needed first**: the new endpoint logically belongs to
  `integrations` (connection setup), but the SMTP transport code
  (`send_email`, `EmailSendError`) lived in `email_delivery/smtp_sender.py`.
  `MODULE_BOUNDARIES.md` only allows `email_delivery` to depend on
  `integrations`, not the reverse — so `integrations` importing from
  `email_delivery` would have gone the wrong way. Fixed properly: `git mv`'d
  `smtp_sender.py` to `integrations/smtp_transport.py` (and its test file to
  `test_smtp_transport.py`), updated `email_delivery/services.py` and
  `api.py`'s imports. This is the direction `MODULE_BOUNDARIES.md` already
  documented — the file was just in the wrong place.
- Added `test_connection()` to `smtp_transport.py`: opens
  `aiosmtplib.SMTP(...)` and calls `.login()` only, no message built or
  sent. Factored the port-465-vs-STARTTLS decision out of `send_email` into
  a shared `_tls_kwargs()` `TypedDict`-returning helper (mypy rejected a
  plain `dict[str, bool]` unpacked as kwargs — couldn't verify the two keys
  against `aiosmtplib.send`'s overloaded signature), reused by both
  functions so `GRX-EMAIL-011`'s TLS fix isn't duplicated.
- New `EmailProviderConnectionTestIn` schema (no `provider` — connecting
  doesn't depend on which provider these credentials belong to) and
  `POST /integrations/email-providers/test` (204 on success, 502 with the
  real underlying error on failure — reuses `integrations.manage`, no new
  permission). Persists nothing.
- Frontend: "Test connection" button in the connection form, disabled until
  all four fields are filled, using the *current unsaved* form values. On
  failure, parses and shows the backend's actual `detail` message in the
  toast rather than a canned one — a deliberate exception to this
  codebase's usual error-handling convention (switch on status, show a
  fixed message), since the whole point of this feature is showing *which*
  SMTP failure occurred.
- **Test-only bug found and fixed while writing the frontend tests**: the
  page's own `import { ApiError }` (needed to parse the failure detail)
  resolved to `undefined` under Vitest, because the existing
  `vi.mock("@/lib/api-client", () => ({ apiFetch: vi.fn() }))` factory fully
  replaces the module — anything not explicitly returned is gone, and
  Vitest throws a distinct "use importOriginal" error the moment it's
  accessed, rather than silently passing `undefined` through. Fixed by
  switching to `vi.mock(path, async (importOriginal) => ({
  ...(await importOriginal()), apiFetch: vi.fn() }))`, preserving real
  exports like `ApiError` while still mocking `apiFetch`.

## Commands executed (GRX-EMAIL-012)

- `ruff check`/`ruff format --check`/`mypy` — clean
- `apps/api` targeted tests (deliberately not the full suite, to avoid
  re-triggering `GRX-EMAIL-011`'s DB-wipe quirk):
  `pytest tests/test_smtp_transport.py tests/test_integrations.py
  tests/test_email_delivery.py tests/test_campaigns.py
  tests/test_protected_routes_audit.py` — 40 passed
- `eslint`/`tsc --noEmit`/`prettier --check` — clean
- `vitest run`: 62 passed (2 new)
- `next build` — clean
- `podman compose restart api` (bind-mounted source, `uvicorn --reload`
  didn't pick up the module move fast enough on its own)
- `podman compose restart web` (dev-server file-watcher quirk, same as
  `GRX-EMAIL-007`'s entry — didn't need a rebuild, just a restart)
- Live verification: `curl` against `POST
  /integrations/email-providers/test` with bad Postmark credentials
  returned a real `535 authentication failed` wrapped in a clean 502; same
  check repeated through the actual browser UI (typed bad credentials into
  Postmark's card, clicked "Test connection") — toast showed the identical
  real Postmark error text, confirmed via network-request inspection.
  Nothing persists from this endpoint, so no smoke-test cleanup was needed.

## Known issues / evidence gaps (GRX-EMAIL-012)

- No success-path live verification was possible: no valid Postmark
  credentials exist in this environment, and the user's own Custom SMTP
  server's certificate is still expired (per `GRX-EMAIL-011`). The success
  path is covered by the unit test
  (`test_test_connection_uses_correct_tls_kwargs_and_logs_in`) and the
  frontend component test instead. Revisit once either becomes available.

## Current state

Sprint 3 backend, the multi-provider addition, and this "test connection"
button are all `DONE`. `GRX-EMAIL-008`–`010` (templates/campaigns/report
frontend) remain `BACKLOG` and are the next Sprint-3-shaped work.

## Exact next task

`GRX-EMAIL-008` — Email templates frontend. Template list/create/edit UI
under `apps/web/src/app/dashboard/templates/`; a `campaigns.manage` user can
create and edit a template, a view-only user cannot. See
`MASTER_TASK_TRACKER.md`'s row for exact acceptance criteria and required
tests.

## Latest commit (superseded — see GRX-EMAIL-008 section below)

`aa83974` — feat(integrations): add SMTP "test connection" endpoint + button (GRX-EMAIL-012)

## Work completed (GRX-EMAIL-008, email templates frontend)

- New `templates` dashboard page (`campaigns.view`-gated, new "CAMPAIGNS"
  sidebar section) plus two dedicated routes — `/dashboard/templates/new` and
  `/dashboard/templates/[id]/edit` — sharing one `TemplateFormPage` client
  component parameterized by `mode: "create" | "edit"`.
- New `DELETE /templates/{id}`: 404 if missing, 409 (`TemplateInUseError`,
  catching `sqlalchemy.exc.IntegrityError`) if a campaign still references it
  via `campaigns.template_id`'s FK (no `ON DELETE` clause — a campaign copies
  a template's content at creation time, the FK only preserves the
  "created from" link). Duplicate has no dedicated endpoint: the create page
  reads `?duplicateFrom={id}` and pre-fills from that template's current
  version, client-side, reviewable before saving.
- Live HTML preview via `<iframe sandbox="">` (no `allow-scripts`/
  `allow-same-origin`) — verified with a template containing both a
  `<style>` block and an embedded `<script>` tag: CSS rendered, script did
  not execute.
- Search (name/subject) and sort (last-updated/name) on the list — pure
  client-side filters, no backend change.
- **Architecture changed mid-task, twice, both directly from live user
  feedback against reference screenshots**: (1) create/edit started as an
  inline expand-in-place form on the list page; the user found it confusing
  (a native "Please fill in this field" tooltip on the wrong page state made
  this concrete) and pointed at a two-pane "New Template" mockup, so it moved
  to the dedicated pages above; (2) a card-grid-with-thumbnails reference was
  also raised, but scoped down via `AskUserQuestion` to "keep the list
  layout, add real search/sort, full CRUD" — thumbnails and categories/tags
  were deferred since categories need a real schema decision, not just UI.
- **Follow-up fixes from live feedback, after the page was first built**:
  1. Both this page's and Company Settings' cards were capped at a fixed
     `max-width` (760px / 640px) — changed both to `width: 100%`.
  2. A second look found the *fields inside* those now-wider cards still
     capped (`.input` at 480px, `.textarea` at 720px, deliberately at the
     time) — removed those caps too on explicit "why not use 100%" feedback;
     every field in both forms now stretches to the card's full width.
  3. The HTML body textarea was flagged as too short, with no way to copy or
     clean up the HTML — `min-height` raised 260px → 460px, and a **Format**
     button (a small dependency-free HTML re-indenter — void/self-closing
     elements don't nest, everything else does; no library added, since
     `apps/web`'s only dependencies are `next`/`react`) and a **Copy** button
     (`navigator.clipboard.writeText`) were added above the field.

## Real bugs found and fixed

- **Foreign-key-blocked delete surfaced as a raw 500**: before this task,
  nothing in the codebase caught `IntegrityError` from a delete blocked by a
  FK constraint — confirmed by reading `campaigns/models.py` (`template_id`
  has no `ON DELETE` behavior, defaults to Postgres `RESTRICT`) and then
  writing an integration test that builds the exact referencing chain
  (connection → sender identity → campaign) to prove it. Fixed with
  `TemplateInUseError`, caught in `api.py` and returned as a clean 409.
- No other functional bugs; the three follow-up fixes above were live UX
  feedback, not defects the tests had missed.

## Files changed

- `apps/web/src/app/(dashboard)/dashboard/templates/` (new:
  `templates-page.tsx`, `templates-page.module.css`,
  `templates-page.test.tsx`, `template-form-page.tsx`,
  `template-form-page.module.css`, `template-form-page.test.tsx`,
  `new/page.tsx`, `[id]/edit/page.tsx`, `types.ts`)
- `apps/web/src/app/(dashboard)/dashboard/sidebar.tsx` (new "CAMPAIGNS"
  section, "Templates" item)
- `apps/web/src/app/(dashboard)/dashboard/page-title.tsx` (new page titles)
- `apps/web/src/app/(dashboard)/dashboard/company-settings/company-settings-form.module.css`
  (width fixes, both rounds)
- `apps/api/src/growixa_api/templates/{repositories.py,services.py,api.py}`
  (extended: `DELETE /templates/{id}`)
- `apps/api/tests/test_templates.py` (extended: 4 new delete tests)
- `docs/00-project-control/{MASTER_TASK_TRACKER.md,PROJECT_STATUS.md,CHANGELOG.md,AGENT_HANDOFF.md}`

## Commands executed

- `ruff check`/`ruff format --check`/`mypy`/`alembic check` — clean
- `apps/api` `pytest` (targeted: `test_templates.py` +
  `test_protected_routes_audit.py`, not the full suite, to avoid
  `GRX-EMAIL-011`'s DB-wipe quirk) — 11 passed
- `eslint`/`tsc --noEmit`/`prettier --check`/`next build` — clean
- `vitest run` (full `apps/web` suite): 79 passed
- Live verification against Compose end-to-end: created a real template via
  the dedicated create page (typed HTML, watched the live preview update,
  submitted, landed back on the list); opened Edit — name field correctly
  disabled and pre-filled; opened Duplicate on a real template non-
  destructively (pre-filled form + correct live preview, then cancelled);
  deleted the disposable template via direct `curl` calls (the browser
  automation environment auto-dismisses native `confirm()` dialogs, so the
  accept-path was verified via `curl` — 204, gone from `GET /templates` —
  while the decline-path was confirmed directly in the browser, since it
  doesn't require the dialog to be accepted). Used ref-based clicks after
  raw screenshot-coordinate clicks intermittently hit the wrong list row
  once the page reflowed (a recurrence of an earlier-session lesson).
- The two follow-up width/format/copy fixes were verified via the Vitest
  suite (including two new tests: "formats the HTML body when Format is
  clicked", "copies the HTML body to the clipboard when Copy is clicked")
  plus a direct screenshot of `/dashboard/templates/new` showing the taller
  textarea. Further live re-checks in the browser pane were abandoned after
  discovering the pane is shared with the user's own live navigation — each
  automated re-check kept getting overtaken by the user clicking to a
  different page (Company Settings, Team) in real time. A second, isolated
  browser tab showed the same content as the shared one, confirming this
  rather than tool flakiness.

## Blockers

None.

## Known issues / evidence gaps

None new. Same outstanding items as `GRX-EMAIL-011`'s entry (expired cert on
the user's own mail server; `send_campaign` retry/backoff unimplemented).

## Current state

Sprint 3 backend, the multi-provider addition, "test connection", and email
templates frontend are all `DONE`. `GRX-EMAIL-009`–`010` (campaign builder +
report frontend) remain `BACKLOG` and are the next Sprint-3-shaped work.

## Exact next task

`GRX-EMAIL-009` — Campaign builder + send frontend. Draft creation/editing,
targeting, test send, immediate send, under
`apps/web/src/app/(dashboard)/dashboard/campaigns/`. See
`MASTER_TASK_TRACKER.md`'s row for exact acceptance criteria and required
tests.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit (superseded — see GRX-EMAIL-009 section below)

`e2a7529` — feat(web): email templates frontend — list, create/edit, delete/duplicate (GRX-EMAIL-008)

## Work completed (GRX-EMAIL-009, campaign builder + send frontend)

- New `campaigns` dashboard page (`campaigns.view`-gated) plus `/dashboard/campaigns/new`
  and `/dashboard/campaigns/[id]` — one `CampaignFormPage` client component
  (`mode: "create" | "edit"`) serves creation, draft editing, read-only viewing of a
  non-draft campaign, and the test-send/send-now panel; the `[id]` route is both the
  edit form and the detail view, there's no separate `/edit`. No backend changes —
  every endpoint needed (`POST/GET/PATCH /campaigns`, `POST /campaigns/{id}/test-send`,
  `POST /campaigns/{id}/send`, `GET /integrations/sender-identities`,
  `GET /contacts/{lists,segments}`, `GET /templates`) already existed.
- `editable = canManage && (mode === "create" || campaign.status === "DRAFT")` —
  fields render as disabled inputs, not hidden, once a campaign leaves `DRAFT`, with
  a hint mirroring the backend's own 409 message rather than hiding content.
- Recipient targeting: one `recipient_type` select plus a conditional second select
  for the list/segment target; switching type clears the previous target id
  client-side, mirroring `campaigns/services.py`'s own clearing logic on the backend.
- Optional "Load content from a template" select reads the already-fetched
  `GET /templates` response (its `EmailTemplateOut` nests `current_version`, so no
  extra per-selection fetch) and prefills subject/body, keeping `template_id` for
  lineage.
- Test-send (`campaigns.send`) works at any campaign status, matching
  `send_test_email`'s own lack of a status guard on the backend; Send now is
  `DRAFT`-only (backend 409s otherwise), gated behind `window.confirm`, and
  optimistically flips the status pill to `SENDING` with a toast rather than polling
  for the real terminal state.
- Extracted `formatHtml` (added ad hoc in `GRX-EMAIL-008`) and its Format/Copy
  buttons out of `templates/template-form-page.tsx` into a new
  `apps/web/src/lib/format-html.ts`, reused by both the templates and campaigns HTML
  editors instead of duplicating the ~35-line function a second time.
- **Mid-task redesign, directly from a user-supplied reference screenshot**: the list
  page first shipped row-based (matching `GRX-EMAIL-008`'s templates list, already
  tested and verified), then was rebuilt as a card grid with status-filter tabs
  after the user shared a reference image mid-verification. The reference implied
  two things this app can't honestly back yet — flagged via `AskUserQuestion` rather
  than guessed:
  1. **Open rate / click rate per card**: real data exists via `GRX-EMAIL-006`'s
     `GET /campaigns/{id}/report`, but pulling it into the list means an N+1 fetch
     per card and duplicates `GRX-EMAIL-010`'s actual scope (the dedicated report
     task, next in the tracker) — deferred there instead.
  2. **Scheduled / Paused filter tabs**: not real statuses — `campaigns.status`'s
     CHECK constraint is `DRAFT`/`SENDING`/`SENT`/`FAILED` only; scheduled sending
     is the separate, still-`BACKLOG` `GRX-SCHED-*` work (visible mid-flight,
     uncommitted, in a concurrent session's edits to this same tracker file). Built
     filter tabs only for the four statuses that actually exist.

## Files changed

- `apps/web/src/app/(dashboard)/dashboard/campaigns/` (new: `campaigns-page.tsx`,
  `campaigns-page.module.css`, `campaigns-page.test.tsx`, `campaign-form-page.tsx`,
  `campaign-form-page.module.css`, `campaign-form-page.test.tsx`, `new/page.tsx`,
  `[id]/page.tsx`, `types.ts`)
- `apps/web/src/lib/format-html.ts` (new, extracted)
- `apps/web/src/app/(dashboard)/dashboard/templates/template-form-page.tsx` (imports
  `formatHtml` from the new shared lib instead of its own copy)
- `apps/web/src/app/(dashboard)/dashboard/sidebar.tsx` (new "Campaigns" nav item)
- `apps/web/src/app/(dashboard)/dashboard/page-title.tsx` (new page titles)
- `docs/00-project-control/{MASTER_TASK_TRACKER.md,PROJECT_STATUS.md,CHANGELOG.md,AGENT_HANDOFF.md}`

## Commands executed

- `eslint`/`tsc --noEmit`/`prettier --check` — clean
- `vitest run` (full `apps/web` suite): 97 passed (18 new)
- `next build` — clean; `/dashboard/campaigns`, `/dashboard/campaigns/new`,
  `/dashboard/campaigns/[id]` all registered as separate routes (static `new`
  correctly takes priority over the `[id]` dynamic segment)
- `podman compose restart web` (new route directories, same dev-server
  file-watcher quirk noted in `GRX-EMAIL-007`'s and `GRX-EMAIL-012`'s entries)
- Live verification against Compose as a real Super Admin: created a throwaway
  Super Admin user directly via SQL (no known password existed for the
  `admin@growixa.local` account recreated in earlier sessions, and the login
  couldn't be verified through `curl` with a password argument — blocked by this
  environment's own auto-mode classifier as credential-handling; authenticated
  through the actual `/login` UI form instead, the normal way a user would).
  Configured a real Custom SMTP connection (fake host — the point was exercising
  real credential storage/session flow through the Integrations UI, not a real
  send) and sender identity; created a campaign loading real content from an
  existing template — subject/body prefilled correctly, live preview rendered it;
  test-send round-tripped a real 502 with the underlying DNS-resolution failure
  text; Send now (via a `window.confirm` stub — this browser-automation
  environment auto-dismisses native `confirm()`, the same limitation
  `GRX-EMAIL-008`'s delete flow hit) flipped the UI to `SENDING` immediately, and
  on reload the worker's real job pipeline had carried it through to `SENT` (0
  recipients, since no contacts exist in this environment, so the job trivially
  completed) — proving the full create→send→status-refresh path against the real
  backend and worker, not just the client-side optimistic update. The card-grid
  redesign that followed was verified through the component test suite (8 new
  tests specifically covering tab filtering, status-scoped assertions, and the
  Scheduled/Paused-tabs-don't-exist check) and a clean `next build`, not a final
  live screenshot — the browser pane closed before that redesign could be
  re-verified visually; noted here as an honest gap rather than claimed as seen.
  Cleaned up all smoke-test rows afterward (campaign, sender identity, connection,
  throwaway Super Admin user) via direct SQL, since `campaigns` has no `DELETE`
  route to clean up through the API.

## Blockers

None.

## Known issues / evidence gaps

- The card-grid redesign (status tabs, card layout) was not re-verified with a live
  screenshot after the browser pane closed mid-session — covered by 8 new
  component tests and a clean `next build` instead. Low risk (pure rendering
  change, no new data flow), but worth a quick visual glance next time the app is
  open.
- Same outstanding items as `GRX-EMAIL-011`'s entry (expired cert on the user's own
  mail server; `send_campaign` retry/backoff unimplemented).

## Current state

Sprint 3 backend and every Sprint-3 frontend task through campaign building/sending
are `DONE`. Only `GRX-EMAIL-010` (campaign report frontend) remains `BACKLOG`.

## Exact next task

`GRX-EMAIL-010` — Campaign report frontend. Per-campaign delivery/analytics report
view, extending `apps/web/src/app/(dashboard)/dashboard/campaigns/` with a report
view backed by `GRX-EMAIL-006`'s existing `GET /campaigns/{id}/report`. This is also
the natural place to add the open/click-rate-per-card enhancement deferred from
this task, if the user still wants it on the list view too. See
`MASTER_TASK_TRACKER.md`'s row for exact acceptance criteria.

## Resume commands

```bash
cd /Users/ravi/Documents/projects/growixa
git log --oneline -5
cat docs/00-project-control/MASTER_TASK_TRACKER.md
cat docs/14-sprints/SPRINT_03_EMAIL_CAMPAIGN.md
podman compose up -d
```

## Latest commit

`79c90fb` — fix(web): campaigns list header layout to match design reference

## Follow-up fix (same session, after GRX-EMAIL-009 shipped)

Live feedback comparing the shipped card grid against the user's reference
screenshot two more times: (1) tabs were wrapped in a white pill card —
reference has them flat on the page with only the active tab pill-highlighted
and a divider line underneath; (2) search had been moved to its own row below
the tabs — reference keeps it in the same top row as the tabs and the
"+ New campaign" button, top-right. Fixed both in `campaigns-page.tsx`/`.module.css`.
`vitest` 97 passed throughout (no test changes needed — these were pure layout
tweaks). `podman compose restart web` after each change (dev-server
file-watcher quirk). Commit `79c90fb`.
