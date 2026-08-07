# Threat Model

- Document ID: DOC-SEC-THREAT
- Status: ACTIVE (expanded per slice, not redesigned)
- Version: 1.3
- Last updated: 2026-08-07
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

## Sprint 5 Phase B (Platform auth boundary) scope

Scope: a new external identity class and a second, structurally separate authentication
boundary — the platform-admin session (`GRX-SAAS-002`) alongside the existing
customer-account session, per
[SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md §Phase B](../14-sprints/SPRINT_05_CUSTOMER_ACCOUNT_PLATFORM.md#phase-b--platform-auth-boundary-grx-saas-002).
No customer-facing feature changes in this phase — the new surface is entirely the
platform-admin login/permission-check path itself.

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T20 | Cross-boundary session confusion | A platform-admin session cookie is accepted by a customer `/auth/*` route, or a customer session cookie is accepted by a `/platform/auth/*` route — either direction would let one identity class act as the other | Separate cookie names and separate login routes (`POST /platform/auth/login` vs `POST /auth/login`); an integration test mints one session type and asserts 401 against the other's routes, both directions — this is Phase B's own stated acceptance criterion, not an aspirational goal |
| T21 | Wrong-permission-dependency bug | A future platform-only route is accidentally protected by `require_permission(...)` (or a customer-account route by `require_platform_permission(...)`), silently granting the wrong identity class access | `require_permission` and `require_platform_permission` are separate functions with no shared flag/parameter that could be mis-set; a static route-audit test (same pattern as the existing `require_permission` coverage test) fails the build if either module imports the other's dependency |
| T22 | Platform-admin credential enumeration | Distinguishing "wrong password" from "no such platform admin" on `POST /platform/auth/login` reveals which emails are provisioned as platform staff | Same generic-failure-message pattern as T11, applied independently to the platform login route |
| T23 | Elevated blast radius of a compromised platform-admin credential | Unlike a compromised customer admin (scoped to one `account_id`), a compromised platform-admin credential could eventually reach cross-account tooling once Phase E's features exist | Phase B itself ships no actual platform-admin *features* — `platform.access` is the only permission code that exists, gating nothing sensitive yet; same Argon2id hashing as customer accounts; Phase E's own design (`FUTURE_SCOPE_PLATFORM_ADMIN.md §Secure support access`) requires reason/ticket/time-limit/full-audit/read-only-by-default for the one genuinely high-risk capability (viewing a customer account), not a blanket "platform admin can do anything" grant |
| T24 | Unauthorized platform-admin provisioning | An attacker (or an over-privileged customer user) creates a new platform-admin identity for themselves | No such endpoint exists — per Phase B's own explicit scope, platform admins are seeded/provisioned directly (mirroring `admin@growixa.local` today), never through self-service signup; there is no attack surface here because there is no code path to attack |

## Explicitly out of scope for Sprint 5 Phase B

Any actual platform-admin feature's threat surface (support-session access to customer
data, billing/provider management, infrastructure monitoring) is out of scope until
Phase E builds it — Phase B is the auth boundary alone. Phase D's billing/webhook
surface gets its own addendum when that phase starts.

## Sprint 5 Phase C (Self-service registration) scope

Scope: the first fully public, unauthenticated write path into this app — anyone can
create an `accounts` row. Every prior write path required either an existing session
(`require_permission`) or a token issued by someone who already had one (invitation
accept). Registration has neither.

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T25 | Registration flooding / account-creation spam | Attacker scripts repeated `POST /accounts/register` calls, creating junk accounts | Same Redis-backed rate limiting as T1/T12, applied to `/accounts/register` and `/accounts/verify-email` under their own bucket, per Phase C's own scope item 5 |
| T26 | Email-registration-status enumeration (accepted, not a defect) | Registering with an already-used email returns a distinguishable "already registered" response, unlike login's deliberately generic failure (T11) | Accepted by design — a registration flow that hid this would make claiming an email impossible to attempt twice by its rightful owner; this is standard practice industry-wide, and the leaked fact ("this email has an account somewhere") is far less sensitive than a password or a specific account's existence |
| T27 | Verification-token guessing | Attacker guesses or brute-forces a verification link | Same mitigation as T6 — `account_verification_tokens.token_hash` is a high-entropy, single-use, time-limited token (`auth/tokens.py`'s existing `generate_token`/`hash_token`), stored hashed |
| T28 | Unverified-account privilege via a stale access token | A `PENDING_VERIFICATION` user somehow obtains a valid access-token cookie before verifying (e.g. a future bug reusing login's token-issuing code path incorrectly) | `login()`'s existing `status == "ACTIVE"` check (DEC-GRX-019) is the single enforcement point — registration itself never calls `create_access_token`/sets any auth cookie, so there is no code path today that could hand a `PENDING_VERIFICATION` user a session at all |
| T29 | Plan-slug tampering | A client sends an arbitrary `selected_plan_slug` value outside the two allowed plans | Rejected at both the API boundary (Pydantic `Literal["starter", "growth"]`) and the DB (`CHECK` constraint) — matches this codebase's existing double-validation pattern for `email_provider_connections.provider` |

## Sprint 5 Phase E — Account/user management (`GRX-SAAS-005`) scope

Scope: the first Phase E capability that lets a platform admin act on a customer
account it does not belong to — a new kind of cross-account reach, deliberately narrow
(status changes and a read-only activity view, no content editing).

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T30 | `accounts.status` silently unenforced (found during this task, not introduced by it) | `accounts.status` has existed since Phase A but `login()`/`refresh()` never read it — a suspended account's users could log in normally, contradicting `SPRINT_05`'s own stated Phase E acceptance criterion | Closed in this task per [DEC-GRX-020](../00-project-control/DECISIONS.md): both `login()` and `refresh()` now check `account.status == "ACTIVE"`, folded into the same generic failure as the existing `user.status` check (no new distinguishable error, preserving T11's posture); a suspend/close also immediately revokes every active session in the account rather than waiting for a token to expire |
| T31 | Suspend/close as a denial-of-service lever | A compromised or rogue platform-admin credential suspends/closes accounts it has no legitimate reason to touch | Gated by `platform.accounts.manage`, granted only to `platform.owner`/`platform.admin` (`DEC-GRX-020`); every status change is recorded (see T32) — this task does not add reason/ticket/approval workflow, since that's `GRX-SAAS-010`'s own higher-trust support-session model, deliberately scoped later per the sprint doc |
| T32 | Untraceable platform-admin action | `audit_logs.actor_user_id` FKs to `users.id`, not `platform_admins.id` — a naive implementation could leave a status change with no recorded actor at all | Per `DEC-GRX-020`, the acting platform admin's id/email is recorded in the audit event's `metadata` JSON (same `actor_user_id=None` shape `login()` already uses for an unresolvable actor), not silently dropped |
| T33 | Cross-account activity leakage via the security-activity view | The account-detail read accidentally returns another account's audit rows, or non-security business events (contact edits, campaign sends) that weren't meant to be platform-admin-visible | The read is scoped by `account_id` through the existing `list_events(account_id=...)` path (same isolation guarantee as every other account-scoped query) and filtered to a fixed security-action allow-list (`DEC-GRX-020` point 4) — not a raw dump of the account's full audit trail |

## Explicitly out of scope for Sprint 5 Phase C

Actual plan *enforcement* (contact/send limits, feature gating) has no threat surface
yet — Phase C only records a plan choice, per its own exclusions. Phase D's payment/
webhook surface is a separate addendum when that phase starts.
