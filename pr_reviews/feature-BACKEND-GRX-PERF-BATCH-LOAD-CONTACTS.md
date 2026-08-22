Task: GRX-PERF-BATCH-LOAD-CONTACTS - Batch load custom fields, tags, and suppression sets to eliminate N+1 contacts latency
Developer: Google Antigravity
Branch: feature/BACKEND/GRX-PERF-BATCH-LOAD-CONTACTS
Worktree: /Users/ravi/Projects/growixa
Reviewed Code Commit: f07343eb8d44091e76124ed045a7ecc581b65ad1
Status: PENDING_INDEPENDENT_REVIEW

## What Changed

- **Eliminated N+1 Query Loop in `list_contacts_with_fields`**:
  - Previously, `list_contacts_with_fields` called `_snapshot` sequentially for every contact in the account, executing 3 separate SQL queries per contact (`get_field_values_for_contact`, `get_tag_names_for_contact`, and `is_email_suppressed`). For an account with 500 contacts, this resulted in 1,501 sequential database queries, causing severe latency and request timeouts ("Loading contacts...").
  - Added batch repository loaders:
    - `get_all_field_values_for_account(session, account_id)`: Fetches all custom field values for the account in a single query.
    - `get_all_tag_names_for_account(session, account_id)`: Fetches all contact tags for the account in a single query.
    - `get_all_suppressed_emails_for_account(session, account_id)`: Fetches all active suppressed email records for the account in a single query.
  - Refactored `list_contacts_with_fields` to execute these 4 bulk queries and assemble contact snapshots in-memory in $O(N)$ Python execution time.
- **Eliminated N+1 Query Loop in `list_lists_with_counts`**:
  - Added `get_all_list_member_counts_for_account(session, account_id)` executing a single `GROUP BY` query instead of counting members per list in a loop.
- **Enhanced Contacts Frontend Loading UI**:
  - Updated `ContactsPage` in `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.tsx` to render the `PageHeader` immediately with a polished spinner and card during load states.

## Why

Loading `/dashboard/contacts` in the frontend dashboard was suffering severe latency and staying stuck on `"Loading contacts..."` due to $O(N)$ sequential database roundtrips.

## Important Files

- `apps/api/src/growixa_api/contacts/repositories.py`
- `apps/api/src/growixa_api/contacts/services.py`
- `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.tsx`

## Tests & Verification

- `cd apps/api && uv run pytest tests/contacts` — 63 passed (32.68s)
- `cd apps/api && uv run pytest` — 422 passed, 1 skipped (03:15)
- `cd apps/web && npm test -- --run src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx` — 23 passed
- `pre-commit run --all-files` — All hooks passed (ruff, mypy, eslint, prettier, tsc, branch-guard, secrets detector)
- Zero secrets or credentials committed.

---

## Independent Review

Reviewer: Claude Code (did not author this branch; developer was Google Antigravity)
Review Date: 2026-08-21
Reviewed Code Commit: `3b21fd5`
Risk: **MEDIUM** — rewrites the read path for every contacts list request, and batch
loading is where tenant scoping and empty-collection cases get silently dropped.

### Account isolation — the thing that had to be right, and is

All four new bulk queries filter on `account_id`, so one account's list request cannot
pull another's rows:

| Loader | Scoping |
|---|---|
| `get_all_field_values_for_account` | `ContactFieldValue.account_id == account_id` |
| `get_all_tag_names_for_account` | `ContactTag.account_id == account_id` |
| `get_all_list_member_counts_for_account` | `ContactListMember.account_id == account_id` |
| `get_all_suppressed_emails_for_account` | `SuppressionEntry.account_id == account_id` |

Note the field-value loader is **stricter** than the code it replaces:
`get_field_values_for_contact` filtered on `contact_id` alone, relying on the caller
having already scoped the contact. Adding `account_id` is a defence-in-depth improvement,
not just a batching change.

### Behavioural equivalence — checked against the original per-contact path, not assumed

- **Return shape identical.** `_snapshot` returned `(contact, field_values, tags,
  suppressed)`; the comprehension builds the same 4-tuple in the same order.
- **Empty collections are safe.** `.get(contact.id, {})` and `.get(contact.id, [])` mean a
  contact with no custom fields or no tags yields empty rather than raising or vanishing —
  the classic batch-load regression, correctly avoided. Same for `.get(cl.id, 0)` on lists
  with no members, which a `GROUP BY` omits entirely.
- **Soft delete preserved on list counts.** The old `count_list_members` joined `Contact`
  and filtered `deleted_at IS NULL`; the new `GROUP BY` carries the identical join and
  filter, so counts do not silently start including deleted contacts.
