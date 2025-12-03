#!/bin/bash
#
# Test Headless Claude - Test any model via LiteLLM/NanoGPT
#
# Usage: test-headless.sh <model> "<prompt>"
#
# Models: coding-qwen, architecture-deepseek, tools-glm,
#         research-minimax, agent-kimi, scripting-hermes
#
# Examples:
#   test-headless.sh coding-qwen "List files in current directory"
#   test-headless.sh agent-kimi "What is 2+2?"
#

MODEL="${1:-coding-qwen}"
PROMPT="${2:-Say hello and confirm which model you are}"

echo "═══════════════════════════════════════════════════════════════"
echo "  HEADLESS CLAUDE TEST"
echo "═══════════════════════════════════════════════════════════════"
echo "Model: $MODEL"
echo "Prompt: $PROMPT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Check if LiteLLM proxy is running
echo "[1/4] Checking LiteLLM proxy..."
# Use /models endpoint instead of /health (more reliable)
if ! curl -s --max-time 5 http://localhost:4000/models > /dev/null 2>&1; then
    echo "⚠️  LiteLLM proxy not running, attempting to start..."

    # Try to start proxy in background
    nohup litellm --config ~/.config/litellm/nanogpt.yaml --port 4000 > /tmp/litellm-test.log 2>&1 &
    PROXY_PID=$!

    # Wait for it to start
    for i in {1..10}; do
        sleep 1
        if curl -s --max-time 3 http://localhost:4000/models > /dev/null 2>&1; then
            echo "✅ LiteLLM proxy started (PID: $PROXY_PID)"
            break
        fi
        echo "   Waiting... ($i/10)"
    done

    if ! curl -s --max-time 3 http://localhost:4000/models > /dev/null 2>&1; then
        echo "❌ Failed to start LiteLLM proxy"
        echo "Check logs: /tmp/litellm-test.log"
        exit 1
    fi
else
    echo "✅ LiteLLM proxy is running"
fi

# Step 2: Check model health
echo ""
echo "[2/4] Checking model health..."
HEALTH_RESP=$(curl -s --max-time 10 http://localhost:4000/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)

if ! echo "$HEALTH_RESP" | jq -e '.choices[0]' > /dev/null 2>&1; then
    echo "❌ Model '$MODEL' is not healthy"
    echo "Response: $HEALTH_RESP"
    echo ""
    echo "Available models: coding-qwen, architecture-deepseek, tools-glm,"
    echo "                  research-minimax, agent-kimi, scripting-hermes"
    exit 1
fi
echo "✅ Model '$MODEL' is healthy"

# Step 3: Switch to NanoGPT settings
echo ""
echo "[3/4] Switching to NanoGPT configuration..."
SETTINGS_FILE="$HOME/.claude/settings.json"
BACKUP_FILE="$HOME/.claude/settings-test-backup.json"
NANO_SETTINGS="$HOME/.claude/settings-nanogpt.json"

if [ ! -f "$NANO_SETTINGS" ]; then
    echo "❌ NanoGPT settings not found at $NANO_SETTINGS"
    exit 1
fi

# Backup current settings
cp "$SETTINGS_FILE" "$BACKUP_FILE"

# Switch to nano settings
cp "$NANO_SETTINGS" "$SETTINGS_FILE"
echo "✅ Switched to NanoGPT settings (backup saved)"

# Step 4: Run headless Claude
echo ""
echo "[4/4] Running headless Claude with model '$MODEL'..."
echo "─────────────────────────────────────────────────────────────────"
echo ""

START_TIME=$(date +%s.%N)

# Run Claude with explicit model
claude --model "$MODEL" --print -p "$PROMPT" 2>&1

EXIT_CODE=$?
END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc)

echo ""
echo "─────────────────────────────────────────────────────────────────"

# Restore original settings
cp "$BACKUP_FILE" "$SETTINGS_FILE"
rm -f "$BACKUP_FILE"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  RESULT"
echo "═══════════════════════════════════════════════════════════════"
echo "Exit code: $EXIT_CODE"
printf "Duration: %.2f seconds\n" "$DURATION"
echo "Settings: Restored to original"
echo "═══════════════════════════════════════════════════════════════"
