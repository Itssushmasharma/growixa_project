# Changelog

- Document ID: DOC-CHANGELOG
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [PROJECT_STATUS](PROJECT_STATUS.md), [DECISIONS](DECISIONS.md), [MASTER_TASK_TRACKER](MASTER_TASK_TRACKER.md)

Reverse-chronological log of material changes to the Growixa repository (documentation and,
from Sprint 1 onward, code). Each entry names what changed and the commit(s) it landed in.

## 2026-07-31 — GRX-DOC-003: Sprint 1 documentation + handoff update (closes Sprint 1)

- Created `FEATURE_STATUS_MATRIX.md` (new): per-feature implementation status, checked
  against actual code rather than trusted from tracker claims alone.
- Found a real gap while doing that check: `GRX-FEAT-027` (Audit Logs) only has the
  write path — `growixa_api/audit/` has no `api.py`, so there's no `GET` endpoint and no
  frontend page, meaning `audit.view` is a permission code nothing checks. Sprint 1's
  acceptance criterion that audit logs be "visible to users with `audit.view`" was never
  actually met. Filed as new task `GRX-AUDIT-002` (`BACKLOG`) rather than left silent.
- Also confirmed Notifications/Usage Metering/Integrations/Admin Portal — all tagged
  "Slice 1" in `FEATURE_CATALOG.md` — were never in Sprint 1's actual task list
  (`SPRINT_01_FOUNDATION.md`'s "Included" section) and remain `NOT_STARTED`; the
  catalog's slice tags reflect the target release, not delivery.
- Updated `PROJECT_STATUS.md` to reference the new matrix and record Sprint 1 as fully
  `DONE` with that one gap tracked, not hidden.
- This closes Sprint 1 for real (all `GRX-FOUND-*`/`GRX-AUTH-*`/`GRX-USER-*`/`GRX-RBAC-*`/
  `GRX-COMPANY-*`/`GRX-AUDIT-001`/`GRX-TEST-*`/`GRX-DEVOPS-001`/`GRX-DOC-003` are `DONE`).
  Commit `2cc3acc`.

## 2026-07-31 — GRX-DEVOPS-001 confirmed DONE

- The user pushed `main` to GitHub and confirmed the CI workflow (`.github/workflows/ci.yml`,
  built in this task's original commit `7ff54dc`) ran green. Moved `GRX-DEVOPS-001` from
  `IN_REVIEW` to `DONE` in the tracker; this unblocks `GRX-DOC-003` (Sprint 1 documentation
  + handoff update), now `READY`. No code changes in this entry — documentation only.

## 2026-07-31 — GRX-CONTACT-009: Consent/suppression frontend (closes Sprint 2)

- Extended `ContactsPage`'s detail panel with a lazy-loaded (on row expand) consent
  history list (`GET /contacts/{id}/consent`, newest-first) and, for managers, an
  inline record-consent form (channel/status selects + optional source input)
  posting to `POST /contacts/{id}/consent`.
- Built `SuppressionPage` (`/dashboard/contacts/suppression`): a list of all
  suppression entries (email, linked contact or "No matching contact", reason
  badge, timestamp) and, for managers, a "+ Suppress an email" form (email, reason
  select, optional contact picker sourced from `GET /contacts`) posting to `POST
  /contacts/suppression`. Since the backend has no unsuppress endpoint by design
  (`GRX-CONTACT-005`), the UI never offers a remove control.
- Re-suppressing an already-suppressed email is handled by matching the POST
  response's `id` against existing state and replacing in place rather than
  appending, mirroring the backend's upsert-on-email semantics — covered by a
  dedicated test and confirmed live.
- Added "Suppression" to the sidebar's AUDIENCE section and a page-title entry.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 46 passed (7 new: 2
  consent-history/record tests on `ContactsPage`, 5 on `SuppressionPage`).
- Live-verified against the rebuilt dev server: recorded GRANTED then WITHDRAWN
  consent for a contact and confirmed newest-first ordering; suppressed an email
  with a linked contact (its Contacts-page row correctly flipped to "Suppressed"),
  re-suppressed the same email with a different reason and confirmed the entry
  updated in place (still exactly one row); confirmed a fresh Analyst sees both the
  consent history and suppression list read-only with no record-consent form and no
  "+ Suppress an email" button.
- This closes GRX-CONTACT-009 — **all of Sprint 2 (GRX-CONTACT-001 through 009) is
  now DONE.** Commit `81332b5`.

## 2026-07-31 — GRX-CONTACT-008: CSV import frontend

- Built `ImportsPage` (`/dashboard/contacts/imports`): a file picker reads the CSV
  header row client-side, auto-guesses common column→field mappings
  (email/first_name/last_name/phone/source), and renders a target select per column
  (including `custom_field:<key>` options from `GET /contacts/custom-fields`).
  Submitting builds a `column_mapping` JSON string and multipart-POSTs to `POST
  /contacts/imports`.
- This was the frontend's first file upload, which surfaced that `apiFetch`
  unconditionally set `Content-Type: application/json` — fixed by skipping that
  header when the body is a `FormData` instance, letting the browser set its own
  multipart boundary. Added `api-client.test.ts` (new, 2 tests) for this
  previously-uncovered shared utility.
- Below the upload form, an import-history list shows filename/status/counts per
  past import, each expandable via "View rows" into per-row email/status/
  error_message detail. The upload card is omitted entirely (not shown disabled) for
  non-managers.
- Added "Imports" to the sidebar's AUDIENCE section and a page-title entry.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 39 passed (7 new).
- Live verification note: the browser-automation tool cannot drive a native file
  picker dialog, so the "select a file" step itself couldn't be exercised through
  the browser. Instead, uploaded a real 3-row CSV via `curl` multipart (identical
  wire format to `fetch`+`FormData`) and confirmed the resulting history entry,
  counts, and row-level detail all rendered correctly in the browser from real
  backend data; confirmed the imported contacts appeared correctly on the Contacts
  page; confirmed a fresh Analyst sees only the history card, no upload form.
- This closes GRX-CONTACT-008. `GRX-CONTACT-009` (consent/suppression frontend) is
  the last remaining Sprint 2 task. Commit `7796f93`.

## 2026-07-31 — GRX-CONTACT-007: Tags/lists/segments frontend

- Extended `ContactsPage`'s detail panel with tag management: removable chips (an
  `×` button calling `DELETE /contacts/{id}/tags/{tag_id}`, resolving the tag's id
  from a fetched `/contacts/tags` list since `ContactOut.tags` only carries names), a
  select to attach an existing tag, and an inline "+ New tag" form that creates a tag
  and attaches it to the contact in one step.
- Built `ListsPage` (`/dashboard/contacts/lists`): create a list, and per-list
  add/remove-by-contact-picker controls. There is deliberately no member-browsing UI
  — the backend only ever exposed `member_count` for `contact_lists`, not a
  members-list endpoint (unlike segments), and adding one was judged out of this
  task's frontend-only scope.
- Built `SegmentsPage` (`/dashboard/contacts/segments`): a rule builder (field,
  operator, value per row — operators filtered to match each field's allowed set,
  with a `custom_field:<key>` sub-input when "Custom field" is selected), a segment
  list with type/member-count badges and a rule-summary, and "View members" backed
  by the existing `GET /contacts/segments/{id}/members`.
- Refactored the per-page `contacts-page.module.css` into a shared
  `shared.module.css` so contacts/lists/segments reuse one set of card, form, row,
  and badge styles instead of duplicating them three times.
- Added "Lists" and "Segments" to the sidebar's AUDIENCE section (gated
  `contacts.view`) and their page-title entries.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 32 passed (13 new).
- Live-verified against the rebuilt dev server: created a tag inline and attached it
  to a contact, detached and reattached it via the dropdown; created a list and
  added a contact (member count 0→1); created a DYNAMIC segment on `tag equals VIP`
  and confirmed it matched the tagged contact, with "View members" showing the right
  email; confirmed an Analyst sees all three pages' data with no write controls.
- This closes GRX-CONTACT-007. `GRX-CONTACT-008` (CSV import frontend) and
  `GRX-CONTACT-009` (consent/suppression frontend) remain `READY`. Commit `262d28a`.

## 2026-07-31 — GRX-CONTACT-006: Contacts frontend

- Built `ContactsPage` (`apps/web/src/app/dashboard/contacts/`): a list of contacts
  with an inline "+ Add contact" create form and an expandable per-row detail/edit
  panel. Page visibility is gated on `contacts.view`; the create form, edit fields,
  and archive/activate button are gated on `contacts.manage` — a view-only user sees
  a "You have view-only access to contacts." note in place of the edit form.
- The detail panel shows created/updated timestamps and read-only tag chips/custom
  fields (assigning tags or editing custom-field values through the UI is
  `GRX-CONTACT-007`'s scope, not this task's) plus the contact's `is_suppressed` flag.
- Added a new "AUDIENCE" sidebar section with a "Contacts" nav link (gated on
  `contacts.view` alone — every role holding `contacts.manage` also holds
  `contacts.view` per RBAC.md's role matrix, so one permission check covers both) and
  a page-title entry.
- `eslint`/`tsc --noEmit`/`prettier --check` clean; `vitest` 19 passed (6 new
  component tests: list rendering, access-denied, view-only hides write controls,
  create, edit, archive).
- Live-verified against the rebuilt dev server: created a contact as Super Admin,
  edited its name inline, archived then re-activated it (toast confirmation each
  time), then logged in as a fresh Analyst and confirmed the same contact was visible
  with no write controls.
- This is the first of Sprint 2's four remaining frontend tasks.
  `GRX-CONTACT-007`/`008`/`009` (tags/lists/segments, CSV import, and
  consent/suppression frontends) all had their only frontend dependency
  (`GRX-CONTACT-006`) satisfied and were flipped to `READY`. Commit `07550c0`.

## 2026-07-31 — GRX-CONTACT-005: Consent & suppression

- Added `consent_records` (insert-only) and `suppression_entries` (upsert-on-email)
  tables (migration `97642610fb46`), matching DATA_MODEL.md's field-level spec exactly.
- `POST`/`GET /contacts/{id}/consent` record and list a contact's consent history per
  channel (`EMAIL`/`SMS`), newest-first. Current status per channel is derived as "most
  recent row" — there is no separate mutable current-status column.
- `POST /contacts/suppression` upserts on the unique `email` index: suppressing an
  already-suppressed email updates `reason`/`suppressed_at` in place (same row, no
  duplicate) rather than creating a second entry. `contact_id` is optional — an
  address can be suppressed with no matching contact (e.g. a hard bounce) — but is
  validated to exist when provided.
- Per the sprint's explicit acceptance criterion ("visibly flagged as suppressed
  wherever contacts are shown"), `ContactOut` gained `is_suppressed: bool`. This
  widened the internal `ContactSnapshot` tuple across every contacts service function
  and API call site to carry the flag through.
- No new permissions — suppression and consent recording were already scoped under
  `contacts.manage` (and viewing under `contacts.view`) in RBAC.md from Slice 2
  planning.
- `ruff`/`mypy` clean; `pytest` 101 passed, 3 skipped (8 new tests); `alembic check` →
  no drift.
- Live-verified against rebuilt Compose containers: recorded GRANTED then WITHDRAWN
  consent for a contact and confirmed the history came back newest-first; suppressed a
  contact's email and confirmed `is_suppressed` flipped true; re-suppressed the same
  email with a different reason and confirmed it updated the existing row instead of
  duplicating; suppressed an email with no matching contact; confirmed an unknown
  `contact_id` 404s.
- This closes out Sprint 2's entire backend slice (contacts, tags, lists, segments,
  CSV import, consent/suppression). `GRX-CONTACT-006` (contacts frontend) is next
  `READY`. Commit `30b5fc2`.

