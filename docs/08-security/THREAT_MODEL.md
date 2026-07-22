# Threat Model — Sprint 1 Scope

- Document ID: DOC-SEC-THREAT
- Status: ACTIVE (Sprint 1 scope; re-evaluated each slice)
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [SECURITY_ARCHITECTURE](SECURITY_ARCHITECTURE.md), [AUTHENTICATION](AUTHENTICATION.md), [RBAC](RBAC.md)

Scope: threats reachable by Sprint 1's surface area (auth, users, roles, company settings,
audit log, dashboard shell). Threats specific to email/social/AI/SEO are deferred to their
owning slice's threat-model update.

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T1 | Credential stuffing / brute force login | Repeated login attempts against known/guessed emails | Redis-backed rate limiting keyed by email+IP; Argon2id slows offline attack if a hash ever leaks |
| T2 | Session hijacking via token theft | XSS reading tokens from client-accessible storage | Tokens are HttpOnly cookies, never in `localStorage`/JS-accessible storage; React's default escaping limits XSS surface |
| T3 | CSRF on state-changing requests | Cross-site form/fetch using the victim's cookies | SameSite cookie attribute + CSRF token/origin check on mutating routes |
| T4 | Refresh-token replay after theft | Attacker reuses a stolen refresh token | Rotation-on-use with reuse detection — reuse of an already-rotated token revokes the whole chain |
| T5 | Privilege escalation via RBAC bypass | A lower-privilege user calls an endpoint missing a permission check | Single centralized `require_permission()` dependency; no endpoint implements its own ad hoc check; code review checklist item |
| T6 | Password-reset / invitation token guessing | Attacker guesses or brute-forces a reset/invite link | Tokens are high-entropy, single-use, short-lived (reset) or bounded-lived (invite), stored hashed so a DB read alone doesn't yield a usable token |
| T7 | Secret/credential leakage via logs | Password hash, token hash, or (later) provider secret logged in plaintext | Structured logging redacts known sensitive field names by default |
| T8 | Account takeover via disabled-account bypass | A disabled user's still-valid access token continues to work until expiry | Disabling a user revokes existing refresh tokens; short access-token lifetime bounds the exposure window |
| T9 | SQL injection | Unsanitized input reaching a raw query | ORM/parameterized queries only; no raw string-built SQL in `repositories/` |
| T10 | Audit log tampering | An admin or attacker with DB access edits/deletes audit history | `audit_logs` is insert-only at the application layer (no UPDATE/DELETE endpoint); DB-level `DELETE`/`UPDATE` grant restriction is a Sprint 1 follow-up if the hosting environment supports role-based DB grants |
| T11 | Enumeration via login error messages | Distinguishing "wrong password" from "no such user" reveals valid emails | Login failure returns a generic error regardless of which check failed |
| T12 | Denial of service via unbounded login/reset requests | Attacker floods the login or password-reset-request endpoint | Same Redis rate limiting as T1, applied to both endpoints |

## Explicitly out of scope for this version

Threats involving external providers (email/social/AI/SEO), file uploads, or webhooks don't
apply yet — those modules don't exist in Sprint 1. Each will get a threat-model addendum
when its owning slice starts (see [AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md)
for the "read only what's relevant, update as you go" workflow this implies).
