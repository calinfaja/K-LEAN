#!/usr/bin/env bash
#
# Test Headless Claude - Test any model via LiteLLM/NanoGPT
# READ-ONLY AUDIT MODE: Full read/search/research access, NO write/edit/delete
# Uses --dangerously-skip-permissions with restricted allowedTools for safe automation
#
# Usage: test-headless.sh <model> "<prompt>" [--unsafe]
#
# Models: qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking,
#         minimax-m2, kimi-k2-thinking, hermes-4-70b
#
# Options:
#   --unsafe    Disable audit mode (allow write operations - NOT RECOMMENDED)
#
# Examples:
#   test-headless.sh qwen3-coder "List files in current directory"
#   test-headless.sh kimi-k2-thinking "What is 2+2?"
#
# Security: Runs in audit mode by default with:
#   - ALLOWED: Read, Grep, Glob, WebSearch, WebFetch, git read ops
#   - DENIED: Write, Edit, rm, mv, git commit/push, any destructive operations
#

MODEL="${1:-qwen3-coder}"
PROMPT="${2:-Say hello and confirm which model you are}"
AUDIT_MODE=true

# Parse --unsafe flag
if [[ "$3" == "--unsafe" ]] || [[ "$2" == "--unsafe" ]]; then
    AUDIT_MODE=false
    if [[ "$2" == "--unsafe" ]]; then
        PROMPT="Say hello and confirm which model you are"
    fi
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  HEADLESS CLAUDE TEST"
echo "═══════════════════════════════════════════════════════════════"
echo "Model: $MODEL"
echo "Prompt: $PROMPT"
echo "Audit Mode: $AUDIT_MODE (read-only)"
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
    echo "Available models: qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking,"
    echo "                  minimax-m2, kimi-k2-thinking, hermes-4-70b"
    exit 1
fi
echo "✅ Model '$MODEL' is healthy"

# Step 3: Create isolated audit config
echo ""
echo "[3/4] Creating isolated config..."
AUDIT_CONFIG_DIR="/tmp/claude-test-$$"
mkdir -p "$AUDIT_CONFIG_DIR"

# Build settings with or without audit mode
if [ "$AUDIT_MODE" = true ]; then
    cat > "$AUDIT_CONFIG_DIR/settings.json" << EOF
{
  "defaultModel": "$MODEL",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$MODEL"
  },
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "LS", "Agent", "Task",
      "WebFetch", "WebSearch",
      "mcp__tavily__tavily-search", "mcp__tavily__tavily-extract",
      "mcp__context7__resolve-library-id", "mcp__context7__get-library-docs",
      "mcp__sequential-thinking__sequentialthinking",
      "mcp__serena__list_dir", "mcp__serena__find_file", "mcp__serena__search_for_pattern",
      "mcp__serena__get_symbols_overview", "mcp__serena__find_symbol",
      "mcp__serena__find_referencing_symbols", "mcp__serena__list_memories",
      "mcp__serena__read_memory", "mcp__serena__get_current_config",
      "mcp__serena__think_about_collected_information",
      "Bash(git diff:*)", "Bash(git log:*)", "Bash(git status:*)",
      "Bash(git show:*)", "Bash(git blame:*)", "Bash(git branch:*)",
      "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)",
      "Bash(find:*)", "Bash(ls:*)", "Bash(tree:*)", "Bash(grep:*)",
      "Bash(rg:*)", "Bash(jq:*)", "Bash(curl -s:*)"
    ],
    "deny": [
      "Write", "Edit", "NotebookEdit",
      "Bash(rm:*)", "Bash(mv:*)", "Bash(cp:*)", "Bash(mkdir:*)",
      "Bash(chmod:*)", "Bash(chown:*)",
      "Bash(git add:*)", "Bash(git commit:*)", "Bash(git push:*)",
      "Bash(git checkout:*)", "Bash(git reset:*)", "Bash(git revert:*)",
      "Bash(npm install:*)", "Bash(pip install:*)", "Bash(sudo:*)",
      "mcp__serena__replace_symbol_body", "mcp__serena__insert_after_symbol",
      "mcp__serena__insert_before_symbol", "mcp__serena__rename_symbol",
      "mcp__serena__write_memory", "mcp__serena__delete_memory", "mcp__serena__edit_memory"
    ]
  }
}
EOF
    echo "✅ Audit mode: read-only permissions configured"
else
    cat > "$AUDIT_CONFIG_DIR/settings.json" << EOF
{
  "defaultModel": "$MODEL",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$MODEL"
  }
}
EOF
    echo "⚠️  Unsafe mode: full permissions (NOT RECOMMENDED)"
fi

# Symlink shared resources
ln -sf ~/.claude/commands "$AUDIT_CONFIG_DIR/commands" 2>/dev/null || true
ln -sf ~/.claude/scripts "$AUDIT_CONFIG_DIR/scripts" 2>/dev/null || true
ln -sf ~/.claude/hooks "$AUDIT_CONFIG_DIR/hooks" 2>/dev/null || true
ln -sf ~/.claude/CLAUDE.md "$AUDIT_CONFIG_DIR/CLAUDE.md" 2>/dev/null || true
ln -sf ~/.claude/.credentials.json "$AUDIT_CONFIG_DIR/.credentials.json" 2>/dev/null || true

# Step 4: Run headless Claude
echo ""
echo "[4/4] Running headless Claude with model '$MODEL'..."
echo "─────────────────────────────────────────────────────────────────"
echo ""

START_TIME=$(date +%s.%N)

# Run Claude with --dangerously-skip-permissions (security via allowedTools in settings.json)
CLAUDE_CONFIG_DIR="$AUDIT_CONFIG_DIR" claude --model "$MODEL" --dangerously-skip-permissions --print -p "$PROMPT" 2>&1

EXIT_CODE=$?
END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc)

echo ""
echo "─────────────────────────────────────────────────────────────────"

# Cleanup
rm -rf "$AUDIT_CONFIG_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  RESULT"
echo "═══════════════════════════════════════════════════════════════"
echo "Exit code: $EXIT_CODE"
printf "Duration: %.2f seconds\n" "$DURATION"
echo "Audit Mode: $AUDIT_MODE"
echo "═══════════════════════════════════════════════════════════════"