## 2026-07-31 — GRX-CONTACT-004: CSV contact import

- Added `contact_imports`/`contact_import_rows` tables (migration `b11cffc2cbcf`).
  `POST /contacts/imports` takes a multipart upload (`file` + a `column_mapping` JSON
  string mapping CSV headers to `email`/`first_name`/`last_name`/`phone`/`source`/
  `custom_field:<key>`), processes it synchronously, and returns imported/updated/
  skipped/error counts plus per-row detail via `GET /contacts/imports/{id}/rows`.
- Row outcomes: a fully blank row is `SKIPPED`; a row with no email value is `ERROR`;
  an email that already exists reuses `create_or_update_contact`'s dedup logic and is
  marked `UPDATED`, a new email `IMPORTED`. A `column_mapping` missing an `email`
  target, or naming an unknown `custom_field:<key>`, returns 400 before any row runs.
- `GET /contacts/imports` and `GET /contacts/imports/{id}` expose import history. No
  new permissions — reuses `contacts.manage`/`contacts.view`.
- Added the `python-multipart` dependency (first use of FastAPI file/form uploads in
  this codebase) and extended ruff's `flake8-bugbear` immutable-calls allowlist with
  `fastapi.File`/`fastapi.Form`.
- `ruff`/`mypy` clean; `pytest` 93 passed, 3 skipped (8 new tests); `alembic check` →
  no drift.
- Live-verified against rebuilt Compose containers: a 3-row CSV (one new email, one
  pre-existing email, one blank email) mapped to `email`/`first_name`/
  `custom_field:plan` produced `imported_count=1`, `updated_count=1`, `error_count=1`;
  the new contact carried its custom field and the existing contact's first name and
  custom field were both updated; a mapping without an `email` target returned 400.
- This closes out Sprint 2's backend CSV import slice. `GRX-CONTACT-005` (consent &
  suppression) is next `READY`. Commit `52fb417`.

## 2026-07-31 — GRX-CONTACT-003: Segments

- Added `segments`/`segment_rules`/`segment_members` tables (migration `18cf808f2b87`)
  and a rule evaluator supporting `status`/`email`/`source` (equals; email also
  supports contains), `tag` (equals), `created_at` (before/after), and
  `custom_field:<key>` (equals/contains) — all AND-combined only, per the Slice 2
  scope decision (no OR/grouping).
- `consent_status` was named as an example field during earlier Slice 2 planning but
  isn't implemented yet, since `consent_records` doesn't exist until `GRX-CONTACT-005`
  — using it now correctly returns 400 as an unsupported field rather than silently
  matching nothing.
- `POST /contacts/segments` validates every rule up front (unknown field, unsupported
  operator for that field, unknown custom-field key, or an unparseable `created_at`
  date all return 400) before creating anything.
- `DYNAMIC` segments compute membership live on every read; `SAVED` segments evaluate
  once at creation and freeze into `segment_members`. Verified live: tagging a new
  contact after creating both segment types changed the `DYNAMIC` segment's count but
  left the `SAVED` one unchanged.
- `ruff`/`mypy` clean; `pytest` 85 passed, 3 skipped (93% coverage, 9 new tests);
  `alembic check` → no drift (needed `index=True` added to `SegmentRule.segment_id` in
  the ORM model to match the migration's explicit index — `alembic check` caught the
  mismatch itself).
- This closes out the backend half of Slice 2's core contact-organization features
  (contacts, tags, lists, segments). `GRX-CONTACT-004` (CSV import) is next `READY`.
  Commit `a725e0e`.

## 2026-07-30 — GRX-CONTACT-002: Tags & lists

- Added `tags`/`contact_tags` and `contact_lists`/`contact_list_members` tables (migration
  `788ff9dd33db`) and their API: `GET`/`POST /contacts/tags`, attach/detach via
  `POST`/`DELETE /contacts/{id}/tags[/{tag_id}]`, `GET`/`POST /contacts/lists`, `GET
  /contacts/lists/{id}`, and member add/remove via `POST`/`DELETE
  /contacts/lists/{id}/members[/{contact_id}]`.
- `ContactOut` now includes `tags: list[str]`; `ContactListOut` includes a live
  `member_count` computed on every read rather than stored and risking drift.
- Tag/list changes emit `contact.tagged`/`contact.list_added` audit events, continuing to
  reuse `audit_logs` rather than a new activity table.
- No RBAC changes needed — `contacts.manage`/`contacts.view` already covered tag/list
  management per this session's Slice 2 planning pass.
- `ruff`/`mypy` clean; `pytest` 76 passed, 3 skipped (94% coverage, 7 new tests); `alembic
  check` → no drift. Live-verified against rebuilt Compose containers: attached/detached a
  tag (tags array updated both times), added/removed a list member (`member_count` went
  0→1→0), and confirmed the same Analyst-view/Viewer-none permission split as
  `GRX-CONTACT-001`.
- Note for future sessions: the full `pytest` run's migration round-trip test drops and
  recreates all tables against the same database Compose uses, wiping any manually
  created accounts (like `admin@growixa.local`) — recreated it again after this run, same
  as after `GRX-CONTACT-001`.
- `GRX-CONTACT-003` (segments) is now the next `READY` task. Commit `1e69461`.

## 2026-07-30 — GRX-CONTACT-001: Contacts schema + CRUD

