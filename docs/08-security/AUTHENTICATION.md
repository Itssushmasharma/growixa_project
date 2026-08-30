# Authentication

- Document ID: DOC-SEC-AUTH
- Status: ACTIVE
- Version: 1.1
- Last updated: 2026-08-31
- Owner: Coding agent
- Related documents: [DECISIONS §DEC-GRX-014](../00-project-control/DECISIONS.md), [DECISIONS §DEC-GRX-037](../00-project-control/DECISIONS.md#dec-grx-037-adopt-iitdevelopers-central-iam-keycloak-for-google-sso--amends-dec-grx-014), [SECURITY_ARCHITECTURE](SECURITY_ARCHITECTURE.md), [RBAC](RBAC.md), [DATA_MODEL](../05-data/DATA_MODEL.md)

Implements [DEC-GRX-014](../00-project-control/DECISIONS.md): application-managed
authentication in FastAPI, PostgreSQL-backed, with an adapter boundary for future OIDC/SSO.
Email/password authentication, sessions, and RBAC remain application-managed. **Corrected
2026-08-31** — this previously said "no Keycloak or third-party auth provider in MVP,"
which is no longer accurate: per [DEC-GRX-037](../00-project-control/DECISIONS.md#dec-grx-037-adopt-iitdevelopers-central-iam-keycloak-for-google-sso--amends-dec-grx-014),
Google sign-in now routes through IITDeveloper's central IAM (Keycloak) — see
§"IITD IAM (Keycloak) — Google SSO" below.

## Password storage

- Hashing: **Argon2id**, tuned parameters set as configuration (not hard-coded) so cost can
  be raised as hardware improves without a schema change.
- Passwords are never logged, never included in audit-event metadata, never returned by any API.

## Token model

| Token | Lifetime | Storage | Purpose |
|---|---|---|---|
| Access token | Short-lived (minutes, exact value configurable) | Not persisted server-side; validated by signature + expiry | Authorizes API requests |
| Refresh token | Longer-lived, rotating | `refresh_tokens.token_hash` (hashed, never stored raw) | Issues a new access token; rotated (old token invalidated, new one issued) on every use |
| Password reset token | Short-lived, single-use | `password_reset_tokens.token_hash` (hashed) | One-time password reset |
| Invitation token | Longer-lived (days), single-use | `user_invitations.token_hash` (hashed) | Admin-issued invite acceptance |

Refresh-token rotation: each use invalidates the presented token and issues a new one
(`replaced_by_token_id` chain in `refresh_tokens`), so a stolen-and-reused old refresh token
is detectable (reuse of an already-rotated token revokes the whole chain).

## Browser session transport

- Access and refresh tokens are delivered to the Next.js frontend as **HttpOnly, Secure,
  SameSite** cookies — never exposed to JavaScript, never stored in `localStorage`.
- `SameSite=Lax` by default (adequate for same-site navigation flows); revisit only if a
  documented cross-site flow requires `Strict` or `None`.

## Flows

**Login:** email + password → verify Argon2id hash → on success, issue access + refresh
token cookies, record `last_login_at`, emit `user.login` audit event. On failure, emit
`user.login_failed` audit event (without leaking whether the email exists) and count toward
rate limiting.

**Logout:** revoke the presented refresh token, clear cookies, emit `user.logout` audit event.

**Logout-all-sessions:** revoke every non-revoked `refresh_tokens` row for the user, emit
`session.revoked` audit event(s).

**Password reset request:** issue a `password_reset_tokens` row (hashed), email the raw
token via the notification channel (out of scope for the token's own storage), emit
`user.password_reset_requested`. Existing sessions are not automatically revoked.

**Password reset completion:** verify token hash + expiry + unused, set new password hash,
mark token used, revoke all existing refresh tokens for the user (force re-login
everywhere), emit `user.password_reset_completed`.

**Invitation:** an Admin/Super Admin creates a `user_invitations` row with a role; the
invitee receives a link with the raw token; on acceptance, verify token hash + expiry +
unused, create the `users` row, assign the role, mark invitation accepted, emit
`invitation.accepted`.

**Account disable:** Admin sets `users.status = 'DISABLED'`; disabled users cannot log in
and their existing refresh tokens are revoked; emit an audit event via the role/user-management
action that triggered it.

**Role change:** any change to a user's `user_roles` rows emits `role.changed` with actor,
target user, old/new roles in the audit metadata.

## Rate limiting

Login attempts are rate-limited via Redis, keyed by a combination of email and IP, using a
fixed window or token-bucket (implementation detail left to the Slice 1 task, not
prescribed further here) with a conservative default (low single-digit attempts per short
window) to blunt credential-stuffing without a documented business need for a specific
number yet — capture the chosen default as a config value, not a magic number in code.

## Centralized authorization

All permission checks route through a single FastAPI dependency (e.g. `require_permission("code")`)
backed by the `permissions`/`role_permissions`/`user_roles` tables — no module re-implements
its own access check. This is what [MODULE_BOUNDARIES.md](../04-architecture/MODULE_BOUNDARIES.md)
means by "authorization is enforced centrally."

## Adapter boundary for future OIDC/SSO

The `auth` module exposes an internal `AuthProvider` interface (issue session, validate
session, resolve identity) that the application-managed implementation satisfies today. A
future OIDC/enterprise-SSO provider would implement the same interface and be selected via
configuration — no call site outside `auth` depends on the concrete implementation. This is
the "adapter boundary" required by [DEC-GRX-014](../00-project-control/DECISIONS.md).

## IITD IAM (Keycloak) — Google SSO

Per [DEC-GRX-037](../00-project-control/DECISIONS.md#dec-grx-037-adopt-iitdevelopers-central-iam-keycloak-for-google-sso--amends-dec-grx-014),
the adapter boundary above is now used for exactly the future need it was built for:
`KeycloakOAuthProvider` (`apps/api/src/growixa_api/auth/oauth/keycloak.py`) implements
the same `OAuthProvider` protocol as the direct Google provider, pointed at
IITDeveloper's central identity realm (`iam_oidc_issuer =
https://auth.iitdeveloper.com/realms/iitd`, `iam_client_id = growixa-app`, both in
`config.py`). The frontend's Google sign-in button
(`apps/web/src/components/auth/google-auth-button.tsx`) routes through
`/auth/oauth/iitd?kc_idp_hint=google`, which uses Keycloak's identity-provider hint to
pass through directly to Google rather than showing a Keycloak login screen first — the
user experience is unchanged, only the token issuer changes (Keycloak-issued tokens via
the IAM realm, rather than Google's tokens consumed directly).

**Scope**: this covers Google sign-in only. Email/password authentication, session
issuance/validation, refresh-token rotation, and RBAC are unaffected — they remain the
application-managed implementation `DEC-GRX-014` specifies, satisfying the same
`AuthProvider` interface as before. A further identity-provider change (a second SSO
provider, or moving email/password auth itself behind IAM) is out of scope for
`DEC-GRX-037` and needs its own decision.

## Audit events (minimum set, Sprint 1)

`user.login`, `user.login_failed`, `user.logout`, `user.password_reset_requested`,
`user.password_reset_completed`, `invitation.accepted`, `role.changed`, `session.revoked`.
