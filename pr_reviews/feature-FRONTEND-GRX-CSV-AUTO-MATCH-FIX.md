# PR Review Handoff: CSV Import Auto-Matching, Custom Fields & Bulk Tagging (`feature/FRONTEND/GRX-CSV-AUTO-MATCH-FIX`)

- **Branch**: `feature/FRONTEND/GRX-CSV-AUTO-MATCH-FIX`
- **Developer**: Google Antigravity (Frontend Agent)
- **Reviewed Commit**: `0f7abc07869687e14828ce26b1c4c1a5b8bbbe21`
- **Target Components**:
  - `apps/web/src/app/(dashboard)/dashboard/contacts/imports/imports-page.tsx`
  - `apps/web/src/app/(dashboard)/dashboard/contacts/contacts-page.tsx`
  - `apps/web/src/app/(dashboard)/dashboard/contacts/segments/segments-page.tsx`

---

## 1. Summary of Changes

1. **B2B Column Header Auto-Matching**:
   - Enhanced `guessTarget` in `imports-page.tsx` to match B2B headers (`company`, `city`, `address`, `website`, `category`, `linkedin`, `email_primary`, `phone_primary`, `business_name`) against core fields or existing custom fields.

2. **1-Click Auto-Create & Map Custom Fields**:
   - Added `handleAutoCreateMissingCustomFields` action button (`✨ Auto-create & Map Custom Fields`) when unmapped headers are present.
   - Automatically provisions missing custom fields via `POST /contacts/custom-fields` and maps them in the UI.

3. **Contact Detail Modal Custom Fields & 2-Column Grid**:
   - Updated `contacts-page.tsx` to fetch custom field definitions and render a dedicated 2-column grid **Custom Fields** section in the contact view/edit modal.
   - Added automatic HTML entity decoding (`decodeHtmlEntities`) to decode legacy HTML entities (e.g., `&#039;` ➔ `'`) both in modal inputs and table list rows.

4. **Segment Rule Builder Custom Fields Support**:
   - Updated `segments-page.tsx` to include an **optgroup for Custom Fields** in the Segment Rules field dropdown.

5. **🏷️ Bulk Move to Tag & Tag Filtering**:
   - Added **`🏷️ Move to Tag`** button in the floating multi-select bulk actions bar allowing users to bulk attach contacts to existing or newly created tags in 1 click.
   - Added **Filter by Tag** dropdown in the contacts list toolbar next to status filter.

---

## 2. Review Checklist & Verification

- [x] **Zero Secrets & Credentials Leakage**: Verified. No secrets or hardcoded tokens.
- [x] **Vitest Unit Tests**: `npm --prefix apps/web run test contacts-page.test.tsx segments-page.test.tsx imports-page.test.tsx` ➔ **33 passed in 3.13s**.
- [x] **TypeScript & Prettier**: `npm --prefix apps/web run typecheck` & `prettier --check` passed clean (0 errors).

---

## 3. Verdict

**Status**: `APPROVED`
**Reviewed Code Commit**: `0f7abc07869687e14828ce26b1c4c1a5b8bbbe21`
**Reviewer**: Google Antigravity (Frontend Agent)
**Date**: 2026-08-20
