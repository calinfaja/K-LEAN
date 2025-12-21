#!/usr/bin/env bash
#
# Quick Review - Single model with health check + fallback
# Uses dynamic model discovery from LiteLLM API
#
# Usage: quick-review.sh <model> "<focus>" [working_dir]
# Run get-models.sh to see available models
#

MODEL="${1:-}"
FOCUS="${2:-General code review}"
WORK_DIR="${3:-$(pwd)}"
SCRIPTS_DIR="$(dirname "$0")"

# Source kb-root.sh for unified paths
if [ -f "$SCRIPTS_DIR/kb-root.sh" ]; then
    source "$SCRIPTS_DIR/kb-root.sh"
else
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
    KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
fi

# Persistent output directory in project's .claude/kln/quickReview/
source "$KB_SCRIPTS_DIR/session-helper.sh"
source "$SCRIPTS_DIR/../lib/common.sh" 2>/dev/null || true
source "$KB_SCRIPTS_DIR/review-logger.sh" 2>/dev/null || true

# Track timing
REVIEW_START_MS=$(($(date +%s%N)/1000000))

# Validate model is specified
if [ -z "$MODEL" ]; then
    echo "ERROR: No model specified" >&2
    echo "Usage: quick-review.sh <model> \"<focus>\" [working_dir]" >&2
    echo "" >&2
    echo "Available models:" >&2
    "$SCRIPTS_DIR/get-models.sh" >&2
    exit 1
fi

# Validate model exists in LiteLLM
if ! "$SCRIPTS_DIR/validate-model.sh" "$MODEL" 2>/dev/null; then
    echo "ERROR: Invalid model '$MODEL'" >&2
    echo "Available models:" >&2
    "$SCRIPTS_DIR/get-models.sh" >&2
    exit 1
fi

# Check model health with fallback
if ! "$SCRIPTS_DIR/health-check-model.sh" "$MODEL" 2>/dev/null; then
    echo "⚠️  Model $MODEL unhealthy, trying fallback..." >&2
    LITELLM_MODEL=$("$SCRIPTS_DIR/get-healthy-models.sh" 1 2>/dev/null | head -1)
    if [ -z "$LITELLM_MODEL" ]; then
        echo "ERROR: No healthy models available" >&2
        exit 1
    fi
    echo "✓ Using $LITELLM_MODEL" >&2
else
    LITELLM_MODEL="$MODEL"
fi

OUTPUT_DIR=$(get_output_dir "quickReview" "$WORK_DIR")
OUTPUT_FILENAME=$(generate_filename "$LITELLM_MODEL" "$FOCUS" ".md")

# Log review start
type log_debug &>/dev/null && log_debug "review" "quick_start" "model=$LITELLM_MODEL" "focus=$FOCUS" "dir=$WORK_DIR"
type log_review_start &>/dev/null && log_review_start "quickReview" "$LITELLM_MODEL" "$FOCUS" "$OUTPUT_DIR/$OUTPUT_FILENAME"

echo "═══════════════════════════════════════════════════════════════"
echo "QUICK REVIEW - $LITELLM_MODEL"
echo "═══════════════════════════════════════════════════════════════"
echo "Focus: $FOCUS"
echo "═══════════════════════════════════════════════════════════════"

cd "$WORK_DIR"

# Search knowledge-db for relevant context
KNOWLEDGE_CONTEXT=""
if [ -x "$KB_PYTHON" ] && [ -f "$KB_SCRIPTS_DIR/knowledge-search.py" ]; then
    # Check if project has knowledge-db
    if [ -d ".knowledge-db" ] || [ -d "../.knowledge-db" ]; then
        KNOWLEDGE_CONTEXT=$("$KB_PYTHON" "$KB_SCRIPTS_DIR/knowledge-search.py" "$FOCUS" --format inject --limit 3 2>/dev/null || echo "")
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

OUTPUT_FILE="$OUTPUT_DIR/$OUTPUT_FILENAME"

# Save as markdown with metadata header
{
    echo "# Quick Review: $FOCUS"
    echo ""
    echo "**Model:** $LITELLM_MODEL"
    echo "**Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Directory:** $WORK_DIR"
    echo ""
    echo "---"
    echo ""
} > "$OUTPUT_FILE"

# Handle both regular and thinking models
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')
[ -z "$CONTENT" ] && CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.reasoning_content // empty')
[ -z "$CONTENT" ] && { echo "ERROR: No response"; echo "$RESPONSE"; exit 1; }

# Append content to markdown file
echo "$CONTENT" >> "$OUTPUT_FILE"

echo ""
echo "$CONTENT"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════"

# Log review complete
REVIEW_END_MS=$(($(date +%s%N)/1000000))
REVIEW_DURATION_MS=$((REVIEW_END_MS - REVIEW_START_MS))
type log_debug &>/dev/null && log_debug "review" "quick_complete" "model=$LITELLM_MODEL" "output=$OUTPUT_FILE"
type log_review_end &>/dev/null && log_review_end "quickReview" "$LITELLM_MODEL" "$OUTPUT_FILE" "success" "$REVIEW_DURATION_MS"

# Auto-extract facts from review (Tier 1)
"$KB_SCRIPTS_DIR/fact-extract.sh" "$CONTENT" "review" "$FOCUS" "$WORK_DIR"
