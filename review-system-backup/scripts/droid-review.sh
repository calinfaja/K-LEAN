#!/usr/bin/env bash
# Factory Droid review script - fast agentic code review
# Usage: droid-review.sh "[model] [focus]" [working_dir]
#
# Uses custom droids (subagents) for thorough file-based analysis

set -e

ARGS="$1"
WORKDIR="${2:-$(pwd)}"

# Parse arguments: first word is model, rest is focus
MODEL=$(echo "$ARGS" | awk '{print $1}')
FOCUS=$(echo "$ARGS" | cut -d' ' -f2-)

# Default model if not specified
if [ -z "$MODEL" ] || [ "$MODEL" = "$FOCUS" ]; then
    MODEL="qwen3-coder"
    FOCUS="$ARGS"
fi

# Default focus if not specified
if [ -z "$FOCUS" ]; then
    FOCUS="Review this codebase for bugs, security issues, and code quality"
fi

# Validate model exists in config (use dynamic discovery)
VALID_MODELS=$(~/.claude/scripts/get-models.sh 2>/dev/null | tr '\n' ' ')
if [ -z "$VALID_MODELS" ]; then
    # Fallback to known models if LiteLLM not running
    VALID_MODELS="qwen3-coder deepseek-v3-thinking glm-4.6-thinking minimax-m2 kimi-k2-thinking hermes-4-70b"
fi

if ! echo "$VALID_MODELS" | grep -qw "$MODEL"; then
    echo "ERROR: Invalid model '$MODEL'"
    echo "Available models: $VALID_MODELS"
    exit 1
fi

# Check if FACTORY_API_KEY is set
if [ -z "$FACTORY_API_KEY" ]; then
    source ~/.bashrc 2>/dev/null || true
    source ~/.profile 2>/dev/null || true
fi

if [ -z "$FACTORY_API_KEY" ]; then
    echo "ERROR: FACTORY_API_KEY not set"
    echo "Run: export FACTORY_API_KEY=fk-YOUR_KEY"
    exit 1
fi

echo "=== Factory Droid Review ==="
echo "Model: $MODEL"
echo "Focus: $FOCUS"
echo "Working directory: $WORKDIR"
echo "============================"
echo ""

# Create review prompt that forces tool usage
REVIEW_PROMPT="You are reviewing code in: $WORKDIR

IMPORTANT: You MUST use your tools to examine the actual files before providing feedback.

## Required Steps:
1. Use Glob to find relevant files (e.g., '**/*.sh' for shell scripts)
2. Use Read to examine each file's actual content
3. Use Grep to search for specific patterns if needed

## Review Focus:
$FOCUS

## Output Requirements:
- Provide specific file:line references for ALL findings
- Grade the code A-F with detailed justification
- List concrete issues found with severity (CRITICAL/WARNING/SUGGESTION)

DO NOT provide generic feedback. Read the files first, then provide specific analysis."

# Determine reasoning effort based on model type
REASONING_EFFORT="low"
if echo "$MODEL" | grep -q "thinking"; then
    REASONING_EFFORT="medium"
fi

echo "Autonomy: medium | Reasoning: $REASONING_EFFORT"
echo ""

# Setup auto-save to project .claude folder
CLAUDE_DIR="$WORKDIR/.claude"
REVIEWS_DIR="$CLAUDE_DIR/reviews"
DROID_OUTPUTS_DIR="$CLAUDE_DIR/droid-outputs/$MODEL"

# Create directory structure if it doesn't exist
mkdir -p "$REVIEWS_DIR/by-date" "$REVIEWS_DIR/by-model" "$REVIEWS_DIR/by-focus"
mkdir -p "$DROID_OUTPUTS_DIR"

# Create timestamp and filename
TIMESTAMP=$(date +%s)
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H-%M-%S)
FOCUS_SLUG=$(echo "$FOCUS" | tr ' ' '_' | tr -cd '[:alnum:]_-' | cut -c1-30)
FILENAME="${TIME}_${MODEL}_${FOCUS_SLUG}.md"

# Paths for saving
BY_DATE_PATH="$REVIEWS_DIR/by-date/$DATE"
BY_MODEL_PATH="$REVIEWS_DIR/by-model/$MODEL"
BY_FOCUS_PATH="$REVIEWS_DIR/by-focus/$FOCUS_SLUG"
DROID_OUTPUT_PATH="$DROID_OUTPUTS_DIR/$FILENAME"

# Create subdirectories
mkdir -p "$BY_DATE_PATH" "$BY_MODEL_PATH" "$BY_FOCUS_PATH"

# Run droid in exec mode with the review prompt
# --auto medium: Required for tool usage (file reads, reversible commands)
# -r: Reasoning effort based on model type
# Capture output to file
cd "$WORKDIR"
{
    echo "# Droid Review Report"
    echo ""
    echo "**Generated**: $DATE $TIME"
    echo "**Model**: $MODEL"
    echo "**Focus**: $FOCUS"
    echo "**Directory**: $WORKDIR"
    echo ""
    echo "---"
    echo ""
    droid exec --auto medium -r "$REASONING_EFFORT" --model "custom:$MODEL" "$REVIEW_PROMPT" 2>&1
} | tee "$DROID_OUTPUT_PATH"

# Create symlinks for cross-reference organization
ln -sf "../../droid-outputs/$MODEL/$FILENAME" "$BY_DATE_PATH/$FILENAME" 2>/dev/null || true
ln -sf "../../droid-outputs/$MODEL/$FILENAME" "$BY_MODEL_PATH/$FILENAME" 2>/dev/null || true
ln -sf "../../droid-outputs/$MODEL/$FILENAME" "$BY_FOCUS_PATH/$FILENAME" 2>/dev/null || true

# Create/update review index
INDEX_FILE="$REVIEWS_DIR/INDEX.md"
{
    echo "# Droid Reviews Index"
    echo ""
    echo "**Last Updated**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "## Summary"
    echo "- **Total Reviews**: $(find "$DROID_OUTPUTS_DIR" -name "*.md" 2>/dev/null | wc -l)"
    echo "- **By Model**: $(ls -1 "$REVIEWS_DIR/by-model" 2>/dev/null | wc -l)"
    echo "- **By Focus**: $(ls -1 "$REVIEWS_DIR/by-focus" 2>/dev/null | wc -l)"
    echo ""
    echo "## Latest Reviews"
    echo ""
    find "$DROID_OUTPUTS_DIR" -name "*.md" -type f 2>/dev/null | sort -r | head -10 | while read -r review; do
        rel_path=$(echo "$review" | sed "s|$DROID_OUTPUTS_DIR/||")
        mtime=$(stat -c %y "$review" 2>/dev/null | cut -d' ' -f1)
        echo "- \`$rel_path\` ($mtime)"
    done
} > "$INDEX_FILE"

# Emit knowledge event
if command -v ~/.claude/scripts/knowledge-events.py &>/dev/null; then
    ~/.claude/scripts/knowledge-events.py emit "knowledge:droid_review" \
        --model "$MODEL" \
        --focus "$FOCUS" \
        --path "$DROID_OUTPUT_PATH" \
        --timestamp "$TIMESTAMP" 2>/dev/null || true
fi

echo ""
echo "=== Review Saved ==="
echo "Location: $DROID_OUTPUT_PATH"
echo "Index: $INDEX_FILE"
