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

## Sprint 5 Phase E — Usage & campaign oversight (`GRX-SAAS-008`) scope

Scope: a second cross-account reach for platform admins — read access to every
account's usage totals and in-flight/failed campaigns, plus one mutating action
(pausing a campaign) reusing an existing, already-tested state transition rather than
new machinery.

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T34 | Pause as a denial-of-service lever | A compromised or rogue platform-admin credential pauses (cancels) a legitimate customer's campaign with no valid abuse reason | Gated by `platform.usage.manage` (`DEC-GRX-021`); the action is audited (see T35); `pause` reuses `campaigns/services.py`'s existing `cancel_campaign` state-machine constraint (`DRAFT`/`SCHEDULED` only), so a campaign already `SENDING`/`SENT` cannot be touched by this path at all — bounding the damage to campaigns that have not yet left the building |
| T35 | Untraceable platform-admin pause | Same class of gap as T32 — `audit_logs.actor_user_id` cannot reference a `platform_admins.id` | Same `DEC-GRX-020`/`DEC-GRX-021` pattern: `actor_user_id=None`, acting admin's id/email in `metadata` |
| T36 | Usage-data cross-account leakage | The per-account usage aggregate accidentally attributes one account's `usage_records` rows to another, or exposes more than the aggregate (e.g. individual contact-level send targets) | The aggregate is a `GROUP BY account_id, operation_type` query with no per-record detail in the response — a compromised platform-admin session learns "how much," never "to whom" |
| T37 | Cross-account campaign-oversight leakage | The queued/failed campaign list exposes campaign body content (subject/HTML) across accounts, beyond what oversight requires | The oversight list returns only status/scheduling metadata (name, status, account, timestamps) — never `subject`/`body_html`/`body_text`, which stay reachable only through the existing account-scoped customer routes |

## Sprint 5 Phase E — Secure support session (`GRX-SAAS-010`) scope

Scope: the sprint's highest-trust platform-admin capability — audited, time-limited,
banner-visible read (and narrowly-gated write) access into one specific customer
account's data, implemented as a dedicated platform-side surface rather than literal
impersonation of the customer's own session (`DEC-GRX-022`).

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T38 | Session hijack via a leaked/logged `support_session_id` | Knowledge of a session's id alone lets a different platform admin (or a captured request) read/write through it | Every session-scoped route requires the caller's *own* authenticated platform-admin id to equal the session's `platform_admin_id`, not just a valid `support_session_id` — matching a session id to the wrong admin 404s the same as an unknown id, so the check leaks no information either way |
| T39 | Stale session still usable after expiry or an explicit end | A session used after its `expires_at` has passed, or after the admin ended it early | Every read/write action re-checks `ended_at IS NULL AND expires_at > now()` at call time (not only when the session was created) — an expired or ended session behaves identically to one that never existed |
| T40 | Write escalation without the write gate | A `READ`-level session, or an admin who never held `platform.support_session.write`, performs the gated write action anyway | Two independent checks, either one alone blocks it: route-level `require_platform_permission("platform.support_session.write")`, and a session-level `access_level == "WRITE"` check in the service layer |
| T41 | Cross-account leakage via a mismatched session | A session-scoped read/write route is called with data belonging to a different account than the session's own `account_id` | Every session-scoped query derives `account_id` from the session row itself — never from a client-supplied value — so the target account is fixed the moment the session is loaded, not re-trusted per request |
| T42 | Invisible support access | An active session reads a customer's data with no way for that customer to notice, defeating the "banner-visible" requirement and enabling unnoticed snooping | `GET /support-sessions/active` (customer-authenticated, no platform permission needed) reports whether any session with `ended_at IS NULL AND expires_at > now()` exists for the caller's own `account_id`; the dashboard shell polls it and shows a persistent banner while true |
| T43 | Raw credential exposure through the write path | The gated write action is later extended to a module holding encrypted secrets (e.g. `integrations`) and starts returning them | Not reachable in this checkpoint — the only write action is `contacts.services.update_contact`, which has no encrypted-secret fields; no session-scoped route reads or writes `integrations`/`email_provider_connections` at all (`DEC-GRX-022` point 5) |

