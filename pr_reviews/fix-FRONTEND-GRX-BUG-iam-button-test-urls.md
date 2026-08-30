Task: Fix stale login/register test URLs after IITD IAM button change
Developer: Claude (Sonnet 5), interactive session
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of developer's session
Branch: fix/FRONTEND/GRX-BUG-iam-button-test-urls
Worktree: /Users/ravi/Projects/growixa (main working directory, not a dedicated worktree)
Base Commit: main @ time of branch creation
Latest Commit: a118dcf162288c282fe1b55eea9d391668bbfe53
Status: APPROVED

## What Changed

Two test files, one assertion each:
- `apps/web/src/app/(auth)/login/page.test.tsx`
- `apps/web/src/app/(auth)/register/page.test.tsx`

Both asserted the Google OAuth button's href as
`http://localhost:8000/auth/oauth/google` (the old direct-Google flow). Updated to
`http://localhost:8000/auth/oauth/iitd?kc_idp_hint=google`, matching what
`GoogleAuthButton` (`apps/web/src/components/auth/google-auth-button.tsx`) has actually
generated since the IITD IAM change merged 2026-08-30.

## Why

`v0.5.9-rc3`'s UAT deploy script ran the full frontend test suite (which apparently
hadn't been run end-to-end since the IAM button change merged) and failed on these two
tests. Root cause: `GRX-AUTH-007-iam-button-flow`'s own review evidence
(`pr_reviews/feature-FRONTEND-GRX-AUTH-007-iam-button-flow.md`) only cites `next build`
compiling and a secrets scan — no vitest run — so this broke silently at merge time and
was only caught now by the deploy script's own gate.

## Important Files

- `apps/web/src/components/auth/google-auth-button.tsx` — confirm this is genuinely the
  current, correct behavior (not itself a bug) before trusting the test update: it always
  sets `kc_idp_hint=google` regardless of `next`, so the base URL with no `next` param is
  exactly `/auth/oauth/iitd?kc_idp_hint=google` — read the component directly, don't take
  my word for it.
- The two test files themselves — confirm the new assertion matches real rendered output,
  not just the component's source.

## Tests

`cd apps/web && npx vitest run` — **322 passed, 0 failed** (up from 320 passed, 2
failed before this fix). Also ran the two files in isolation first:
`npx vitest run "src/app/(auth)/login/page.test.tsx" "src/app/(auth)/register/page.test.tsx"`
— 7 passed, 0 failed. Lint/typecheck/prettier all passed as part of the commit's
pre-commit hooks.

## Known Issues / Evidence Gaps

- This is a narrow, mechanical fix (assertion values only) — no behavior change, the
  component itself is untouched. Reviewer's main job is confirming the new expected URL
  is actually correct (per the component read above), not re-litigating the IAM decision
  itself (`DEC-GRX-037` already covers that).
- Worth asking, not blocking: should `GRX-AUTH-007-iam-button-flow`'s original review
  record be amended to note the missed test run, so this doesn't read as if that PR's
  review evidence was always incomplete without explanation? Reviewer's call whether that
  belongs in this PR or a separate note.

## Review Findings

1. **Component behavior verified directly** — read
   `apps/web/src/components/auth/google-auth-button.tsx` (HEAD, not the PR's description
   of it). Confirmed: `queryParams` always sets `kc_idp_hint=google`; `redirect_target`
   is only added `if (next && next.startsWith("/") && !next.startsWith("//"))`. With no
   `next` query param (the test render scenario in both `page.test.tsx` files), the
   resulting href is exactly `${apiUrl}/auth/oauth/iitd?kc_idp_hint=google"`, which with
   the test env's `apiUrl` is `http://localhost:8000/auth/oauth/iitd?kc_idp_hint=google`
   — matches the new assertion in both files exactly.
2. **Diff scope verified with `git diff d8f8824..a118dcf`** (base commit to the fix
   commit): exactly 2 files changed, 1 line each —
   `apps/web/src/app/(auth)/login/page.test.tsx` and
   `apps/web/src/app/(auth)/register/page.test.tsx`. Both changes are the same
   single-line href-assertion update (old direct-Google URL → new IITD IAM URL). No
   component/behavior source touched — `google-auth-button.tsx` is untouched in this
   diff.
3. **Full test suite run independently**: `cd apps/web && npx vitest run` →
   `53 test files passed (53)`, `322 tests passed (322)`, 0 failed. Matches the PR's
   claimed numbers exactly (up from the reported 320/2-failed baseline before this fix).
4. **Full branch scope check** (`git diff d8f8824..837f8c5`, base to current HEAD
   including the handoff-add commit): only the 2 test files plus this handoff markdown
   file changed — no scope creep.
5. **Secrets scan**: `git diff d8f8824..a118dcf | grep -iE "key|secret|token|password|api_key|credential"`
   — no matches. The only content changed is a query-string value
   (`kc_idp_hint=google`), which is a public OAuth IDP hint parameter, not a credential.
6. Narrow, mechanical, correctly-scoped test fix. No behavior change. No UI/customer-
   facing change beyond what `DEC-GRX-037` / `GRX-AUTH-007` already shipped and is
   already live — human approval requirement correctly assessed as "Not Required" per
   the handoff.

## Review Decision
APPROVED

## Reviewed Code Commit
a118dcf162288c282fe1b55eea9d391668bbfe53

## Review Record Commit
38f76864a3b0304f184cab1dfbaaf73cb0ed8077

## Human Approval
Not Required — test-assertion-only change matching already-approved, already-live
component behavior (`DEC-GRX-037`); no new UI/UX, customer-facing behavior change, or
high-risk surface.

Status: APPROVED
