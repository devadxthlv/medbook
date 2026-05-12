#!/bin/bash
set -e

APP_DIR="/home/ubuntu/medbook"

echo "=== MedBook Deploy: $(date) ==="
cd "$APP_DIR"

echo ">>> Pulling latest code..."
git pull origin main

echo ">>> Rebuilding Docker image..."
docker compose -f docker-compose.prod.yml build web

echo ">>> Restarting services..."
docker compose -f docker-compose.prod.yml up -d

echo ">>> Cleaning old images..."
docker image prune -f

echo ">>> Running smoke test..."
bash scripts/smoke_test.sh

echo "=== Deploy complete ==="
