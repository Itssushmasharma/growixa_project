Task: chore/DEVOPS — promote already-tested UAT (RC) image to production instead of
rebuilding from source, to conserve exhausted GitHub Free Actions minutes.
Developer: (see branch commit author — not this reviewer)
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of
developer's session
Branch: chore/DEVOPS/promote-uat-image-to-production
PR: https://github.com/iitdeveloper-git/growixa/pull/35
Worktree: /Users/ravi/Projects/growixa/.worktrees/grx-promote-prod
Base Commit: main (as of review)
Latest Commit: 5fb326facebf1479db6aea2e0ef530ae8e2666e4
Status: APPROVED

## What Changed

`.github/workflows/deploy-production.yml`:
- New `resolve-source` job (no `needs`): computes `release_tag` (from pushed tag or
  `workflow_dispatch.release_tag`) and `source_tag` (`workflow_dispatch.source_rc_tag` or
  auto-derived `${release_tag}-rc1`); runs `docker buildx imagetools inspect` against GHCR
  for `growixa-api/worker/web:$source_tag`; outputs `promote=true` only if all three exist.
- `test` and `build-and-push` gained `needs: [resolve-source, (test)]` and
  `if: needs.resolve-source.outputs.promote != 'true'` — now fallback-only. Their own local
  "Determine Release Tag" steps were removed in favor of `resolve-source`'s output.
- New `promote` job (`if: promote == 'true'`): `docker buildx imagetools create` retags the
  RC images as `$release_tag` and `latest` per service — registry-side manifest copy, no
  rebuild/pull.
- `deploy` now `needs: [resolve-source, test, build-and-push, promote]` with
  `if: always() && resolve-source.result == 'success' && (promote.result == 'success' ||
  build-and-push.result == 'success')`; its own "Determine Release Tag" step was removed,
  using `needs.resolve-source.outputs.release_tag` instead. The `actions/checkout@v4` step
  was moved to after the "Ensure target directory permissions" SSH step but still before
  the "Sync deploy files to OVH VPS" scp step that needs the local `deploy/` directory.
- `notify-failure`'s `needs` expanded to include `resolve-source`, `promote`.

`.agents/skills/growixa-infra/SKILL.md`: short doc addition describing the promote-vs-
fallback behavior and the `source_rc_tag` escape hatch.

## Why

GitHub Free plan's Actions minutes are exhausted this cycle. A production tag `vX.Y.Z`
almost always names the exact commit already tested and built as `vX.Y.Z-rc1` for UAT
minutes/hours earlier. This implements "build once, promote the same artifact" — standard
CI/CD practice, cheaper and safer (prod runs the exact bytes UAT verified, no rebuild
drift) — falling back to the original full test+build path when no matching RC image is
found.

## Important Files

- `.github/workflows/deploy-production.yml` (the entire behavioral change)
- `.agents/skills/growixa-infra/SKILL.md` (doc-only)

## Tests

No automated tests apply to workflow YAML in this repo (no actionlint/CI-runner
harness configured here). Verification performed by this review:
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy-production.yml'))"`
  → valid YAML.
- `actionlint` not installed in this environment — not run.
- No live execution: this workflow only truly runs end-to-end when a real `vX.Y.Z`
  production tag is pushed. **This review is static/by-hand tracing of the YAML job graph,
  not a live-run confirmation** — flagged explicitly per the task brief, and the developer
  flagged the same limitation.

## Known Issues / Evidence Gaps

- Not exercised against real GHCR images/tags in this PR (explicitly out of scope for a
  static review; only a real production tag push will prove it end-to-end).