- First Slice 2 implementation task. Added `contacts`, `contact_custom_fields`,
  `contact_field_values` tables (migration `209d29349ccf`) and
  `contacts.manage`/`contacts.view` permission codes + role grants (Super
  Admin/Admin/Marketing Manager manage; those three plus Analyst view; Viewer gets
  neither, per RBAC.md's Slice 2 rationale).
- `POST /contacts` creates or updates by email (the sole dedup key — no fuzzy matching);
  `GET /contacts`, `GET /contacts/{id}`, `PATCH /contacts/{id}`, `PATCH
  /contacts/{id}/status` (archive/unarchive); `GET`/`POST /contacts/custom-fields`.
  Contact activity reuses the existing `audit_logs` table rather than a new one
  (`contact.created`/`updated`/`archived`).
- **Real bug found and fixed during live verification**: `Contact.updated_at`'s
  server-side `onupdate` expires that attribute after `session.commit()`; reading it
  synchronously afterward (as the API's response serialization does) raised
  `sqlalchemy.exc.MissingGreenlet`. Fixed with an explicit `await
  session.refresh(contact)` right after each mutating commit. Worth checking whether
  `company_profile`'s equivalent `onupdate` column has the same latent bug — its existing
  test suite only ever creates a profile once per test, never exercises a second `PUT`
  against an already-saved row.
- Extended `test_auth_schema_seed.py`'s exact-match permission-set assertion to include
  the two new codes — a legitimate extension of Sprint 1's test now that Slice 2 adds
  permissions, not a regression.
- `ruff`/`mypy` clean; `pytest` 69 passed, 3 skipped (94% coverage, 12 new tests);
  `alembic check` → no drift. Live-verified against rebuilt Compose containers: created a
  contact with a custom field value, re-created with the same email (dedup confirmed —
  same id, list count stayed at 1), archived then reactivated (audit event confirmed via
  DB query), and confirmed Analyst gets 200 on list/403 on create while Viewer gets 403
  on both.
- Also recreated the `admin@growixa.local` smoke-test account, which the full pytest run's
  migration round-trip test (`test_migrations.py`) wiped as a side effect of dropping and
  recreating all tables against the same database Compose uses — a pre-existing test
  characteristic, not something introduced by this task, but worth knowing before running
  the full suite against a Compose stack with data you want to keep.
- `GRX-CONTACT-002` (tags & lists) is now the next `READY` task. Commit `7ec6c93`.

## 2026-07-30 — Sprint 2 (Contacts) planning

- All tracked Sprint 1 tasks are `DONE` except `GRX-DEVOPS-001` (push confirmation) and
  `GRX-DOC-003` (blocked on it) — per the user's direction, moved on to planning Slice 2
  (Contacts) rather than waiting.
- Extended `DATA_MODEL.md`, `DATABASE_SCHEMA.md`, and `ERD.md` with full field-level detail
  for `contacts`, `contact_custom_fields`/`contact_field_values`, `tags`/`contact_tags`,
  `contact_lists`/`contact_list_members`, `segments`/`segment_rules`/`segment_members`,
  `contact_imports`/`contact_import_rows`, and `consent_records`/`suppression_entries`.
  Notable design calls: dedup is email-only; segment rules are AND-only in Slice 2 (no
  OR/grouping); "contact activity history" reuses the existing `audit_logs` table instead
  of a new one; `consent_records` is insert-only (compliance history) while
  `suppression_entries` is a fast current-state upsert-on-email table — deliberately
  different patterns for different jobs.
- Extended `RBAC.md` with `contacts.manage`/`contacts.view` and a Slice 2 role matrix —
  Marketing Manager gets full manage access (matches its stated scope), Analyst gets
  view-only, Content Creator and Viewer get neither yet (no stated Slice 2 need; Sprint 1
  set the precedent that view access is granted explicitly per module, not assumed).
- Wrote `SPRINT_02_CONTACTS.md` (scope, exclusions, acceptance criteria) and a Slice 2
  readiness gate in `DEVELOPMENT_READINESS.md`, mirroring Sprint 1's structure.
- Added nine tasks to `MASTER_TASK_TRACKER.md` (`GRX-CONTACT-001`–`009`): schema+CRUD,
  tags/lists, segments, CSV import, consent/suppression — each with a frontend
  counterpart. `GRX-CONTACT-001` is the first `READY` task.
- Planning only — no code written yet for Slice 2.

## 2026-07-30 — Toast notification system (UI polish, no tracker ID)

- Found while manually testing `GRX-USER-002`: form errors only showed as an inline red
  banner easy to miss, and successful role/status changes gave no feedback at all. Added a
  shared `ToastProvider`/`useToast()` (`apps/web/src/components/toast/`), wired into the
  root layout so it's available app-wide.
- Login, company settings, and the Team page now show errors and successes as an
  auto-dismissing (5s) popup in the top-right corner instead of (or in addition to) inline
  banners. The Team page's invite-token success banner stays inline since it holds an
  actionable value the admin needs to copy, not a transient message.
- Added a proper `--color-error` token to `globals.css` (previously every page hardcoded
  the same `rgba(244, 63, 94, ...)` value inline).
- `eslint`/`prettier`/`tsc` clean; Vitest 17 passed (4 new for the toast component, 3
  existing test files updated to wrap renders in `ToastProvider`); `next build` succeeds;
  Playwright 4 passed (unaffected). Live-verified in a real browser against rebuilt
  Compose containers: a failed login showed an error toast, a successful role change
  showed a success toast, both auto-dismissed after 5 seconds.
- Not filed as a tracked `GRX-*` task — a UI-quality fix found and resolved during manual
  testing, not a Sprint 1/2 backlog item. A related, not-yet-fixed gap: unlike self-disable
  (blocked), there's no guard against changing your own role and accidentally losing
  `users.manage` — flagged to the product owner, not yet actioned.

## 2026-07-29 — GRX-FOUND-007: RabbitMQ connectivity and worker skeleton

- Added the shared `JobEnvelope` schema and a `publish_job()` producer to
  `apps/api/src/growixa_api/jobs/`, plus an `admin.access`-gated `POST
  /system/jobs/healthcheck` so the pipeline can be triggered and tested — Sprint 1 has no
  real business job to trigger it otherwise.
- New standalone `apps/worker/` app (own `pyproject.toml`, `Dockerfile`, ruff/mypy config
  mirroring `apps/api`) connects to RabbitMQ, declares the `grx.system.healthcheck` queue,
  and logs each job it processes. Kept as its own deployable app rather than an entrypoint
  inside `apps/api`, per `SYSTEM_ARCHITECTURE.md`'s "independently scalable Python
  workers" — corrected a stale `LOCAL_DEVELOPMENT.md` line that had said otherwise.
- Wired into `compose.yaml` as a new `worker` service, into `ci.yml` as a new parallel job
  (no service containers needed — the worker's own tests are pure-unit against a fake AMQP
  message), and into `.pre-commit-config.yaml` (ruff/format/mypy hooks mirroring `apps/api`'s).
- `ruff`/`mypy` clean on both apps; `apps/api` `pytest` 58 passed, 3 skipped (95%
  coverage) — the new producer round-trip test skips locally for the same
  host-unreachable-broker reason as `GRX-FOUND-006`'s Redis test, but runs for real in CI;
  `apps/worker` `pytest` 2 passed. Live-verified against rebuilt Compose containers:
  triggered a real healthcheck job as a smoke Admin via curl, confirmed
  `docker compose logs worker` showed the exact same `job_id` being processed; confirmed a
  Viewer gets 403; `/health`'s `rabbitmq` check still reports `ok`.
- This was the last `BACKLOG` Sprint 1 task. Only `GRX-DEVOPS-001` (push confirmation) and
  `GRX-DOC-003` (blocked on that same push) remain open in Sprint 1. Commit `a0a1eea`.

## 2026-07-29 — GRX-USER-002: User management screens (list, invite, disable, role assignment)

- Backend: `GET /roles` (gated on `users.manage`, since it only backs the role-picker
  dropdown — not exposing the full permission matrix), `GET /users` (list with roles +
  status), `PATCH /users/{id}/status`, `PATCH /users/{id}/role`. Self-disable is blocked
  (no `seed_first_admin` CLI yet, so a self-lockout would be unrecoverable); disabling a
  user revokes all their active sessions; role changes emit a `role.changed` audit event
  with old/new roles.
- Frontend: `/dashboard/team` — lists members, invites new users (shows the raw invite
  token directly since there's no email delivery yet), changes roles, disables/enables.
  Sidebar's "Team" link only renders for users with `users.manage`.
- `ruff`/`mypy` clean, `pytest` 55 passed (95% coverage, 10 new); frontend
  lint/format/typecheck/build clean, Vitest 14 passed (5 new), Playwright 4 passed (1 new
  e2e: invite → accept → login). Live-verified in a real browser against rebuilt Compose
  containers: invited a user, changed their role, disabled them (session revoked, login
  now 401), confirmed self-disable is blocked in the UI.
- This was the last tracked Sprint 1 task; all Sprint 1 tasks are now `DONE` except
  `GRX-DEVOPS-001`'s pending push confirmation. Commit `22ba450`.

## 2026-07-27 — GRX-COMPANY-002: Company settings screen

- Built the company profile + brand voice form at `/dashboard/company-settings`. Extended
  `GET /auth/me` to also return the caller's permission codes (new `permissions/repositories.py`
  helper, new `MeOut` schema) so the UI can render editable vs. read-only correctly — only
  Admin/Super Admin hold `company.settings.edit` per RBAC.md, everyone else sees the same
  data with every field disabled and a view-only note, rather than a form that would only
  fail on submit.
- Saves company then brand profile in sequence on one "Save changes" click (brand requires
  company to exist first, per `GRX-COMPANY-001`'s existing 400 behavior).
- Sidebar gained a real `SETTINGS` section (`Company`); the topbar title is now
  route-driven instead of hardcoded to "Dashboard".
- Found and fixed a real Vitest/RTL bug while writing the component test: without
  `test.globals: true`, `@testing-library/react`'s automatic `afterEach(cleanup)` never
  registers, so DOM from one test leaks into the next in the same file. Fixed with an
  explicit `afterEach(cleanup)` in `vitest.setup.ts`.
- `ruff`/`mypy` clean, `pytest` 45 passed/2 skipped; frontend lint/format/typecheck/build
  clean, Vitest 5 passed (4 new, mocked `apiFetch`), Playwright 3 passed (unaffected).
  Live-verified against rebuilt Compose containers as both an Admin (edits, saves,
  survives reload) and a Viewer (same data, fully disabled, no Save button). Commit
  `9989373`.

## 2026-07-27 — GRX-DEVOPS-001: CI pipeline (IN_REVIEW)

- Picked immediately after `GRX-FOUND-008` — both dependencies (`GRX-TEST-001`,
  `GRX-TEST-002`) were already `DONE` (the tracker still marked it `BACKLOG`, corrected as
  part of this pick, same pattern as `GRX-FOUND-006` and `GRX-AUTH-004` earlier). This
  locks in every testing investment made across this session so future regressions get
  caught automatically instead of relying on an agent session remembering to re-verify.
- Added `.github/workflows/ci.yml` implementing all 8 stages from `TEST_STRATEGY.md`
  §CI test stages, split across 3 jobs rather than one linear pipeline — an explicit,
  flagged refinement that preserves the documented "fail fast, in order" intent while
  actually running faster: `backend` and `frontend` run in parallel (independent stacks,
  stages 1–3 shared plus each side's own tests/build), and `e2e` (`needs: [backend,
  frontend]`) only stands up the expensive full stack once the cheap checks already
  passed.
- `backend` job runs against real GitHub Actions service containers for Postgres, Redis,
  and RabbitMQ — meaning **Redis is host-reachable in CI**, unlike local dev
  (`GRX-FOUND-006`'s documented finding that Compose's `redis` has no host port mapping).
  The tests that skip locally for that exact reason (`test_redis.py`, the rate-limit
  integration test) will actually execute for real in CI — exactly the outcome flagged as
  intentional when those skips were written.
- Migration check step runs `alembic upgrade head && alembic check` — deliberately
  distinct from `test_migrations.py`'s upgrade/downgrade round-trip (already covered by
  the `Tests` step): `alembic check` catches a model changed without a matching
  migration, which the round-trip test doesn't verify on its own.
- `e2e` job runs the real Compose stack (`docker compose up postgres redis rabbitmq api`)
  — deliberately omitting the `web` container, since Playwright already brings its own
  Next.js instance (`playwright.config.ts`'s `webServer`); standing up both would just
  build the frontend twice for no benefit.
- Made `apps/web/tests/e2e/{global-setup,global-teardown}.ts` compose-binary-portable: a
  new `COMPOSE_BIN` env var (default `podman`, this project's local dev tool; CI sets
  `docker`, what GitHub's runners actually have) means the identical e2e suite runs
  unmodified in both environments — no CI-specific test duplication.
- Locally re-verified every command the workflow runs, since the workflow itself can't be
  executed without pushing: `ruff check`/`ruff format --check`/`mypy` clean;
  `alembic upgrade head && alembic check` → "No new upgrade operations detected";
  `pytest` → 45 passed, 2 skipped; frontend `eslint`/`prettier --check`/`tsc --noEmit`/
  `vitest run` all clean; `next build` → succeeds, correctly classifies `/`/`/login`
  static and `/dashboard` dynamic; `npm run test:e2e` → 3 passed with the new
  `COMPOSE_BIN` parameterization defaulting to `podman` (unchanged local behavior).
  Workflow YAML syntax-validated with `python3 -c "import yaml; yaml.safe_load(...)"`.
- **Left at `IN_REVIEW`, not `DONE`.** A real green run on GitHub Actions has not been
  observed — confirming one requires pushing to the remote, which this session will not
  do without the user's explicit go-ahead (pushing is a permission-gated action). Move to
  `DONE` once the user pushes and a run is confirmed green; if it fails, the failure will
  be in something this local re-verification couldn't reach (GHA-specific networking,
  action version pinning, etc.) rather than in the commands themselves. Commit `7ff54dc`.

## 2026-07-27 — GRX-FOUND-008: Dashboard shell

- Picked immediately after `GRX-TEST-002` gave the frontend a real test harness. The user
  directed this UI work explicitly, pointing to the previously captured design reference
  (`DESIGN_REFERENCES.md` + `mockups/growixa-login-and-dashboard-mockup.html`) and a fresh
  screenshot of the same dashboard mockup for visual grounding.
- **Two small, necessary backend additions**, discovered while scoping this frontend task
  (not originally listed in its Files/Modules column): CORS middleware
  (`cors_allowed_origins` setting, defaulting to `localhost:3000` and `localhost:3100`) so
  a browser can complete the cross-origin, credentialed fetches auth relies on; and
  `GET /auth/me` (identifies the session via the access-token cookie itself, the same
  shape as `/refresh`/`/logout-all` — no separate permission needed, added to the
  route-protection audit's allowlist alongside them). Without `/auth/me` there is no way
  for a Server Component to determine "is this user logged in," since the access token is
  HttpOnly and unreadable by client-side JS.
- Frontend: `globals.css` design tokens (colors, gradients, card/pill styles) taken
  directly from the design brief; a real email+password `/login` page (dark navy
  gradient, glass card) — not the mockup's demo "Sign in as Super Admin/Team Member"
  buttons, since the real backend needs actual credentials; an authenticated
  `/dashboard` route whose layout calls `getCurrentUser()` server-side and redirects to
  `/login` on failure, rendering a sidebar + top bar shell around an empty-state landing
  page. Root `/` now redirects to `/dashboard`, which is the actual auth gate.
- Per `DESIGN_REFERENCES.md`'s scope caveat, the sidebar wires up only the "Dashboard" nav
  item for real — Contacts/Campaigns/Team/Settings/etc. have no page behind them yet in
  Sprint 1, so they're not rendered at all (not even as inert placeholders), rather than
  shipping dead links.
- `ruff`/`mypy` clean; `pytest` 45 passed, 2 skipped (unchanged skip count/reason from
  `GRX-AUTH-004`). Frontend `eslint`/`prettier --check`/`tsc --noEmit`/Vitest all clean.
  Added a Playwright global setup/teardown that creates and deletes a fixed e2e test user
  directly via the ORM inside the `api` container (no public "create user" endpoint
  exists). 3 e2e tests passed against real Compose Postgres/Redis: an anonymous visit to
  `/dashboard` (and separately to `/`) redirects to `/login`; a full login shows the
  dashboard shell (sidebar, top bar, correct user name, empty-state card) and logging out
  clears the session for real, confirmed by re-visiting `/dashboard` afterward and landing
  back on `/login`.
- **A real bug found and fixed during Compose verification, not caught by the host-run
  Playwright suite**: server-side fetches issued from inside the `web` container used
  `NEXT_PUBLIC_API_URL=http://localhost:8000`, but `localhost` inside that container
  resolves to the container itself, not the `api` container — every dashboard visit 500'd
  in the real Dockerized stack even though it worked perfectly via `next build && next
  start` on the host (where both processes genuinely do share one `localhost`). Fixed by
  adding a server-only `API_INTERNAL_URL` (falls back to `NEXT_PUBLIC_API_URL` when unset,
  so running outside Docker needs no change) and setting it to `http://api:8000` — the
  Compose service DNS name — in `compose.yaml`. This is exactly the kind of gap Playwright
  running against a host-built app can't catch, which is why this task's verification
  included rebuilding both containers and driving the actual login → dashboard → logout
  flow in a real browser against them, not just trusting the e2e suite's green result.
- Cosmetic, non-blocking: the icon-mark PNG asset has an opaque light backdrop baked in,
  which shows as a small white square against the dark login card rather than blending in
  — a future visual-polish pass could swap in the monochrome/white logo variant instead;
  not worth blocking this task over. Commit `886329a`.

## 2026-07-27 — GRX-FEAT-SMS-001: SMS Marketing & Twilio Integration documentation

- Added feature specification `docs/02-features/FEATURE_SMS_MARKETING.md` detailing Admin Twilio provider credential setup, E.164 phone formatting, SMS consent management (`OPTED_IN`/`OPTED_OUT`), SMS campaign composer with 160-char / GSM-7 segment calculator, and Twilio DLR / `STOP` opt-out webhooks.
- Updated `MVP_SCOPE.md`, `ROADMAP.md` (Release 1.2), `FEATURE_CATALOG.md`, and `PROJECT_STATUS.md` to stage SMS Marketing in Release 1.2.

## 2026-07-27 — GRX-TEST-002: Frontend test foundation

- Picked ahead of `GRX-FOUND-008` (dashboard shell) — the user directed frontend/UI work
  next, pointing to the design reference already captured in `DESIGN_REFERENCES.md`, but
  `GRX-FOUND-008`'s own "Required Tests" (a frontend e2e smoke test) has nothing to run in:
  `apps/web` had zero test tooling. Same reasoning as why `GRX-TEST-001` (backend test
  foundation) was done before most backend feature work this session.
- Added Vitest + React Testing Library + jsdom for component tests
  (`vitest.config.ts`, `vitest.setup.ts`) and Playwright for e2e (`playwright.config.ts`,
  Chromium only for now). `npm run test` / `npm run test:e2e` scripts added.
- One trivial component test (`src/app/page.test.tsx`) renders the existing `HomePage` and
  asserts its heading — will be revisited once `GRX-FOUND-008` changes what the root route
  renders. One e2e smoke test (`tests/e2e/smoke.spec.ts`) drives a real
  `next build && next start` and confirms the root route returns 200 with the heading
  visible.
- Playwright's dev server runs on port 3100 (not 3000) specifically so the e2e suite never
  collides with the Compose `web` container, which developers may have running at the same
  time on the standard port.
- `npm run lint`/`format:check`/`typecheck` all pass; `npm run test` → 1 passed; `npm run
  test:e2e` → 1 passed. Rebuilt the `web` image with the new devDependencies and confirmed
  `/` still returns 200 and an unknown route still 404s in Compose — no regression from
  adding test tooling. No CI pipeline exists yet (`GRX-DEVOPS-001`, which depends on this
  task); a green local test suite is this task's actual deliverable, matching
  `GRX-TEST-001`'s equivalent backend evidence. Commit `a804186`.

## 2026-07-27 — GRX-AUTH-004: Login rate limiting

- Picked immediately after `GRX-FOUND-006` (Redis connectivity) unblocked it — the highest
  remaining P0 backend task, and it closes T1 (credential stuffing/brute force) and T12
  (unbounded login/reset flooding) from `THREAT_MODEL.md` on the exact `/auth/login` and
  `/auth/password-reset/request` endpoints built in the two sessions before this one.
- Added `rate_limit_max_attempts` (default 5) and `rate_limit_window_seconds` (default 60)
  settings, and `auth/rate_limit.py`'s `enforce_rate_limit()`: a Redis `INCR`+`EXPIRE`
  fixed-window counter keyed `grx:ratelimit:{bucket}:{identifier}` — the exact key format
  `LOCAL_DEVELOPMENT.md` already documented in its Redis-inspection section, ahead of this
  task even existing. Both `/auth/login` (bucket `login`) and
  `/auth/password-reset/request` (bucket `password_reset_request`) call it keyed by
  `email:ip`, so the two endpoints are limited independently and the same email can't
  exhaust the other endpoint's budget.
- **Explicit, flagged design call: the limiter fails open on `RedisError`.** If Redis is
  unreachable, `enforce_rate_limit()` swallows the error and allows the request through
  rather than raising — a Redis outage must degrade *security posture*, not *availability*
  of login/password-reset entirely (the same trade-off `/health` already makes by reporting
  "degraded" instead of crashing). This also has a load-bearing practical consequence:
  Compose's `redis` service has no host port mapping (`GRX-FOUND-006`'s finding), so every
  host-run `pytest` login/password-reset test in this whole session continues to pass
  unaffected — the limiter transparently no-ops under that specific, documented
  environment constraint instead of breaking 40+ pre-existing tests.
- `ruff`/`mypy` clean; `pytest` 43 passed, 2 skipped (95% coverage). Five pure unit tests
  against a fake in-memory Redis stand-in cover the limiter logic directly (allows up to
  max, raises past max, isolates by identifier, isolates by bucket, fails open on
  `RedisError`) with no real Redis needed. One integration test exercises the real
  `/auth/login` endpoint end-to-end and skips under host-run pytest for the same documented
  reason as `GRX-FOUND-006`'s `test_redis.py`.
- Rebuilt the `api` image and verified live against real Compose Redis: 6 wrong-password
  attempts against one email+IP returned `401×5` then `429`; a *correct* password against
  that same already-limited identifier also returned `429` (rate limiting is
  identity-keyed, not correctness-keyed — the intended defense, since checking the
  password before the limiter would let an attacker's eventual correct guess bypass
  protection entirely); a different email+IP logged in normally (`200`), proving
  unaffected traffic elsewhere; the same 5-then-429 pattern was confirmed independently on
  `/auth/password-reset/request`. Verified via `redis-cli KEYS "grx:ratelimit:*"` that the
  real keys match the documented naming exactly, then cleaned up. Commit `5c26200`.

## 2026-07-27 — GRX-FOUND-006: Redis connectivity

- Picked because its only listed dependency (`GRX-FOUND-003`, FastAPI application
  foundation) was already `DONE` — the tracker still marked it `BACKLOG`, a stale status
  corrected as part of this pick — and because it directly unblocks `GRX-AUTH-004` (login
  rate limiting), a P0 security task (T1/T12 in THREAT_MODEL.md) covering the exact
  login/password-reset-request endpoints built in the last two sessions.
- Added `growixa_api/redis.py`: a module-level pooled `redis.asyncio` client built from
  `settings.redis_url`, plus a `get_redis()` FastAPI dependency generator — the same shape
  as `db.py`'s `engine`/`get_session()`. This is the reusable client `GRX-AUTH-004`'s rate
  limiter (and later locks/idempotency keys) will import, rather than each future feature
  opening its own throwaway connection.
- `health.py`'s Redis check previously opened a new client, pinged it, and closed it on
  every single `/health` request; it now reuses the shared pooled client, matching the
  Postgres engine-reuse fix already landed alongside `GRX-AUTH-005`.
- **Environment-constraint finding**: Compose's `redis` service has no host port mapping
  by design (`compose.yaml`'s comment, confirmed in `LOCAL_DEVELOPMENT.md`'s Redis
  inspection section: "not required to be reachable from outside the compose network").
  Only Postgres/RabbitMQ are host-mapped, so a host-run pytest process cannot open a real
  TCP connection to Redis. The new connectivity smoke test (`tests/test_redis.py`) skips
  with an explicit reason under this documented constraint rather than being written to
  silently pass or made to fail the whole suite; real set/get/delete round-trip
  correctness was instead verified live via the shared client executed inside the running
  `api` container.
- `ruff`/`mypy` clean; `pytest` 38 passed, 1 skipped (95% coverage, unchanged from before —
  the skip contributes no missed lines). Rebuilt the `api` image; `GET /health` still
  returns `{"status":"ok",...}` using the new pooled client; a live
  set → get → delete → get(None) sequence run inside the `api` container via
  `growixa_api.redis.client` confirmed correct round-trip behavior against the real
  Compose Redis instance. Commit `32aacdf`.

## 2026-07-27 — GRX-AUTH-005: Password reset flow

- Picked as the last P0 backend auth task remaining (everything else `READY` at that point
  was frontend work) — closes the final account-recovery gap in the auth system.
- Added `password_reset_tokens` table (migration `bb25de08ba84`), matching
  `DATABASE_SCHEMA.md`'s spec exactly: `user_id` FK `ON DELETE CASCADE`, unique `token_hash`,
  `expires_at`, `used_at`. Reused the already-generalized `generate_token()`/`hash_token()`
  from `auth/tokens.py` (no new token machinery needed).
- `auth/services.py`: `request_password_reset()` always records a
  `user.password_reset_requested` audit event and always runs the same code shape regardless
  of whether the account exists — only the returned raw token differs (a string vs. `None`).
  `complete_password_reset()` validates the token (exists, unused, unexpired), sets the new
  password hash, marks the token used, calls the existing `revoke_all_active_sessions()`
  (built in `GRX-AUTH-003`) to kill every active session, and records
  `user.password_reset_completed`.
- **Enumeration-safety design (THREAT_MODEL.md T11)**: `POST /auth/password-reset/request`
  always returns the same generic message regardless of whether the email is registered.
  The raw token is additionally echoed back in the response, but **only** when
  `settings.environment == "local"` — mirroring the existing `Secure`-cookie
  environment-conditional pattern and GRX-USER-001's invitation-token interim behavior.
  Verified via a monkeypatched-`ENVIRONMENT=production` test that the token is `null` for
  both known and unknown emails outside local dev.
- Both new endpoints (`/auth/password-reset/request`, `/auth/password-reset/complete`) are
  public (no session yet) and added to the route-protection audit's allowlist.
- `ruff`/`mypy` clean; `pytest` 38 passed (95% coverage) incl. full request→complete
  round-trip (old password rejected, new password works, sessions revoked, all three audit
  events emitted), identical response for known/unknown email, and invalid/reused-token
  rejection. Rebuilt the `api` image, confirmed `alembic current` → head, and ran a live curl
  request→complete flow against Compose with direct `psql` verification of audit events,
  refresh-token revocation, and the reset token's `used_at`. Commit `730519b`.

## 2026-07-27 — GRX-USER-001: Internal user invitation + acceptance

- Picked next per explicit user direction as "most needed": the only way to add any user
  to the system besides the still-unbuilt `seed_first_admin` CLI (flagged since
  `GRX-AUTH-001`) or direct DB manipulation.
- **First cross-cutting refactor of already-`DONE` auth code this session**: generalized
  `auth/tokens.py`'s `generate_refresh_token`/`hash_refresh_token` to
  `generate_token`/`hash_token` — invitation tokens need the exact same "high-entropy
  opaque token, SHA-256 hash for lookup" treatment as refresh tokens
  (AUTHENTICATION.md's token model lists both under the same shape), and duplicating that
  logic under an invitation-specific name would just be the same code twice. Verified only
  `auth/services.py` called the old names before renaming, so this was a safe,
  contained rename — updated its 2 call sites, all 28 pre-existing tests still passed
  afterward.
- Added `user_invitations` table (migration `f356da0136c3`) — both indexes
  `DATABASE_SCHEMA.md` specifies: a plain one on `email`, and a partial one on
  `email WHERE accepted_at IS NULL` for "does this email already have an open invite"
  lookups.
- Added `roles/repositories.py` (`get_role_by_name`) — `roles`'s first repository file,
  needed to resolve an invitation's `role_name` (e.g. "Viewer") to the seeded role's UUID.
- `users/services.py`: `invite_user()` resolves the role, checks the email isn't already
  registered (fails fast for the admin rather than only failing at acceptance),
  generates+hashes a token, and returns `(invitation, raw_token)` — the raw token only
  ever exists in memory, never persisted. `accept_invitation()` re-validates
  not-yet-accepted/not-expired/email-still-free (closes a race between two acceptances or
  the person registering some other way in between), creates the `User`, assigns the
  `UserRole`, marks the invitation accepted, and records `invitation.accepted` (Sprint 1's
  audit event set) with `actor_user_id` set to the **new** user (they're the one taking
  the accepting action, even though an admin initiated the invite).
- **Explicit, flagged scope decision — not a silent shortcut**: `POST /users/invitations`
  returns the raw invitation token directly in its JSON response. Sprint 1 has no
  email-delivery channel at all (no task for it exists in the tracker), so there is
  currently no other way for the invitee to receive it. This is the correct interim
  behavior given the constraint, not the intended end state — revisit the moment a
  notifications/email-delivery task exists, at which point the token should be sent
  out-of-band and dropped from the API response entirely.
- Added `apps/api/tests/test_users_invitations.py`: full invite → accept round-trip (role
  assigned, audit event recorded with the right actor), non-admin invite attempt (403,
  via the real `users.manage` permission check — no test-only bypass), unknown role (400),
  inviting an already-registered email (409), accepting with an invalid token (400), and
  accepting an already-accepted token (400, replay protection).
- Verified beyond the automated suite: rebuilt the `api` image, then ran a real
  login → invite → accept flow via curl against the live Compose stack, confirming via
  direct `psql` queries that the new user got the correct role and the
  `invitation.accepted` audit row was recorded.
- Verified: `ruff`/`format --check`/`mypy` clean across 63 source files; `pytest` 34
  passed, 94% coverage.
- `GRX-USER-001` marked `DONE`. `GRX-USER-002` (user management screens, frontend) is
  newly `READY`, alongside the already-`READY` `GRX-AUTH-005`, `GRX-TEST-002`,
  `GRX-COMPANY-002`, `GRX-FOUND-008`. This completes the third step of the user-directed
  "most needed" sequence this session (`GRX-AUTH-002` → `GRX-AUTH-003` → `GRX-USER-001`).
- Commit: `87d2110`.

## 2026-07-27 — GRX-AUTH-003: Refresh-token rotation + session revocation

- Picked next per explicit user direction as "most needed first": closes a real security
  gap `GRX-AUTH-002` left open by design (refresh tokens issued, but no rotation, no reuse
  detection — a stolen refresh token could otherwise be replayed indefinitely).
- Added `POST /auth/refresh` and `POST /auth/logout-all` — both public routes (added to
  the route-protection audit's allowlist) that identify the acting user via the refresh
  token itself, consistent with the existing `/auth/logout`, rather than via
  `get_current_user_id`/`require_permission`.
- `auth/services.refresh()`: looks up the presented token; if already revoked by a
  *previous rotation* (not by logout), treats this as a reuse/compromise signal and calls
  the new `revoke_all_active_sessions()` to kill every session for that user — not just
  reject the one request — before raising. Otherwise rotates: issues a new access +
  refresh token, marks the presented one `revoked_at` + `replaced_by_token_id` pointing at
  the new one (the `refresh_tokens` column that existed since `GRX-AUTH-002`'s migration
  but stayed unused until now), and re-validates `user.status == "ACTIVE"` on every
  refresh (defense in depth beyond relying solely on disable always successfully revoking
  sessions elsewhere).
- Added `auth/services.revoke_all_active_sessions(session, user_id, *, reason)` —
  deliberately public (not `_`-prefixed) and does not commit itself, so a future
  disable-user action (no such endpoint exists yet; out of `apps/api/auth/`'s own scope)
  can call it as one step in a larger transaction. Records a `session.revoked` audit event
  (Sprint 1's audit event set) with the reason and count, only when it actually revoked
  something.
- `auth/services.logout_all()` reuses the same revoke function, keyed off the presented
  refresh token — logging out "everywhere" from any one of your own sessions.
- Added `apps/api/tests/test_auth_refresh.py`: rotation (new cookies issued, old token
  revoked with the correct `replaced_by_token_id`), reuse detection (replaying the
  pre-rotation token 401s *and* revokes the entire chain including the token it had
  already rotated to), `logout-all` across two simulated devices (two separate
  `AsyncClient`s, since one client's cookie jar would silently overwrite the first
  session's refresh cookie on a second login), disable-revokes-sessions (proves the
  `revoke_all_active_sessions()` building block works, since no disable-user endpoint
  exists to exercise end-to-end yet), and expired-token rejection.
- Verified beyond the automated suite: rebuilt the `api` image, then ran a real
  login → refresh → replay-old-token flow via curl against the live Compose stack,
  confirming via direct `psql` queries that *both* refresh tokens ended up revoked and the
  `session.revoked` audit row was recorded with `reason: "refresh_token_reuse_detected"`.
  Cleaned up the smoke-test user/rows afterward.
- Verified: `ruff`/`format --check`/`mypy` clean across 57 source files; `pytest` 28
  passed, 94% coverage.
- `GRX-AUTH-003` marked `DONE`. No task became newly `READY` from this alone — nothing
  else in the tracker lists it as a dependency yet.
- Commit: `27a22af`.

## 2026-07-27 — GRX-AUTH-002: Password hashing + login/logout

- Picked next per explicit user direction: P0, backend-only, continuing the session's
  backend momentum rather than branching into frontend work (`GRX-TEST-002`) or a P1 task
  (`GRX-COMPANY-002`).
- Added `apps/api/src/growixa_api/auth/security.py`: Argon2id `hash_password`/
  `verify_password`, cost parameters (`argon2_time_cost`/`memory_cost`/`parallelism`) added
  to `Settings` as configuration per
  [AUTHENTICATION.md](../08-security/AUTHENTICATION.md) ("tuned parameters set as
  configuration... so cost can be raised as hardware improves"), defaulting to
  argon2-cffi's own OWASP-baseline `PasswordHasher` defaults.
- Added `apps/api/src/growixa_api/auth/tokens.py`: `create_access_token` — the **issuing**
  half of the JWT that `permissions.dependencies.get_current_user_id` (`GRX-RBAC-001`) has
  been verifying since that task, same signing key/algorithm, closing the gap flagged at
  the time. Also refresh-token generation (`secrets.token_urlsafe`) and hashing
  (SHA-256 — fast/deterministic is correct here since, unlike a password, a refresh token
  is already high-entropy, not a low-entropy brute-forceable input).
- Added the `refresh_tokens` table (migration `ea25a5343142`) — deferred from
  `GRX-AUTH-001` since that task's own scope was schema for users/roles/permissions only;
  needed now because issuing a refresh token requires persisting its hash. Includes
  `replaced_by_token_id`, populated only once `GRX-AUTH-003` (rotation) lands, but present
  now as part of the fixed schema in DATABASE_SCHEMA.md.
- Added `apps/api/src/growixa_api/users/repositories.py` (`get_user_by_email`) — the
  `users` module's first repository file; `auth` depends on `users` for identity lookup per
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md), so this lookup belongs
  there, not duplicated inside `auth`.
- `auth/services.py`: `login()` raises a single `InvalidCredentialsError` for unknown
  email, wrong password, *and* disabled accounts alike — deliberately indistinguishable
  per [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T11, each still recording a
  `user.login_failed` audit event (with `entity_id` set only when a user was actually
  found, so the audit trail itself still distinguishes them for legitimate incident
  response — that distinction just never reaches the HTTP response). Successful login
  updates `last_login_at`, issues both tokens, and records `user.login`. `logout()`
  revokes the presented refresh token and records `user.logout`.
- `auth/api.py`: `POST /auth/login` and `POST /auth/logout`, added to the
  route-protection audit's public allowlist (they are the entry points before a session
  exists). Cookies are `HttpOnly` + `SameSite=Lax` unconditionally; `Secure` is
  conditional on `settings.environment != "local"` — local dev runs over plain HTTP, and a
  browser will not resend a `Secure` cookie without HTTPS.
- Added `apps/api/tests/test_auth_login.py`: valid login (cookies present, **no token
  values in the JSON body** — verified directly per T2, not assumed), identical generic
  error for wrong-password vs. unknown-email (compared byte-for-byte, not just both-401),
  disabled-account rejection, and logout (revokes the token row, clears both cookies,
  records the audit event). Extended the shared `user_factory` (`GRX-TEST-001`) to hash a
  real, known password (`DEFAULT_TEST_PASSWORD`) and accept an explicit `email` override,
  rather than duplicating user-creation logic for this task's tests.
- **Real bug found and fixed — this one affects every coverage number recorded so far this
  session.** `auth/services.py` showed 50% coverage despite all 4 new tests passing with
  assertions that only make sense if the "uncovered" lines ran (audit rows created,
  `last_login_at` set, tokens revoked). Root cause: SQLAlchemy's async engine bridges into
  the sync DBAPI driver via `greenlet_spawn`, and coverage.py's default tracer does not
  follow into that greenlet context, silently under-reporting any code that runs on the
  other side of an `await session.execute(...)`/`commit()` call. Fixed by adding
  `concurrency = ["greenlet"]` to `[tool.coverage.run]`. Total coverage jumped from 85% to
  **94%** on rerun — the true baseline was always higher; this was purely a measurement
  bug, not new code appearing. `GRX-TEST-001`'s previously-recorded 87% baseline is now
  known to have been an undercount for the same reason; not retroactively rewritten there
  (historical evidence is point-in-time), but flagged here since this is where it was found.
- Verified beyond the automated suite: rebuilt the `api` image, confirmed `alembic current`
  reports the new head inside the container, then ran a real login → wrong-password →
  logout flow via curl against the live Compose stack — inspected the actual `Set-Cookie`
  headers (`HttpOnly`, `SameSite=lax`, correct `Max-Age` matching config, no `Secure` in
  local) and confirmed logout's `Set-Cookie` headers clear both cookies (`Max-Age=0`).
  Cleaned up the smoke-test user/rows afterward.
- Verified: `ruff`/`format --check`/`mypy` clean across 56 source files; `pytest` 23 passed,
  94% coverage (corrected).
- `GRX-AUTH-002` marked `DONE`. `GRX-AUTH-003` (refresh-token rotation + session
  revocation), `GRX-AUTH-005` (password reset flow), and `GRX-FOUND-008` (dashboard shell,
  frontend) are newly `READY`, alongside the already-`READY` `GRX-TEST-002`,
  `GRX-USER-001`, `GRX-COMPANY-002`. `GRX-AUTH-004` (rate limiting) still needs
  `GRX-FOUND-006` (Redis connectivity), not yet started.
- Commit: `b7cf4d8`.

## 2026-07-25 — GRX-COMPANY-001: Company profile + brand settings

- First task this session to ship real, RBAC-gated HTTP endpoints (previous tasks were
  schema/dependency foundations with no routes of their own besides `/health`).
- Added `apps/api/src/growixa_api/company/{models,schemas,repositories,services,api}.py`
  and the equivalent `brand/` module, following the full layered structure from
  [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md) for the first time
  (`models` → `repositories` → `services` → `api`, plus `schemas` for the Pydantic
  request/response shapes) since this is the first task that actually needs every layer.
- `company_profile`/`brand_profiles` are true singletons per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) — "exactly one row, enforced in the
  service, not a DB constraint." Implemented as get-then-upsert in `company/services.py`
  and `brand/services.py`, explicitly documented as **not race-safe** against two
  concurrent first-time saves (acceptable for Sprint 1's single-admin-at-a-time usage; a
  unique constraint or advisory lock would close that gap if it ever matters).
- `brand` depends on `company` per module boundaries — `brand.services` calls
  `company.repositories.get_company_profile` directly (the documented same-request
  cross-module call pattern) and raises a small domain error
  (`CompanyProfileRequiredError`) if no company profile exists yet, translated to a 400 at
  the API layer. No new permission codes were invented for brand — RBAC.md's existing
  `company.settings.view`/`company.settings.edit` cover both, matching RBAC.md's own
  framing of brand as part of company settings.
- Added migration `1abf62872712` (clean autogenerate: `company_profile` then
  `brand_profiles`, correct FK order).
- Added `apps/api/tests/test_company_settings.py`: admin edit+view, viewer view-only (403
  on edit) for *both* company and brand, unauthenticated 401, and the
  brand-requires-company-first 400 case. Since both tables are true singletons shared
  across the whole test run, every test clears both tables before and after itself via an
  autouse fixture — order-independent by construction, not by accident.
- Verified beyond the automated suite: rebuilt the `api` image, confirmed
  `alembic current` reports the new head inside the container, and ran a live end-to-end
  curl flow against the running Compose stack (mint a real Admin JWT inside the container,
  `PUT`/`GET /company/profile`, `PUT /brand/profile`) — real HTTP round-trip, not just the
  test suite's ASGI transport.
- Verified: `ruff`/`format --check`/`mypy` clean across 45 source files; `pytest` 19 passed
  (14 pre-existing + 5 new), 86% coverage.
- `GRX-COMPANY-001` marked `DONE`. `GRX-COMPANY-002` (company settings screen, frontend) is
  newly `READY`, alongside the already-`READY` `GRX-TEST-002`, `GRX-AUTH-002`,
  `GRX-USER-001`. This completes the user-specified sequence
  (`GRX-AUDIT-001` → `GRX-TEST-001` → `GRX-COMPANY-001`).
- Commit: `e40f6f8`.

## 2026-07-25 — GRX-TEST-001: Backend test foundation

- Added `apps/api/tests/conftest.py`: a `user_factory` fixture (async, factory-function
  pattern) that creates a real user, optionally assigns it an existing seeded role, and
  deletes every user it created at teardown. Kept deliberately simple — commit-and-cleanup
  per creation, not a transactional-rollback session — see the module's own docstring and
  [AGENT_HANDOFF.md](AGENT_HANDOFF.md) for why the heavier pattern wasn't adopted now.
- Refactored `test_require_permission.py` (`GRX-RBAC-001`) and `test_audit_log.py`
  (`GRX-AUDIT-001`) to use the shared `user_factory` instead of their own near-identical
  ad hoc fixtures — the direct point of this task, not incidental cleanup.
- Added `pytest-cov` and `[tool.coverage.run]` config (`source = ["growixa_api"]`,
  tests excluded). Current baseline: **87%** line coverage (`pytest` with default addopts).
  No enforced minimum threshold yet — establishing the baseline measurement is this task's
  job; a specific enforced number is better decided once `GRX-DEVOPS-001` wires up CI and
  there's more code to judge a rational threshold against.
- Registered a `pytest.mark.integration` marker (in `pyproject.toml`, avoiding
  "unknown marker" warnings) and applied it to every test that touches a real backing
  service: `test_audit_log.py`, `test_auth_schema_seed.py`, `test_migrations.py`, and two of
  `test_require_permission.py`'s four tests (the other two — missing/invalid token — never
  reach `get_session` because `get_current_user_id` raises first, per FastAPI's
  parameter-order dependency resolution, and were left unmarked *and separately verified* to
  need no DB — see below).
- **Verified the split is real, not just labeled**: ran
  `pytest -m "not integration"` with `DATABASE_URL`/`REDIS_URL`/`RABBITMQ_URL` all pointed
  at unreachable hosts — all 7 unit-tier tests still passed. This is the actual proof (not
  an assumption) that the unit/integration boundary holds.
- No CI pipeline exists yet (`GRX-DEVOPS-001`, which depends on this task and
  `GRX-TEST-002`, hasn't started) — this task's own acceptance criterion
  ("`pytest` runs green ... in CI") is satisfied by `pytest` running green locally with the
  new foundation in place, matching how earlier foundation tasks satisfied "smoke test"
  criteria before their own supporting infrastructure existed.
- Verified: `ruff`/`format --check`/`mypy` clean across 31 source files; `pytest` 14 passed
  (same 14 as before this task — this task changed test *infrastructure*, not test *count*).
- `GRX-TEST-001` marked `DONE`. No task became newly `READY` from this alone (only
  `GRX-DEVOPS-001` depends on it, and that also needs `GRX-TEST-002`, not done). Per
  explicit user direction, `GRX-COMPANY-001` is next.
- Commit: `de55382`.

## 2026-07-25 — GRX-AUDIT-001: Audit log module

- **Task-ordering note**: this was the deferred half of the `GRX-AUDIT-001`/`GRX-AUTH-001`
  ordering issue flagged during `GRX-AUTH-001` — `audit_logs.actor_user_id` FKs to
  `users.id`, so this task genuinely needed `GRX-AUTH-001` done first. It was, so this
  proceeded cleanly.
- Added `apps/api/src/growixa_api/audit/models.py`: `AuditLog` matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly — indexes on
  `(entity_type, entity_id)`, `actor_user_id`, and `created_at`; the DB column `metadata` is
  mapped to a Python attribute named `event_metadata` since SQLAlchemy's `DeclarativeBase`
  already reserves `.metadata` for the ORM's own `MetaData` object.
- Added migration `6575d09949f9` (clean autogenerate, no hand-editing needed beyond
  ruff-driven line wrapping) creating `audit_logs`.
- Added `apps/api/src/growixa_api/audit/repositories.py` (`create_audit_log`,
  `list_audit_logs` — raw persistence only) and `services.py` (`record_event`,
  `list_events`). `record_event` redacts known-sensitive metadata keys (`password`,
  `password_hash`, `token`, `token_hash`, `refresh_token`, `access_token`, `secret`) to
  `"[REDACTED]"` before the row is ever written — the "structured-log redaction" half of
  this task's description, and defense-in-depth for
  [THREAT_MODEL.md](../08-security/THREAT_MODEL.md) T7 (secret leakage in logs). No
  `update`/`delete` function exists anywhere in either module — the "insert-only" property
  is enforced by omission, not a runtime guard.
- Added `apps/api/tests/test_audit_log.py`: write→list round-trip (real Postgres), a
  system-actor event (`actor_user_id=None`, explicitly allowed per the schema doc), and a
  redaction test asserting sensitive keys are stripped while unrelated keys survive intact.
- Added `apps/api/tests/test_audit_insert_only.py`: introspects `audit.repositories` and
  `audit.services` via `inspect.getmembers` and asserts no public function name contains
  "update"/"delete"/"modify"/"edit" — the tracker's required "negative test for missing
  update/delete routes," adapted to code-path auditing since no HTTP API layer exists yet
  in this module (matches the broader wording in
  [TEST_STRATEGY.md §Audit-log tests](../10-testing/TEST_STRATEGY.md#audit-log-tests): "no
  application code path... updates or deletes").
- **Real bug found and fixed while validating this task**: the write/list test's fixture
  teardown (deleting its throwaway test user) initially failed with a Postgres FK violation
  — `actor_user_id` correctly has no `ON DELETE CASCADE` (an audit trail must survive the
  actor being removed), so the test's own audit row was still referencing that user. Fixed
  by having the fixture delete its audit rows before the user.
- **Second, more interesting bug found and fixed**: `test_require_permission.py` started
  intermittently failing with `asyncpg.exceptions.InternalServerError: cache lookup failed
  for type ...` when run in the same session as `test_migrations.py`. Root cause:
  `test_migrations.py`'s downgrade-then-upgrade round trip was dropping and recreating the
  `citext` Postgres extension (added in `GRX-AUTH-001`'s migration, downgrade path) — each
  `CREATE EXTENSION` assigns the type a new internal OID, which poisons asyncpg's
  per-connection type cache for any already-pooled connection (recall `growixa_api.db`'s
  engine/pool is a session-wide singleton) that later touches a `citext` column. Fixed by no
  longer dropping the `citext` extension in that migration's `downgrade()` — a common,
  low-risk exception to full reversibility (table-level state is still fully reversible;
  leaving an installed extension behind is standard practice) that eliminates the whole
  class of failure rather than papering over one symptom of it.
- Verified: `ruff`/`format --check`/`mypy` clean across 30 source files; `pytest` 14 passed
  (10 pre-existing + 4 new); rebuilt the `api` image, `podman compose exec api alembic
  current` → new head, `/health` unaffected.
- `GRX-AUDIT-001` marked `DONE`. `GRX-AUTH-002` and `GRX-USER-001` (both depended on this
  and `GRX-AUTH-001`, both now done) are newly `READY`, alongside the already-`READY`
  `GRX-TEST-001`, `GRX-TEST-002`, `GRX-COMPANY-001`. Per explicit user direction, the next
  two tasks to pick up are `GRX-TEST-001` then `GRX-COMPANY-001`.
- Commit: `2b1dd7e`.

## 2026-07-25 — Design reference intake (not a tracker task)

- Product owner supplied brand assets (`apps/web/src/assets/`: primary, stacked, icon,
  wordmark, monochrome logo variants) and a self-contained HTML mockup covering the login
  screen and a full dashboard concept, plus a written design brief.
- Saved as [`docs/03-ux-ui/DESIGN_REFERENCES.md`](../03-ux-ui/DESIGN_REFERENCES.md) +
  [`docs/03-ux-ui/mockups/growixa-login-and-dashboard-mockup.html`](../03-ux-ui/mockups/growixa-login-and-dashboard-mockup.html)
  so this context survives outside chat history for whichever future session builds
  `GRX-AUTH-002`'s login UI or `GRX-FOUND-008`'s dashboard shell.
- **Explicit scope caveat recorded in that doc**: the brief describes the full eventual
  product (Contacts, Campaigns, Social, AI Assistant, Billing, ...), almost all of which is
  out of Sprint 1 per [SPRINT_01_FOUNDATION.md](../14-sprints/SPRINT_01_FOUNDATION.md) — this
  is reference material, not an approved implementation spec for any current task. No UI was
  built from it in this session.
- Added a `check-added-large-files` exclusion in `.pre-commit-config.yaml` for
  `apps/web/src/assets/` and `docs/03-ux-ui/mockups/` (several logo PNGs and the mockup HTML
  legitimately exceed the repo's default 1MB cap).
- Three additional files the brief references (`Growixa Dashboard v2.dc.html`,
  `Growixa Onboarding.dc.html`, `Growixa Style Options.dc.html`) were not available locally —
  noted as missing in the reference doc in case they're added later.
- Not tied to a `GRX-*` tracker row — this is reference intake, not an implementation task.

## 2026-07-24 — GRX-RBAC-001: Centralized permission-check dependency

- **Scope decision, made explicit up front**: `require_permission()` cannot function
  without some way to resolve "who is making this request," but token issuance/validation
  is conceptually `auth`-module territory per
  [AUTHENTICATION.md §Centralized authorization](../08-security/AUTHENTICATION.md#centralized-authorization)
  and the `AuthProvider` adapter-boundary language — and `apps/api/auth/` doesn't exist yet
  (`GRX-AUTH-002`). Resolved by adding a narrowly-scoped `get_current_user_id()` to the
  `permissions` module: it only *verifies* an already-issued JWT cookie and extracts the
  user id — genuine, working code (hand-craft a validly-signed JWT with the same
  `jwt_signing_key` and it correctly authenticates), not a stub — but it issues nothing.
  `GRX-AUTH-002`'s login endpoint is what will actually mint that cookie. This mirrors how
  `GRX-FOUND-004`'s `apiFetch` was real code nothing called yet.
- Added `apps/api/src/growixa_api/permissions/repositories.py`:
  `user_has_permission(session, user_id, code) -> bool`, an ORM query joining
  `Permission`/`RolePermission`/`UserRole` — the only place in this module that talks to
  the database directly, per [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md).
  Note: `permissions`'s dependency table only lists `roles`, but this query necessarily also
  reads `users.models.UserRole` (owned by `users`) since a permission check inherently spans
  both — a read-only cross-module dependency, not a boundary violation (comparable to how
  `analytics` is documented to read across all modules).
- Added `apps/api/src/growixa_api/permissions/dependencies.py`:
  - `get_current_user_id(request) -> uuid.UUID` — decodes the `access_token` cookie via
    PyJWT (`HS256`, `Settings.jwt_signing_key`), 401s on missing/invalid/expired.
  - `RequirePermission` — a callable class (not a closure) so a route-protection audit can
    `isinstance()`-check a route's dependency tree; depends on `get_current_user_id` and
    `get_session`, 403s if `user_has_permission` is false, otherwise returns the user id.
  - `require_permission(code)` — the public factory matching the exact name used in
    [AUTHENTICATION.md](../08-security/AUTHENTICATION.md).
- Added `apps/api/tests/test_require_permission.py`: allowed / 403 / 401-missing-token /
  401-invalid-token cases, using the **real** Viewer role seeded by `GRX-AUTH-001`'s
  migration (Viewer has `company.settings.view`, not `users.manage`, per RBAC.md) — no
  fixture-only fake roles, the actual Sprint 1 seed data.
- Added `apps/api/tests/test_protected_routes_audit.py`, per
  [TEST_STRATEGY.md §RBAC authorization tests](../10-testing/TEST_STRATEGY.md#rbac-authorization-tests):
  walks every `APIRoute` in `create_app()` and asserts each one not explicitly allowlisted
  as public is guarded by a `RequirePermission` dependency somewhere in its dependency tree.
  Trivially true today (only `/health`, allowlisted) but becomes a real regression trap the
  moment the first protected route ships.
- **Bug found and fixed (test infra, not app code)**: `growixa_api.db`'s async engine/pool
  is a module-level singleton shared for the whole test process; pytest-asyncio's default
  function-scoped event loop meant a second async DB-touching test could be handed a pooled
  asyncpg connection opened under a *different* (already-closed) loop, raising
  `RuntimeError: ... attached to a different loop`. Fixed by setting
  `asyncio_default_fixture_loop_scope`/`asyncio_default_test_loop_scope = "session"` in
  `pyproject.toml` so the whole test session shares one loop.
- **Bug found and fixed (test infra)**: the route-protection audit initially found zero
  `APIRoute`s at all — this FastAPI version (`0.139.2`) doesn't flatten
  `include_router()`'s routes directly into `app.routes` the way older versions did; it
  wraps them in an internal `_IncludedRouter` object exposing the real routes via
  `.original_router.routes`. Fixed by recursing through that wrapper (via `getattr`, not by
  importing the private class) rather than assuming a flat route list.
- Also added `extend-immutable-calls = ["fastapi.Depends", ...]` to ruff's `flake8-bugbear`
  config — B008 otherwise flags FastAPI's own required `Depends(...)`-in-defaults pattern as
  a mutable-default-argument bug, which it isn't.
- Verified: `ruff`/`format --check`/`mypy` clean across 23 source files; `pytest` 9 passed
  (4 pre-existing + 1 seed-data + 4 new); rebuilt the `api` image, `/health` unaffected.
- `GRX-RBAC-001` marked `DONE`. `GRX-COMPANY-001` (depended on this and `GRX-FOUND-005`,
  both now done) is newly `READY`, alongside the already-`READY` `GRX-AUDIT-001`,
  `GRX-TEST-001`, `GRX-TEST-002`.
- Commit: `7e77444`.

## 2026-07-24 — GRX-AUTH-001: Users, roles, permissions schema + seed

- **Task-ordering note**: picked this task ahead of the other three tasks that became
  `READY` alongside it after `GRX-FOUND-005` (`GRX-AUDIT-001`, `GRX-TEST-001`,
  `GRX-TEST-002`), even though the tracker doesn't encode the dependency: `audit_logs`
  (`GRX-AUDIT-001`) has `actor_user_id uuid FK → users.id` per
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md), so the `users` table has to exist
  first. The tracker's `GRX-AUDIT-001` row only lists `GRX-FOUND-005` as a dependency — this
  is a real gap worth fixing in a future tracker-hygiene pass, not something to silently
  work around by reordering without a note.
- Added `apps/api/src/growixa_api/{roles,permissions,users}/models.py`: SQLAlchemy 2.0
  models (`Role`; `Permission`, `RolePermission`; `User`, `UserRole`) matching
  [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md) exactly — UUID PKs generated
  application-side (`default=uuid.uuid4`, no `pgcrypto` dependency), `CITEXT` email (case-
  insensitive per the schema doc), the `status IN ('ACTIVE','DISABLED')` check constraint.
  Split module-by-module per [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)
  (`permissions` owns `role_permissions`; `users` owns `user_roles`, since it references
  `assigned_by_user_id`). Only `models.py` was added per module — no `api/`, `services/`,
  `repositories/` yet, since this task's scope is schema + seed only (those layers have no
  real logic to hold yet; endpoints are `GRX-AUTH-002`/`GRX-RBAC-001`).
  `migrations/env.py` now imports all three model modules so `Base.metadata` is fully
  populated for `--autogenerate`.
- Added migration `d330e8b64b48` (autogenerated table DDL, hand-edited to add
  `CREATE EXTENSION IF NOT EXISTS citext` and seed data): creates all 5 tables in FK-safe
  order, then seeds the 6 Sprint 1 roles, 6 permission codes, and the full 16-row
  `role_permissions` matrix, exactly per [RBAC.md](../08-security/RBAC.md)'s role →
  permission table. Seed rows use fixed (not per-run-random) UUIDs hardcoded in the
  migration, generated once, so the migration is reproducible. Uses `sa.table()`/
  `op.bulk_insert()` proxies rather than importing the ORM models directly, per Alembic's
  own guidance (so a future model change can't silently rewrite this migration's meaning).
  Downgrade drops the 5 tables and the `citext` extension — full round-trip to empty.
- Added `apps/api/tests/test_auth_schema_seed.py`: an integration-tier test (real Postgres,
  same reasoning as `GRX-FOUND-005`'s migration test) asserting the *exact* set of 6 role
  names, *exact* set of 6 permission codes, and the *exact* role→permission matrix (not just
  row counts) match RBAC.md after `alembic upgrade head`.
- Verified: `ruff check`/`format --check`/`mypy` clean; `pytest` 4 passed (2 health + the
  generic migration round-trip from `GRX-FOUND-005`, now covering both migrations, + this
  task's seed-data test); spot-checked seed data directly via `psql` in the `postgres`
  container (6 roles, 6 permission codes, 16 `role_permissions` rows); rebuilt the `api`
  image and confirmed `podman compose exec api alembic current` reports the new head.
- **Known gap, explicitly not addressed in this task**: `LOCAL_DEVELOPMENT.md` documents a
  `python -m growixa_api.cli.seed_first_admin` command "finalized when `GRX-AUTH-001` ... is
  implemented," but no tracker task actually owns it, and it needs Argon2id password
  hashing, which is `GRX-AUTH-002`'s explicit scope (`apps/api/auth/`). Building it here
  would mean creating `apps/api/auth/` ahead of the task that owns that module. Left as a
  gap to resolve when `GRX-AUTH-002` is picked up (or as its own tracker line item) rather
  than silently expanding this task's scope into another module's territory.
- `GRX-AUTH-001` marked `DONE`. `GRX-RBAC-001` (its only dependency was this task) is newly
  `READY`, alongside the already-`READY` `GRX-AUDIT-001`, `GRX-TEST-001`, `GRX-TEST-002`.
- Commit: `daf9bc7`.

## 2026-07-24 — GRX-FOUND-004: Next.js application foundation

- Added `apps/web/src/lib/api-client.ts`: a small typed `fetch` wrapper (`apiFetch<T>`) that
  prepends `getApiUrl()`, sends `credentials: "include"` (auth is HttpOnly-cookie-based per
  [DEC-GRX-014](DECISIONS.md), not bearer tokens), and throws a typed `ApiError` on any
  non-2xx response instead of leaving every caller to check `response.ok`. Not yet consumed
  by any UI — nothing calls the API from the frontend until `GRX-AUTH-002`/`GRX-USER-002` —
  but this is genuine, working infrastructure (foundation work, explicitly allowed to stand
  alone per [DEFINITION_OF_DONE.md §No placeholder completion](DEFINITION_OF_DONE.md#no-placeholder-completion)),
  not a stub.
- Added `apps/web/src/app/not-found.tsx` as the routing-baseline piece: Next.js App Router's
  convention for a real custom 404, verified to actually return 404 (not just exist).
- Reworded `apps/web/src/app/page.tsx`'s placeholder copy — it referenced `GRX-FOUND-002`
  ("Placeholder page for local Docker Compose validation"), which was accurate when it was
  added as a stopgap for that task's stack validation, but this task is what actually
  establishes the app shell, so the copy no longer references a specific task.
- No changes to `.env.example`/env config — `NEXT_PUBLIC_API_URL` and `getApiUrl()` were
  already established in `GRX-FOUND-001`/`GRX-FOUND-002` and remain the single env surface.
- Verified: `npm run lint`, `format:check`, `typecheck`, and `build` all pass. Local smoke
  test (`next start`): `/` → 200 (renders "Growixa"), an unknown route → 404. Rebuilt the
  `web` Docker image and re-verified through the full Compose stack: all 5 services healthy,
  `GET /` → 200, unknown route → 404, `api`'s `/health` unaffected.
- No automated test harness was added — `GRX-TEST-002` (test runner config, component test
  harness, one e2e smoke test) is a separate, already-tracked task that owns building that
  infrastructure; this task's "smoke test loads root route" requirement was satisfied via
  the manual/scripted verification above, consistent with how `GRX-FOUND-002`'s smoke-test
  requirement was satisfied before any test runner existed.
- `GRX-FOUND-004` marked `DONE`. `GRX-AUDIT-001`, `GRX-AUTH-001`, `GRX-TEST-001` (already
  `READY` from `GRX-FOUND-005`), and `GRX-TEST-002` (newly `READY` — its only dependency was
  this task) are all now `READY`.
- Commit: `8269436`.

## 2026-07-24 — GRX-FOUND-005: PostgreSQL connectivity + Alembic foundation

- Added `apps/api/src/growixa_api/db.py`: SQLAlchemy 2.0 `DeclarativeBase` (`Base`), a
  module-level async engine (`pool_pre_ping=True`) built from `Settings.database_url`, an
  `async_sessionmaker`, and a `get_session()` FastAPI dependency (async generator) for
  future modules (`GRX-AUDIT-001`, `GRX-AUTH-001`, etc.) to depend-inject.
- Initialized Alembic with the async template (`alembic init -t async migrations`):
  `apps/api/alembic.ini` and `apps/api/migrations/{env.py,script.py.mako,versions/}`.
  `migrations/env.py` is wired to read `DATABASE_URL` from `growixa_api.config.get_settings()`
  (overriding `alembic.ini`'s placeholder URL at runtime, so there is one source of truth for
  the connection string) and sets `target_metadata = Base.metadata` for future autogeneration.
  Customized `script.py.mako` to match this project's ruff config (`collections.abc.Sequence`,
  `X | Y` union syntax) so every future generated migration passes lint without manual edits.
- Added the first migration (`migrations/versions/9ca09405a2b3_initial_empty_migration.py`):
  genuinely empty `upgrade`/`downgrade` (`pass`) — establishes the `alembic_version`
  tracking table baseline only; no application tables exist yet (those are `GRX-AUDIT-001`/
  `GRX-AUTH-001`/`GRX-COMPANY-001`, per [DATABASE_SCHEMA.md](../05-data/DATABASE_SCHEMA.md)).
- Added `apps/api/tests/test_migrations.py`: an integration-tier smoke test (real Postgres
  required, per [TEST_STRATEGY.md §Database migration tests](../10-testing/TEST_STRATEGY.md#database-migration-tests))
  that runs `alembic upgrade head` → asserts the head revision is recorded → `alembic
  downgrade base` → asserts no revision is recorded → `upgrade head` again, using Alembic's
  Python API directly (a plain sync test, since Alembic's async `env.py` calls
  `asyncio.run(...)` internally and cannot be nested inside pytest-asyncio's event loop).
- **Bug found and fixed**: `greenlet` — required by SQLAlchemy's async engine — was missing
  from `apps/api/pyproject.toml`. It happened to resolve as a transitive dependency inside
  the Docker image's `pip install`, masking the gap, but was absent from the local `uv`-
  managed dev venv, so any async engine use (including the `/health` checks added in
  `GRX-FOUND-002`) would have failed outside Docker. Added `greenlet>=3.1` as an explicit
  dependency.
- **Bug found and fixed**: `apps/api/Dockerfile` only ever `COPY`'d `pyproject.toml`,
  `README.md`, and `src/` — `alembic.ini` and `migrations/` were never in the image or the
  `compose.yaml` bind mounts, so `docker compose exec api alembic upgrade head` (this task's
  literal acceptance criterion, and the command documented in
  [LOCAL_DEVELOPMENT.md](../11-devops/LOCAL_DEVELOPMENT.md)) would have failed. Added them to
  the Dockerfile `COPY` steps and added matching bind mounts in `compose.yaml` (consistent
  with the existing `src` mount) so migrations stay live-editable like application code.
- Verified: `ruff check` 0 errors, `ruff format --check` pass, `mypy` 0 issues (11 source
  files), `pytest` 3 passed (2 health + 1 migration round-trip against real Compose
  Postgres). `alembic upgrade head` / `alembic current` succeed both from the host (via
  `localhost:5433`) and via `podman compose exec api alembic upgrade head` against the
  running Compose Postgres.
- `GRX-FOUND-005` marked `DONE`. `GRX-AUDIT-001`, `GRX-AUTH-001`, and `GRX-TEST-001` (all
  depend only on `GRX-FOUND-005`) are now `READY`, alongside the still-open `GRX-FOUND-004`.
- Commit: `0cff500`.

## 2026-07-23 — GRX-FOUND-003: FastAPI application foundation

- Refactored the ad hoc FastAPI app added during `GRX-FOUND-002` validation into a proper
  app-factory structure: `growixa_api/app.py` (`create_app()`, sets title/version, mounts
  the health router), `growixa_api/health.py` (`GET /health` route plus three isolated,
  independently-testable `_check_postgres`/`_check_redis`/`_check_rabbitmq` functions),
  `growixa_api/main.py` (thin `app = create_app()` uvicorn entrypoint — unchanged Docker
  CMD reference).
- OpenAPI docs (`/docs`, `/redoc`, `/openapi.json`) are enabled — this is FastAPI's default
  when nothing disables it; verified reachable (200) rather than left as an unverified
  assumption.
- Added `apps/api/tests/test_health.py`: two tests (all-dependencies-ok, one-dependency-
  degraded) that assert full response-body shape, not just status code, per
  [TEST_STRATEGY.md §Rules preventing shallow tests](../10-testing/TEST_STRATEGY.md#rules-preventing-tasks-from-being-marked-done-with-shallow-tests).
  Tests monkeypatch the three check functions directly (no real DB/Redis/MQ connection) and
  set required `Settings` env vars via `monkeypatch.setenv` + `get_settings.cache_clear()`,
  so the unit suite runs without any backing service, per
  [TEST_STRATEGY.md §Backend unit-test approach](../10-testing/TEST_STRATEGY.md#backend-unit-test-approach).
- Fixed a stale `pyproject.toml` mypy override (`growixa_api.tests.*`, a module path that
  never matched the actual `apps/api/tests/` layout) to `tests.*`, and added
  `apps/api/tests/__init__.py`.
- Verified: `ruff check` 0 errors, `ruff format --check` pass, `mypy` 0 issues (7 source
  files), `pytest` 2 passed. Rebuilt the `api` Docker image and re-validated the full
  Compose stack: all 5 services healthy, `GET /health` → 200
  `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`,
  `GET /docs` and `GET /openapi.json` → 200.
- `GRX-FOUND-003` marked `DONE`. `GRX-FOUND-004` (Next.js application foundation) and
  `GRX-FOUND-005` (PostgreSQL connectivity + Alembic foundation) are both now `READY`
  (only one to be worked at a time per [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md)).
- Commit: `c69eb10`.

## 2026-07-23 — GRX-FOUND-002: Docker Compose local environment

- Added `compose.yaml` defining `postgres` (16-alpine), `redis` (7-alpine), `rabbitmq`
  (3-management-alpine), `api`, and `web` services on a shared bridge network, with
  healthchecks and `depends_on: condition: service_healthy` gating startup order.
- Added `apps/api/Dockerfile` (python:3.13-slim, editable install, `uvicorn --reload`) and
  `apps/web/Dockerfile` (node:22-alpine, `npm run dev`) — local-development images, not
  production-optimized (no multi-stage/distroless build or non-root hardening yet).
- Added a minimal `growixa_api` app (`main.py`, `config.py`) with a real `GET /health`
  endpoint that checks Postgres/Redis/RabbitMQ connectivity, so the compose stack has
  something functional to validate against ahead of `GRX-FOUND-003`.
- Added a minimal Next.js `apps/web/src/app/` (App Router `layout.tsx`/`page.tsx`) and
  `next.config.mjs` so `apps/web` builds/serves, ahead of `GRX-FOUND-004`.
- Added root `.env.example` documenting all Compose-level variables (DB/MQ credentials,
  host port mappings, JWT signing settings per [DEC-GRX-014](DECISIONS.md)).
- Validated end-to-end: `podman compose up -d` brings up all 5 services `healthy`;
  `GET /health` returns `{"status":"ok","checks":{"postgres":"ok","redis":"ok","rabbitmq":"ok"}}`;
  the web root returns HTTP 200.
- Fixed a podman-compose bug encountered during validation: a multi-word `CMD`-array
  healthcheck test (`api` service's `python -c "..."` health check) was being incorrectly
  re-split into separate argv tokens by podman-compose, breaking the check even though the
  app itself was healthy. Switched to `CMD-SHELL` form in `compose.yaml`, which
  podman-compose preserves as a single string correctly.
- Local-environment note (not a repo change): the default `POSTGRES_PORT=5432` in
  `.env.example` can collide with a natively-running Postgres on the host; `.env` is
  gitignored so this is a per-machine `.env` adjustment, not a schema/compose change.
- `GRX-FOUND-002` marked `DONE`; `GRX-FOUND-003` (FastAPI application foundation) now `READY`.
- Commit: `76354d2`.

## 2026-07-23 — GRX-FOUND-001: repository and development tooling

- First Sprint 1 implementation task. Added `apps/api/` (FastAPI/Python tooling: `ruff`,
  `mypy`, `pytest`, `.venv`, `.env.example`) and `apps/web/` (Next.js/TypeScript tooling:
  ESLint 9 flat config, Prettier, `tsc`, `.env.example`) — tooling and config only, no
  application code yet.
- Added `.pre-commit-config.yaml` wiring lint/format/type-check for both apps plus standard
  hygiene hooks; installed the git hook.
- Fixed 3 `npm audit` findings (moderate `postcss` XSS, high `sharp`/`libvips` CVEs, both
  pinned internally by Next.js on every current release) via a `package.json` `overrides`
  block. Verified 0 vulnerabilities after.
- All required checks verified passing: `ruff check`, `ruff format --check`, `mypy`,
  `eslint`, `prettier --check`, `tsc --noEmit`, `pre-commit run --all-files`.
- `GRX-FOUND-001` marked `DONE`; `GRX-FOUND-002` (Docker Compose) now `READY`.
- Commit: `42f8b37`.

## 2026-07-22 — Documentation gate closed; Sprint 1 authorized

- Added standalone [`docs/10-testing/TEST_STRATEGY.md`](../10-testing/TEST_STRATEGY.md) and
  [`docs/11-devops/LOCAL_DEVELOPMENT.md`](../11-devops/LOCAL_DEVELOPMENT.md), closing the
  last two distributed-only gaps in the Development Readiness Gate.
- [`DEVELOPMENT_READINESS.md`](DEVELOPMENT_READINESS.md) now shows every mandatory Slice 1
  gate item as `PASS` with a standalone document as evidence.
- Sprint 1 implementation authorized to begin at `GRX-FOUND-001`.

## 2026-07-22 — Slice 1 readiness: architecture, data, security baseline

- Resolved [OQ-001](OPEN_QUESTIONS.md) via [DEC-GRX-014](DECISIONS.md): application-managed
  FastAPI authentication (Argon2id, rotating refresh tokens, HttpOnly/Secure/SameSite
  cookies, centralized RBAC, OIDC/SSO adapter boundary for later). No Keycloak/third-party
  provider in MVP.
- Added `docs/04-architecture/` (SYSTEM_ARCHITECTURE, MODULE_BOUNDARIES,
  BACKGROUND_JOB_ARCHITECTURE), `docs/05-data/` (DATA_MODEL, ERD, DATABASE_SCHEMA), and
  `docs/08-security/` (SECURITY_ARCHITECTURE, AUTHENTICATION, RBAC, THREAT_MODEL) for Slice
  1 scope.
- Added [`MASTER_TASK_TRACKER.md`](MASTER_TASK_TRACKER.md) seeded with Sprint 1 tasks and
  [`SPRINT_01_FOUNDATION.md`](../14-sprints/SPRINT_01_FOUNDATION.md).
- Development Readiness Gate for Slice 1 reached PASS (with two items still in distributed
  form, closed in the entry above).
- Commit: `cc46e6d`.

## 2026-07-22 — Scope correction: Growixa remains the broader growth platform

- Corrected an earlier documentation pass that had read as a full product pivot. Logged as
  [DEC-GRX-001](DECISIONS.md): Growixa's positioning stays "AI-powered growth and marketing
  automation platform"; only the **first release** scope narrowed to email/social/contacts/
  AI-assist/scheduling/analytics. SEO/AEO/GEO/website-intelligence work from the original
  discovery PRD is preserved and mapped to future releases V1.5–V3 in
  [`FUTURE_SCOPE_SEO_AEO_GEO.md`](../01-product/FUTURE_SCOPE_SEO_AEO_GEO.md), not dropped.
- Relabeled `docs/archive/source-prd-seo-aeo-geo-website-intelligence/` (previously named as
  if it were an unrelated/superseded product) to reflect it as valid future-release source
  material.
- Added `docs/01-product/` (PRODUCT_VISION, PRD, MVP_SCOPE, ROADMAP,
  FUTURE_SCOPE_SEO_AEO_GEO), `docs/02-features/FEATURE_CATALOG.md` (stub), and
  `docs/00-project-control/` core docs (PROJECT_STATUS, ASSUMPTIONS, OPEN_QUESTIONS,
  DECISIONS, DEFINITION_OF_DONE, DEVELOPMENT_READINESS) and
  `docs/12-development/AGENT_EXECUTION_RULES.md`.
- Commit: `50b93cf`.

## 2026-07-22 — Repository initialized

- `git init`, `.gitignore`, root `README.md`.
- Original SEO/AEO/GEO discovery PRD (from an uploaded `.docx`) converted to Markdown and
  placed under `docs/archive/` (naming corrected in the entry above).
- Commit: `92bbdad`.
