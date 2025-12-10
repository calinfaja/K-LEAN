#!/bin/bash
#
# Validate Model - Check if model name exists in LiteLLM
#
# Usage: validate-model.sh <model-name>
# Exit 0 if valid, 1 if invalid (prints available models)
#

MODEL="$1"
SCRIPTS_DIR="$(dirname "$0")"

if [ -z "$MODEL" ]; then
    echo "ERROR: No model specified" >&2
    echo "Available models:" >&2
    "$SCRIPTS_DIR/get-models.sh" >&2
    exit 1
fi

AVAILABLE=$("$SCRIPTS_DIR/get-models.sh" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "ERROR: Could not get models from LiteLLM" >&2
    exit 1
fi

if echo "$AVAILABLE" | grep -qx "$MODEL"; then
    exit 0
else
    echo "ERROR: Invalid model '$MODEL'" >&2
    echo "Available models:" >&2
    echo "$AVAILABLE" >&2
    exit 1
fi
