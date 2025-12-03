#!/bin/bash
# LiteLLM Review Helper Script
# Usage: litellm-review.sh <model> <system_prompt_file> <user_prompt>

set -e

LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"
MODEL="${1:-coding-qwen}"
SYSTEM_PROMPT="${2:-}"
USER_PROMPT="${3:-}"

# Model mapping
case "$MODEL" in
  qwen|coding)
    MODEL_ID="coding-qwen"
    ;;
  deepseek|architecture)
    MODEL_ID="architecture-deepseek"
    ;;
  glm|tools|standards)
    MODEL_ID="tools-glm"
    ;;
  *)
    MODEL_ID="$MODEL"
    ;;
esac

# Check if LiteLLM is running
if ! curl -s "$LITELLM_URL/health" > /dev/null 2>&1; then
  echo "ERROR: LiteLLM not responding at $LITELLM_URL"
  echo "Start it with: litellm --config /path/to/config.yaml"
  exit 1
fi

# Build request
if [ -n "$SYSTEM_PROMPT" ] && [ -f "$SYSTEM_PROMPT" ]; then
  SYSTEM_CONTENT=$(cat "$SYSTEM_PROMPT")
else
  SYSTEM_CONTENT="You are an expert code reviewer."
fi

# Make API call
RESPONSE=$(curl -s "$LITELLM_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "model": "$MODEL_ID",
  "messages": [
    {"role": "system", "content": $(echo "$SYSTEM_CONTENT" | jq -Rs .)},
    {"role": "user", "content": $(echo "$USER_PROMPT" | jq -Rs .)}
  ],
  "temperature": 0.3,
  "max_tokens": 3000
}
EOF
)

# Extract and print response
echo "$RESPONSE" | jq -r '.choices[0].message.content // .error.message // "Unknown error"'
