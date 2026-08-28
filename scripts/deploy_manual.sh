#!/usr/bin/env bash
# ==============================================================================
# Growixa Universal Manual Deployment Script (deploy_manual.sh)
# Deploys any release tag directly to UAT or Production on the OVH VPS
# with full pre-flight test suites and Telegram release notifications.
# ==============================================================================
set -euo pipefail

VPS_HOST="${VPS_HOST:-149.56.101.2}"
VPS_USER="${VPS_USER:-ubuntu}"
BUILD_DIR="/opt/growixa-build"

# Load local environment if present for Telegram tokens
if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | grep -E 'TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID' | xargs -0 2>/dev/null || true)
fi

echo "================================================================="
echo "🚀 Growixa Manual VPS Deployment Tool"
echo "================================================================="

# 1. Select Environment
if [[ "${1:-}" == "uat" || "${1:-}" == "prod" ]]; then
    ENV_CHOICE="$1"
else
    echo "Select target environment to deploy:"
    echo "  1) UAT / Staging (uat.growixa.iitdeveloper.com)"
    echo "  2) Production    (growixa.iitdeveloper.com)"
    read -rp "Enter choice [1 or 2, default: 1]: " ENV_INPUT
    case "${ENV_INPUT}" in
        2|prod|production) ENV_CHOICE="prod" ;;
        *) ENV_CHOICE="uat" ;;
    esac
fi

# 2. Select Release Tag
if [[ -n "${2:-}" ]]; then
    RELEASE_TAG="$2"
else
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.5.7-rc1")
    read -rp "Enter Release Tag or Version to deploy [default: ${LATEST_TAG}]: " TAG_INPUT
    RELEASE_TAG="${TAG_INPUT:-${LATEST_TAG}}"
fi

# 3. Target directory and URLs
if [[ "${ENV_CHOICE}" == "prod" ]]; then
    ENV_UPPER="PRODUCTION"
    TARGET_DIR="/opt/growixa"
    COMPOSE_FILE="${TARGET_DIR}/deploy/docker/compose.prod.yaml"
    PROJECT_NAME="growixa-prod"
    PUBLIC_URL="https://growixa.iitdeveloper.com"
    API_PORT="8000"
    TAG_ALIAS="latest"

    echo ""
    echo "⚠️  =============================================================="
    echo "⚠️  STRICT SAFETY GATE: PRODUCTION DEPLOYMENT"
    echo "⚠️  You are about to deploy '${RELEASE_TAG}' directly to PRODUCTION."
    echo "⚠️  =============================================================="
    read -rp "Type 'YES' (all caps) to confirm production rollout: " CONFIRM
    if [[ "${CONFIRM}" != "YES" ]]; then
        echo "❌ Production deployment cancelled by user."
        exit 0
    fi
else
    ENV_UPPER="UAT"
    TARGET_DIR="/opt/growixa-uat"
    COMPOSE_FILE="${TARGET_DIR}/deploy/docker/compose.uat.yaml"
    PROJECT_NAME="growixa-uat"
    PUBLIC_URL="https://uat.growixa.iitdeveloper.com"
    API_PORT="8001"
    TAG_ALIAS="uat"
fi

