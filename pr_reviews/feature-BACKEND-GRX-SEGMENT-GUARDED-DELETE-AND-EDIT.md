# PR Review Handoff: Guarded Segment Deletion, Segment Editing & Centralized Constants

**Branch**: `feature/BACKEND/GRX-SEGMENT-GUARDED-DELETE-AND-EDIT`
**Status**: `READY_FOR_REVIEW`
**Developer**: Antigravity
**Reviewed Code Commit**: `0ffc0b9`

---

## 1. Summary of Changes

- **Guarded Segment Deletion (`DELETE /contacts/segments/{segment_id}`)**:
  - Implemented active campaign check (`DRAFT`, `SCHEDULED`, `DISPATCHING`, `SENDING`). If any active campaign references the segment, deletion is rejected with `HTTP 409 Conflict` and detailed campaign conflict payload.
  - Automatically unlinks historical campaigns (`SENT`, `CANCELLED`, `FAILED`) by setting `recipient_segment_id = NULL` so reporting & analytics remain intact.
  - Cleans up segment rules, segment members, and deletes the segment row with audit log emission (`segment.deleted`).
- **Segment Editing (`PUT /contacts/segments/{segment_id}`)**:
  - Allows updating segment name, type (`DYNAMIC` / `SAVED`), and rules list.
  - Validates rules, updates ruleset atomically, refreshes member counts, and logs audit event (`segment.updated`).
- **Rule Matching Parity**:
  - Added support for `tag` `contains` (case-insensitive substring match) and contact fields (`first_name`, `last_name`, `phone`) across API repository and Worker recipient resolver.
- **Centralized Constants & Clean Code Enforcement**:
  - Extracted shared segment rule fields and operators to `growixa_api/contacts/constants.py` with `StrEnum` and typed dictionaries.
  - Defined corresponding frontend constants `SEGMENT_RULE_FIELDS` and `SEGMENT_RULE_OPERATORS` in `types.ts`.
  - Added new trap rule to `.agents/skills/growixa-developer/SKILL.md` enforcing centralized constants and enums across all features.
- **Frontend Segment UI**:
  - Added Edit Modal, Delete Modal (with active campaign 409 conflict alert presentation), dynamic rule operators dropdown, and toast notifications.

---

## 2. Testing & Verification

- `uv run pytest tests/contacts` — 67 passed (100%).
- `uv run pytest` — 420 passed, 8 skipped (100%).
- `npm test` (web) — 51 test files, 280 tests passed (100%).
- `uv run pre-commit run --all-files` — all hooks passed (ruff, mypy, eslint, prettier, typecheck, secret detection).

---

## 3. Review Focus Points

1. Account isolation in segment deletion & update service.
2. Active campaign conflict check correctness and historical campaign unlinking.
3. No secrets or credentials leaked in source code or diffs.

---

## Independent Review

Reviewer: Claude Code (did not author this branch; developer was Antigravity)
Review Date: 2026-08-22
Reviewed Code Commit: `0ffc0b9`
Risk: **HIGH** — changes `apps/worker/.../recipients.py`, which decides who actually
receives campaign mail, and adds a destructive delete path.

Reviewed in an isolated worktree; the shared root workspace carries other sessions' state
and contaminates whole-repo gate runs.

### The trap this branch had to avoid, and did

`AGENTS.md` and the developer skill both single out the same failure: **the worker resolves
recipients independently of the API**, so a segment rule added on one side does not reach
the other. This branch adds `first_name`, `last_name`, `phone` and tag `contains` to the
rule vocabulary — exactly the change that breaks if only half lands.

I compared both builders field by field rather than assuming. `_build_rule_condition` in
`apps/api/.../contacts/repositories.py` and in `apps/worker/.../recipients.py` are
**semantically identical across all nine field types** — `status`, `email`, `first_name`,
`last_name`, `phone`, `source`, `tag`, `created_at`, `custom_field:*` — with the same
`equals` vs `ilike(f"%{value}%")` split and the same tag subquery shape. Preview and send
will agree.

The worker model also gained the matching columns, and the worker's outer query keeps
`account_id`, `status == "ACTIVE"` and `deleted_at IS NULL`.

### Guarded delete — the status set is complete, which is the part that decides correctness

`list_active_campaigns_referencing_segment` blocks on
`DRAFT, SCHEDULED, DISPATCHING, SENDING`. Checked against the `ck_campaigns_status` CHECK
constraint, the full vocabulary is `DRAFT, SCHEDULED, DISPATCHING, SENDING, SENT,
CANCELLED, FAILED` — so the blocking set is **exactly the four non-terminal states**, and
the three terminal ones are unlinked instead. A scheduled campaign cannot have its segment
deleted out from under it, which is the failure that would matter most.

The 409 names the blocking campaigns (`'Name' (STATUS)`), so the user can act on it rather
than being told "no".

