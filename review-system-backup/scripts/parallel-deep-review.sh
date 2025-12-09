#!/bin/bash
#
# Parallel Deep Review - Runs 3 headless Claude instances with different LiteLLM models
# READ-ONLY AUDIT MODE: Full read/search/research access, NO write/edit/delete
# Uses --dangerously-skip-permissions with restricted allowedTools for safe automation
#
# Usage: parallel-deep-review.sh "<prompt>" [working_dir]
#
# Security: Each instance runs in audit mode with:
#   - ALLOWED: Read, Grep, Glob, WebSearch, WebFetch, git read ops, MCP search tools
#   - DENIED: Write, Edit, rm, mv, git commit/push, any destructive operations
#

set -e

PROMPT="${1:-Review the codebase for issues}"
WORK_DIR="${2:-$(pwd)}"

# Persistent output directory in project's .claude/kln/asyncDeepAudit/
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR=$(get_output_dir "asyncDeepAudit" "$WORK_DIR")
TIME_STAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_FILE="$OUTPUT_DIR/${TIME_STAMP}_parallel_$(echo "$PROMPT" | tr ' ' '-' | tr -cd '[:alnum:]-_' | head -c 30).md"

# Create isolated config directories for each model
CONFIG_DIR_BASE="/tmp/claude-review-config-$TIME_STAMP"
mkdir -p "$CONFIG_DIR_BASE/qwen"
mkdir -p "$CONFIG_DIR_BASE/kimi"
mkdir -p "$CONFIG_DIR_BASE/glm"

# Temp output files (will be merged into single markdown)
TEMP_OUTPUT_DIR="/tmp/parallel-review-$$"
mkdir -p "$TEMP_OUTPUT_DIR"
OUTPUT_QWEN="$TEMP_OUTPUT_DIR/qwen.txt"
OUTPUT_KIMI="$TEMP_OUTPUT_DIR/kimi.txt"
OUTPUT_GLM="$TEMP_OUTPUT_DIR/glm.txt"

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
for model in qwen3-coder kimi-k2-thinking glm-4.6-thinking; do
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

# Function to create audit settings for a model
# Audit mode: full read access, NO write/edit/delete
create_audit_settings() {
    local config_dir="$1"
    local model="$2"
    cat > "$config_dir/settings.json" << EOF
{
  "defaultModel": "$model",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$model",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$model",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$model"
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
      "mcp__serena__think_about_task_adherence",
      "mcp__serena__think_about_whether_you_are_done",
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
}

# Create audit settings for each model
create_audit_settings "$CONFIG_DIR_BASE/qwen" "qwen3-coder"
create_audit_settings "$CONFIG_DIR_BASE/kimi" "kimi-k2-thinking"
create_audit_settings "$CONFIG_DIR_BASE/glm" "glm-4.6-thinking"

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

# Function to run a single review using isolated config via CLAUDE_CONFIG_DIR
run_review() {
    local model_name=$1
    local config_dir=$2
    local output_file=$3
    local litellm_model=$4

    echo "[$(date +%H:%M:%S)] Starting $model_name review..."

    cd "$WORK_DIR"

    # Symlink shared resources to the temp config dir
    ln -sf ~/.claude/commands "$config_dir/commands" 2>/dev/null || true
    ln -sf ~/.claude/scripts "$config_dir/scripts" 2>/dev/null || true
    ln -sf ~/.claude/hooks "$config_dir/hooks" 2>/dev/null || true
    ln -sf ~/.claude/CLAUDE.md "$config_dir/CLAUDE.md" 2>/dev/null || true
    ln -sf ~/.claude/.credentials.json "$config_dir/.credentials.json" 2>/dev/null || true

    # Run with CLAUDE_CONFIG_DIR pointing to isolated config (no settings file race!)
    # --dangerously-skip-permissions with restricted allowedTools = safe audit mode
    CLAUDE_CONFIG_DIR="$config_dir" claude --model "$litellm_model" --dangerously-skip-permissions --print "$SYSTEM_PROMPT

USER REQUEST: $PROMPT

Directory: $WORK_DIR

Investigate using your tools. Be thorough." > "$output_file" 2>&1

    echo "[$(date +%H:%M:%S)] $model_name review complete"
}

# No backup needed - each review uses its own isolated config directory

# Run all 3 in parallel with explicit LiteLLM model names
# Using reliable models: qwen (code), kimi (architecture), glm (standards)
# No delays needed - each has its own config dir, no race conditions!
run_review "QWEN" "$CONFIG_DIR_BASE/qwen" "$OUTPUT_QWEN" "qwen3-coder" &
PID_QWEN=$!

run_review "KIMI" "$CONFIG_DIR_BASE/kimi" "$OUTPUT_KIMI" "kimi-k2-thinking" &
PID_KIMI=$!

run_review "GLM" "$CONFIG_DIR_BASE/glm" "$OUTPUT_GLM" "glm-4.6-thinking" &
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

# No restore needed - we used isolated config directories

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "ALL REVIEWS COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"

# Build combined markdown output file
{
    echo "# Parallel Deep Audit: $PROMPT"
    echo ""
    echo "**Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Directory:** $WORK_DIR"
    echo "**Models:** qwen3-coder (code), kimi-k2-thinking (architecture), glm-4.6-thinking (standards)"
    echo ""
    echo "---"
} > "$OUTPUT_FILE"

# Display and save results
ALL_CONTENT=""

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "QWEN REVIEW (Code Quality, Bugs)"
echo "═══════════════════════════════════════════════════════════════════"
if [ -f "$OUTPUT_QWEN" ]; then
    QWEN_CONTENT=$(cat "$OUTPUT_QWEN")
    ALL_CONTENT="$ALL_CONTENT\n$QWEN_CONTENT"
    echo "$QWEN_CONTENT"
    {
        echo ""
        echo "## QWEN (Code Quality, Bugs)"
        echo ""
        echo "$QWEN_CONTENT"
    } >> "$OUTPUT_FILE"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "KIMI REVIEW (Architecture, Planning)"
echo "═══════════════════════════════════════════════════════════════════"
if [ -f "$OUTPUT_KIMI" ]; then
    KIMI_CONTENT=$(cat "$OUTPUT_KIMI")
    ALL_CONTENT="$ALL_CONTENT\n$KIMI_CONTENT"
    echo "$KIMI_CONTENT"
    {
        echo ""
        echo "## KIMI (Architecture, Planning)"
        echo ""
        echo "$KIMI_CONTENT"
    } >> "$OUTPUT_FILE"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "GLM REVIEW (Standards, Compliance)"
echo "═══════════════════════════════════════════════════════════════════"
if [ -f "$OUTPUT_GLM" ]; then
    GLM_CONTENT=$(cat "$OUTPUT_GLM")
    ALL_CONTENT="$ALL_CONTENT\n$GLM_CONTENT"
    echo "$GLM_CONTENT"
    {
        echo ""
        echo "## GLM (Standards, Compliance)"
        echo ""
        echo "$GLM_CONTENT"
    } >> "$OUTPUT_FILE"
fi

# Cleanup temp files
rm -rf "$TEMP_OUTPUT_DIR"
rm -rf "$CONFIG_DIR_BASE"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════════"

# Auto-extract facts from all reviews (Tier 1)
[ -n "$ALL_CONTENT" ] && ~/.claude/scripts/fact-extract.sh "$ALL_CONTENT" "review" "$PROMPT" "$WORK_DIR"
