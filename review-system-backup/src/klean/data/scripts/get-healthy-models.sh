#!/bin/bash
#
# Get Healthy Models - Returns first N healthy models from LiteLLM
# Uses /chat/completions endpoint for health checks (per LiteLLM/NanoGPT docs)
#
# Usage: get-healthy-models.sh [count]
# Default count: 5
# Exit 1 if no healthy models found
#

COUNT="${1:-5}"
SCRIPTS_DIR="$(dirname "$0")"

# Get all models
MODELS=$("$SCRIPTS_DIR/get-models.sh" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$MODELS" ]; then
    echo "ERROR: Could not get models from LiteLLM" >&2
    exit 1
fi

HEALTHY=()

# Check each model until we have enough healthy ones
while IFS= read -r model; do
    [ -z "$model" ] && continue

    if "$SCRIPTS_DIR/health-check-model.sh" "$model" 2>/dev/null; then
        HEALTHY+=("$model")
        [ ${#HEALTHY[@]} -ge "$COUNT" ] && break
    fi
done <<< "$MODELS"

if [ ${#HEALTHY[@]} -eq 0 ]; then
    echo "ERROR: No healthy models found" >&2
    exit 1
fi

printf '%s\n' "${HEALTHY[@]}"
