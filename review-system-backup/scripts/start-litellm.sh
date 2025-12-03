#!/bin/bash
#
# Start LiteLLM Proxy - Ensures port 4000 is available
#
# Usage: start-litellm.sh
#

PORT=4000
CONFIG="$HOME/.config/litellm/nanogpt.yaml"

echo "Starting LiteLLM proxy on port $PORT..."

# Check if port is already in use
if lsof -i :$PORT > /dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use"

    # Check if it's LiteLLM
    if lsof -i :$PORT | grep -q "litellm\|python"; then
        echo "   Looks like LiteLLM is already running"
        read -p "   Kill existing process? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            fuser -k $PORT/tcp 2>/dev/null
            sleep 2
        else
            echo "   Use the existing instance or kill it manually:"
            echo "   fuser -k $PORT/tcp"
            exit 1
        fi
    else
        echo "   Another process is using port $PORT:"
        lsof -i :$PORT | head -3
        echo ""
        echo "   Free the port first: fuser -k $PORT/tcp"
        exit 1
    fi
fi

# Start LiteLLM
echo "Starting LiteLLM..."
litellm --config "$CONFIG" --port $PORT

