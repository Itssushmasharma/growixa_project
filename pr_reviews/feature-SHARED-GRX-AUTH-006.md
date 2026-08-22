# PR Review Handoff: Google OAuth 2.0 / SSO Integration

**Branch**: `feature/SHARED/GRX-AUTH-006`
**Status**: `READY_FOR_REVIEW`
**Developer**: Antigravity
**Reviewed Code Commit**: `2aac344`


---

## 1. Summary of Changes

- **Database & Data Model**:
  - Added Alembic migration `e1f2a3b4c5d6_oauth_identities_table_and_nullable_password.py` creating the `oauth_identities` table (`user_id`, `account_id`, `provider`, `provider_user_id`, `email`, `avatar_url`) and altering `users.password_hash` to be `nullable=True`.
  - Added `OAuthIdentity` model in `apps/api/src/growixa_api/users/models.py`.
- **Multi-Provider Architecture (`apps/api/src/growixa_api/auth/oauth/`)**:
  - Implemented generic `OAuthProvider` Protocol and `OAuthUserProfile` schema in `base.py`.
  - Implemented `GoogleOAuthProvider` in `google.py` handling OpenID Connect scopes (`openid email profile`), authorization redirect URL building, code exchange, and user profile fetching.
  - Implemented `OAuthProviderRegistry` in `registry.py` for extensible provider resolution (GitHub, Microsoft, etc.).
- **Auth Services & Session Issuance (`apps/api/src/growixa_api/auth/services.py`)**:
  - Added `create_oauth_authorize_url` using single-use Redis-backed CSRF state tokens with short TTL.
  - Added `complete_oauth_callback` with single-use state verification/consumption, code exchange, email verification check, user resolution/linking/registration, audit event logging (`user.login`, `account.registered`), and JWT access/refresh token cookie issuance.
- **FastAPI Endpoints (`apps/api/src/growixa_api/auth/api.py`)**:
  - Added `GET /auth/oauth/{provider}`: Redirects browser to provider consent screen with state token and optional `redirect_target`.
  - Added `GET /auth/oauth/{provider}/callback`: Handles OAuth redirect, sets HttpOnly secure session cookies via `_set_auth_cookies`, and redirects to frontend destination.
- **Frontend Authentication UI (`apps/web`)**:
  - Created `<GoogleButton />` with official Google SVG icon and dark aesthetic in `src/components/auth/google-button.tsx`.
  - Created `<AuthDivider />` in `src/components/auth/auth-divider.tsx`.
  - Wired Google Sign-In into `apps/web/src/app/(auth)/login/page.tsx` with error toast handling.
  - Wired Google 1-Click Registration into `apps/web/src/app/(auth)/register/page.tsx`.

---

## 2. Testing & Verification

- `cd apps/api && uv run pytest tests/auth/test_auth_oauth.py tests/permissions/test_protected_routes_audit.py` — Passed (9 tests).
- `cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run --extra dev mypy src` — Passed (0 errors, 189 source files).
- `cd apps/web && npm test` — Passed (51 test files, 285 tests passed).
- `cd apps/web && npm run typecheck && npm run lint && npm run format:check` — Passed.
- Pre-commit hooks passed cleanly with zero secret leaks detected.

---

## 3. Review Focus Points

1. **Security & CSRF Protection**: Atomic consumption and validation of Redis state tokens in `complete_oauth_callback`.
2. **Account Linking Policy**: Safe matching by verified email (`is_email_verified`), preventing account hijacking.
3. **Session Cookie Isolation**: Identical `HttpOnly`, `Secure`, `SameSite` cookie issuance mechanism as email/password login.
4. **Provider-Agnostic Extensibility**: Generic `OAuthProvider` Protocol allows adding GitHub or other providers with zero schema migrations.

---

## 4. Independent Review Verdict

- **Reviewer**: Google Antigravity (independent review session)
- **Verdict**: `APPROVED`
- **Reviewed Code Commit**: `2aac344`
- **Date**: 2026-08-23
- **Status**: `APPROVED`
