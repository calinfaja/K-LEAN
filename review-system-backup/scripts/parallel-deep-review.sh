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
TIMESTAMP=$(date +%s)

# Create isolated config directories for each model
CONFIG_DIR_BASE="/tmp/claude-review-$TIMESTAMP"
mkdir -p "$CONFIG_DIR_BASE/qwen"
mkdir -p "$CONFIG_DIR_BASE/deepseek"
mkdir -p "$CONFIG_DIR_BASE/glm"

# Output directory and files
OUTPUT_DIR="/tmp/claude-reviews"
mkdir -p "$OUTPUT_DIR"
OUTPUT_QWEN="$OUTPUT_DIR/review-qwen-$TIMESTAMP.txt"
OUTPUT_DEEPSEEK="$OUTPUT_DIR/review-deepseek-$TIMESTAMP.txt"
OUTPUT_GLM="$OUTPUT_DIR/review-glm-$TIMESTAMP.txt"

# Check LiteLLM is running
if ! curl -s http://localhost:4000/health > /dev/null 2>&1; then
    echo "ERROR: LiteLLM proxy not running on localhost:4000"
    echo "Start it with: start-nano-proxy"
    exit 1
fi

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

# DEEPSEEK (runs as haiku)
cat > "$CONFIG_DIR_BASE/deepseek/settings.json" << 'EOF'
{
  "defaultModel": "architecture-deepseek",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "architecture-deepseek",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "architecture-deepseek",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "architecture-deepseek"
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

    echo "[$(date +%H:%M:%S)] Starting $model_name review..."

    # Copy essential claude config files
    cp -r ~/.claude/commands "$config_dir/" 2>/dev/null || true
    cp -r ~/.claude/skills "$config_dir/" 2>/dev/null || true

    # Set config directory and run
    export HOME_BACKUP="$HOME"

    # Use a subshell with modified HOME to isolate the config
    (
        # Create minimal home structure
        mkdir -p "$config_dir/.claude"
        cp "$config_dir/settings.json" "$config_dir/.claude/settings.json"

        # Copy MCP config if exists
        if [ -f ~/.claude/mcp.json ]; then
            cp ~/.claude/mcp.json "$config_dir/.claude/"
        fi

        cd "$WORK_DIR"

        # Run with settings override by copying to actual location temporarily
        # This is a workaround since Claude doesn't support custom config dirs
        cp "$config_dir/settings.json" ~/.claude/settings.json

        claude --print "$SYSTEM_PROMPT

USER REQUEST: $PROMPT

Directory: $WORK_DIR

Investigate using your tools. Be thorough." > "$output_file" 2>&1
    )

    echo "[$(date +%H:%M:%S)] $model_name review complete"
}

# Backup original settings
cp ~/.claude/settings.json ~/.claude/settings-parallel-backup.json

# Run all 3 in parallel
run_review "QWEN" "$CONFIG_DIR_BASE/qwen" "$OUTPUT_QWEN" &
PID_QWEN=$!

# Small delay to avoid race on settings file
sleep 2

run_review "DEEPSEEK" "$CONFIG_DIR_BASE/deepseek" "$OUTPUT_DEEPSEEK" &
PID_DEEPSEEK=$!

sleep 2

run_review "GLM" "$CONFIG_DIR_BASE/glm" "$OUTPUT_GLM" &
PID_GLM=$!

# Wait for all to complete
echo ""
echo "Waiting for all reviews to complete (this may take 2-5 minutes each)..."
echo "  QWEN (PID: $PID_QWEN)"
echo "  DEEPSEEK (PID: $PID_DEEPSEEK)"
echo "  GLM (PID: $PID_GLM)"
echo ""

wait $PID_QWEN
QWEN_EXIT=$?
echo "✓ QWEN complete (exit: $QWEN_EXIT)"

wait $PID_DEEPSEEK
DEEPSEEK_EXIT=$?
echo "✓ DEEPSEEK complete (exit: $DEEPSEEK_EXIT)"

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
echo "DEEPSEEK REVIEW (Architecture, Design)"
echo "═══════════════════════════════════════════════════════════════════"
cat "$OUTPUT_DEEPSEEK"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "GLM REVIEW (Standards, MISRA)"
echo "═══════════════════════════════════════════════════════════════════"
cat "$OUTPUT_GLM"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "REVIEW FILES SAVED TO:"
echo "  $OUTPUT_QWEN"
echo "  $OUTPUT_DEEPSEEK"
echo "  $OUTPUT_GLM"
echo "═══════════════════════════════════════════════════════════════════"

# Cleanup temp configs
rm -rf "$CONFIG_DIR_BASE"
