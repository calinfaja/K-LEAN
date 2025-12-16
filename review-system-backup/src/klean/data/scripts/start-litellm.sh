#!/bin/bash
#
# K-LEAN LiteLLM Proxy Starter
# ============================
# Single canonical script for starting LiteLLM proxy
#
# Usage: start-litellm.sh [port]
#

set -e

PORT="${1:-4000}"
CONFIG_DIR="$HOME/.config/litellm"
ENV_FILE="$CONFIG_DIR/.env"
CONFIG_FILE="$CONFIG_DIR/config.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 K-LEAN LiteLLM Proxy"
echo "========================"

# Check config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Config not found: $CONFIG_FILE${NC}"
    echo "   Run: k-lean install"
    exit 1
fi

# Load environment variables from .env
if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading environment from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "   Create one from .env.example:"
    echo "   cp $CONFIG_DIR/.env.example $CONFIG_DIR/.env"
    exit 1
fi

# Validate API key is configured
if [ -z "$NANOGPT_API_KEY" ] || [ "$NANOGPT_API_KEY" = "your-nanogpt-api-key-here" ]; then
    echo -e "${RED}❌ NANOGPT_API_KEY not configured${NC}"
    echo "   Edit $ENV_FILE and add your NanoGPT API key"
    echo "   Get one at: https://nano-gpt.com"
    exit 1
fi

# Check if port is already in use
if lsof -i :$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"

    # Check if it's LiteLLM already running
    if curl -s --max-time 2 "http://localhost:$PORT/models" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✓ LiteLLM is already running${NC}"
        exit 0
    fi

    echo "   Another process is using port $PORT:"
    lsof -i :$PORT | head -3
    echo ""
    echo "   Free the port: fuser -k $PORT/tcp"
    exit 1
fi

echo "📡 Starting on port $PORT..."
echo "   Config: $CONFIG_FILE"
echo ""

# Start LiteLLM
exec litellm --config "$CONFIG_FILE" --port "$PORT"
