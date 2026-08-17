Task: GRX-INFRA-005 - Fix GHCR Compose production Postgres port collision
Developer: Codex
Reviewer: Codex (fresh session - same tool as developer, no other tool available)
Branch: feature/BACKEND/fix-prod-compose-port-collision
Worktree: /Users/ravi/Projects/growixa
Base Commit: 097363d
Latest Commit: 1f1a48e
Status: CHANGES_REQUESTED

## What Changed

- Removed the production Postgres host publish on `127.0.0.1:5432`.
- Added stable Compose project names for production and UAT deploy/backup commands.
- Pinned existing Docker volume names so the project-name migration keeps current data volumes attached.
- Updated OVH runbook, infra playbook, changelog, project status and tracker.

## Why

The production GHCR deploy failed during migrations because Compose tried to recreate Postgres with host port `5432`, which was already allocated. Production services already use Docker DNS at `postgres:5432`, so the host bind is unnecessary.

## Important Files

- `deploy/docker/compose.prod.yaml`
- `deploy/scripts/deploy_prod.sh`
- `deploy/scripts/backup_db.sh`
- `docs/11-devops/OVH_VPS_DEPLOYMENT.md`

## Tests

- `bash -n deploy/scripts/deploy_prod.sh deploy/scripts/deploy_uat.sh deploy/scripts/backup_db.sh`
- `python3 scripts/tracker_to_csv.py --check`
- `git diff --check`
- Rendered prod and UAT Compose configs with fake secrets; prod rendered no `5432` host publish, UAT kept `5433`, and both preserved existing Docker volume names.
- Diff-level token pattern scan found no committed credentials.

## Known Issues / Evidence Gaps

- Did not start local Docker containers or run a live VPS deploy from this environment.

## Review Findings

1. [P1] The branch is stale against `main` and would remove the customer password-reset flow if merged. `git diff main..HEAD` includes unrelated deletions of `apps/web/src/app/(auth)/forgot-password/page.tsx`, `apps/web/src/app/(auth)/reset-password/page.tsx`, their tests, the login "Forgot password?" link, password-reset email delivery in `apps/api/src/growixa_api/notifications/email.py`, and the password-reset background task in `apps/api/src/growixa_api/auth/api.py`. This is outside `GRX-INFRA-005` and would regress a shipped auth feature. Rebase/merge current `main` and keep the infra PR diff limited to the compose/scripts/docs/tracker changes.

2. [P1] The deploy scripts switch from Docker Compose's previous implicit project name to `growixa-prod`/`growixa-uat` and immediately start replacement backing services without stopping or guarding against the legacy `docker` project containers. On the current VPS shape, `deploy/scripts/deploy_prod.sh:35` can start a second Postgres against the same pinned `docker_postgres_data` volume while the old `docker-postgres-1` is still running, and `deploy/scripts/deploy_prod.sh:41` can then collide with the old API/web host ports (`8000`/`3000`). UAT has the same pattern in `deploy/scripts/deploy_uat.sh:35` and `deploy/scripts/deploy_uat.sh:41` for the legacy `docker` project and its pinned `docker_*_uat_data` volumes. Add a safe one-time migration/guard: detect the old project, stop/remove its containers before creating the renamed project (without deleting volumes), or fail with explicit operator steps before any new container can attach to the old data volumes.

## Review Decision
CHANGES_REQUESTED

## Reviewed Code Commit
2b8b10bd6eb02f41a7d32d89ff30fb02ec05518f

## Review Record Commit
<sha>

## Human Approval
Not Required

Status: CHANGES_REQUESTED