## Explicitly out of scope for Sprint 5 Phase C

Actual plan *enforcement* (contact/send limits, feature gating) has no threat surface
yet — Phase C only records a plan choice, per its own exclusions. Phase D's payment/
webhook surface is a separate addendum when that phase starts.

## Slice 5 (Social Publishing) scope

Scope: the first third-party OAuth integration in the codebase (Instagram Business via
Meta's Graph API), a public-read media bucket (required by Instagram's fetch-by-URL
publishing API), and a scheduled-publish pipeline structurally identical to Slice 4's
email dispatch pipeline (`DEC-GRX-023`, `DEC-GRX-024`).

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T44 | OAuth CSRF / connection hijack | An attacker tricks a victim into completing an OAuth flow that attaches the attacker's Instagram account to the victim's Growixa account (or steers a victim's own flow to attach to the attacker's account) | Server-generated, single-use `state` param (`secrets.token_urlsafe(32)`), stored in Redis tied to the initiating `account_id`, deleted on first read, 600s TTL; the callback cross-checks the stored `account_id` against the current session's `account_id` before persisting a connection |
| T45 | Access-token leakage via logs | `social_connections.access_token_encrypted`, or its decrypted form, ends up in application logs | Same secret-redaction convention as SMTP credentials (`DEC-GRX-009`); the token is decrypted only in-memory, inside the worker's publish call, never logged |
| T46 | Path traversal / object-store abuse via media path | A client-influenced filename is used unsanitized to build the Supabase object key | The object path is entirely server-generated (`{account_id}/{social_post_id}/{uuid4}.jpg`), never derived from the client-supplied filename |
| T47 | Cross-account post/connection access | Guessing another account's `social_post_id` or `social_connection_id` | Standard `account_id`-scoped repository lookups (same convention as every other module); a cross-account guess 404s, matching `test_cross_tenant_isolation.py`'s existing convention |
| T48 | Public-bucket media exposure | Instagram's Content Publishing API requires media at a plain, unauthenticated, fetchable URL — the storage bucket holding post images is public-read by requirement, not by mistake | Object paths are non-enumerable (UUID-random, no listing enabled on the bucket); scoped to this one bucket only, explicitly never reused for private/sensitive file storage (`DEC-GRX-024`); accepted risk, same shape as the existing unsubscribe-link-guessing risk (T18) |
| T49 | Expired/dead token causes repeated guaranteed-fail publish attempts | A Page access token dies (revoked, or the 60-day long-lived token expires) between connection and a later scheduled publish | Graph API error code 190 is classified `PermanentPublishError` and short-circuits the retry ladder immediately (rather than burning all 3 attempts against a token that can never succeed); the connection's `last_error` surfaces "reconnect required" |
| T50 | Rate-limit / platform-reputation abuse | A compromised account with `social.publish` mass-publishes, risking Instagram's per-account rate limits or the connected Page's standing | No additional rate-limiting is built in this slice beyond the existing `usage_records` audit trail; accepted risk for MVP, same framing as other usage-abuse risks (T18) |
| T51 | SSRF via the media-fetch URL | Instagram's container-create call takes an `image_url` parameter — if that URL were ever client-influenced, it could be used to probe internal network addresses | Not reachable: `image_url` is always the storage adapter's own server-constructed public URL (fixed Supabase base + server-generated path), never a client-supplied value |

## Explicitly out of scope for Slice 5

Video and carousel (multi-image) posts — deferred; the `media_type`/`position` columns on
`social_post_media` are forward-compatible, but the service layer enforces "exactly one
JPEG image" this slice. A proactive daily token-refresh ticker — deferred in favor of
inline refresh-at-publish-time; revisit if scheduled-far-in-advance posts start hitting
dead tokens in practice. Multi-Page/multi-Instagram-account customers — the OAuth flow
takes the first Facebook Page with a linked Instagram Business Account, no picker UI.
Platform-admin oversight of social connections/posts across accounts — a future,
separately-scoped capability (comparable to `GRX-SAAS-007`), not part of this slice.

