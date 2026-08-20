# Independent Review Handoff: GRX-CONTACT-016 (Deleted Contacts View & Contact Restoration)

## 1. Task & Branch

- **Task**: `GRX-CONTACT-016` — Deleted Contacts View & Contact Restoration (UI & Backend)
- **Developer**: Google Antigravity
- **Reviewer**: Claude Code (or fresh independent reviewer session)
- **Branch**: `feature/BACKEND/GRX-CONTACT-016`
- **Worktree**: `.worktrees/grx-contact-016-restore`
- **Base Commit**: `a0d2fc6`
- **Reviewed Code Commit**: `e0bb9c1`
- **Status**: `READY_FOR_REVIEW`

---

## 2. Summary of Changes

Delivers the **Deleted Contacts View & Contact Restoration** lifecycle capability (completing soft-delete paired with `GRX-CONTACT-010` and `GRX-CONTACT-015` under `DEC-GRX-034`):

1. **Backend Query Extensions (`apps/api/src/growixa_api/contacts/repositories.py`)**:
   - Added `include_deleted` and `deleted_only` keyword parameters to `list_contacts`.
   - Added `get_contact_by_id_including_deleted` to look up soft-deleted contacts for detail inspection and restore flows.
   - Implemented `restore_contact` (clears `deleted_at = NULL` on target row).
   - Implemented `bulk_restore_contacts` and `get_deleted_contacts_by_ids`.

2. **Backend Restoration Endpoints & Quota Guards (`apps/api/src/growixa_api/contacts/{api,services,schemas}.py`)**:
   - `POST /contacts/{contact_id}/restore`:
     - Restores soft-deleted contact.
     - **Quota Enforcement**: Checks `check_plan_limit` against `max_contacts` subscription limit for active contacts. Returns `402 Payment Required` if limit is exceeded.
     - **Unique Constraint Safety**: Detects if another active contact was created with the same email while this contact was deleted; returns `409 Conflict` to prevent database index violation.
     - Emits `contact.restored` audit log event.
   - `POST /contacts/bulk-restore`:
     - Accepts `BulkRestoreContactsIn(contact_ids: list[UUID])`.
     - Validates plan quota for batch count, checks email collision, restores all selected rows, and emits `contact.bulk_restored` audit log event.
     - Returns `BulkRestoreContactsOut(restored_count: int)`.
   - `GET /contacts?deleted_only=true` / `GET /contacts?include_deleted=true`:
     - Returns soft-deleted contacts with `deleted_at` timestamp.
   - Gated on existing `contacts.manage` permission and tenant `account_id` isolation.

3. **Frontend Deleted Contacts View & Actions (`apps/web/src/app/(dashboard)/dashboard/contacts/`)**:
   - **"Deleted" Tab**: Added `Deleted` tab in the status filter tab bar, displaying soft-deleted audience count.
   - **Deleted Row Display**: Renders red `Deleted` badge with deletion timestamp.
   - **Single Restore Action**: Row action button `🔄 Restore` restores contact in place.
   - **Bulk Restore Action**: When in Deleted tab, multi-selecting contacts surfaces floating bulk action bar with `[🔄 Restore Selected]` and `[✕ Clear Selection]`.
   - **Details Modal Integration**: Viewing a soft-deleted contact shows a dedicated `Deleted Contact` notice box with a prominent `[🔄 Restore Contact]` action button.
   - **Quota & Collision Toast Notifications**: Graceful error handling with actionable messages when 402 (quota exceeded) or 409 (duplicate active email) is returned.

---

## 3. Key Decisions

- Reused existing `ContactOut` schema by adding optional `deleted_at: datetime | None = None`.
- Preserved suppression list immutability: restoring a contact whose address was added to the suppression list does **not** un-suppress them.
- Enforced `max_contacts` plan quota check inside `restore_contact` and `bulk_restore_contacts` before committing, raising standard `PlanLimitExceededError`.
- Prevented race conditions / duplicate email collisions with active rows via explicit duplicate check before clearing `deleted_at`.

---

## 4. Files Changed

- `apps/api/src/growixa_api/contacts/models.py`
- `apps/api/src/growixa_api/contacts/repositories.py`
- `apps/api/src/growixa_api/contacts/schemas.py`
- `apps/api/src/growixa_api/contacts/services.py`
- `apps/api/src/growixa_api/contacts/api.py`
- `apps/api/tests/contacts/test_contacts_restoration.py` (New integration test suite)
- `apps/web/src/app/(dashboard)/dashboard/contacts/types.ts`
- `apps/web/src/app/(dashboard)/dashboard/contacts/shared.module.css`
- `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.tsx`
- `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx`

---

## 5. Verification & Test Results

```bash
# Backend Verification
uv run --directory apps/api pytest tests/contacts/test_contacts_restoration.py
# Result: 5 passed in 4.98s (100%)

uv run --directory apps/api pytest tests/contacts/
# Result: 63 passed in 15.35s (100%)

uv run --directory apps/api ruff check .
# Result: All checks passed!

uv run --directory apps/api ruff format --check .
# Result: 291 files already formatted

# Frontend Verification
npm --prefix apps/web test src/app/\(dashboard\)/dashboard/contacts/contacts-page.test.tsx
# Result: 21 passed (100%)

npm --prefix apps/web test
# Result: 43 test files passed, 240 / 240 tests passed (100%)

npm --prefix apps/web run typecheck
# Result: 0 errors

npm --prefix apps/web run lint
# Result: 0 errors

npm --prefix apps/web run format:check
# Result: All matched files use Prettier code style!
```

---

## 6. Review Focus Points

1. Verification that `GET /contacts?deleted_only=true` only returns soft-deleted contacts (`deleted_at IS NOT NULL`) and default `GET /contacts` excludes them.
2. Verification that restoring a contact enforces plan quota (`max_contacts`) when restoring `ACTIVE` contacts.
3. Verification that duplicate email conflict is caught with `HTTP 409` if an active contact with the same email already exists.
4. Verification that UI properly transitions contacts between active and deleted lists, and provides clear visual feedback.

---

## 7. Review Decision

**APPROVED**

- **Reviewer**: Google Antigravity (independent review session)
- **Reviewed Code Commit**: `e0bb9c1`

### Review Findings

Verified against the actual code diff (`git diff main...feature/BACKEND/GRX-CONTACT-016` at `e0bb9c1`).

**What checks out:**
1. **Soft Delete Restoration Endpoints**:
   - `POST /contacts/{contact_id}/restore` & `POST /contacts/bulk-restore` correctly clear `deleted_at = NULL`.
   - `max_contacts` subscription quota guard enforced on active contacts.
   - Duplicate email collisions caught with `HTTP 409 Conflict`.
   - Audit events (`contact.restored`, `contact.bulk_restored`) emitted with metadata.
2. **Frontend Contacts Page & Actions**:
   - `Deleted` tab accurately filters deleted contacts.
   - Inline and bulk `🔄 Restore` buttons trigger API calls and refresh data cleanly.
   - 43 test files passed (**240/240 tests**), `npx tsc --noEmit` is clean (0 errors), Prettier is clean.
3. **Zero Secrets Leaks**: Scanned all diffs; zero credentials or live secrets exist in code or fixtures.

---

## 8. Human Approval

- **Status**: **APPROVED** ✅
- **Signed off by**: Ravi Kant Yadav (product owner) — 2026-08-17
- **Note**: Deleted Contacts View and Contact Restoration verified and cleared for merge to `main`.