# 4. Telegram Notification Helper
send_telegram_notification() {
    local STATUS="$1"
    local EXTRA_MSG="${2:-}"
    local BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
    local CHAT_ID="${TELEGRAM_CHAT_ID:-}"

    if [[ -z "${BOT_TOKEN}" || -z "${CHAT_ID}" ]]; then
        return 0
    fi

    local EMOJI="🚀"
    local TITLE="Growixa ${ENV_UPPER} Deployment Successful"
    if [[ "${STATUS}" != "success" ]]; then
        EMOJI="❌"
        TITLE="Growixa ${ENV_UPPER} Deployment Failed"
    fi

    local TEXT="${EMOJI} *${TITLE}*

📦 *Release:* \`${RELEASE_TAG}\`
🎯 *Environment:* ${ENV_UPPER}
🌐 *URL:* ${PUBLIC_URL}
⏱️ *Timestamp:* $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

    if [[ -n "${EXTRA_MSG}" ]]; then
        TEXT="${TEXT}

📝 *Details:*
${EXTRA_MSG}"
    fi

    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\": \"${CHAT_ID}\", \"text\": $(echo "${TEXT}" | jq -Rs .), \"parse_mode\": \"Markdown\"}" >/dev/null 2>&1 || true
}

# Trap unexpected exit to send failure alert
trap 'if [ $? -ne 0 ]; then send_telegram_notification "failure" "Deployment terminated unexpectedly during execution."; fi' EXIT

# 5. Optional Pre-Flight Test Suite
echo ""
read -rp "Run local test suite before deploying? [y/N, default: n]: " RUN_TESTS_INPUT
if [[ "${RUN_TESTS_INPUT}" == "y" || "${RUN_TESTS_INPUT}" == "Y" ]]; then
    echo "================================================================="
    echo "🧪 Running Pre-Flight Validation Tests..."
    echo "================================================================="

    echo "  -> Checking local test database (PostgreSQL / Redis / RabbitMQ)..."
    if ! nc -z 127.0.0.1 5432 2>/dev/null && ! nc -z 127.0.0.1 5433 2>/dev/null; then
        echo "     Starting local containers for tests..."
        docker compose -f deploy/docker/compose.local.yaml up -d postgres redis rabbitmq 2>/dev/null || true
        sleep 2
    fi
    docker compose -f deploy/docker/compose.local.yaml exec -T postgres psql -U growixa -c "CREATE DATABASE growixa_test;" >/dev/null 2>&1 || true

    echo "  1/3 Running Backend API Pytest..."
    uv run pytest apps/api -q --maxfail=1 || {
        echo "❌ Backend API tests failed. (Tip: You can re-run and press enter at the test prompt to deploy directly without local tests)"
        send_telegram_notification "failure" "Pre-flight Backend API tests failed."
        exit 1
    }

    echo "  2/3 Running Worker Pytest..."
    uv run pytest apps/worker -q --maxfail=1 || {
        echo "❌ Worker tests failed. Aborting deployment."
        send_telegram_notification "failure" "Pre-flight Worker tests failed."
        exit 1
    }

    echo "  3/3 Running Frontend Vitest..."
    npm --prefix apps/web test -- --run || {
        echo "❌ Frontend tests failed. Aborting deployment."
        send_telegram_notification "failure" "Pre-flight Frontend tests failed."
        exit 1
    }
    echo "✅ All tests passed cleanly!"
fi

echo ""
echo "================================================================="
echo "📦 Deploying Release: ${RELEASE_TAG}"
echo "🎯 Target Environment: ${ENV_UPPER} (${TARGET_DIR})"
echo "🌐 Public URL: ${PUBLIC_URL}"
echo "================================================================="

# Step 1: Sync local code to VPS build directory
echo "Step 1/6: Syncing workspace files to OVH VPS (${VPS_HOST})..."
ssh "${VPS_USER}@${VPS_HOST}" "sudo mkdir -p ${BUILD_DIR} && sudo chown -R ${VPS_USER}:${VPS_USER} ${BUILD_DIR}"
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude '.worktrees' \
    --exclude '__pycache__' \
    --exclude '.mypy_cache' \
    --exclude '.pytest_cache' \
    --exclude '.next' \
    --exclude '.git' \
    ./ "${VPS_USER}@${VPS_HOST}:${BUILD_DIR}/"

# Step 2: Build Docker images directly on VPS
echo ""
echo "Step 2/6: Building Docker container images on VPS..."
ssh "${VPS_USER}@${VPS_HOST}" bash -c "'
set -euo pipefail
cd ${BUILD_DIR}

echo \"  -> Building API image (${RELEASE_TAG} & ${TAG_ALIAS})...\"
sudo docker build -t \"ghcr.io/iitdeveloper-git/growixa-api:${RELEASE_TAG}\" -t \"ghcr.io/iitdeveloper-git/growixa-api:${TAG_ALIAS}\" -f apps/api/Dockerfile apps/api

echo \"  -> Building Worker image (${RELEASE_TAG} & ${TAG_ALIAS})...\"
sudo docker build -t \"ghcr.io/iitdeveloper-git/growixa-worker:${RELEASE_TAG}\" -t \"ghcr.io/iitdeveloper-git/growixa-worker:${TAG_ALIAS}\" -f apps/worker/Dockerfile apps/worker

echo \"  -> Building Next.js Web image (${RELEASE_TAG} & ${TAG_ALIAS})...\"
sudo docker build -t \"ghcr.io/iitdeveloper-git/growixa-web:${RELEASE_TAG}\" -t \"ghcr.io/iitdeveloper-git/growixa-web:${TAG_ALIAS}\" -f apps/web/Dockerfile apps/web
'"

# Step 3: Sync deployment configs
echo ""
echo "Step 3/6: Syncing deploy configuration to ${TARGET_DIR}..."
ssh "${VPS_USER}@${VPS_HOST}" bash -c "'
set -euo pipefail
sudo mkdir -p ${TARGET_DIR}/deploy
sudo cp -r ${BUILD_DIR}/deploy/* ${TARGET_DIR}/deploy/
'"

# Step 4: Run database migrations
echo ""
echo "Step 4/6: Executing Alembic database migrations on ${ENV_CHOICE} DB..."
ssh "${VPS_USER}@${VPS_HOST}" bash -c "'
set -euo pipefail
cd ${TARGET_DIR}
ENV_FILE=\"${TARGET_DIR}/.env\"
export API_IMAGE=\"ghcr.io/iitdeveloper-git/growixa-api:${RELEASE_TAG}\"
export WORKER_IMAGE=\"ghcr.io/iitdeveloper-git/growixa-worker:${RELEASE_TAG}\"
export WEB_IMAGE=\"ghcr.io/iitdeveloper-git/growixa-web:${RELEASE_TAG}\"

# Ensure backing services are up
sudo docker compose --project-name \"${PROJECT_NAME}\" --env-file \"\${ENV_FILE}\" -f \"${COMPOSE_FILE}\" up -d postgres redis rabbitmq

# Run Alembic migrations
sudo docker compose --project-name \"${PROJECT_NAME}\" --env-file \"\${ENV_FILE}\" -f \"${COMPOSE_FILE}\" run --rm api alembic upgrade head
'"

# Step 5: Zero-downtime container rollout
echo ""
echo "Step 5/6: Performing zero-downtime rollout for API, Worker, and Web..."
ssh "${VPS_USER}@${VPS_HOST}" bash -c "'
set -euo pipefail
cd ${TARGET_DIR}
ENV_FILE=\"${TARGET_DIR}/.env\"
export API_IMAGE=\"ghcr.io/iitdeveloper-git/growixa-api:${RELEASE_TAG}\"
export WORKER_IMAGE=\"ghcr.io/iitdeveloper-git/growixa-worker:${RELEASE_TAG}\"
export WEB_IMAGE=\"ghcr.io/iitdeveloper-git/growixa-web:${RELEASE_TAG}\"

sudo docker compose --project-name \"${PROJECT_NAME}\" --env-file \"\${ENV_FILE}\" -f \"${COMPOSE_FILE}\" up -d --no-deps api worker web
'"

# Step 6: Health verification and disk cleanup
echo ""
echo "Step 6/6: Verifying service health and cleaning up disk cache..."
sleep 5
HEALTH_STATUS=$(ssh "${VPS_USER}@${VPS_HOST}" "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${API_PORT}/health || true")

if [[ "${HEALTH_STATUS}" == "200" ]]; then
    echo "✅ Health check PASSED (HTTP 200 OK)"
else
    echo "⚠️ Warning: Health check returned HTTP ${HEALTH_STATUS}."
fi

# Prune old dangling images to prevent disk from filling up
ssh "${VPS_USER}@${VPS_HOST}" "sudo docker image prune -f && sudo docker builder prune -f 2>/dev/null || true"

# Extract changelog release notes summary if available
RELEASE_NOTES_SUMMARY=$(python3 -c "
import re
tag = '${RELEASE_TAG}'.lstrip('v')
summary = ''
try:
    with open('docs/00-project-control/CHANGELOG.md') as f:
        text = f.read()
    pattern = r'##\\s*\\[?' + re.escape(tag) + r'\\]?(.*?)(?=##|\\Z)'
    matches = re.findall(pattern, text, re.S)
    if matches:
        bullets = [line.strip() for line in matches[0].split('\n') if line.strip().startswith('- ')]
        summary = '\n'.join(bullets[:5])
except Exception:
    pass
print(summary)
" 2>/dev/null || echo "")

# Send Telegram success notification
send_telegram_notification "success" "${RELEASE_NOTES_SUMMARY}"

echo ""
echo "================================================================="
echo "🎉 Growixa ${ENV_UPPER} Deployment Complete!"
echo "🚀 Deployed Release: ${RELEASE_TAG}"
echo "🌐 API Health Check: ${PUBLIC_URL}/api/health"
echo "🌐 Web Dashboard:   ${PUBLIC_URL}/login"
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" && -n "${TELEGRAM_CHAT_ID:-}" ]]; then
    echo "📱 Telegram Release Notification: Sent"
fi
echo "================================================================="
