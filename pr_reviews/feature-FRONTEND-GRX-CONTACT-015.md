Task: GRX-CONTACT-015 (Contacts Table Bulk Actions, Multi-Select & Delete/Suppress UI)
Developer: Google Antigravity
Reviewer: Pending Independent Review
Branch: feature/FRONTEND/GRX-CONTACT-015
Worktree: .worktrees/grx-contact-015-ui
Base Commit: c14fd9ecf4a66e6b4ad85b0d015c71b6fc2f232e
Latest Commit: a3f76fa5008f605b456221a429d0b3b94e6d9d13
Status: READY_FOR_REVIEW

## What Changed

1. **Table Multi-Select & Selection State**:
   - Added `selectedIds` state tracking selected contact IDs.
   - Added row checkboxes next to avatar/identity column in `/dashboard/contacts`.
   - Added table header checkbox supporting select all on page and indeterminate tri-state when a subset is selected.
   - Clicking row checkbox updates selection with row highlight without triggering details modal.

2. **Floating Bulk Actions Toolbar**:
   - Added a sleek floating frosted-glass bulk action toolbar that appears when `selectedIds.size > 0` and user has `contacts.manage` permission.
   - Displays selection badge (`"{count} selected"`).
   - "Delete Selected" button opens bulk delete confirmation modal.
   - "Move to Suppression" button performs bulk suppression with `reason: "MANUAL"`, updates contact suppression badges, and displays toast notification.
   - "Clear Selection" button resets selection state.

3. **Single Contact & Audience Purge Deletion**:
   - Added "Delete contact" button in contact details modal for quick single-contact deletion.
   - Added "Purge Audience" button in toolbar action area when user has `contacts.manage` permission and audience exists.

4. **Delete Confirmation Modal & Suppression Option (DEC-GRX-034 §4 & §4a)**:
   - Unified confirmation modal handling SINGLE, BULK, and PURGE deletion modes.
   - Added optional checkbox: *"Also add to suppression list (prevents future emails from being sent to these addresses even if re-imported)"* unchecked by default per DEC-GRX-034 §4a.
   - Informs user that historical campaign delivery reports and statistics remain intact.
   - Executes `DELETE /contacts/{id}`, `POST /contacts/bulk-delete`, or `DELETE /contacts/all` and triggers suppression API calls when checkbox is enabled.

5. **Test Suite & Type Safety**:
   - Added 7 new test cases in `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx` (18/18 tests passing).
   - All 43 frontend test suites in `apps/web` (237/237 tests) passing 100%.
   - Full TypeScript typecheck (`npm run typecheck`) and ESLint (`npm run lint`) clean with 0 errors.

## Why

Per DEC-GRX-034, contacts are the core communication unit of Growixa. Customers need full UI capability to multi-select, delete selected contacts, move contacts to suppression list, and purge audience while preserving historical campaign delivery metrics and giving optional intent-based suppression control.

## Important Files

- `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.tsx`
- `apps/web/src/app/(dashboard)/dashboard/contacts/shared.module.css`
- `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx`

## Tests

1. **Contacts Page Unit & Component Tests**:
   - `npm --prefix apps/web test src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx` -> 18 passed in 1.25s.
2. **Full Web Test Suite**:
   - `npm --prefix apps/web test` -> 43 test files passed, 237 tests passed in 15.59s.
3. **Typecheck & Linter**:
   - `npm --prefix apps/web run typecheck` -> 0 errors.
   - `npm --prefix apps/web run lint` -> 0 errors.

## Review Focus

1. Verify multi-select checkboxes on `/dashboard/contacts`, select-all header checkbox, and indeterminate behavior.
2. Verify floating bulk action toolbar appears when items are selected and is hidden for view-only users.
3. Verify Delete confirmation modal and optional "Also add to suppression list" checkbox functionality.
4. Verify all tests, typechecks, and linters pass cleanly.

---

## Independent Review Results

<!-- Reviewer fills this section -->
Reviewer: Pending
Review Date: Pending
Reviewed Code Commit: Pending
Review Decision: PENDING
