Task: Feature - customer forgot-password/reset flow
Developer: Codex
Reviewer:
Branch: feature/FRONTEND/password-forgot-reset-flow
Worktree: /Users/ravi/Projects/growixa
Base Commit: 097363dcfbcc3ddbb0ea1f8e0d63cb9d6a128440
Latest Commit: e500e67ea08401a928aae3416ceb9cf42d390d6e
Status: READY_FOR_REVIEW

## What Changed

- Added platform transactional password-reset email delivery using the existing DB-configured provider/env SMTP fallback path.
- Wired `/auth/password-reset/request` to queue reset email delivery only when a real reset token is created, while keeping public responses generic.
- Added customer-facing `/forgot-password` and `/reset-password?token=...` pages, plus a login-page "Forgot password?" link.
- Kept the existing 30-minute password-reset TTL unchanged and preserved single-use/reset-token rejection behavior.
- Replaced one non-ASCII dash in `apps/api/alembic.ini` so Alembic config can be read under ASCII-locale test environments.

## Why

The backend already had secure reset tokens and completion logic, but customers had no UI or email delivery channel to request and use reset links.

## Important Files

- `apps/api/src/growixa_api/auth/api.py`
- `apps/api/src/growixa_api/notifications/email.py`
- `apps/web/src/app/(auth)/forgot-password/page.tsx`
- `apps/web/src/app/(auth)/reset-password/page.tsx`

## Tests

- `cd apps/api && uv run --extra dev pytest tests/auth/test_auth_password_reset.py tests/email_delivery/test_notifications_email.py` - passed, 12 tests
- `cd apps/api && uv run --extra dev ruff check .` - passed
- `cd apps/api && uv run --extra dev ruff format --check .` - passed
- `cd apps/api && uv run --extra dev mypy .` - passed
- `cd apps/api && uv run --extra dev pytest` - passed, 405 passed, 8 skipped, 1 warning
- `cd apps/web && npm run test -- login/page.test.tsx forgot-password/page.test.tsx reset-password/page.test.tsx api-client.test.ts` - passed, 15 tests
- `cd apps/web && npm run test` - passed, 50 files, 270 tests
- `cd apps/web && npm run lint` - passed with 0 errors; existing warnings remain in unrelated contacts/social files
- `cd apps/web && npm run typecheck` - passed
- `cd apps/web && npm run format:check` - passed

## Known Issues / Evidence Gaps

- No live SMTP send was performed; SMTP/provider boundaries are covered with mocked transport tests following existing project convention.
- Existing frontend lint warnings outside this change remain in `contacts-page.tsx` and `social/post-form-page.tsx`.

## Review Findings


## Review Decision
CHANGES_REQUESTED / APPROVED

## Reviewed Code Commit
e500e67ea08401a928aae3416ceb9cf42d390d6e

## Review Record Commit

## Human Approval
Required; this is customer-facing authentication UX.

Status: READY_FOR_REVIEW
