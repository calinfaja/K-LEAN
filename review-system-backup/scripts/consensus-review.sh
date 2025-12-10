#!/bin/bash
#
# Consensus Review - Multiple models in parallel with dynamic discovery
# Uses first 5 healthy models from LiteLLM API
#
# Usage: consensus-review.sh "<focus>" [working_dir]
#

FOCUS="${1:-General code review}"
WORK_DIR="${2:-$(pwd)}"
SCRIPTS_DIR="$(dirname "$0")"

# Persistent output directory in project's .claude/kln/quickCompare/
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR=$(get_output_dir "quickCompare" "$WORK_DIR")
TIME_STAMP=$(date +%Y-%m-%d_%H-%M-%S)
OUTPUT_FILE="$OUTPUT_DIR/${TIME_STAMP}_consensus_$(echo "$FOCUS" | tr ' ' '-' | tr -cd '[:alnum:]-_' | head -c 30).md"

echo "═══════════════════════════════════════════════════════════════"
echo "CONSENSUS REVIEW - Getting healthy models..."
echo "═══════════════════════════════════════════════════════════════"

# Get first 5 healthy models dynamically
HEALTHY_MODELS=$("$SCRIPTS_DIR/get-healthy-models.sh" 5 2>/dev/null)

if [ -z "$HEALTHY_MODELS" ]; then
    echo "ERROR: No healthy models found" >&2
    echo "Check if LiteLLM proxy is running: start-nano-proxy" >&2
    exit 1
fi

MODEL_COUNT=$(echo "$HEALTHY_MODELS" | wc -l)
echo "Found $MODEL_COUNT healthy models:"
echo "$HEALTHY_MODELS" | while read model; do echo "  ✓ $model"; done

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

# System prompt for all models
SYSTEM_PROMPT="Concise code reviewer.$KNOWLEDGE_SUFFIX"

# Launch each healthy model in parallel
while IFS= read -r model; do
    [ -z "$model" ] && continue
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    curl -s --max-time 120 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"system\", \"content\": $(echo "$SYSTEM_PROMPT" | jq -Rs .)}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$TEMP_DIR/$SAFE_NAME.json" &
    PIDS="$PIDS $!"
    echo "  Launched: $model"
done <<< "$HEALTHY_MODELS"

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

# Build model list for header
MODELS_LIST=$(echo "$HEALTHY_MODELS" | tr '\n' ', ' | sed 's/, $//')

# Start building the markdown output file
{
    echo "# Consensus Review: $FOCUS"
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
    JSON_FILE="$TEMP_DIR/$SAFE_NAME.json"

    if [ -f "$JSON_FILE" ]; then
        MODEL_CONTENT=$(get_response "$JSON_FILE")
        ALL_CONTENT="$ALL_CONTENT\n$MODEL_CONTENT"
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "$model"
        echo "═══════════════════════════════════════════════════════════════"
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
rm -rf "$TEMP_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════"

# Auto-extract facts from all reviews (Tier 1)
[ -n "$ALL_CONTENT" ] && ~/.claude/scripts/fact-extract.sh "$ALL_CONTENT" "review" "$FOCUS" "$WORK_DIR"
