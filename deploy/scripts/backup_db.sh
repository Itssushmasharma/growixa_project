#!/usr/bin/env bash
# ==============================================================================
# Growixa Production & UAT PostgreSQL Automated Backup Script
# Retention: 14 days daily backups with gzip compression
# ==============================================================================
set -euo pipefail

BACKUP_DIR="/opt/growixa/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=14
PROD_COMPOSE_FILE="/opt/growixa/deploy/docker/compose.prod.yaml"
PROD_ENV_FILE="/opt/growixa/.env"
UAT_COMPOSE_FILE="/opt/growixa-uat/deploy/docker/compose.uat.yaml"
UAT_ENV_FILE="/opt/growixa-uat/.env"

mkdir -p "${BACKUP_DIR}"

echo "=== [$(date)] Starting PostgreSQL Backup ==="

# 1. Backup Production Database
if sudo docker compose --project-name growixa-prod --env-file "${PROD_ENV_FILE}" -f "${PROD_COMPOSE_FILE}" ps --services | grep -q postgres; then
    PROD_BACKUP_FILE="${BACKUP_DIR}/growixa_prod_${TIMESTAMP}.sql.gz"
    echo "Dumping Production database -> ${PROD_BACKUP_FILE}"
    sudo docker compose --project-name growixa-prod --env-file "${PROD_ENV_FILE}" -f "${PROD_COMPOSE_FILE}" exec -T postgres pg_dump -U growixa growixa | gzip > "${PROD_BACKUP_FILE}"
    echo "Production backup completed: $(ls -lh "${PROD_BACKUP_FILE}" | awk '{print $5}')"
fi

# 2. Backup UAT Database (if active)
if [[ -d "/opt/growixa-uat" && -f "${UAT_ENV_FILE}" ]] && sudo docker compose --project-name growixa-uat --env-file "${UAT_ENV_FILE}" -f "${UAT_COMPOSE_FILE}" ps --services | grep -q postgres; then
    UAT_BACKUP_FILE="${BACKUP_DIR}/growixa_uat_${TIMESTAMP}.sql.gz"
    echo "Dumping UAT database -> ${UAT_BACKUP_FILE}"
    sudo docker compose --project-name growixa-uat --env-file "${UAT_ENV_FILE}" -f "${UAT_COMPOSE_FILE}" exec -T postgres pg_dump -U growixa growixa_uat | gzip > "${UAT_BACKUP_FILE}"
    echo "UAT backup completed: $(ls -lh "${UAT_BACKUP_FILE}" | awk '{print $5}')"
fi

# 3. Retention Pruning (remove backups older than 14 days)
echo "Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +${RETENTION_DAYS} -exec rm -f {} \;

echo "=== [$(date)] Backup and Pruning Finished Successfully ==="