### Account isolation

Every new repository function is `account_id`-scoped:
`list_active_campaigns_referencing_segment`, `unlink_historical_campaigns_referencing_segment`,
`delete_segment_row` (all three of `SegmentRule`, `SegmentMember`, `Segment`),
`replace_segment_rules`, and `refresh_saved_segment_members`. `update_segment_row` carries
no explicit filter but resolves through `get_segment_by_id(session, account_id, segment_id)`
and returns `None` otherwise, so it is scoped too — I checked rather than assuming from the
absence of a `where`.

### Gates, re-run independently

Backend: `ruff check` **All checks passed** · `ruff format --check` **295 files already
formatted** · `mypy` **Success, 293 source files**.

Frontend: `typecheck` clean · `format:check` clean · segment suite **7 passed**. Dependency
files are byte-identical to `origin/main`, which is what makes reusing an existing
`node_modules` valid here — verified before relying on it, not after.

Thirteen backend segment tests including the two that pin the new contract:
`test_delete_segment_blocked_when_targeted_by_active_campaign` and
`test_delete_segment_succeeds_when_not_in_use`, plus `test_update_segment_name_type_and_rules`.

### F1 — three new rule fields ship with no test

`first_name`, `last_name` and `phone` were added to both builders, and **nothing exercises
them**. The suite has `test_status_rule_matches_active_contacts` and
`test_tag_contains_operator_evaluates_matches` but no equivalent for the three new fields.
These decide who receives mail; a typo in one branch of a ternary would be invisible.

One parameterised test over the three fields × `equals`/`contains` closes it cheaply.

### F2 — nothing prevents the API and worker drifting apart again, and this is the one to fix

This is the more valuable of the two. The branch introduces
`contacts/constants.py` with a `SegmentRuleField` StrEnum and uses it throughout the API —
good. But `apps/worker/.../recipients.py` still matches on **string literals** and imports
none of it (`grep` for `SegmentRuleField` in the worker returns 0). So the constants are
centralised *within the API only*, and the worker remains the side that can silently fall
behind.

The apps are separate packages, so a shared import is not free — but a test is. Something
that asserts both builders accept the same field/operator set, and raises on the same
unsupported input, would turn the repo's most-repeated trap into a CI failure instead of a
review catch. Right now the parity I verified by reading is guaranteed by nothing.

### F3 — `unlink_historical_campaigns_referencing_segment` does not do what its docstring says

The docstring says it unlinks "historical/completed campaigns (SENT, CANCELLED, FAILED)".
The query has **no status filter at all** — it nulls `recipient_segment_id` for *every*
campaign in the account referencing that segment. It is correct in practice only because
its single caller runs it after the active-campaign guard has already passed. Called
directly by anything else, it would silently unlink a scheduled campaign. Either add the
status filter the docstring claims, or reword it to say the guard is the caller's
responsibility.

### Not a finding — a pre-existing divergence, recorded so it is not attributed here

The API's `_matching_contacts_query` filters `account_id` and `deleted_at` but **not**
`status`, while the worker additionally requires `status == "ACTIVE"`. So a segment preview
can count `ARCHIVED` contacts that will never be mailed, and the number the user sees can
exceed the number sent. I checked `origin/main`: both sides are byte-identical there, so
**this branch neither introduces nor worsens it.** Worth its own task; not this branch's to
carry.

Also not findings: the one-line change to
`pr_reviews/feature-BACKEND-GRX-AUTO-REASSIGN-SENDER-IDENTITIES.md` is a trailing-newline
strip from the `fix end of files` hook, not an edit to another branch's review record. No
secrets, no new permission codes (reuses `contacts.manage`/`contacts.view`), no migration.

### Evidence gap

**I could not run `pytest`** — Docker is unavailable on this machine, so the test database
is unreachable and a run fails at connection rather than at assertions. The thirteen backend
tests are read, not executed. Frontend tests did run. Someone with a working stack should
run `pytest tests/contacts` before merge; on a change that alters recipient resolution, a
green backend suite is worth having.

## Review Decision

**APPROVED**

The one thing that had to be right — API and worker resolving segment rules identically — is
right, and the guarded delete's blocking set is complete against the actual status
vocabulary. F1 and F2 are missing durability, not defects: I found no incorrect behaviour.
F2 in particular should become a follow-up task rather than being lost in this file.

## Reviewed Code Commit

`0ffc0b9`

## Human Approval

**Required** — this adds a destructive delete for a customer-facing object and changes which
contacts a campaign resolves to. Worth confirming one product point explicitly: deleting a
segment **permanently unlinks it from completed campaigns** (`recipient_segment_id` set to
`NULL`), so historical campaign records will no longer show which segment they targeted.
That is a reporting trade-off, not just an implementation detail.
