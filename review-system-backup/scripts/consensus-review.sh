#!/bin/bash
#
# Consensus Review - 3 models in parallel with health check
# Skips unhealthy models, runs what's available
#
# Usage: consensus-review.sh "<focus>" [working_dir]
#

FOCUS="${1:-General code review}"
WORK_DIR="${2:-$(pwd)}"

# Persistent output directory in project's .claude/kln/quickCompare/
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR=$(get_output_dir "quickCompare" "$WORK_DIR")
TIME_STAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_FILE="$OUTPUT_DIR/${TIME_STAMP}_consensus_$(echo "$FOCUS" | tr ' ' '-' | tr -cd '[:alnum:]-_' | head -c 30).md"

# Health check
check_model_health() {
    local resp=$(curl -s --max-time 5 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$1\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)
    echo "$resp" | jq -e '.choices[0]' > /dev/null 2>&1
}

# Check proxy
curl -s --max-time 3 http://localhost:4000/models > /dev/null 2>&1 || { echo "ERROR: LiteLLM not running"; exit 1; }

echo "═══════════════════════════════════════════════════════════════"
echo "CONSENSUS REVIEW - Checking model health..."
echo "═══════════════════════════════════════════════════════════════"

# Check which models are healthy
HEALTHY_MODELS=""
for model in qwen3-coder deepseek-v3-thinking glm-4.6-thinking; do
    if check_model_health "$model"; then
        echo "✓ $model - healthy"
        HEALTHY_MODELS="$HEALTHY_MODELS $model"
    else
        echo "✗ $model - unhealthy (skipping)"
    fi
done

[ -z "$HEALTHY_MODELS" ] && { echo "ERROR: No healthy models"; exit 1; }

echo ""
echo "Focus: $FOCUS"
echo "Directory: $WORK_DIR"
echo "═══════════════════════════════════════════════════════════════"

cd "$WORK_DIR"

# Search knowledge-db for relevant context
KNOWLEDGE_CONTEXT=""
PYTHON="$HOME/.venvs/knowledge-db/bin/python"
if [ -x "$PYTHON" ] && [ -f "$HOME/.claude/scripts/knowledge-search.py" ]; then
    if [ -d ".knowledge-db" ] || [ -d "../.knowledge-db" ]; then
        KNOWLEDGE_CONTEXT=$("$PYTHON" "$HOME/.claude/scripts/knowledge-search.py" "$FOCUS" --format inject --limit 3 2>/dev/null || echo "")
        if [ -n "$KNOWLEDGE_CONTEXT" ] && [ "$KNOWLEDGE_CONTEXT" != "No relevant prior knowledge found." ]; then
            echo "📚 Found relevant prior knowledge"
        fi
    fi
fi

DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)
[ -z "$DIFF" ] && DIFF=$(git diff 2>/dev/null | head -300)
[ -z "$DIFF" ] && DIFF="No git changes found."

PROMPT="Review this code for: $FOCUS

CODE:
$DIFF

Provide: Grade (A-F), Risk, Top 3 Issues, Verdict"

echo "Starting parallel reviews..."

# Build knowledge suffix for system prompts
KNOWLEDGE_SUFFIX=""
if [ -n "$KNOWLEDGE_CONTEXT" ] && [ "$KNOWLEDGE_CONTEXT" != "No relevant prior knowledge found." ]; then
    KNOWLEDGE_SUFFIX="

$KNOWLEDGE_CONTEXT

Consider this prior knowledge if relevant."
fi

# Launch healthy models in parallel
PIDS=""

# Temp files for JSON responses
TEMP_DIR="/tmp/consensus-$$"
mkdir -p "$TEMP_DIR"

if echo "$HEALTHY_MODELS" | grep -q "qwen3-coder"; then
    SYSTEM_QWEN="Code reviewer: bugs, memory safety.$KNOWLEDGE_SUFFIX"
    curl -s --max-time 90 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"qwen3-coder\", \"messages\": [{\"role\": \"system\", \"content\": $(echo "$SYSTEM_QWEN" | jq -Rs .)}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$TEMP_DIR/qwen.json" &
    PID_QWEN=$!
    PIDS="$PIDS $PID_QWEN"
