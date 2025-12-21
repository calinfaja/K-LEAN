#!/usr/bin/env bash
#
# Health Check Model - Check if a specific model is healthy
# Uses /chat/completions endpoint with a test message (per LiteLLM/NanoGPT docs)
#
# Usage: health-check-model.sh <model-name>
# Exit 0 if healthy, 1 if not
#

MODEL="$1"

if [ -z "$MODEL" ]; then
    echo "Usage: health-check-model.sh <model-name>" >&2
    exit 1
fi

LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"

# Health check via chat completions (the correct way per NanoGPT docs)
RESP=$(curl -s --max-time 5 "$LITELLM_URL/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)

# Check if we got a valid response with choices
echo "$RESP" | jq -e '.choices[0]' > /dev/null 2>&1
