#!/bin/bash
DOMAIN="3-27-246-227.nip.io"

echo "Testing $DOMAIN..."

# Check HTTPS with retries
MAX_RETRIES=5
RETRY_COUNT=0
SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    STATUS=$(curl -s -k -o /dev/null -w "%{http_code}" https://$DOMAIN/health/)
    if [ "$STATUS" = "200" ]; then
        echo "✅ HTTPS reachable — HTTP $STATUS"
        SUCCESS=true
        break
    else
        echo "⚠️ Attempt $((RETRY_COUNT+1)) failed: HTTP $STATUS. Retrying in 5s..."
        sleep 5
        RETRY_COUNT=$((RETRY_COUNT+1))
    fi
done

if [ "$SUCCESS" = false ]; then
    echo "❌ HTTPS NOT reachable after $MAX_RETRIES attempts."
    exit 1
fi

# Check HTTP -> HTTPS redirect
REDIRECT=$(curl -s -k -o /dev/null -w "%{redirect_url}" http://$DOMAIN/)
if [[ "$REDIRECT" == "https://$DOMAIN/"* ]]; then
    echo "✅ HTTP -> HTTPS redirect working"
else
    echo "❌ HTTP -> HTTPS redirect NOT working: $REDIRECT"
    exit 1
fi

