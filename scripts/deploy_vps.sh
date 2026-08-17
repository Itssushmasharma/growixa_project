#!/usr/bin/env bash
set -euo pipefail

# Growixa 1-Click Production VPS Deployment & Migration Script
# Location: /opt/growixa/scripts/deploy_vps.sh

PROJECT_DIR="${PROJECT_DIR:-/opt/growixa}"
COMPOSE_FILE="${PROJECT_DIR}/compose.yaml"

echo "=================================================="
echo " Starting Growixa Production Deployment: $(date -u)"
echo "=================================================="

cd "${PROJECT_DIR}"

echo "Step 1: Pulling latest changes from main branch..."
git fetch origin main
git checkout main
git pull origin main

echo "Step 2: Building updated Docker images..."
docker compose -f "${COMPOSE_FILE}" build --pull

echo "Step 3: Backing up the database before migrating..."
# A migration is the one irreversible step in this script. The nightly cron backup
# can be up to 24h stale, so take a fresh one here -- this is the restore point if
# `alembic upgrade head` corrupts or drops data. `set -e` aborts the deploy if the
# backup fails, which is deliberate: never migrate without a usable restore point.
"${PROJECT_DIR}/scripts/backup_db.sh"

echo "Step 4: Running database migrations (alembic)..."
docker compose -f "${COMPOSE_FILE}" run --rm api alembic upgrade head

echo "Step 5: Restarting application containers with zero/minimal downtime..."
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

echo "Step 6: Verifying system health..."
sleep 5
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅ Health check PASSED: Growixa API is online and healthy."
else
    echo "❌ Health check FAILED: the API did not return 200 after deployment."
    echo "   Inspect with: docker compose -f ${COMPOSE_FILE} logs api"
    echo "   A pre-migration backup was taken in Step 3 -- see the restore procedure"
    echo "   in docs/11-devops/OVH_VPS_DEPLOYMENT.md if you need to roll the database back."
    # Exit non-zero so cron, CI and any wrapper see a failed deploy.
    # Note: Dangling images are preserved on failure to allow rapid rollback.
    exit 1
fi

echo "Step 7: Cleaning up unused dangling Docker images..."
# Prune only after health check confirms new containers are operational,
# preventing premature deletion of rollback images.
docker image prune -f

echo "=================================================="
echo " Growixa Deployment Successfully Completed!"
echo "=================================================="
