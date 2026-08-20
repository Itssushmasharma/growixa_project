# PR Review — feature/SHARED/GRX-USER-003

## Summary

Adds the complete team invitation email flow (GRX-USER-003):

1. **Shared branded email layout** (`notifications/layout.py`) — `EmailContent` dataclass + `render()` producing an inline-CSS HTML part (~3.5 KB, well under Gmail's 102 KB clip limit) and a matching plain-text fallback. All three transactional emails (verification, password reset, invitation) now use this single layout.
2. **Invitation email sender** (`notifications/email.py`) — `send_invitation_email` with identical fire-and-forget contract as the two existing senders. Resolution order: DB-configured platform provider → env SMTP → no-op logged.
3. **Service layer** (`users/services.py`) — `invite_user` now returns `InvitationCreated` carrying `account_name`, `role_name`, `invited_by_name`, and `raw_token` so the route can populate both the email and the response without a second DB round-trip.
4. **API route** (`users/api.py`) — invitation email dispatched as a `BackgroundTask` after the invitation row is committed, exactly matching the pattern used for verification email.
5. **Frontend accept page** (`(auth)/accept-invitation/page.tsx`) — full-name + password + confirm-password form, success state, expired/invalid state, Suspense wrapper, uses existing `login.module.css` tokens.
6. **Team page fallback** (`team/team-page.tsx`) — replaced raw opaque token in the post-invite success banner with a full `accept-invitation?token=...` URL the admin can copy and paste.

## Branch

`feature/SHARED/GRX-USER-003`

## Commit Under Review

`e4b4536`

## Files Changed

- `apps/api/src/growixa_api/notifications/layout.py` [NEW]
- `apps/api/src/growixa_api/notifications/email.py` [MODIFIED]
- `apps/api/src/growixa_api/users/services.py` [MODIFIED]
- `apps/api/src/growixa_api/users/schemas.py` [MODIFIED]
- `apps/api/src/growixa_api/users/api.py` [MODIFIED]
- `apps/api/src/growixa_api/accounts/repositories.py` [MODIFIED]
- `apps/api/tests/email_delivery/test_email_layout.py` [NEW]
- `apps/api/tests/email_delivery/test_notifications_email.py` [MODIFIED]
- `apps/web/src/app/(auth)/accept-invitation/page.tsx` [NEW]
- `apps/web/src/app/(auth)/accept-invitation/page.test.tsx` [NEW]
- `apps/web/src/app/(dashboard)/dashboard/team/team-page.tsx` [MODIFIED]
- `apps/web/src/app/(dashboard)/dashboard/team/team-page.test.tsx` [MODIFIED]
- `docs/00-project-control/MASTER_TASK_TRACKER.csv` [MODIFIED]

## Test Results (developer)

| Suite | Result |
|---|---|
| Layout unit tests (7 tests, no DB) | PASSED |
| Team page unit tests (5 tests) | PASSED |
| Accept-invitation page unit tests (4 tests) | PASSED |
| API ruff check | PASSED |
| API ruff format | PASSED |
| API mypy (notifications + users) | PASSED — no issues in 13 source files |
| Web ESLint | PASSED — 0 errors |
| Web TypeScript | PASSED |
| Pre-commit hooks (14 hooks) | ALL PASSED |

## Primary Review Focus

1. **Secrets / credentials** — no real secrets committed; token is opaque/short-lived.
2. **Email layout** — inline CSS only, no external assets, plain-text fallback present.
3. **Fire-and-forget contract** — `send_invitation_email` swallows `EmailSendError`, logs, never re-raises.
4. **Account isolation** — `invite_user` already scoped by `account_id`; no new surface.
5. **Accept page UX** — no token → expired state; API 4xx → expired state (enumeration-safe).

## Risk: LOW

Additive change. No schema migrations. No existing endpoint contracts changed. Email layout is a pure refactor of existing senders. New page is a standalone route.

---

## Review Findings

- **Branded Email Layout (`notifications/layout.py`)**: Confirmed clean, robust inline-CSS layout with zero external asset dependencies and a complete plain-text fallback.
- **Transactional Delivery (`notifications/email.py`)**: Confirmed fire-and-forget contract (`send_invitation_email`) properly catches and logs exceptions without blocking API responses.
- **Frontend Accept-Invitation Page (`(auth)/accept-invitation/page.tsx`)**: Confirmed complete form handling with password validation, token resolution, and proper Suspense boundary.
- **Team Page URL Fallback (`team/team-page.tsx`)**: Admins now get a copyable `accept-invitation?token=...` link directly upon sending an invitation.
- **Security & Zero Secrets Audit**: Clean; short-lived hashed tokens used, no hardcoded credentials.
- **Test Evidence**:
  - `pytest tests/email_delivery/ tests/users/`: **53 passed in 11.27s**
  - `vitest run accept-invitation/page.test.tsx team-page.test.tsx`: **9 passed**
  - `tsc --noEmit` & `eslint`: **0 errors**

## Verdict

APPROVED

**Reviewed Code Commit**: e4b4536
**Reviewer**: Google Antigravity (independent review session)
**Date**: 2026-08-20

Status: APPROVED
