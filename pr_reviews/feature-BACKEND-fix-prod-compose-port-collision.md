Task: GRX-INFRA-005 - Fix GHCR Compose production Postgres port collision
Developer: Codex
Reviewer:
Branch: feature/BACKEND/fix-prod-compose-port-collision
Worktree: /Users/ravi/Projects/growixa
Base Commit: 097363d
Latest Commit: 1f1a48e
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


## Review Decision
CHANGES_REQUESTED / APPROVED

## Reviewed Code Commit
<sha>

## Review Record Commit
<sha>

## Human Approval
Not Required

Status:
