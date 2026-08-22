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
