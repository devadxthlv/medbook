#!/bin/bash
IP="3.27.246.227"

echo "Testing $IP..."

STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$IP/)
if [ "$STATUS" = "200" ] || [ "$STATUS" = "301" ] || [ "$STATUS" = "302" ]; then
    echo "✅ Site reachable — HTTP $STATUS"
else
    echo "❌ Site NOT reachable — HTTP $STATUS"
    echo "Container status:"
    docker ps
    echo "Recent logs:"
    docker compose -f docker-compose.prod.yml logs --tail=30
    exit 1
fi
