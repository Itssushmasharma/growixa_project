#!/usr/bin/env bash
# ==============================================================================
# Growixa UAT / Staging Rollout Script (deploy_uat.sh)
# Usage: ./deploy_uat.sh [IMAGE_TAG]
# Example: ./deploy_uat.sh v1.0.0-rc1
# ==============================================================================
set -euo pipefail

RELEASE_TAG="${1:-uat}"
UAT_DIR="/opt/growixa-uat"
COMPOSE_FILE="${UAT_DIR}/deploy/docker/compose.uat.yaml"

echo "================================================================="
echo "🧪 Deploying Growixa UAT / Staging (${RELEASE_TAG}) to OVH VPS"
echo "================================================================="

cd "${UAT_DIR}"

if [[ ! -f ".env" ]]; then
    echo "❌ Error: UAT .env file not found at ${UAT_DIR}/.env"
    exit 1
fi

ENV_FILE="${UAT_DIR}/.env"

export API_IMAGE="ghcr.io/iitdeveloper-git/growixa-api:${RELEASE_TAG}"
export WORKER_IMAGE="ghcr.io/iitdeveloper-git/growixa-worker:${RELEASE_TAG}"
export WEB_IMAGE="ghcr.io/iitdeveloper-git/growixa-web:${RELEASE_TAG}"

echo "📦 Pulling release candidate images from GitHub Container Registry..."
sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull api worker web

echo "🗄️ Executing PostgreSQL database migrations on UAT DB..."
sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" run --rm api alembic upgrade head

echo "🔄 Performing container rollout on UAT stack..."
sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --no-deps api worker web

echo "⏳ Waiting for services to initialize..."
sleep 5

echo "🩺 Probing UAT health status..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://uat.growixa.iitdeveloper.com/api/health || true)
if [[ "${HEALTH_STATUS}" == "200" ]]; then
    echo "✅ UAT Health Check PASSED (HTTP 200 OK)"
else
    echo "ℹ️ UAT Health Check returned HTTP ${HEALTH_STATUS} (Ensure uat.growixa DNS record is configured)."
fi

sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps
echo "================================================================="
echo "🎉 Growixa UAT Deployment (${RELEASE_TAG}) Complete!"
echo "================================================================="
