Task: Reduce GitHub Actions minutes usage (GitHub Free plan's 2,000 included minutes/month
exhausted this billing cycle, largely from redundant `ci.yml` runs) — PR #34
Developer: (no handoff file existed prior to this review; attributed to branch author per
`git log`, Ravi Kant Yadav)
Reviewer: Claude Code growixa-reviewer subagent — independent context, no memory of
developer's session, fresh review
Branch: chore/DEVOPS/reduce-ci-minutes
Worktree: /Users/ravi/Projects/growixa/.worktrees/grx-ci-minutes
Base Commit: 96ed41aaaf87d36b9c34984c4b8a32ad946d0fa8 (main)
Latest Commit: 90044529e111a36390ee16a59c0fbb7b14c296eb
Status: APPROVED

## What Changed

Single commit `9004452 chore(ci): cut Actions minutes usage on ci.yml`, touching exactly
two files (`git diff main...HEAD --stat` confirmed, no other files changed):

- `.github/workflows/ci.yml` (61 lines changed)
- `.github/workflows/dependency-audit.yml` (new file, 70 lines)

Six changes as described in the task brief:
1. `paths-ignore` via YAML anchor `&docs-only-paths` on `push`, referenced with
   `*docs-only-paths` on `pull_request`, for docs/governance-only paths.
2. Top-level `concurrency: group: ci-${{ github.workflow }}-${{ github.ref }}`,
   `cancel-in-progress: true`.
3. `pip` caching (`actions/setup-python@v5` `cache: pip` + `cache-dependency-path`) added
   to `backend` and `worker` jobs.
4. `e2e` job: `docker/setup-buildx-action@v3` + `docker/build-push-action@v6` builds and
   loads `growixa-api:latest` with a GHA cache backend before `docker compose up` (now
   without `--build`).
5. `e2e` job: `actions/cache@v4` caches `~/.cache/ms-playwright` before
   `npx playwright install chromium --with-deps`.
6. Removed the inline `Dependency security audit` steps (`pip-audit`, `npm audit`) from
   `backend`/`worker`/`frontend`; added new `.github/workflows/dependency-audit.yml`
   running the same scans weekly (Mon 03:00 UTC) + `workflow_dispatch`, with its own
   Telegram failure-alert job mirroring `ci.yml`'s `notify-on-failure` pattern.

## Why

Cut Actions-minutes consumption without changing what gets tested — only when/how much
gets rebuilt on each run.

## Important Files

- `.github/workflows/ci.yml`
- `.github/workflows/dependency-audit.yml`
- `compose.yaml` (read-only, to verify point 4)

## Tests

No test suite applies (pure CI config, no application code touched). Verification done
by direct inspection/tooling, not by running the actual GitHub Actions workflow (account's
Actions minutes are exhausted this billing cycle, so this PR's own CI run could not be
relied on as evidence — confirmed by re-reading the task brief's note and not attempting
to treat a green check as proof).

## Known Issues / Evidence Gaps

- Could not run `actionlint` (not installed, no network access to install it in this
  sandbox) — relied on `yaml.safe_load` for structural parse validity plus manual
  line-by-line inspection of `needs:`/`if:`/expression syntax instead.
- Could not confirm `docker/setup-buildx-action@v3` and `docker/build-push-action@v6` are
  live, non-yanked tags on the GitHub Marketplace (no network access) — these are very
  widely used, current major-version tags as of this reviewer's training; risk assessed
  as low.
- Branch protection / required status checks on `main` could not be inspected
  (`gh api repos/.../branches/main/protection` → 403, feature requires GitHub Pro on a
  private repo) — see finding below on why this matters for `paths-ignore`.

## Review Findings

**Scope**: Confirmed via `git diff main...HEAD --stat` and a stat re-run excluding both
workflow files (empty output) — the diff touches exactly the two stated workflow files,
nothing else. No scope creep.

**YAML validity**: Both files parse cleanly under `yaml.safe_load` (Python). Manually
walked `ci.yml`'s full structure (`on`, `concurrency`, `env`, all five jobs, `needs:`,
`if: failure()`, `${{ }}` expressions) — no syntax defects. `dependency-audit.yml` mirrors
`ci.yml`'s `notify-on-failure` job structure (same `iitdeveloper-git-shared-workflows`
Telegram action, same `secrets.TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` reference pattern).

