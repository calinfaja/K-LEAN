#!/bin/bash
# K-LEAN LiteLLM Proxy Starter
# ============================
# Loads environment variables and starts the LiteLLM proxy

set -e

LITELLM_CONFIG_DIR="${HOME}/.config/litellm"
ENV_FILE="${LITELLM_CONFIG_DIR}/.env"
CONFIG_FILE="${LITELLM_CONFIG_DIR}/config.yaml"

# Check config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ LiteLLM config not found: $CONFIG_FILE"
    echo "   Run the K-LEAN installer first"
    exit 1
fi

# Load environment variables
if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading environment from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "⚠️  No .env file found at $ENV_FILE"
    echo "   Copy .env.example to .env and add your API keys"
    exit 1
fi

# Validate required vars
if [ -z "$NANOGPT_API_KEY" ] || [ "$NANOGPT_API_KEY" = "your-nanogpt-api-key-here" ]; then
    echo "❌ NANOGPT_API_KEY not configured"
    echo "   Edit $ENV_FILE and add your NanoGPT API key"
    exit 1
fi

# Parse arguments
PORT="${1:-4000}"
shift 2>/dev/null || true  # Remove port from $@

echo "🚀 Starting LiteLLM proxy on port $PORT"
echo "   Config: $CONFIG_FILE"
echo ""

# Start LiteLLM
exec litellm --config "$CONFIG_FILE" --port "$PORT" "$@"
