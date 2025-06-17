#!/bin/bash
# Health check script for n8n-interface-team

HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
TIMEOUT="${TIMEOUT:-5}"

# Perform health check
response=$(curl -s -w "\n%{http_code}" --connect-timeout $TIMEOUT "$HEALTH_URL")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    echo "✓ Health check passed"
    echo "Response: $body"
    exit 0
else
    echo "✗ Health check failed"
    echo "HTTP Code: $http_code"
    echo "Response: $body"
    exit 1
fi
