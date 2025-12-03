#!/bin/bash
#
# Quick Review - Single model with health check + fallback
#
# Usage: quick-review.sh <model> "<focus>" [working_dir]
#

MODEL="${1:-qwen}"
FOCUS="${2:-General code review}"
WORK_DIR="${3:-$(pwd)}"

# Session-based output directory (each Claude instance gets its own folder)
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR="$SESSION_DIR"
TIME_STAMP=$(date +%H%M%S)

MODELS_PRIORITY="coding-qwen architecture-deepseek tools-glm"

get_litellm_model() {
    case "$1" in
        qwen) echo "coding-qwen" ;;
        deepseek) echo "architecture-deepseek" ;;
        glm) echo "tools-glm" ;;
        *) echo "coding-qwen" ;;
    esac
}

check_model_health() {
    local resp=$(curl -s --max-time 5 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$1\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)
    echo "$resp" | jq -e '.choices[0]' > /dev/null 2>&1
}

find_healthy_model() {
    check_model_health "$1" && { echo "$1"; return 0; }
    echo "⚠️  $1 unhealthy, trying fallback..." >&2
    for m in $MODELS_PRIORITY; do
        [ "$m" != "$1" ] && check_model_health "$m" && { echo "✓ Using $m" >&2; echo "$m"; return 0; }
    done
    return 1
}

# Check proxy
curl -s --max-time 3 http://localhost:4000/models > /dev/null 2>&1 || { echo "ERROR: LiteLLM not running"; exit 1; }

# Find healthy model
PREFERRED=$(get_litellm_model "$MODEL")
LITELLM_MODEL=$(find_healthy_model "$PREFERRED")
[ -z "$LITELLM_MODEL" ] && { echo "ERROR: No healthy models"; exit 1; }

echo "═══════════════════════════════════════════════════════════════"
echo "QUICK REVIEW - $LITELLM_MODEL"
echo "═══════════════════════════════════════════════════════════════"
echo "Focus: $FOCUS"
echo "═══════════════════════════════════════════════════════════════"

cd "$WORK_DIR"

# Search knowledge-db for relevant context
KNOWLEDGE_CONTEXT=""
PYTHON="$HOME/.venvs/knowledge-db/bin/python"
if [ -x "$PYTHON" ] && [ -f "$HOME/.claude/scripts/knowledge-search.py" ]; then
    # Check if project has knowledge-db
    if [ -d ".knowledge-db" ] || [ -d "../.knowledge-db" ]; then
        KNOWLEDGE_CONTEXT=$("$PYTHON" "$HOME/.claude/scripts/knowledge-search.py" "$FOCUS" --format inject --limit 3 2>/dev/null || echo "")
    fi
fi

DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)
[ -z "$DIFF" ] && DIFF=$(git diff 2>/dev/null | head -300)
[ -z "$DIFF" ] && DIFF="No git changes found."

PROMPT="Review this code for: $FOCUS

CODE:
$DIFF

Provide: Grade (A-F), Risk, Issues, Verdict (APPROVE/REQUEST_CHANGES)"

# Build system prompt with optional knowledge context
SYSTEM_PROMPT="Concise code reviewer."
if [ -n "$KNOWLEDGE_CONTEXT" ] && [ "$KNOWLEDGE_CONTEXT" != "No relevant prior knowledge found." ]; then
    SYSTEM_PROMPT="Concise code reviewer.

$KNOWLEDGE_CONTEXT

Use this prior knowledge if relevant to the review."
    echo "📚 Found relevant prior knowledge"
fi

RESPONSE=$(curl -s --max-time 60 http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$LITELLM_MODEL\",
    \"messages\": [
      {\"role\": \"system\", \"content\": $(echo "$SYSTEM_PROMPT" | jq -Rs .)},
      {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 1500
  }")

OUTPUT_FILE="$OUTPUT_DIR/quick-$LITELLM_MODEL-$TIME_STAMP.json"
echo "$RESPONSE" > "$OUTPUT_FILE"

# Handle both regular and thinking models
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')
[ -z "$CONTENT" ] && CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.reasoning_content // empty')
[ -z "$CONTENT" ] && { echo "ERROR: No response"; echo "$RESPONSE"; exit 1; }

echo ""
echo "$CONTENT"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════"
