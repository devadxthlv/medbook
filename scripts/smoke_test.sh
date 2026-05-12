#!/bin/bash
DOMAIN="3-27-246-227.nip.io"

echo "Testing $DOMAIN..."

# Check HTTPS
STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health/)
if [ "$STATUS" = "200" ]; then
    echo "✅ HTTPS reachable — HTTP $STATUS"
else
    echo "❌ HTTPS NOT reachable — HTTP $STATUS"
    exit 1
fi

# Check HTTP -> HTTPS redirect
REDIRECT=$(curl -s -o /dev/null -w "%{redirect_url}" http://$DOMAIN/)
if [[ "$REDIRECT" == "https://$DOMAIN/"* ]]; then
    echo "✅ HTTP -> HTTPS redirect working"
else
    echo "❌ HTTP -> HTTPS redirect NOT working: $REDIRECT"
    exit 1
fi

