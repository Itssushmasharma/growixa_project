Task: Product intake triage (no single GRX-* ID — product-management pass); introduces DEC-GRX-033 (PROPOSED), DEC-GRX-034 (APPROVED), OQ-014..028, GRX-CONTACT-010..015
Developer: Claude (product/feature manager role)
Reviewer: Claude Code (fresh session — same tool as author, no other tool available; documented fallback. Did not author this branch.)
Branch: claude/growixa-product-triage-36bdef
Worktree: .claude/worktrees/growixa-product-triage-36bdef
Base Commit: f789dbb4a7be4de078d9d5d5c538939c096a0f9a
Latest Commit: 2fe4577
Status: APPROVED — cleared for merge

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

Reviewer: Claude Code — a **fresh session, same tool as the author, no other tool
available**: the explicitly-documented weaker fallback per AGENT_EXECUTION_RULES.md
§Who reviews. This session did not write any part of this branch and verified every
claim below against the real files and the real application code.

All five review-focus points check out. Each was verified, not taken on trust.

**Focus 2 — DEC-GRX-034's three code claims: all three are exactly right.** This mattered
most, since `GRX-CONTACT-010` is specified on top of them:

| Claim | Verified |
|---|---|
| `contacts` has a *plain* unique constraint on `(account_id, email)` | ✅ `contacts/models.py:28` — `UniqueConstraint("account_id", "email", name="ux_contacts_account_id_email")`, no partial predicate |
| worker `recipients.py` filters `status == 'ACTIVE'` in **four** places | ✅ exactly four — lines 65, 81, 96, 104 of `apps/worker/src/growixa_worker/recipients.py` |
| `suppression_entries.contact_id` is nullable with no cascade | ✅ `Mapped[uuid.UUID \| None]`, `ForeignKey("contacts.id")` with no `ondelete` |

The first claim is the load-bearing one: because the constraint is plain rather than
partial, a soft-deleted contact's address stays blocked, and re-importing it would fail on
a row the customer cannot see. §2's partial-unique-index remedy is the correct fix, and it
cites a real precedent in the same codebase (`ux_suppression_entries_account_id_domain`,
which I confirmed uses exactly that `postgresql_where` shape).

**Focus 3 — the design cannot un-suppress.** Structurally confirmed, not just asserted:
`suppression_entries` is keyed on `email`/`domain`, and `contact_id` is a nullable
back-reference with no cascade, so deleting a contact cannot remove its suppression row.
§4 states the rule outright ("Deleting a contact must never un-suppress them") and cites
`DEC-GRX-008` correctly. §4a's rejection of suppress-as-delete is well-argued on its own
terms — it would make *more* data visible, degrade the opt-out evidence, and route an
accidental deletion through a control that is permanent by design.

**Focus 1 — scope discipline holds.** `DEC-GRX-033` is `PROPOSED` and states that nothing
may enter `MASTER_TASK_TRACKER.md` while it stays that way. I grepped the tracker for lead
intelligence, enrichment, scraping, voice qualification, data brokers and purchased lists:
**zero matches**. `GRX-CONTACT-014` is `BLOCKED` as required; `010` is `READY`, the rest
`BACKLOG` — exactly the distribution claimed.

**Focus 4 — merge integrity confirmed.** Every one of the 103 `GRX-*` tracker rows on
`main` is present on the branch (set difference is empty); the branch has 109, i.e. the
six new `GRX-CONTACT-010..015` rows and nothing lost from either side.

**Focus 5 — decision statuses are honest.** `DEC-GRX-033` records `PROPOSED` with an
explicit build-freeze clause; `DEC-GRX-034` records `APPROVED` attributed to the product
owner on 2026-08-16, with the rejected alternative preserved in §4a rather than discarded.
Nothing is marked approved that the handoff does not claim was actually approved.

Scope is docs-only — `git diff main...HEAD` touches only `docs/` and `pr_reviews/`, no
code, tests, migrations or dependencies. Nothing to run.

The two disclosures in §Known Issues are accurate and correctly scoped: the jurisdictional
and vendor claims are secondary-source research rather than cleared positions (`OQ-027`
already requires counsel), and `FEATURE_STATUS_MATRIX.md` Slices 3–6 remains stale, flagged
in place rather than half-fixed. Both are the right calls.

**One live tension to surface, not a defect in this branch.** `DEC-GRX-033` is `PROPOSED`
and forbids building external-contact-acquisition work while it stays that way — but a
branch doing exactly that already exists unmerged (`claude/extract-email-number-d98ed3`,
"UAE business directory scraper and contact dataset tooling"), and untracked `ALL_DATA.csv`
/ `scripts/` sit in the working tree. This branch is what makes that visible, which is a
point in its favour; the sequencing question belongs to the product owner. Recorded here
so approving this branch is not mistaken for approving `DEC-GRX-033`.

## Review Decision
APPROVED

## Reviewed Code Commit
2fe4577

## Review Record Commit
(this commit)

## Human Approval
**GRANTED.** Signed off by Ravi Kant Yadav (product owner) — 2026-08-16. These are
product-scope documents; `DEC-GRX-034` was approved in-session on 2026-08-16 and the
branch as a whole is now explicitly cleared for merge to `main`.

Scope of this sign-off, recorded so it is not read more broadly later: it approves the
triage pass, `DEC-GRX-034` (contact soft deletion), the `GRX-CONTACT-010..015` task rows,
and the `OQ-014..028` / `T81–T89` additions. It does **not** approve `DEC-GRX-033`, which
remains `PROPOSED` and continues to bar external-contact-acquisition work from being built
or entered into `MASTER_TASK_TRACKER.md` until separately confirmed.

Status: APPROVED — cleared for merge