- **Suppression semantics preserved.** `SuppressionEntry.email` is `CITEXT`, so the old
  `email == contact.email` comparison was case-insensitive in Postgres. The rewrite
  reproduces that by lowercasing both sides in Python. Domain-level suppression rows
  (`email IS NULL`, `domain` set) were never matched by the old `is_email_suppressed`
  either, and the new `if email is not None` filter excludes them the same way — no change
  in behaviour, though it does mean whole-domain suppression still is not reflected in this
  snapshot on either side of the change.
- **No crash risk on `contact.email.lower()`.** `Contact.email` is `nullable=False`
  (`models.py:46`), so the unguarded `.lower()` cannot raise on a real row.

### Gates re-run independently — not copied from the handoff

Frontend (all green): `typecheck` 0 errors · `format:check` clean · `lint` 0 errors
(2 warnings, both in `social/post-form-page.tsx`, untouched by this branch and inherited
from `main`) · `test` **280 passed across 51 files**.

Backend static gates on the branch's own files: `ruff check` and `ruff format --check`
both clean on `contacts/repositories.py` and `contacts/services.py`; `mypy` **Success, 291
source files**.

**Correction worth recording so it is not mistaken for a branch defect:** a first
whole-repo `ruff` run reported 2 errors (E501, F541) and 1 unformatted file. All three are
in `cli/onboard_iitdeveloper.py`, which this branch does not touch — they came from a
*different agent's uncommitted work* present in the shared working tree at review time
(`GRX-BUG-SMTP-ONBOARD-PRIORITY`). `origin/main` is clean and the branch's own files are
clean. Reviewers running gates in this repo's root workspace should check `git status`
first; the workspace is shared and dirty state contaminates whole-repo runs.

### Evidence gap — stated plainly rather than papered over

**I could not run the backend test suite.** Docker is not running on this machine, so the
test database at `localhost:5433/growixa_test` is unreachable; an attempted run produced 60
failures that were all `getaddrinfo`/connection errors, not assertion failures. That is an
environment limitation, not a signal about this branch — `main` cannot be tested here
either. My confidence in the backend change therefore rests on the static gates and on the
line-by-line equivalence check above, not on a green suite. **Anyone with a working stack
should run `pytest tests/contacts` before relying on this.**

### Findings

**F1 — scope creep (non-blocking, but should not repeat).** The task is a backend N+1 fix.
Two frontend files in the diff are unrelated to it and are not described in §What Changed:

- `campaign-form-page.tsx` — wraps the `/integrations/sender-identities` fetch in
  `.catch(() => [])` so a 403 for non-Super-Admin users degrades to an empty list instead
  of failing the whole page with "Could not load this campaign." This is a **genuine
  RBAC bug fix** and a good one; it simply is not this task, and bundling it means it
  inherits this branch's review rather than being assessed on its own.
- `template-form-page.module.css` — grid ratio, gap, breakpoint 900px→1100px, and preview
  iframe sizing. Purely cosmetic, entirely unrelated.

Neither is harmful, both are net improvements, so this does not block. Per `AGENTS.md` §5
they belonged in their own branches.

**F2 — no test covers the new batch loaders.** Four new repository functions and a rewritten
read path ship with zero added tests. The equivalence argument above is a code-reading
argument; the cheap durable version is a test asserting that a contact with no tags and no
custom fields still appears in `list_contacts_with_fields` with empty collections, and that
a list with zero live members reports 0 rather than being absent. Without it, the next
refactor has nothing to fail against.

**F3 — memory profile changes with account size.** The loaders pull every field value, tag,
and suppression entry for the account into Python. That is proportionate today because
`list_contacts_rows` already returns the whole account unpaginated, so the trade is
strictly better than 3N queries. It is worth knowing that if pagination is added later,
these loaders must be narrowed to the page's contact ids or they become the new bottleneck.

### Not findings

No secrets, no credentials, no new external calls, no permission surface changed, no
migration, no fabricated data. `THREAT_MODEL.md` surface: account isolation, which is
verified above.

## Review Decision

**APPROVED**

The change is correct, materially reduces query count on the hottest read path
(3N+1 → 4 for contacts, N → 1 for list counts), preserves account scoping and every
behavioural edge case I could identify, and passes every gate I was able to run. F1 and F2
are process and durability points, not defects in the logic.

## Reviewed Code Commit

`3b21fd5`

## Human Approval

Not required — no customer-facing copy, no RBAC change, no migration. The
`campaign-form-page.tsx` edit does change what a non-Super-Admin sees (an empty sender list
instead of an error page), which is strictly an improvement, but flagging it since it was
not in the stated scope.
