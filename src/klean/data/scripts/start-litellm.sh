#!/usr/bin/env bash
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

echo "K-LEAN LiteLLM Proxy"
echo "===================="

# Check config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: Config not found: $CONFIG_FILE${NC}"
    echo "   Run: kln install"
    exit 1
fi

# Check for quoted os.environ (common mistake that breaks auth)
# Ignore commented lines (starting with #)
if grep -v '^\s*#' "$CONFIG_FILE" | grep -q '"os.environ/' || grep -v '^\s*#' "$CONFIG_FILE" | grep -q "'os.environ/"; then
    echo -e "${RED}ERROR: Config has quoted os.environ/ - this breaks authentication!${NC}"
    echo "   Fix: Remove quotes around os.environ/... values"
    echo "   Quick fix: sed -i 's/\"os.environ\\/\\([^\"]*\\)\"/os.environ\\/\\1/g' $CONFIG_FILE"
    exit 1
fi

# Load environment variables from .env
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo -e "${YELLOW}WARNING: No .env file found${NC}"
    echo "   Create one from .env.example:"
    echo "   cp $CONFIG_DIR/.env.example $CONFIG_DIR/.env"
    exit 1
fi

# Validate API key is configured
if [ -z "$NANOGPT_API_KEY" ] || [ "$NANOGPT_API_KEY" = "your-nanogpt-api-key-here" ]; then
    echo -e "${RED}ERROR: NANOGPT_API_KEY not configured${NC}"
    echo "   Edit $ENV_FILE and add your NanoGPT API key"
    echo "   Get one at: https://nano-gpt.com"
    exit 1
fi

# Validate API base is configured
if [ -z "$NANOGPT_API_BASE" ]; then
    echo -e "${YELLOW}WARNING: NANOGPT_API_BASE not set - auto-detecting...${NC}"

    # Check subscription status
    SUBSCRIPTION_CHECK=$(curl -s --max-time 5 "https://nano-gpt.com/api/subscription/v1/usage" \
        -H "Authorization: Bearer $NANOGPT_API_KEY" 2>/dev/null)

    if echo "$SUBSCRIPTION_CHECK" | grep -q '"active":true'; then
        export NANOGPT_API_BASE="https://nano-gpt.com/api/subscription/v1"
        echo -e "${GREEN}   Subscription account detected${NC}"
    else
        export NANOGPT_API_BASE="https://nano-gpt.com/api/v1"
        echo -e "${YELLOW}   Pay-per-use account detected${NC}"
    fi

    # Save to .env for future runs
    echo "NANOGPT_API_BASE=$NANOGPT_API_BASE" >> "$ENV_FILE"
    echo -e "${GREEN}   Saved to $ENV_FILE${NC}"
fi

# Check if port is already in use
if lsof -i :$PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: Port $PORT is already in use${NC}"

    # Check if it's LiteLLM already running
    if curl -s --max-time 2 "http://localhost:$PORT/models" > /dev/null 2>&1; then
        echo -e "${GREEN}   LiteLLM is already running${NC}"
        exit 0
    fi

    echo "   Another process is using port $PORT:"
    lsof -i :$PORT | head -3
    echo ""
    echo "   Free the port: fuser -k $PORT/tcp"
    exit 1
fi

echo "Starting on port $PORT..."
echo "   Config: $CONFIG_FILE"
echo ""

# Add callbacks to Python path for thinking models support
# This allows LiteLLM to load callbacks.thinking_transform
export PYTHONPATH="$CONFIG_DIR:${PYTHONPATH:-}"

# Find litellm binary - check pipx venv first, then system PATH
LITELLM_BIN=""
if [ -f "$HOME/.local/share/pipx/venvs/kln-ai/bin/litellm" ]; then
    LITELLM_BIN="$HOME/.local/share/pipx/venvs/kln-ai/bin/litellm"
elif command -v litellm &> /dev/null; then
    LITELLM_BIN="litellm"
else
    echo -e "${RED}ERROR: litellm not found${NC}"
    echo "   Expected in: ~/.local/share/pipx/venvs/kln-ai/bin/litellm"
    exit 1
fi

# Start LiteLLM
exec "$LITELLM_BIN" --config "$CONFIG_FILE" --port "$PORT"
