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

echo "Step 3: Running database migrations (alembic)..."
docker compose -f "${COMPOSE_FILE}" run --rm api alembic upgrade head

echo "Step 4: Restarting application containers with zero/minimal downtime..."
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans

echo "Step 5: Cleaning up unused dangling Docker images..."
docker image prune -f

echo "Step 6: Verifying system health..."
sleep 5
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅ Health check PASSED: Growixa API is online and healthy."
else
    echo "⚠️ Warning: Health check returned non-200. Check 'docker compose logs api'."
fi

echo "=================================================="
echo " Growixa Deployment Successfully Completed!"
echo "=================================================="
