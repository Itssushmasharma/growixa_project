#!/usr/bin/env bash
set -e

echo "=== Running Database Migrations ==="
alembic -c /app/apps/api/alembic.ini upgrade head

echo "=== Starting Growixa Worker Process ==="
python -m growixa_worker.main &
WORKER_PID=$!

echo "=== Starting Growixa API (FastAPI) on Port 7860 ==="
uvicorn growixa_api.main:app --host 0.0.0.0 --port 7860 &
API_PID=$!

# Handle graceful shutdown on SIGTERM / SIGINT
trap "echo 'Stopping services...'; kill -TERM $WORKER_PID $API_PID 2>/dev/null || true" SIGTERM SIGINT

# Wait for either process to exit
wait -n $WORKER_PID $API_PID