## Slice 6 (AI Assistant) scope

Scope: multi-provider AI content generation (OpenAI, Azure OpenAI, Anthropic, Ollama),
platform-admin-configured default + per-account bring-your-own credentials, always
assistive (never sends/publishes directly — `DEC-GRX-006`). The first feature in this
codebase where customer-supplied free text (a rewrite request, a topic brief) is sent to
an external LLM, and the first where a customer/admin can supply an arbitrary outbound
`base_url` (`DEC-GRX-026`, `DEC-GRX-027`).

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| T52 | SSRF via customer/admin-supplied `base_url` | Azure OpenAI/Ollama connections take a free-text `base_url`; a malicious value could target cloud metadata endpoints (`169.254.169.254`) or internal services, with the API server's own credentials/network position | `ai/providers/base.py`'s shared validator rejects non-http(s) schemes and resolves+rejects private/loopback/link-local/multicast ranges and the metadata address specifically, applied uniformly to both `platform_ai_provider_config.base_url` and `ai_provider_connections.base_url` — no admin/customer asymmetry (`DEC-GRX-027`) |
| T53 | DNS rebinding bypassing save-time-only validation | A `base_url` hostname resolves to a public IP when the connection is saved (passing validation), then to a private/internal IP by the time it's actually called | The validator re-resolves and re-checks at **call time**, not only at save time, for every generation request through a custom-`base_url` adapter |
| T54 | Open-redirect-assisted SSRF | A validated `base_url` returns an HTTP redirect to an internal address on the actual call | Redirect targets are re-validated through the same IP-range check before being followed; no unchecked redirect-follow |
| T55 | AI provider API key leakage via logs or prompts | `ai_provider_connections`/`platform_ai_provider_config`'s encrypted API key, or its decrypted form, ends up in application logs or is accidentally interpolated into a prompt sent to the model itself | Same secret-redaction convention as SMTP/Instagram credentials (`DEC-GRX-009`); decrypted only in-memory inside the provider adapter's own request construction, never logged, never included in `input_context`/prompt text (`GRX-AI-005`) |
| T56 | Prompt injection via untrusted rewrite/brief input | A user (or content copy-pasted from an external source) includes text designed to make the model ignore its system prompt or leak instructions | Per `GRX-AI-007`, all such input is treated as untrusted data, never as instructions — the system prompt in `ai/prompts/templates.py` is never built by concatenating untrusted text into an instruction position; generation output is always human-reviewed before it can reach a send/publish path (`DEC-GRX-006`), bounding the practical impact to "bad suggestion," not an executed action |
| T57 | Cross-account generation/connection access | Guessing another account's `ai_generations.id` or `ai_provider_connections.id` | Standard `account_id`-scoped repository lookups (same convention as every other module); a cross-account guess 404s, matching `test_cross_tenant_isolation.py`'s existing convention |
| T58 | Runaway generation cost / usage abuse | A compromised account with `ai.manage` triggers a large volume of generation calls, running up cost against the platform's own default provider credentials | No hard rate limit built in this slice; every call writes both `ai_generations` (token/cost detail) and a `usage_records` row, giving the platform admin's existing usage view real visibility into per-account AI cost for the first time — accepted risk for MVP, same framing as Slice 5's T50, revisit with real usage data |
| T59 | Deterministic authorization bypass via model output | A capability's output is misused to influence *who* can do something (e.g. a prompt response accidentally treated as an authorization decision) | Not reachable by construction — no capability function ever returns or consumes a permission/role value; `GRX-AI-004` (deterministic authorization) is enforced structurally, not by model behavior |

## Explicitly out of scope for Slice 6

A proactive cost-cap/rate-limit enforcement mechanism (only visibility via `usage_records`
this slice — see T58). A customer-facing prompt-template editor (`DEC-GRX-028` — templates
are code-defined). Multi-step/autonomous agent workflows and LangGraph adoption
(`DEC-GRX-012` — MVP AI is single-shot assistive generation only). A UI for picking
per-generation model/temperature/other inference parameters beyond the connection's
configured `default_model` — kept to what `MVP_SCOPE.md §E` actually asks for.
