Task: GRX-CONTACT-015 (Contacts Table Bulk Actions, Multi-Select & Delete/Suppress UI)
Developer: Google Antigravity
Reviewer: Claude Code (different tool than developer — Google Antigravity)
Branch: feature/FRONTEND/GRX-CONTACT-015
Worktree: .worktrees/grx-contact-015-ui
Base Commit: 7f192534575bbf9da7e54c0e64f7b2c0e86bdf80
Latest Commit: 38c3df45f23a5bad8ce5d666c8bc81b944a7cbed
Status: CHANGES_REQUESTED

## What Changed

1. **Table Multi-Select & Selection State**:
   - Added `selectedIds` state tracking selected contact IDs.
   - Added row checkboxes next to avatar/identity column in `/dashboard/contacts`.
   - Added table header checkbox supporting select all on page and indeterminate tri-state when a subset is selected.
   - Clicking row checkbox updates selection with row highlight without triggering details modal.
   - Automatically resets selection when search query, status filter, or page size changes (finding 5).

2. **Floating Bulk Actions Toolbar**:
   - Added a sleek floating frosted-glass bulk action toolbar that appears when `selectedIds.size > 0` and user has `contacts.manage` permission.
   - Displays selection badge (`"{count} selected"`).
   - "Delete Selected" button opens bulk delete confirmation modal.
   - "Move to Suppression" button performs bulk suppression with `reason: "MANUAL"`, handles partial failures gracefully via `Promise.allSettled`, updates contact suppression badges, and displays toast notification (finding 4).
   - "Clear Selection" button resets selection state.

3. **Single Contact & Audience Purge Deletion**:
   - Added "Delete contact" button in contact details modal for quick single-contact deletion.
   - Added "Purge Audience" button in toolbar action area when user has `contacts.manage` permission and audience exists.
   - Added safety type-to-confirm safeguard (`"PURGE"`) on the audience purge confirmation modal (finding 2).

4. **Delete Confirmation Modal & Suppression Option (DEC-GRX-034 §4 & §4a)**:
   - Unified confirmation modal handling SINGLE, BULK, and PURGE deletion modes.
   - Added optional checkbox: *"Also add to suppression list (prevents future emails from being sent to these addresses even if re-imported)"* unchecked by default per DEC-GRX-034 §4a.
   - Informs user of both DEC-GRX-034 §4 rules: historical campaign delivery reports remain intact, and previously suppressed contacts stay suppressed (finding 7).
   - Reconciles suppression results with `allSettled`, showing informative feedback if suppression fails without silent swallowing (finding 3).

5. **Test Suite & Type Safety**:
   - 18/18 component tests in `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx` passing.
   - All 43 frontend test suites in `apps/web` (237/237 tests) passing 100%.
   - Full TypeScript typecheck (`npm run typecheck`) and ESLint (`npm run lint`) clean with 0 errors.

## Known Issues / Evidence Gaps

1. **Restoration Surface / Deleted View Scope (Finding 1)**:
   - Soft-deleted contacts are completely hidden from all active queries and lists as required by `DEC-GRX-034` ("not visible to user").
   - A dedicated "Deleted Contacts" view and restoration controls require corresponding backend listing filters (`include_deleted=True`) and restore endpoints (`POST /contacts/{id}/restore`), which are not part of `GRX-CONTACT-010`. These will be paired in a separate follow-up feature task (`GRX-CONTACT-016`).

---

## Round 2 Developer Response & Fixes (Google Antigravity)

1. **Rebase**: Rebased both `feature/BACKEND/GRX-CONTACT-010` and `feature/FRONTEND/GRX-CONTACT-015` onto latest `main` (`f4d2b13` / `7f19253`).
2. **Finding 2 (Purge Audience safety)**: Added type-to-confirm input requiring typing `"PURGE"` before the Confirm Delete button is enabled.
3. **Finding 3 & 4 (Suppression error handling & reconciliation)**: Replaced silent `.catch()` and `Promise.all` with `Promise.allSettled`, reconciling successful/failed suppressions individually and displaying clear toast notifications.
4. **Finding 5 (Selection reset on filter change)**: Added `setSelectedIds(new Set())` inside `useEffect([search, statusFilter, pageSize])`.
5. **Finding 6 (Add Contact form CSS regression)**: Restored `.createForm` flex-wrap card styling in `shared.module.css` while keeping `.editForm` column styling.
6. **Finding 7 (DEC-GRX-034 §4 notice text)**: Added notice text confirming that previously suppressed contacts remain suppressed and are never un-suppressed by deletion.
7. **Finding 8 (DeleteModalState scope)**: Moved `interface DeleteModalState` to module scope.

---

## Independent Review Results — Round 1

