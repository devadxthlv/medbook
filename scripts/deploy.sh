#!/bin/bash
set -e

APP_DIR="/home/ubuntu/medbook"

echo "=== MedBook Deploy: $(date) ==="
cd "$APP_DIR"

echo ">>> Pulling latest code..."
git fetch --all
git reset --hard origin/main

echo ">>> Rebuilding Docker image..."
docker compose -f docker-compose.prod.yml build web

echo ">>> Restarting services..."
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec -T nginx nginx -s reload || true

echo ">>> Waiting for services to be healthy..."
# Wait up to 120 seconds for the web container to be healthy
WEB_CONTAINER=$(docker compose -f docker-compose.prod.yml ps -q web)
for i in {1..24}; do
    if docker inspect --format='{{json .State.Health.Status}}' "$WEB_CONTAINER" | grep -q '"healthy"'; then
        echo "✅ Web container is healthy."
        break
    fi
    echo "Waiting for web container health... ($((i*5))s)"
    sleep 5
    if [ $i -eq 24 ]; then
        echo "❌ Timeout waiting for web container health."
        docker compose -f docker-compose.prod.yml logs web
        exit 1
    fi
done

echo ">>> Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

echo ">>> Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo ">>> Cleaning old images..."
docker image prune -f

echo ">>> Running smoke test..."
bash scripts/smoke_test.sh

echo "=== Deploy complete ==="
