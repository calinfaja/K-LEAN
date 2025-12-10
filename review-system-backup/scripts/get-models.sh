#!/bin/bash
#
# Get Models - Returns all models from LiteLLM API (sorted)
# Usage: get-models.sh
# Exit 1 if LiteLLM not running
#

LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"

RESPONSE=$(curl -s --max-time 5 "$LITELLM_URL/v1/models" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$RESPONSE" ]; then
    echo "ERROR: LiteLLM not running at $LITELLM_URL" >&2
    exit 1
fi

# Check if response is valid JSON with data
if ! echo "$RESPONSE" | jq -e '.data' > /dev/null 2>&1; then
    echo "ERROR: Invalid response from LiteLLM" >&2
    exit 1
fi

# Extract and sort model IDs
MODELS=$(echo "$RESPONSE" | jq -r '.data[].id' | sort)

if [ -z "$MODELS" ]; then
    echo "ERROR: No models found in LiteLLM" >&2
    exit 1
fi

echo "$MODELS"
