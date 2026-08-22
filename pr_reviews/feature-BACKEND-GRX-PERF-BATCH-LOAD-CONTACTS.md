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
