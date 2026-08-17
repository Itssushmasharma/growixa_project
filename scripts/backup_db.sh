#!/usr/bin/env bash
set -euo pipefail

# Growixa Automated PostgreSQL Backup Script
# Location: /opt/growixa/scripts/backup_db.sh

BACKUP_DIR="${BACKUP_DIR:-/opt/growixa/backups}"
COMPOSE_FILE="${COMPOSE_FILE:-/opt/growixa/compose.yaml}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="${BACKUP_DIR}/growixa_pg_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting Growixa PostgreSQL Backup..."

# Extract database credentials or fallback to defaults
docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_dump -U growixa growixa | gzip > "${FILENAME}"

# Verify backup size
FILESIZE=$(stat -c%s "${FILENAME}" 2>/dev/null || stat -f%z "${FILENAME}" 2>/dev/null || echo 0)
if [ "${FILESIZE}" -lt 100 ]; then
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] ERROR: Backup file is empty or too small (${FILESIZE} bytes)!"
    exit 1
fi

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup completed successfully: ${FILENAME} (${FILESIZE} bytes)"

# Enforce retention policy (delete backups older than RETENTION_DAYS)
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "growixa_pg_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup routine finished."
