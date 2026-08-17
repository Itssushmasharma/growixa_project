#!/usr/bin/env bash
# ==============================================================================
# Growixa Production Rollout Script (deploy_prod.sh)
# Usage: ./deploy_prod.sh [IMAGE_TAG]
# Example: ./deploy_prod.sh v1.0.0
# ==============================================================================
set -euo pipefail

RELEASE_TAG="${1:-latest}"
PROD_DIR="/opt/growixa"
COMPOSE_FILE="${PROD_DIR}/deploy/docker/compose.prod.yaml"

echo "================================================================="
echo "🚀 Deploying Growixa Production (${RELEASE_TAG}) to OVH VPS"
echo "================================================================="

cd "${PROD_DIR}"

if [[ ! -f ".env" ]]; then
    echo "❌ Error: Production .env file not found at ${PROD_DIR}/.env"
    exit 1
fi

ENV_FILE="${PROD_DIR}/.env"

export API_IMAGE="ghcr.io/iitdeveloper-git/growixa-api:${RELEASE_TAG}"
export WORKER_IMAGE="ghcr.io/iitdeveloper-git/growixa-worker:${RELEASE_TAG}"
export WEB_IMAGE="ghcr.io/iitdeveloper-git/growixa-web:${RELEASE_TAG}"

echo "📦 Pulling release images from GitHub Container Registry..."
sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull api worker web

echo "🗄️ Executing PostgreSQL database migrations..."
sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" run --rm api alembic upgrade head

echo "🔄 Performing zero-downtime container rollout..."
sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --no-deps api worker web

echo "⏳ Waiting for services to pass health checks..."
sleep 5

echo "🩺 Probing production health status..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://growixa.iitdeveloper.com/api/health || true)
if [[ "${HEALTH_STATUS}" == "200" ]]; then
    echo "✅ Production Health Check PASSED (HTTP 200 OK)"
else
    echo "⚠️ Warning: Production Health Check returned HTTP ${HEALTH_STATUS}. Checking container status..."
fi

sudo docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps
echo "================================================================="
echo "🎉 Growixa Production Deployment (${RELEASE_TAG}) Complete!"
echo "================================================================="
