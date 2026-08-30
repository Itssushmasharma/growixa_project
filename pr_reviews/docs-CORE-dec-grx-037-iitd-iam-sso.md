Task: Formalize IITD IAM (Keycloak) adoption — DEC-GRX-037 + retroactive GRX-AUTH-008/009
Developer: Claude (Sonnet 5), interactive session
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: docs/CORE/dec-grx-037-iitd-iam-sso
Worktree: /Users/ravi/Projects/growixa (main working directory, not a dedicated worktree)
Base Commit: main @ time of branch creation (rebased onto latest main before this handoff)
Latest Commit: 0cad435c2ab90846e37f227f517c7d64f1bdf8c6
Status: READY_FOR_REVIEW

## What Changed

Docs-only. Four files:
- `docs/00-project-control/DECISIONS.md` — new `DEC-GRX-037`, amending (not reversing)
  `DEC-GRX-014`'s "no Keycloak/third-party auth provider" clause; cross-reference added
  to `DEC-GRX-014`'s own Status line.
- `docs/08-security/AUTHENTICATION.md` — corrects the now-false "No Keycloak or
  third-party auth provider in MVP" line, adds a new "IITD IAM (Keycloak) — Google SSO"
  section describing what's actually live.
- `docs/00-project-control/MASTER_TASK_TRACKER.md` (+ regenerated `.csv`) — adds
  `GRX-AUTH-008` (backend) and `GRX-AUTH-009` (frontend), retroactively tracking work
  that was merged 2026-08-30 without ever having its own tracker row.

## Why

`feature/BACKEND/GRX-IAM-SSO-001` and `feature/FRONTEND/GRX-AUTH-007-iam-button-flow`
merged into `main` on 2026-08-30, adding a `KeycloakOAuthProvider` pointed at
IITDeveloper's central IAM and rewiring Google sign-in to route through it. `DEC-GRX-014`
(still `APPROVED`, never previously superseded) explicitly required a new logged decision
before any Keycloak/third-party provider could be introduced — this had not happened.
Neither of the two merged branches' reviews checked `DECISIONS.md` or
`AUTHENTICATION.md` (both reviews were code-quality-only: tests, lint, secrets scan), and
neither branch had a real `MASTER_TASK_TRACKER.md` row (both borrowed `GRX-AUTH-007`'s
ID in merge-commit messages only — that ID belongs to a different, already-`DONE`
UI-redesign task). The product owner was shown this finding directly in chat and
explicitly directed: keep the IAM integration, formalize it with a decision, and update
the docs — this branch does exactly that, nothing more (no code changes).

## Important Files

- `docs/00-project-control/DECISIONS.md` — `DEC-GRX-037` is the substantive content;
  verify it accurately scopes the amendment (Google SSO only; email/password auth,
  sessions, RBAC explicitly stated as unaffected) rather than reading as a full reversal
  of `DEC-GRX-014`.
- `docs/08-security/AUTHENTICATION.md` — verify the new IAM section's factual claims
  (issuer URL, client ID, `kc_idp_hint` behavior, which files implement it) against the
  actual merged code in `apps/api/src/growixa_api/auth/oauth/keycloak.py` and
  `apps/web/src/components/auth/google-auth-button.tsx` — this doc should describe what
  is genuinely live, not what this branch's author believes is live.
- `docs/00-project-control/MASTER_TASK_TRACKER.md` — verify `GRX-AUTH-008`/`009`'s
  evidence (commit SHAs `227d69b`/`fe1bc93` backend, `6450142`/`a7013ab` frontend) are
  real commits on `main` with the content described.

## Tests

N/A — documentation only, no code/config/schema changed. (The code these tasks retroactively
describe was already merged and tested in its own prior review cycles — this branch does
not re-test that code, only documents it accurately.)

## Known Issues / Evidence Gaps

- This is a retroactive formalization of already-merged code, not new implementation —
  reviewer should confirm the *documentation* is accurate, not re-review the IAM code
  itself (that already went through its own review cycle, however incomplete it turned
  out to be).
- Worth reviewer judgment: does `DEC-GRX-037`'s scoping (amends only the Keycloak clause,
  everything else in `DEC-GRX-014` stands) actually hold up, or does allowing Google SSO
  through a third-party-adjacent IAM have implications for other parts of `DEC-GRX-014`
  (e.g. the audit-events list, session model) that aren't addressed here? This is the
  single most consequential judgment call in this branch.
- `python3 scripts/tracker_to_csv.py --check` was run and is clean after regenerating the
  CSV in this branch — reviewer should re-run it to confirm, not just trust this note.

## Review Findings

Scope: verified `git diff main...HEAD --stat` touches exactly the four claimed files
(`DECISIONS.md`, `AUTHENTICATION.md`, `MASTER_TASK_TRACKER.md` + `.csv`) plus this handoff
— no code, no other tracker rows, no other decision's status silently changed. No
non-docs changes present.