fi

if echo "$HEALTHY_MODELS" | grep -q "deepseek-v3-thinking"; then
    SYSTEM_DS="Architect: design, coupling.$KNOWLEDGE_SUFFIX"
    curl -s --max-time 120 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"deepseek-v3-thinking\", \"messages\": [{\"role\": \"system\", \"content\": $(echo "$SYSTEM_DS" | jq -Rs .)}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$TEMP_DIR/deepseek.json" &
    PID_DEEPSEEK=$!
    PIDS="$PIDS $PID_DEEPSEEK"
fi

if echo "$HEALTHY_MODELS" | grep -q "glm-4.6-thinking"; then
    SYSTEM_GLM="Compliance: MISRA, standards.$KNOWLEDGE_SUFFIX"
    curl -s --max-time 120 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"glm-4.6-thinking\", \"messages\": [{\"role\": \"system\", \"content\": $(echo "$SYSTEM_GLM" | jq -Rs .)}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$TEMP_DIR/glm.json" &
    PID_GLM=$!
    PIDS="$PIDS $PID_GLM"
fi

# Wait for all
for pid in $PIDS; do
    wait $pid
done

# Helper to extract content from regular or thinking models
get_response() {
    # Check content first, if empty check reasoning_content (for thinking models)
    local content=$(jq -r '.choices[0].message.content // empty' "$1")
    if [ -n "$content" ]; then
        echo "$content"
    else
        jq -r '.choices[0].message.reasoning_content // "No response"' "$1"
    fi
}

# Start building the markdown output file
{
    echo "# Consensus Review: $FOCUS"
    echo ""
    echo "**Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Directory:** $WORK_DIR"
    echo "**Models:** qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking"
    echo ""
    echo "---"
} > "$OUTPUT_FILE"

# Display and save results for healthy models only
ALL_CONTENT=""

if [ -f "$TEMP_DIR/qwen.json" ]; then
    QWEN_CONTENT=$(get_response "$TEMP_DIR/qwen.json")
    ALL_CONTENT="$ALL_CONTENT\n$QWEN_CONTENT"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "QWEN (Code Quality)"
    echo "═══════════════════════════════════════════════════════════════"
    echo "$QWEN_CONTENT"
    {
        echo ""
        echo "## QWEN (Code Quality)"
        echo ""
        echo "$QWEN_CONTENT"
    } >> "$OUTPUT_FILE"
fi

if [ -f "$TEMP_DIR/deepseek.json" ]; then
    DS_CONTENT=$(get_response "$TEMP_DIR/deepseek.json")
    ALL_CONTENT="$ALL_CONTENT\n$DS_CONTENT"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "DEEPSEEK (Architecture)"
    echo "═══════════════════════════════════════════════════════════════"
    echo "$DS_CONTENT"
    {
        echo ""
        echo "## DEEPSEEK (Architecture)"
        echo ""
        echo "$DS_CONTENT"
    } >> "$OUTPUT_FILE"
fi

if [ -f "$TEMP_DIR/glm.json" ]; then
    GLM_CONTENT=$(get_response "$TEMP_DIR/glm.json")
    ALL_CONTENT="$ALL_CONTENT\n$GLM_CONTENT"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "GLM (Standards)"
    echo "═══════════════════════════════════════════════════════════════"
    echo "$GLM_CONTENT"
    {
        echo ""
        echo "## GLM (Standards)"
        echo ""
        echo "$GLM_CONTENT"
    } >> "$OUTPUT_FILE"
fi

# Cleanup temp files
rm -rf "$TEMP_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════"

# Auto-extract facts from all reviews (Tier 1)
[ -n "$ALL_CONTENT" ] && ~/.claude/scripts/fact-extract.sh "$ALL_CONTENT" "review" "$FOCUS" "$WORK_DIR"
