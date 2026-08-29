Task: GRX-EMAIL-016 — add tracker row for platform-published default/public email
templates, and promote it from BACKLOG to READY (PR #48)
Developer: (tracker-only change; commit author Ravi Kant Yadav / prior session)
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of
developer's session
Branch: docs/BACKEND/promote-grx-email-016-ready
Worktree: /Users/ravi/Projects/growixa (main checkout, branch checked out directly)
Base Commit: efa5806 (docs(schema): add missing account_id to email_templates/_versions, #47)
Latest Commit: 0d90f58
Status: READY_FOR_REVIEW

## What Changed

Two commits, tracker-only:
1. `12e0011` — adds a new `GRX-EMAIL-016` row (`docs/00-project-control/MASTER_TASK_TRACKER.md`
   + generated `.csv`) for a platform-team-only default/public email template feature:
   clone-not-edit semantics, new `platform.templates.manage` RBAC permission, and a
   schema-representation choice (reserved system account preferred over nullable
   `account_id`).
2. `0d90f58` — flips that row's status `BACKLOG` → `READY`, sets `Assigned Agent` to
   `Claude Code`, citing `GRX-EMAIL-002` and `GRX-EMAIL-008` as DONE dependencies.

## Why

Land a previously-drafted, cherry-picked tracker row on `origin` and clear it for pickup.

## Important Files

- `docs/00-project-control/MASTER_TASK_TRACKER.md`
- `docs/00-project-control/MASTER_TASK_TRACKER.csv`

## Tests

N/A — pure prose/tracker change. Verified `python3 scripts/tracker_to_csv.py --check`.

## Known Issues / Evidence Gaps

None found.

## Review Findings

**Scope (confirmed).** `git diff efa5806..0d90f58 --stat` shows exactly two files touched:
`MASTER_TASK_TRACKER.md` (+1 line) and `MASTER_TASK_TRACKER.csv` (+1 line). No other file
in the repo changed across either commit. Matches the stated tracker-only scope.

**Dependency gate (confirmed, not just claimed).** Checked both dependency rows directly
in the current tracker (not the PR's own assertion):
- `GRX-EMAIL-002` — status `DONE`, `Completed At` 2026-08-03, evidence cell documents
  migration `d36211c53aed`, integration tests, live Compose verification, commit `1dac3ff`.
- `GRX-EMAIL-008` — status `DONE`, `Completed At` 2026-08-06, evidence cell documents
  the templates frontend, tests (11 backend + 79 frontend), live Compose verification,
  commit `e2a7529`.
Both are genuinely `DONE` per the tracker's own record, not placeholders or stale
in-progress rows. The tracker's rule ("READY only after dependencies are DONE") is
satisfied.

**CSV sync (confirmed).** `python3 scripts/tracker_to_csv.py --check` → `up to date
(141 tasks)`. No drift between the markdown and generated CSV.

**Technical claims spot-checked against real code (all grounded):**
- `apps/api/src/growixa_api/templates/models.py`: both `EmailTemplate.account_id` and
  `EmailTemplateVersion.account_id` are declared `Mapped[uuid.UUID]` with `nullable=False`
  today — confirms the row's premise that there is no platform/global concept yet and the
  representation choice is a real open decision, not invented.
- Cited permissions `platform.ai.manage`, `platform.email.manage`,
  `platform.validation.manage` all exist in `docs/08-security/RBAC.md` (with matching
  `require_platform_permission(...)` wiring in
  `apps/api/src/growixa_api/platform_admin/api.py:165-168`) and are documented as
  `platform.owner`/`platform.admin`-only. The row's "follow this exact shape" instruction
  for the new `platform.templates.manage` permission is grounded in a real, consistent
  existing pattern, not fabricated.
- `docs/02-features/FEATURE_CATALOG.md:30` — `GRX-FEAT-012 | Email Templates | 3 |
  EMAIL_TEMPLATES.md | NOT_STARTED` confirmed to exist exactly as cited; `EMAIL_TEMPLATES.md`
  itself does not yet exist under `docs/02-features/`, matching the row's own caveat ("new
  ... if it doesn't exist yet by the time this is picked up").

**Secrets scan.** `git diff` across both commits contains no credentials, API keys,
tokens, or private key material — pure task-description prose reusing existing doc
terminology ("token", "password" appear only inside unrelated pre-existing tracker rows
shown as diff context, not as new secret values). No finding.

**Scope creep.** None — diff is limited to the one new row plus its status flip, nothing
else touched.

**Design-of-record risk noted for the next developer (not a blocker for this PR):** the
row itself, once work starts, will function as the design document. It correctly frames
the two open decisions (nullable `account_id` vs. reserved system account; clone-not-edit
as hard requirement) as things to settle in implementation, and correctly scopes out the
higher-risk open marketplace variant. This is a documentation/scheduling decision, not new
runtime logic, so no code-level behavioral testing applies here.

## Review Decision
APPROVED

## Reviewed Code Commit
0d90f58cc26a764497e321af716c4ab487a9ac35

## Review Record Commit
(recorded at commit time of this file)

## Human Approval
Not Required — backend/internal tracker documentation change with nothing to visually or
product-judge; the row itself already documents that the product owner approved the
underlying idea from the 2026-08-30 brainstorm.

Status: APPROVED
