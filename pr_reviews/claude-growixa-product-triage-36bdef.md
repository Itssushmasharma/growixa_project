Task: Product intake triage (no single GRX-* ID — product-management pass); introduces DEC-GRX-033 (PROPOSED), DEC-GRX-034 (APPROVED), OQ-014..028, GRX-CONTACT-010..015
Developer: Claude (product/feature manager role)
Reviewer: UNASSIGNED — must be a different agent/tool; the author is disqualified
Branch: claude/growixa-product-triage-36bdef
Worktree: .claude/worktrees/growixa-product-triage-36bdef
Base Commit: f789dbb4a7be4de078d9d5d5c538939c096a0f9a
Latest Commit: 7587775b3d8b33fdf939494857479a18566fff25
Status: READY_FOR_REVIEW

## What Changed

Documentation only — no application code, tests, migrations, or dependencies touched.

1. Triaged all 10 docs in the local (gitignored) `need_review_docs/` intake folder into the
   tracked product docs. Three had already shipped ad hoc without ever being registered:
   Email Validation (`GRX-SAAS-016`/`017`), suppression extensions (`GRX-SAAS-015`), and
   the MVP-tier dashboards (`GRX-SAAS-014`). Registered them in FEATURE_CATALOG,
   FEATURE_STATUS_MATRIX and ROADMAP.
2. Opened the `FUTURE_SCOPE_LEAD_INTELLIGENCE.md` gate at the product owner's direction:
   `DEC-GRX-033` (PROPOSED, not approved) plus THREAT_MODEL T81–T89, which had no
   provenance/consent coverage before.
3. `DEC-GRX-034` (APPROVED by the product owner in-session, 2026-08-16) — contact soft
   deletion via `deleted_at`, structurally enforced invisibility, partial unique index.
4. Six new task rows (`GRX-CONTACT-010`..`015`); one `READY`, one `BLOCKED`, rest `BACKLOG`.
5. `OQ-014`..`OQ-028`, plus `OQ-SUB-001/002/003` which three tracked docs already cited as
   blockers but which had never been written down anywhere.

## Why

The intake folder had drifted badly from reality in both directions — features described as
"needs review" were already in production, while FEATURE_STATUS_MATRIX still claimed Slices
3–6 were unstarted. Product decisions were being made in conversation without landing in
DECISIONS.md or OPEN_QUESTIONS.md.

## Important Files

- `docs/00-project-control/DECISIONS.md` — DEC-GRX-033 (PROPOSED), DEC-GRX-034 (APPROVED)
- `docs/00-project-control/OPEN_QUESTIONS.md` — OQ-014..028, OQ-SUB-*
- `docs/00-project-control/MASTER_TASK_TRACKER.md` — GRX-CONTACT-010..015
- `docs/08-security/THREAT_MODEL.md` — T81–T89 (pre-build section; controls required, none built)
- `docs/02-features/FEATURE_CATALOG.md`, `FEATURE_STATUS_MATRIX.md`, `ROADMAP.md`

## Tests

None run — no code changed. Verified instead that `git diff main..HEAD` is confined to
`docs/`, and that merging `main` (66 commits) into this branch dropped nothing: all of
main's MASTER_TASK_TRACKER content is intact alongside the new rows.

## Known Issues / Evidence Gaps

- **Jurisdictional and vendor claims come from secondary web sources, not statutes or
  counsel.** The Postmark AUP finding (OQ-020) was read from Postmark's published terms;
  data-broker registration and privacy-regime claims are from secondary sources. `OQ-027`
  records that external counsel must validate these before anything ships. A reviewer
  should treat them as research, not cleared positions.
- `FEATURE_STATUS_MATRIX.md` Slices 3–6 remains stale. Flagged in-place for a full
  re-audit; deliberately not fixed here, as that is a `GRX-DOC-003`-sized pass.
- `DEC-GRX-033` is PROPOSED and must not be treated as approved. `DEC-GRX-034` is approved.

## Review Focus

1. **Scope discipline** — confirm nothing unapproved reached MASTER_TASK_TRACKER. Every
   Lead Intelligence item should be catalogued but unscheduled; `GRX-CONTACT-014` should be
   `BLOCKED`, not `BACKLOG`.
2. **DEC-GRX-034's three code claims**, which the implementation depends on: `contacts`
   has a plain unique constraint on `(account_id, email)`; the worker's `recipients.py`
   filters `status == 'ACTIVE'` in four places; `suppression_entries` has only a nullable
   `contact_id` with no cascade. Verify against the code — if any is wrong, GRX-CONTACT-010
   is mis-specified.
3. **DEC-GRX-034 vs DEC-GRX-008** — confirm the design cannot un-suppress a contact.
4. **Merge integrity** — confirm the `main` merge dropped no tracker rows from either side.
5. **Decision statuses** — confirm PROPOSED/APPROVED are recorded as stated, and that no
   decision was marked APPROVED without the product owner actually saying so.

## Review Findings

_(reviewer to complete)_

## Review Decision
_(reviewer to complete — APPROVED / CHANGES_REQUESTED)_

## Reviewed Code Commit
_(reviewer to complete)_

## Review Record Commit
_(reviewer to complete)_

## Human Approval
**Required.** These are product-scope documents. `DEC-GRX-034` was approved by the product
owner in-session on 2026-08-16; the branch as a whole still needs their explicit sign-off
recorded here before merge.

Status: READY_FOR_REVIEW