1. **DEC-GRX-037 scoping (the consequential judgment call)** — read `DEC-GRX-014`'s full
   original text (Options/Decision/Rationale/Consequences, incl. the full requirements
   list: PostgreSQL-backed users, Argon2id hashing, session/refresh-token model, audit
   events for login/logout/failed-login/password-reset/invitation/role-change/session-
   revocation, "centralized authentication and authorization services", and the adapter
   boundary) against `DEC-GRX-037`'s full text. Then verified against the real merged
   code rather than trusting either document's framing:
   - `apps/api/src/growixa_api/auth/services.py::complete_oauth_callback` is the single
     shared code path for both `GoogleOAuthProvider` and `KeycloakOAuthProvider` — same
     function resolves/links/provisions the user, calls `record_event` (audit), and
     issues the app's own HttpOnly session cookies regardless of which OAuth provider
     was used. Confirmed by reading the function body (lines ~368-470): Keycloak/IITD
     login does not bypass application session issuance or audit logging — it only
     replaces where the *profile* (email, sub, name) comes from. This substantiates the
     "sessions, audit, RBAC unaffected" claim in both docs rather than it being an
     unverified assertion.
   - The amendment is narrowly and accurately scoped: it amends only `DEC-GRX-014`'s
     "no Keycloak/third-party provider" clause; the audit-events list, session/token
     model, and "centralized authentication services" requirement are all still
     satisfied by the same code path and are not contradicted by this change. This holds
     up under inspection, not just under the branch's own telling.
   - One thing worth naming for a future decision, not a blocker here: `DEC-GRX-014`'s
     original rationale for rejecting third-party auth explicitly cited a
     "data-residency question" as a non-issue for a single-tenant internal tool — that
     premise is now genuinely different (auth now depends on `auth.iitdeveloper.com`
     being available, and IITDeveloper's own IAM now holds identity data for Growixa
     users). `DEC-GRX-037`'s rationale addresses this implicitly (same-org IAM, not an
     unrelated third party) but doesn't explicitly discuss availability/dependency risk
     of a single external auth realm. Not a blocker for a docs-only formalization of
     already-shipped, already-tested code — but a legitimate follow-up for whoever owns
     ongoing IAM operational risk.

2. **AUTHENTICATION.md factual accuracy** — checked directly against code, not the
   branch's own claims:
   - `apps/api/src/growixa_api/config.py` lines 139-141: `iam_oidc_issuer =
     "https://auth.iitdeveloper.com/realms/iitd"`, `iam_client_id = "growixa-app"` — both
     match the doc exactly.
   - `apps/api/src/growixa_api/auth/oauth/keycloak.py`: `KeycloakOAuthProvider`
     implements the standard OIDC authorization-code exchange (`/protocol/openid-connect/
     token` then `/protocol/openid-connect/userinfo`) and satisfies the same
     `OAuthUserProfile` shape as `GoogleOAuthProvider` — matches the doc's description of
     it implementing the `OAuthProvider` protocol.
   - `apps/api/src/growixa_api/auth/oauth/registry.py`: `"iitd": KeycloakOAuthProvider()`
     and `"keycloak": KeycloakOAuthProvider()` both registered — matches.
   - `apps/web/src/components/auth/google-auth-button.tsx` lines 19/25: sets
     `kc_idp_hint=google` and builds `href` from `${apiUrl}/auth/oauth/iitd?...` — matches
     the doc's stated route and hint exactly.
   - Doc's claim that this is Google-sign-in-only, with email/password/session/RBAC
     unaffected, is consistent with the shared-callback-path finding in item 1.

3. **GRX-AUTH-008/009 tracker evidence** — ran `git show <sha> --stat` for all four SHAs
   the tracker cites: `227d69b` (merge commit, real, touches
   `auth/oauth/{api,base,google,keycloak,registry}.py` as described), `fe1bc93`
   (implementation commit, matching message/content), `6450142` (merge commit, touches
   `google-auth-button.tsx` + adds the frontend handoff file), `a7013ab` (implementation
   commit, matches). All four exist on `main` with content matching the tracker's
   description — not fabricated.

4. **Tracker formatting**: ran `python3 scripts/tracker_to_csv.py --check` myself —
   `up to date (148 tasks)`, exit 0. Clean.

5. **Prior-review claim check**: grepped `pr_reviews/feature-BACKEND-GRX-IAM-SSO-001.md`
   and `pr_reviews/feature-FRONTEND-GRX-AUTH-007-iam-button-flow.md` for
   `DECISIONS`/`DEC-GRX`/`AUTHENTICATION.md` — zero matches in either file, confirming
   the branch's claim that both prior reviews were code-quality-only and never checked
   governance docs.

6. **Secrets scan**: `git diff main...HEAD` grepped for secret/token/password/api-key/
   private-key patterns — all hits are prose describing the design (e.g. "password
   hashing", "refresh-token rotation", "no secrets" in a test-result note) or unrelated
   pre-existing tracker rows picked up by the same grep; no real credential, live token,
   or private key present. `iam_client_secret` config default is an empty string
   (env-loaded), consistent with the existing pattern for other provider secrets.

7. **Human Approval quote**: confirmed the verbatim quote ("keep it, formalize with a
   decision and update — we will use this IITD IAM", 2026-08-31) is present in
   `DEC-GRX-037`'s own Context section in `DECISIONS.md` (not just asserted in the
   handoff) — specific, dated, and attributed. This is the standard mechanism this
   project uses to record in-chat product-owner sign-off; it is as verifiable as that
   mechanism gets from inside a review.

No blocking issues found. This branch is docs-only, accurately describes already-merged,
already-tested code, and does not itself introduce new auth/RBAC/billing behavior.

## Review Decision
APPROVED

## Reviewed Code Commit
0cad435c2ab90846e37f227f517c7d64f1bdf8c6

## Review Record Commit
d9f83f7c70f74cd18309ad14e81b36db3aaf9e54

## Human Approval
Granted. Product owner (Ravi Kant Yadav) directed this formalization explicitly in chat
2026-08-31 ("keep it, formalize with a decision and update — we will use this IITD IAM"),
after being shown the governance-violation finding directly. Verified present verbatim in
`DEC-GRX-037`'s Context section in `DECISIONS.md`, not just the handoff. This branch
documents that decision; it does not itself introduce new customer-facing behavior (the
behavior is already live from the prior merges) or new auth/RBAC/billing code.

Status: APPROVED
