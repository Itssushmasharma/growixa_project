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
COMPOSE_PROJECT_NAME="growixa-prod"
LEGACY_COMPOSE_PROJECT_NAME="docker"

guard_legacy_compose_project() {
    local legacy_containers
    legacy_containers=$(sudo docker ps -a \
        --filter "label=com.docker.compose.project=${LEGACY_COMPOSE_PROJECT_NAME}" \
        --format "{{.Names}}" | sort || true)

    if [[ -z "${legacy_containers}" ]]; then
        return
    fi

    cat <<EOF
❌ Legacy Docker Compose project '${LEGACY_COMPOSE_PROJECT_NAME}' still has containers:
${legacy_containers}

This deploy now uses the stable project name '${COMPOSE_PROJECT_NAME}'. Starting it while
legacy '${LEGACY_COMPOSE_PROJECT_NAME}' containers exist can attach two Postgres containers
to the same preserved volume or collide on API/web ports.

Inspect before retrying:
  sudo docker ps -a --filter label=com.docker.compose.project=${LEGACY_COMPOSE_PROJECT_NAME}
  sudo ss -ltnp 'sport = :5432'

After confirming the legacy containers are the old production stack and not serving live
traffic, stop and remove only the containers, not volumes:
  cd ${PROD_DIR}
  sudo docker compose --project-name ${LEGACY_COMPOSE_PROJECT_NAME} --env-file ${ENV_FILE} -f ${COMPOSE_FILE} stop
  sudo docker compose --project-name ${LEGACY_COMPOSE_PROJECT_NAME} --env-file ${ENV_FILE} -f ${COMPOSE_FILE} rm -f

Then rerun this deployment.
EOF
    exit 1
}

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

guard_legacy_compose_project

echo "📦 Pulling release images from GitHub Container Registry..."
sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" pull api worker web

echo "🧱 Ensuring production backing services are running..."
sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d postgres redis rabbitmq

echo "🗄️ Executing PostgreSQL database migrations..."
sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" run --rm api alembic upgrade head

echo "🔄 Performing zero-downtime container rollout..."
sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up -d --no-deps api worker web

echo "⏳ Waiting for services to pass health checks..."
sleep 5

echo "🩺 Probing production health status..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://growixa.iitdeveloper.com/api/health || true)
if [[ "${HEALTH_STATUS}" == "200" ]]; then
    echo "✅ Production Health Check PASSED (HTTP 200 OK)"
else
    echo "⚠️ Warning: Production Health Check returned HTTP ${HEALTH_STATUS}. Checking container status..."
fi

sudo docker compose --project-name "${COMPOSE_PROJECT_NAME}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" ps

echo "🧹 Pruning old dangling images and container build cache..."
sudo docker image prune -f
sudo docker builder prune -f 2>/dev/null || true

echo "================================================================="
echo "🎉 Growixa Production Deployment (${RELEASE_TAG}) Complete!"
echo "================================================================="
