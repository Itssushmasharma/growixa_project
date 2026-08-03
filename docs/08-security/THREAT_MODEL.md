# Threat Model

- Document ID: DOC-SEC-THREAT
- Status: ACTIVE (expanded per slice, not redesigned)
- Version: 1.1
- Last updated: 2026-08-01
- Owner: Coding agent
- Related documents: [SECURITY_ARCHITECTURE](SECURITY_ARCHITECTURE.md), [AUTHENTICATION](AUTHENTICATION.md), [RBAC](RBAC.md)

## Sprint 1 scope

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

## Explicitly out of scope for Sprint 1

Threats involving external providers (email/social/AI/SEO), file uploads, or webhooks
didn't apply in Sprint 1 — those modules didn't exist yet. Each gets a threat-model
addendum when its owning slice starts (see
[AGENT_EXECUTION_RULES.md](../12-development/AGENT_EXECUTION_RULES.md) for the "read only
what's relevant, update as you go" workflow this implies). Slice 3's addendum follows.

## Slice 3 (Email Marketing) scope

Scope: threats reachable by Slice 3's new surface area — provider credential storage,
outbound sending, and inbound Postmark webhooks.

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T13 | SMTP credential leakage via logs | `email_provider_connections.smtp_password_encrypted` (or its decrypted form) logged in plaintext during send | Same redaction pattern as T7, extended to this field name; decrypted only in-memory inside the worker's send call, never passed to a logger |
| T14 | Forged provider webhook events | Attacker POSTs a fake "delivered"/"bounced"/"complained" payload to the public webhook endpoint, poisoning delivery status, suppression data, or analytics | Postmark's webhook URL is configured with HTTP Basic Auth credentials (stored alongside the provider connection, encrypted at rest); the endpoint rejects any request that fails that check before touching `email_events`/`message_deliveries` |
| T15 | Suppression-check bypass | A bug in the send pipeline delivers to an address on `suppression_entries` or with `consent_records` status `WITHDRAWN` | Enforced once, server-side, inside the `email_delivery` module's send path (not the UI) per [DEC-GRX-008](../00-project-control/DECISIONS.md) — covered by a dedicated negative integration test, same pattern as Sprint 1's RBAC negative tests |
| T16 | Personalization-variable injection | A contact's own field value (e.g. `first_name` containing HTML/script) is substituted unescaped into `body_html`, altering the sent email's markup | Every personalization substitution is HTML-escaped before insertion into `body_html`; only merge-tag replacement, never a template-language `eval` |
| T17 | Recipient/delivery data exposure | Campaign recipient emails or delivery status exposed to a user without `campaigns.view` | Same centralized `require_permission()` enforcement as every other module (T5's mitigation applies unchanged) |
| T18 | Sender-reputation abuse via bulk send | A compromised or malicious `campaigns.send` account mass-sends, damaging the shared Postmark sending reputation | Partially mitigated by `usage_records` giving an audit trail of every send (who, how many, when); rate-limiting or a send-approval workflow is not built in Slice 3 — accepted risk for a single-tenant, all-internal-user MVP, revisit if real abuse is observed |
| T19 | SSRF via provider connection host | `email_provider_connections.smtp_host`/`smtp_port` point the worker's outbound connection somewhere internal | Only `integrations.manage` (Super Admin only, per [RBAC.md](RBAC.md#slice-3-permission-codes)) can set this value — no lower-privilege path reaches it; accepted risk at the same trust level as any other Super-Admin-only configuration |

## Explicitly out of scope for Slice 3

Threats involving social/AI/SEO providers, file uploads, or a second email provider don't
apply yet. Slice 4's scheduling/cancellation surface (a scheduled job that must not
execute twice, a cancel race against an in-flight send) gets its own addendum when that
slice starts.
