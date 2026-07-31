#!/bin/bash
# Health check for Quiz App
# If the backend is unhealthy, kill the uvicorn process so systemd restarts it

HEALTH_URL="http://localhost:9200/api/health"
MAX_FAILURES=3
FAIL_FILE="/tmp/quiz-app-health-failures"

response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null)

if [ "$response" != "200" ]; then
    failures=$(cat "$FAIL_FILE" 2>/dev/null || echo 0)
    failures=$((failures + 1))
    echo "$failures" > "$FAIL_FILE"

    if [ "$failures" -ge "$MAX_FAILURES" ]; then
        logger -t quiz-app-health "[FATAL] $MAX_FAILURES consecutive health check failures. Killing uvicorn to trigger restart."
        pkill -f "uvicorn backend.main:app"
        rm -f "$FAIL_FILE"
    else
        logger -t quiz-app-health "[WARN] Health check failed ($failures/$MAX_FAILURES). HTTP $response"
    fi
else
    # Reset counter on success
    rm -f "$FAIL_FILE"
fi