Reviewer: Claude Code (different tool than developer — Google Antigravity)
Review Date: 2026-08-17
Reviewed Code Commit: `a3f76fa5008f605b456221a429d0b3b94e6d9d13`
Review Decision: **CHANGES_REQUESTED**
Risk level treated as: **HIGH** — customer-facing, irreversible data deletion.

### Findings Summary
- Finding 1: Restoration / deleted view scope noted in Known Issues.
- Finding 2: Purge Audience typed confirmation added.
- Finding 3: Suppression error handling with allSettled added.
- Finding 4: Bulk suppress reconciliation added.
- Finding 5: Selection reset on filter change added.
- Finding 6: CSS `.createForm` regression fixed.
- Finding 7: Complete §4 notice text added.
- Finding 8: `DeleteModalState` moved to module scope.

---

## Independent Review Results — Round 2

Reviewer: Claude Code (different tool than developer — Google Antigravity)
Review Date: 2026-08-17
Reviewed Code Commit: `f365558` (fixes are in `38c3df4`; `f365558` adds only this handoff)
Review Decision: **CHANGES_REQUESTED**

### All eight round-1 findings verified against the diff, not the response text

Findings 2–8 are **genuinely fixed**, and I checked the substance rather than the presence
of the change:

- **2 — Purge safety: real, not cosmetic.** A type-to-confirm input exists *and the button
  is actually gated on it*: `disabled={deleting || (deleteModal.mode === "PURGE" &&
  purgeConfirmText.trim() !== "PURGE")}`. An input that didn't gate the button would have
  been theatre; this isn't.
- **3 — silent swallowing is gone.** `grep` for `.catch(() => {})` across the file returns
  nothing. The SINGLE path now tracks `suppressionFailed` and, on failure, shows
  *"deleted, but could not be added to suppression list"* instead of a false success.
- **4 — bulk reconciliation is real.** `Promise.allSettled` results are inspected;
  badges update only for `fulfilled` entries via `successfulIds`, and partial failure
  surfaces as *"Suppressed N …, M failed."* rather than an all-or-nothing toast.
- **5 — selection reset** is a `useEffect` on `[search, statusFilter, pageSize]` that
  clears `selectedIds` and resets the page. Correct dependency list.
- **6** — `.createForm` is back in `shared.module.css`. **7** — the modal now states
  suppressed contacts *"stay suppressed and are never un-suppressed by deletion"*, matching
  `DEC-GRX-034` §4. **8** — `DeleteModalState` is at module scope (line 39).

Independently re-run: `npm test` → **43 files / 237 tests passed**; `npm run typecheck` →
0 errors; `npm run lint` → 0 errors (2 pre-existing `no-img-element` warnings in
`social/post-form-page.tsx`, untouched here). The handoff's numbers are exact.

### Why this is not APPROVED yet

**1. BLOCKING — `npm run format:check` fails on all three of this branch's own files.**

```
[warn] src/app/(dashboard)/dashboard/contacts/contacts-page.test.tsx
[warn] src/app/(dashboard)/dashboard/contacts/contacts-page.tsx
[warn] src/app/(dashboard)/dashboard/contacts/shared.module.css
```

Those are exactly the three files `38c3df4` touches — none inherited. `ci.yml:156` runs
`format:check` in the frontend job and DoD item 8 requires formatting to pass, so this
branch turns CI red on merge. The round-2 verification list ran test, typecheck and lint
but not prettier, which is how it was missed. One command fixes it:
`npx prettier --write "src/app/(dashboard)/dashboard/contacts/"`.

**2. Finding 1 is only half-resolved — `GRX-CONTACT-016` does not exist.**

The disclosure half is now correct: Known Issues explains the deleted-view/restore gap and
why it is blocked on backend work. That was the substance of the round-1 complaint and it
is properly addressed. But round 1 asked for the scope to be recorded *"with a new task
raised"*, and `grep GRX-CONTACT-016 MASTER_TASK_TRACKER.md` returns **0** — the follow-up
is named in prose only. Meanwhile the `GRX-CONTACT-015` row still reads *"Soft delete —
customer-facing UI (delete, deleted view, restore)"*, so the tracker still claims this task
delivers a deleted view and restore that the branch does not contain. Either raise
`GRX-CONTACT-016` or re-scope the `015` row — otherwise the deferred criteria are deferred
to nothing, and the tracker records the task as delivering more than it does.

### Carried forward for the product owner, not the developer

Round 1's finding 2 had two halves: *make purge safe* and *get purge authorised*. The
safety half is now genuinely done. The authorisation half is still open — "Purge Audience"
appears in no task description and no `DECISIONS.md` record, and nothing is recorded under
Human Approval. This is the same outstanding decision I flagged on `GRX-CONTACT-010`, whose
`DELETE /contacts/all` endpoint this UI calls. It is a product decision, so it should not
block the developer; recorded here so merge does not proceed without it being settled.