- Minor, non-blocking: the `promote` job's retag loop (`for svc in api worker web; do
  docker buildx imagetools create ...`) has no explicit `set -e`, but GitHub Actions'
  default `bash` shell for `run:` steps already applies `-eo pipefail`, so a mid-loop
  failure (e.g. `worker` retag fails after `api` succeeded) stops the job immediately,
  leaving a partial retag on GHCR (api retagged, worker/web not). This is a registry
  hygiene wrinkle, not a deploy-safety issue — the `deploy` job's `if:` correctly requires
  `promote.result == 'success'`, so a partial/failed `promote` still blocks `deploy`. Same
  class of risk already existed pre-change in `build-and-push`'s three sequential
  build-push steps, so this isn't a regression introduced by this branch. Not a blocker.
- Pre-existing (unmodified by this branch): `notify-success`'s Telegram message uses
  `${{ github.ref_name }}` for `release_tag`, which is wrong for `workflow_dispatch`
  triggers (would show the dispatched ref/branch, not the `release_tag` input) — this bug
  already existed before this PR and is out of scope here.

## Review Findings

**Scope**: `git diff main...HEAD --stat` touches exactly the two files described —
`.github/workflows/deploy-production.yml` and `.agents/skills/growixa-infra/SKILL.md`.
`.github/workflows/deploy-uat.yml` has a 0-line diff (confirmed via `git diff main...HEAD
-- .github/workflows/deploy-uat.yml`) — UAT still always runs full test+build, which is
correct since UAT is where the real testing that this promote scheme depends on must
happen. No scope creep.

**Secrets**: `git diff main...HEAD | grep -iE "secret|token|password|key"` (excluding
known `secrets.*` references and existing env var names already present pre-change)
returned no hits. No new secrets/credentials introduced; all auth continues to flow
through `secrets.GITHUB_TOKEN`, `secrets.OVH_VPS_*`, `secrets.TELEGRAM_*` — all pre-
existing repository secrets, none hardcoded, none logged.

**Auth/permissions**: workflow-level `permissions: contents: read, packages: write` is
unchanged from before this PR. `packages: write` on `GITHUB_TOKEN` covers both
`docker buildx imagetools inspect` (read) in `resolve-source` and `docker buildx imagetools
create` (write) in `promote` — no new PAT or secret needed, matches the design intent.

**`docker buildx imagetools create`/`inspect` semantics**: both operate purely against the
registry manifest API via the buildx builder set up by `docker/setup-buildx-action@v3` and
the registry session established by `docker/login-action@v3` — no local pull, no rebuild.
This matches documented Docker Buildx behavior and the developer's claim.

**Job graph — traced by hand for both paths and failure modes** (this was the deepest
part of the review, given the risk level):

*Key GitHub Actions rule applied*: a job with `needs` and a **custom `if:` that does not
include a status-check function** (`success()`/`failure()`/`always()`/`cancelled()`) still
has an implicit `success()` ANDed in — and `success()` over a `needs` list is false if
*any* needed job did not itself succeed, including a job that was **skipped**. A job whose
`if:` *does* include `always()` bypasses that implicit check entirely and is evaluated
purely on its own explicit condition. `failure()` (used bare, no `always()`) only becomes
true if a needed job's result is exactly `'failure'` — a skipped needed job does not
trigger it.

- *Promote path* (`resolve-source.outputs.promote == 'true'`): `test`'s `if:` evaluates
  false → skipped. `build-and-push` needs `[resolve-source, test]`; because `test` is
  skipped, the implicit `success()` check makes `build-and-push` skip regardless of its own
  `if:` value — correct, matches intent. `promote` needs only `[resolve-source]`
  (succeeded) and its own `if:` is true → runs. `deploy`'s `if:` uses `always()` so bypasses
  the implicit-skip rule and is evaluated purely on its explicit clause:
  `resolve-source.result == 'success' && (promote.result == 'success' ||
  build-and-push.result == 'success')` → true (promote succeeded) → `deploy` runs. Correct.
- *Promote path, `promote` job fails* (e.g. registry write error): `deploy`'s explicit
  clause becomes `success && (false || false)` (build-and-push is still skipped, not
  success) → false → `deploy` correctly does **not** run. No accidental deploy on failure.
- *Fallback path* (`promote == 'false'`, no matching RC image): `test`'s `if:` is true and
  its own `needs` (`resolve-source`, succeeded) implicit-success passes → runs. If `test`
  succeeds, `build-and-push`'s `if:` is true and its `needs` (`resolve-source`, `test`,
  both succeeded) implicit-success passes → runs. `promote`'s `if:` is false → skipped.
  `deploy`'s explicit clause: `promote.result == 'success'` is false (skipped) but
  `build-and-push.result == 'success'` is true → `deploy` runs. This reproduces the
  original (pre-PR) workflow's behavior exactly for this case — confirmed no regression.
- *Fallback path, `test` fails*: `build-and-push` needs `test` (failed) → implicit
  `success()` makes it skip regardless of its own `if:`. `promote` skipped (flag false).
  `deploy`'s explicit clause: both disjuncts false (build-and-push skipped, promote
  skipped) → `deploy` correctly does not run.
- *Fallback path, `build-and-push` fails*: same result — `deploy`'s explicit clause has
  `build-and-push.result == 'success'` false and `promote.result == 'success'` false (still
  skipped) → `deploy` does not run.
- *`resolve-source` itself fails* (e.g. bad tag parsing, GHCR login failure): every
  downstream job that needs it (`test`, `build-and-push`, `promote`) is skipped via the
  implicit-success rule regardless of their own `if:` clauses. `deploy`'s explicit clause
  requires `resolve-source.result == 'success'`, which is false → `deploy` does not run.
  `notify-failure` (`if: failure()`, `needs` includes `resolve-source`) correctly fires
  because a needed job's result is exactly `'failure'`.
- **No scenario traced produces the two named worst-case bugs**: (a) `deploy` never runs
  when both `promote` and `build-and-push` were merely skipped (both disjuncts require
  `== 'success'`, and "skipped" never satisfies that), and (b) `deploy` never runs when
  either artifact-producing job actually failed (same reasoning). Both failure modes
  described in the task brief are correctly prevented by the explicit `if:` clause.
- `notify-failure`'s expanded `needs` list is safe: `if: failure()` only fires on an actual
  `'failure'` result among its needs, never on `'skipped'`, so the two new fallback-only
  jobs (`test`, `build-and-push`) being legitimately skipped on the promote path, and
  `promote` being legitimately skipped on the fallback path, does not spuriously trigger a
  failure notification. Confirmed by tracing all scenarios above — no path produces a
  false-positive or false-negative notification.

**Checkout reordering in `deploy`**: `actions/checkout@v4` moved from first step to after
"Ensure target directory permissions on VPS" (a pure remote-SSH step with no dependency on
local repo files) and still runs before "Sync deploy files to OVH VPS" (which uses
`source: "deploy/"`, requiring the local checkout). Confirmed harmless — SSH step doesn't
read the workspace, checkout precedes the step that needs it.

**Backward-compatible fallback**: traced above — when `resolve-source` finds no matching
RC image, the resulting `test` → `build-and-push` → `deploy` sequence is behaviorally
identical to the pre-PR workflow (same steps, same tag source now via `resolve-source`
output instead of a duplicated local "Determine Release Tag" step, same gating). No
regression for that case.

**Doc accuracy**: `.agents/skills/growixa-infra/SKILL.md`'s added description
(`growixa-*:v1.0.0-rc1`, same version number, `-rc1` convention) matches the workflow's
actual auto-derivation logic (`SOURCE="${TAG}-rc1"` when `source_rc_tag` is blank).

## Review Decision
APPROVED

## Reviewed Code Commit
5fb326facebf1479db6aea2e0ef530ae8e2666e4

## Review Record Commit
(recorded by this commit — see branch log)

## Human Approval
Required. This is a HIGH-RISK change to the real production deployment pipeline (OVH VPS,
GHCR images, `OVH_VPS_HOST/USER/SSH_KEY`, `GITHUB_TOKEN`, Telegram secrets) per
AGENTS.md §4.5 and the task's own risk framing. Independent-agent review here is
static/by-hand YAML tracing only — this workflow has **not** been exercised end-to-end
against real GHCR images (no RC image existed to test the promote path against at review
time). The first real production tag push after merge will be the first live execution of
`resolve-source`/`promote`. Given AGENTS.md §1.1's own stricter rule ("NEVER push
production release tags or trigger production deployment without explicit, prior user
confirmation"), the product owner should explicitly approve both (a) merging this workflow
change, and (b) being the one to authorize/observe the first production tag push that
exercises it live, treating that first run as the real validation this static review
cannot provide.

Status: APPROVED
