#!/usr/bin/env bash
#
# Parallel Deep Review - Runs headless Claude instances with LiteLLM models
# Uses dynamic model discovery - runs first 3 healthy models (headless is resource-heavy)
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
SCRIPTS_DIR="$(dirname "$0")"

# Source kb-root.sh for unified paths
if [ -f "$SCRIPTS_DIR/kb-root.sh" ]; then
    source "$SCRIPTS_DIR/kb-root.sh"
else
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
    KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
fi

# Persistent output directory in project's .claude/kln/asyncDeepAudit/
source "$KB_SCRIPTS_DIR/session-helper.sh"
OUTPUT_DIR=$(get_output_dir "asyncDeepAudit" "$WORK_DIR")
TIME_STAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_FILE="$OUTPUT_DIR/${TIME_STAMP}_parallel_$(echo "$PROMPT" | tr ' ' '-' | tr -cd '[:alnum:]-_' | head -c 30).md"

echo "═══════════════════════════════════════════════════════════════════"
echo "PARALLEL DEEP REVIEW - Getting healthy models..."
echo "═══════════════════════════════════════════════════════════════════"

# Get first 3 healthy models (headless instances are resource-heavy)
HEALTHY_MODELS=$("$SCRIPTS_DIR/get-healthy-models.sh" 3 2>/dev/null)

if [ -z "$HEALTHY_MODELS" ]; then
    echo "ERROR: No healthy models available" >&2
    echo "Check if LiteLLM proxy is running: start-nano-proxy" >&2
    exit 1
fi

MODEL_COUNT=$(echo "$HEALTHY_MODELS" | wc -l)
echo "Found $MODEL_COUNT healthy models:"
echo "$HEALTHY_MODELS" | while read model; do echo "  ✓ $model"; done
echo ""

# Create config and temp directories
CONFIG_DIR_BASE="/tmp/claude-review-config-$TIME_STAMP"
TEMP_OUTPUT_DIR="/tmp/parallel-review-$$"
mkdir -p "$TEMP_OUTPUT_DIR"

# Create config directory for each model
while IFS= read -r model; do
    [ -z "$model" ] && continue
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    mkdir -p "$CONFIG_DIR_BASE/$SAFE_NAME"
done <<< "$HEALTHY_MODELS"

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

# Create audit settings for each healthy model
while IFS= read -r model; do
    [ -z "$model" ] && continue
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    create_audit_settings "$CONFIG_DIR_BASE/$SAFE_NAME" "$model"
done <<< "$HEALTHY_MODELS"

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

# Run all healthy models in parallel
# No delays needed - each has its own config dir, no race conditions!
declare -A PIDS
while IFS= read -r model; do
    [ -z "$model" ] && continue
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    OUTPUT_TXT="$TEMP_OUTPUT_DIR/$SAFE_NAME.txt"
    run_review "$model" "$CONFIG_DIR_BASE/$SAFE_NAME" "$OUTPUT_TXT" "$model" &
    PIDS[$model]=$!
done <<< "$HEALTHY_MODELS"

# Wait for all to complete
echo ""
echo "Waiting for all reviews to complete (this may take 2-5 minutes each)..."
for model in "${!PIDS[@]}"; do
    echo "  $model (PID: ${PIDS[$model]})"
done
echo ""

for model in "${!PIDS[@]}"; do
    wait ${PIDS[$model]}
    EXIT_CODE=$?
    echo "✓ $model complete (exit: $EXIT_CODE)"
done

# No restore needed - we used isolated config directories

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "ALL REVIEWS COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"

# Build model list for header
MODELS_LIST=$(echo "$HEALTHY_MODELS" | tr '\n' ', ' | sed 's/, $//')

# Build combined markdown output file
{
    echo "# Parallel Deep Audit: $PROMPT"
    echo ""
    echo "**Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Directory:** $WORK_DIR"
    echo "**Models:** $MODELS_LIST"
    echo ""
    echo "---"
} > "$OUTPUT_FILE"

# Display and save results for each model dynamically
ALL_CONTENT=""

while IFS= read -r model; do
    [ -z "$model" ] && continue
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    OUTPUT_TXT="$TEMP_OUTPUT_DIR/$SAFE_NAME.txt"

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "$model"
    echo "═══════════════════════════════════════════════════════════════════"
    if [ -f "$OUTPUT_TXT" ]; then
        MODEL_CONTENT=$(cat "$OUTPUT_TXT")
        ALL_CONTENT="$ALL_CONTENT\n$MODEL_CONTENT"
        echo "$MODEL_CONTENT"
        {
            echo ""
            echo "## $model"
            echo ""
            echo "$MODEL_CONTENT"
        } >> "$OUTPUT_FILE"
    fi
done <<< "$HEALTHY_MODELS"

# Cleanup temp files
rm -rf "$TEMP_OUTPUT_DIR"
rm -rf "$CONFIG_DIR_BASE"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════════"

# Auto-extract facts from all reviews (Tier 1)
[ -n "$ALL_CONTENT" ] && "$KB_SCRIPTS_DIR/fact-extract.sh" "$ALL_CONTENT" "review" "$PROMPT" "$WORK_DIR"
