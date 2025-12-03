#!/bin/bash
#
# Parallel Deep Review - Runs 3 headless Claude instances with different LiteLLM models
# Each instance has FULL TOOL ACCESS and runs in an isolated config directory
#
# Usage: parallel-deep-review.sh "<prompt>" [working_dir]
#

set -e

PROMPT="${1:-Review the codebase for issues}"
WORK_DIR="${2:-$(pwd)}"

# Session-based output directory (each Claude instance gets its own folder)
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR="$SESSION_DIR"
TIME_STAMP=$(date +%H%M%S)

# Create isolated config directories for each model
CONFIG_DIR_BASE="/tmp/claude-review-config-$TIME_STAMP"
mkdir -p "$CONFIG_DIR_BASE/qwen"
mkdir -p "$CONFIG_DIR_BASE/kimi"
mkdir -p "$CONFIG_DIR_BASE/glm"

# Output files
OUTPUT_QWEN="$OUTPUT_DIR/deep-qwen-$TIME_STAMP.txt"
OUTPUT_KIMI="$OUTPUT_DIR/deep-kimi-$TIME_STAMP.txt"
OUTPUT_GLM="$OUTPUT_DIR/deep-glm-$TIME_STAMP.txt"

# Health check function (test actual model response)
check_model_health() {
    local model="$1"
    local resp=$(curl -s --max-time 10 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)
    echo "$resp" | jq -e '.choices[0]' > /dev/null 2>&1
}

# Check which models are healthy
# Using qwen, kimi, glm - these are proven reliable for tool use
# Avoided: deepseek (empty output), hermes (hallucinates), minimax (timeout)
echo "Checking model health..."
HEALTHY_MODELS=""
for model in coding-qwen agent-kimi tools-glm; do
    if check_model_health "$model"; then
        echo "✓ $model - healthy"
        HEALTHY_MODELS="$HEALTHY_MODELS $model"
    else
        echo "✗ $model - unhealthy (will skip)"
    fi
done

if [ -z "$HEALTHY_MODELS" ]; then
    echo "ERROR: No healthy models available"
    echo "Check if LiteLLM proxy is running: start-nano-proxy"
    exit 1
fi
echo ""

echo "═══════════════════════════════════════════════════════════════════"
echo "PARALLEL DEEP REVIEW - 3 Models with Full Tool Access"
echo "═══════════════════════════════════════════════════════════════════"
echo "Directory: $WORK_DIR"
echo "Prompt: $PROMPT"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Starting 3 parallel review instances..."
echo ""

# Create settings for each model - ALL model overrides needed!
# QWEN (runs as sonnet)
cat > "$CONFIG_DIR_BASE/qwen/settings.json" << 'EOF'
{
  "defaultModel": "coding-qwen",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "coding-qwen",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "coding-qwen",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "coding-qwen"
  }
}
EOF

# KIMI (runs as haiku) - reliable for tool use
cat > "$CONFIG_DIR_BASE/kimi/settings.json" << 'EOF'
{
  "defaultModel": "agent-kimi",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "agent-kimi",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "agent-kimi",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "agent-kimi"
  }
}
EOF

# GLM (runs as opus)
cat > "$CONFIG_DIR_BASE/glm/settings.json" << 'EOF'
{
  "defaultModel": "tools-glm",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "tools-glm",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "tools-glm",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "tools-glm"
  }
}
EOF

# Common system prompt for investigators
SYSTEM_PROMPT="You are an independent code reviewer with FULL TOOL ACCESS.

YOUR CAPABILITIES:
- READ any file in the codebase
- GREP to search for patterns
- BASH to run git, find, etc.

YOUR MISSION: Investigate thoroughly. VERIFY findings with tools.

OUTPUT FORMAT:
## Grade: [A-F]
## Risk: [CRITICAL/HIGH/MEDIUM/LOW]
## Critical Issues
| File:Line | Issue | Evidence |
## Warnings
| File:Line | Issue |
## Verdict: [APPROVE/REQUEST_CHANGES]
"

# Function to run a single review
run_review() {
    local model_name=$1
    local config_dir=$2
    local output_file=$3
    local litellm_model=$4

    echo "[$(date +%H:%M:%S)] Starting $model_name review..."

    cd "$WORK_DIR"

    # Use settings-nanogpt.json to route through LiteLLM, then specify model explicitly
    cp ~/.claude/settings-nanogpt.json ~/.claude/settings.json 2>/dev/null || true

    # Run with explicit model via --model flag
    claude --model "$litellm_model" --print "$SYSTEM_PROMPT

USER REQUEST: $PROMPT

Directory: $WORK_DIR

Investigate using your tools. Be thorough." > "$output_file" 2>&1

    echo "[$(date +%H:%M:%S)] $model_name review complete"
}

# Backup original settings
cp ~/.claude/settings.json ~/.claude/settings-parallel-backup.json

# Run all 3 in parallel with explicit LiteLLM model names
# Using reliable models: qwen (code), kimi (architecture), glm (standards)
run_review "QWEN" "$CONFIG_DIR_BASE/qwen" "$OUTPUT_QWEN" "coding-qwen" &
PID_QWEN=$!

# Small delay to avoid race on settings file
sleep 2

run_review "KIMI" "$CONFIG_DIR_BASE/kimi" "$OUTPUT_KIMI" "agent-kimi" &
PID_KIMI=$!

sleep 2

run_review "GLM" "$CONFIG_DIR_BASE/glm" "$OUTPUT_GLM" "tools-glm" &
PID_GLM=$!

# Wait for all to complete
echo ""
echo "Waiting for all reviews to complete (this may take 2-5 minutes each)..."
echo "  QWEN (PID: $PID_QWEN)"
echo "  KIMI (PID: $PID_KIMI)"
echo "  GLM (PID: $PID_GLM)"
echo ""

wait $PID_QWEN
QWEN_EXIT=$?
echo "✓ QWEN complete (exit: $QWEN_EXIT)"

wait $PID_KIMI
KIMI_EXIT=$?
echo "✓ KIMI complete (exit: $KIMI_EXIT)"

wait $PID_GLM
GLM_EXIT=$?
echo "✓ GLM complete (exit: $GLM_EXIT)"

# Restore original settings
cp ~/.claude/settings-parallel-backup.json ~/.claude/settings.json
rm -f ~/.claude/settings-parallel-backup.json

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "ALL REVIEWS COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"

# Display results
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "QWEN REVIEW (Code Quality, Bugs)"
echo "═══════════════════════════════════════════════════════════════════"
cat "$OUTPUT_QWEN"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "KIMI REVIEW (Architecture, Planning)"
echo "═══════════════════════════════════════════════════════════════════"
cat "$OUTPUT_KIMI"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "GLM REVIEW (Standards, Compliance)"
echo "═══════════════════════════════════════════════════════════════════"
cat "$OUTPUT_GLM"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "REVIEW FILES SAVED TO:"
echo "  $OUTPUT_QWEN"
echo "  $OUTPUT_KIMI"
echo "  $OUTPUT_GLM"
echo "═══════════════════════════════════════════════════════════════════"

# Cleanup temp configs
rm -rf "$CONFIG_DIR_BASE"