**YAML anchor (`&docs-only-paths`/`*docs-only-paths`)**: Valid YAML anchor/alias syntax.
Confirmed via parse that both `push.paths-ignore` and `pull_request.paths-ignore` resolve
to the identical 8-item list (`docs/**`, `pr_reviews/**`, `AGENTS.md`, `CLAUDE.md`,
`RELEASE_NOTES.md`, `.agents/**`, `.claude/**`, `.github/copilot-instructions.md`).

**Point 4 — image tag matching (the highest-risk item, verified empirically, not just by
reading)**: Ran `docker compose config --images` in the worktree against the unmodified
`compose.yaml` (project name `growixa`, `api` service has no explicit `image:` key). Output
confirmed the service resolves to image name `growixa-api` — Compose's default tag when
none is specified is `latest`, i.e. `growixa-api:latest`, exactly matching the `tags:
growixa-api:latest` used in the new `docker/build-push-action@v6` step. So the later
`docker compose up -d postgres redis rabbitmq api` (no `--build`) will find and reuse the
already-built, GHA-cache-backed image rather than rebuilding or failing to find it. Even in
the worst case where the tag were wrong, Compose's documented behavior is to build
automatically if the referenced image doesn't exist locally (not to hard-fail) — so a
mismatch would have silently defeated the caching optimization rather than broken the job,
but empirically there is no mismatch here.

**Removed vs. moved (point 6)**: Diffed the removed "Dependency security audit" steps
against the new workflow — `pip-audit apps/api`, `pip-audit apps/worker`, and
`npm audit --audit-level=high` (apps/web) are all present, unchanged, in
`dependency-audit.yml`. No test/audit coverage was dropped, only its cadence (every push →
weekly + on-demand). No other steps were removed from `ci.yml`; lint/format/typecheck/
test/build/e2e steps are all still present and unchanged.

**Concurrency**: Standard `cancel-in-progress` pattern keyed on `github.ref`, scoped per
workflow name — will not cross-cancel unrelated workflows or branches. No correctness
concern.

**Caching**: `actions/setup-python@v5` `cache: pip` + `cache-dependency-path` is the
documented mechanism; worker job correctly lists both `apps/worker/pyproject.toml` and
`apps/api/pyproject.toml` since the worker job installs both. `actions/cache@v4` for
Playwright browsers is a standard, low-risk addition — a cache miss/corruption at worst
falls back to the existing `npx playwright install chromium --with-deps` step actually
reinstalling (that step is unconditional, not skipped on cache hit), so this cannot break
the job, only fail to save time on a miss.

**Secrets**: `git diff main...HEAD | grep -iE "password|secret|token|key"` shows only (a)
unchanged context lines around the pre-existing CI-only fake `ci_pg_password` credential
(already present on `main`, not introduced by this branch), (b) a Playwright cache `key:`
(not a credential), and (c) `${{ secrets.TELEGRAM_BOT_TOKEN }}` / `${{
secrets.TELEGRAM_CHAT_ID }}` — references to the GitHub Actions secrets store, mirroring
the existing pattern already used in `ci.yml`'s `notify-on-failure` job. No real secret,
credential, or token value is hardcoded anywhere in the diff.

**One non-blocking observation for the developer's awareness (not a defect in this
branch)**: `paths-ignore` combined with required status checks can, on some repos, leave a
PR's required check permanently pending if the workflow never runs for a docs-only diff.
I attempted to check whether `main` has branch protection with required status checks
matching `ci.yml`'s job names; the GitHub API returned 403 (branch protection requires
GitHub Pro on a private repo), which itself confirms no required-status-check gate is
configured on this repository today. So this is a non-issue under the *current*
repository configuration — flagging only so it's on record if branch protection is ever
added later, since re-adding required checks with `paths-ignore` present would need the
GitHub-recommended workaround (an always-run no-op job under the same check name).

No hardcoded secrets, no scope creep, no coverage regression, no broken mechanics found.

## Review Decision
APPROVED

## Reviewed Code Commit
90044529e111a36390ee16a59c0fbb7b14c296eb

## Review Record Commit
c94554b2b7700c6e6f0051a43631bdf0f37f2794

## Human Approval
Not Required — pure CI/infrastructure config change, no application code, no UI/UX or
customer-facing behavior, no auth/RBAC/billing/migration surface touched.

Status: APPROVED
