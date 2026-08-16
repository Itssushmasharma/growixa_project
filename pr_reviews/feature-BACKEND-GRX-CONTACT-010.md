Task: GRX-CONTACT-010 (Contact Deletion & Bulk Operations API)
Developer: Google Antigravity
Reviewer: Pending Independent Review
Branch: feature/BACKEND/GRX-CONTACT-010
Worktree: .worktrees/grx-contact-010-deletion
Base Commit: 8d751290b2844c2452dbdcf0a7b6fc5d5430de7e
Latest Commit: b68d487a06a8647c8d0d009c6d3d4813a5679f3b
Status: READY_FOR_REVIEW

## What Changed

1. **Alembic Migration (`c1d2e3f4a5b6_contact_soft_deletion_and_partial_index.py`) & Models (DEC-GRX-034)**:
   - Added `deleted_at: Mapped[datetime | None]` nullable timestamp column to `contacts` table.
   - Dropped strict `ux_contacts_account_id_email` unique constraint.
   - Created partial unique index `ux_contacts_account_id_email` on `["account_id", "email"]` with `postgresql_where=text("deleted_at IS NULL")`.
   - Updated `apps/api/src/growixa_api/contacts/models.py` and `apps/worker/src/growixa_worker/models.py`.

2. **Repository Layer Invisibility & Soft Deletion**:
   - `get_contact_by_id`, `get_contact_by_email`, `list_contacts`, `count_active_contacts`, dynamic segment queries (`_matching_contacts_query`), saved segment queries, and list member count queries in `growixa_api/contacts/repositories.py` all filter `Contact.deleted_at.is_(None)`.
   - `count_active_contacts` and `get_contact_growth` in `growixa_api/dashboard/repositories.py` filter `Contact.deleted_at.is_(None)`.
   - All 4 recipient resolution query paths (`_resolve_dynamic_segment`, `_resolve_saved_segment`, `_resolve_list`, `_resolve_all_contacts`) in `growixa_worker/recipients.py` filter `Contact.deleted_at.is_(None)`.
   - Implemented `soft_delete_contact`, `bulk_soft_delete_contacts`, and `purge_all_contacts_in_account` in repositories.

3. **Service & Protected API Endpoints**:
   - `DELETE /contacts/{contact_id}`: Soft-deletes a single contact (returns 204 No Content, 404 if already deleted or not found). Emits `contact.deleted` audit log.
   - `POST /contacts/bulk-delete`: Accepts `BulkDeleteContactsIn(contact_ids: list[UUID])` and returns `BulkDeleteContactsOut(deleted_count: int)`. Emits `contact.bulk_deleted` audit log.
   - `DELETE /contacts/all`: Soft-deletes all non-deleted contacts for the tenant account and returns `{"deleted_count": int}`. Emits `contact.purged` audit log.
   - All endpoints require `contacts.manage` permission and authenticated tenant context.

4. **Integration Test Suite**:
   - Created `apps/api/tests/test_contacts_deletion.py` (8 tests) covering single soft delete, 404 behavior, clean re-creation of same email via partial unique index, bulk delete, whole account audience purge, RBAC analyst restriction (403), unauthenticated rejection (401), and segment/list membership exclusion.
   - Added `test_soft_deleted_contacts_are_excluded_from_send` in `apps/worker/tests/test_send_campaign.py`.

## Why

Per DEC-GRX-034, contacts are the core communication unit of Growixa. Customers need full control to delete individual contacts, bulk-delete selected audience members, or purge an entire audience while preserving historical campaign delivery metrics, maintaining immutable suppression records, and allowing clean re-imports of previously deleted email addresses without database constraint collisions.

## Important Files

- `apps/api/migrations/versions/c1d2e3f4a5b6_contact_soft_deletion_and_partial_index.py`
- `apps/api/src/growixa_api/contacts/models.py`
- `apps/api/src/growixa_api/contacts/repositories.py`
- `apps/api/src/growixa_api/contacts/schemas.py`
- `apps/api/src/growixa_api/contacts/services.py`
- `apps/api/src/growixa_api/contacts/api.py`
- `apps/api/src/growixa_api/dashboard/repositories.py`
- `apps/worker/src/growixa_worker/models.py`
- `apps/worker/src/growixa_worker/recipients.py`
- `apps/api/tests/test_contacts_deletion.py`
- `apps/worker/tests/test_send_campaign.py`

## Tests

1. **New Integration Test Suite**:
   - `uv run --directory apps/api pytest tests/test_contacts_deletion.py` -> 8 passed in 2.19s.
2. **All Contact & Core API Tests**:
   - `uv run --directory apps/api pytest tests/test_contacts*.py tests/test_protected_routes_audit.py` -> 53 passed in 8.27s.
3. **Full API Test Suite**:
   - `uv run --directory apps/api pytest tests/` -> 396 passed, 8 skipped in 52.62s.
4. **Worker Test Suite**:
   - `uv run --directory apps/worker pytest tests/` -> 29 passed in 1.63s.
5. **Linting & Formatting**:
   - `uv run --directory apps/api ruff check .` -> All checks passed.
   - `uv run --directory apps/api ruff format --check .` -> All files formatted.
   - `uv run --directory apps/worker ruff check .` -> All checks passed.
   - `uv run --directory apps/worker ruff format --check .` -> All files formatted.
6. **Type Checking**:
   - `uv run --directory apps/api mypy .` -> Success: no issues found in 288 source files.
   - `uv run --directory apps/worker mypy .` -> Success: no issues found in 20 source files.

## Known Issues / Evidence Gaps

None.

## Review Findings

*Pending independent review.*

## Review Decision

PENDING

## Reviewed Code Commit

b68d487a06a8647c8d0d009c6d3d4813a5679f3b

## Review Record Commit

Pending review.

## Human Approval

Not Required (Standard backend API addition matching DEC-GRX-034 specification).

Status: READY_FOR_REVIEW
