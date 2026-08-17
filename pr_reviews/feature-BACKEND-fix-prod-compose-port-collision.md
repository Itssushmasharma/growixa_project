Task: GRX-INFRA-005 - Fix GHCR Compose production Postgres port collision
Developer: Codex
Reviewer: Codex (fresh session - same tool as developer, no other tool available)
Branch: feature/BACKEND/fix-prod-compose-port-collision
Worktree: /Users/ravi/Projects/growixa
Base Commit: 097363d
Latest Commit: a63084e
Status: READY_FOR_REVIEW

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

1. [RESOLVED] The branch is now scoped to infra/docs/tracker/review files. The earlier stale-branch diff that would have removed the customer password-reset flow is no longer present in `git diff main..HEAD`.

2. [RESOLVED] The deploy scripts now fail fast if legacy Compose project `docker` containers still exist before starting the renamed `growixa-prod` or `growixa-uat` stacks, and the runbook documents container-only removal without deleting volumes. Committed in `a63084e`.

## Developer Response

- Rebased onto current `main` so the branch no longer carries stale password-reset reversions.
- Added legacy Compose project guards to `deploy_prod.sh` and `deploy_uat.sh`.
- Updated OVH runbook, changelog, tracker and project status.
- Re-ran `bash -n deploy/scripts/deploy_prod.sh deploy/scripts/deploy_uat.sh deploy/scripts/backup_db.sh`, `python3 scripts/tracker_to_csv.py --check` and `git diff --check`.

## Review Decision
CHANGES_REQUESTED / APPROVED

## Reviewed Code Commit
<sha>

## Review Record Commit
<sha>

## Human Approval
Not Required

Status: READY_FOR_REVIEW
