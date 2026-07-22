# Security Architecture

- Document ID: DOC-SEC-ARCH
- Status: ACTIVE
- Version: 1.0
- Last updated: 2026-07-22
- Owner: Coding agent
- Related documents: [AUTHENTICATION](AUTHENTICATION.md), [RBAC](RBAC.md), [THREAT_MODEL](THREAT_MODEL.md), [PRD §26–28](../01-product/PRD.md)

## Control areas

| Control area | Sprint 1 requirement |
|---|---|
| Authentication | See [AUTHENTICATION.md](AUTHENTICATION.md) — application-managed, Argon2id, rotating refresh tokens, HttpOnly/Secure/SameSite cookies |
| Authorization | RBAC enforced server-side via a single centralized dependency — see [RBAC.md](RBAC.md) |
| Secrets | No provider secrets exist yet in Sprint 1 (no email/social/AI providers connected); the secret-storage pattern (encrypted at rest, via a secret manager or DB-level encryption, never logged) must exist as infrastructure before Slice 3 needs it |
| Transport | TLS for all non-local traffic; local Docker Compose may run plain HTTP between containers on a private network |
| Input validation | Pydantic schemas validate all request bodies; no raw dict access to user input in `services/` |
| SQL injection | SQLAlchemy ORM/parameterized queries only — no raw string-interpolated SQL |
| XSS | React's default escaping; no `dangerouslySetInnerHTML`/raw HTML rendering of user input in Sprint 1 screens (none of Sprint 1's screens render rich user content) |
| CSRF | SameSite cookies plus a CSRF token or origin check on state-changing requests, since cookie-based auth is used |
| Rate limiting | Redis-backed login rate limiting (see [AUTHENTICATION.md](AUTHENTICATION.md)) |
| Audit logging | `audit_logs` table, insert-only, covers the Sprint 1 event list in [AUTHENTICATION.md](AUTHENTICATION.md#audit-events-minimum-set-sprint-1) |
| Secret redaction in logs | Structured logging must redact `password_hash`, `token_hash`, and any future provider secret fields by field name, not by hoping call sites remember |
| Data isolation | Single-tenant — no cross-account isolation problem exists, but user-to-user isolation still applies (a Viewer must not see admin-only data) via RBAC, not a data-partitioning scheme |

## Not yet applicable in Sprint 1 (documented for continuity)

- Webhook signature validation — no external provider sends webhooks yet.
- File-upload security (type/size validation, malware-scanning strategy) — no file upload
  feature in Sprint 1.
- SSRF protection — relevant once the platform makes outbound calls to user-supplied URLs
  (crawler, future SEO track) or provider callback URLs; not exercised by Sprint 1.
- Prompt-injection defenses — relevant from Slice 6 (AI assistant) onward; the general rule
  (treat all external/imported content as untrusted data, never as instructions) is already
  recorded as GRX-AI-007 in [PRD.md](../01-product/PRD.md#23-ai-requirements) for when it's built.

## Compliance posture

Growixa does not claim formal GDPR, SOC 2, or ISO certification. Use "compliance-ready
controls" in any product copy or documentation that discusses this, per PRD §28.

## Data retention

Default retention periods for audit logs, sessions, and (later) contact/campaign history
are not yet decided — see [OQ-008](../00-project-control/OPEN_QUESTIONS.md). Sprint 1 does
not implement an auto-expiry job; this is a documented gap, not an oversight.
