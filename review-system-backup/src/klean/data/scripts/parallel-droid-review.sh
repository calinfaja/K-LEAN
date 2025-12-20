#!/usr/bin/env bash
# Parallel Factory Droid review - runs 3 models simultaneously
# Usage: parallel-droid-review.sh "[focus]" [working_dir]

set -e

SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/../lib/common.sh" 2>/dev/null || true

FOCUS="${1:-Comprehensive code review for bugs, security, architecture, and best practices}"
WORKDIR="${2:-$(pwd)}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Setup project-specific .claude folder for persistent storage
CLAUDE_DIR="$WORKDIR/.claude"
PROJECT_OUTPUT_DIR="$CLAUDE_DIR/droid-outputs/parallel-reviews/$TIMESTAMP"
REVIEWS_DIR="$CLAUDE_DIR/reviews"

# Fallback to /tmp if .claude not writable
OUTPUT_DIR="$PROJECT_OUTPUT_DIR"
if ! mkdir -p "$OUTPUT_DIR" 2>/dev/null; then
    OUTPUT_DIR="/tmp/droid-audit-$TIMESTAMP"
    mkdir -p "$OUTPUT_DIR"
    echo "Warning: Using temp directory: $OUTPUT_DIR"
fi

# Create review structure
mkdir -p "$REVIEWS_DIR/by-date" "$REVIEWS_DIR/by-model" "$REVIEWS_DIR/by-focus"

# Get models dynamically from LiteLLM (first 3 healthy)
HEALTHY_MODELS=$(~/.claude/scripts/get-healthy-models.sh 3 2>/dev/null)
if [ -z "$HEALTHY_MODELS" ]; then
    # Fallback to known models if LiteLLM not running
    MODELS=("qwen3-coder" "deepseek-v3-thinking" "glm-4.6-thinking")
else
    # Convert newline-separated list to array
    readarray -t MODELS <<< "$HEALTHY_MODELS"
fi

# Check if FACTORY_API_KEY is set
if [ -z "$FACTORY_API_KEY" ]; then
    source ~/.bashrc 2>/dev/null || true
fi

if [ -z "$FACTORY_API_KEY" ]; then
    echo "ERROR: FACTORY_API_KEY not set"
    echo "Run: export FACTORY_API_KEY=fk-YOUR_KEY"
    exit 1
fi

# Log parallel audit start
type log_debug &>/dev/null && log_debug "droid" "parallel_start" "models=${MODELS[*]}" "focus=$FOCUS" "dir=$WORKDIR"

echo "=== Factory Droid Parallel Audit ==="
echo "Focus: $FOCUS"
echo "Working directory: $WORKDIR"
echo "Models: ${MODELS[*]}"
echo "Output: $OUTPUT_DIR"
echo "====================================="
echo ""

# Launch all droids in parallel
declare -A PIDS
cd "$WORKDIR"

for model in "${MODELS[@]}"; do
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    OUTPUT_FILE="$OUTPUT_DIR/$SAFE_NAME.md"

    echo "Starting $model..."
    (
        echo "# $model Review" > "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "**Focus:** $FOCUS" >> "$OUTPUT_FILE"
        echo "**Time:** $(date)" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "---" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"

        # Create review prompt that forces tool usage
        REVIEW_PROMPT="You are reviewing code in: $WORKDIR

IMPORTANT: You MUST use your tools to examine the actual files before providing feedback.

## Required Steps:
1. Use Glob to find relevant files
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
        REASONING="low"
        if echo "$model" | grep -q "thinking"; then
            REASONING="medium"
        fi

        # --auto medium: Required for tool usage
        # -r: Set reasoning based on model type
        droid exec --auto medium -r "$REASONING" --model "custom:$model" "$REVIEW_PROMPT" >> "$OUTPUT_FILE" 2>&1

        echo "" >> "$OUTPUT_FILE"
        echo "---" >> "$OUTPUT_FILE"
        echo "*Completed at $(date)*" >> "$OUTPUT_FILE"
    ) &
    PIDS[$model]=$!
done

echo ""
echo "Waiting for all droids to complete..."
echo ""

# Wait for all to complete and report status
FAILED=0
for model in "${!PIDS[@]}"; do
    pid=${PIDS[$model]}
    if wait $pid; then
        echo "✓ $model completed"
    else
        echo "✗ $model failed"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=== Results ==="

# Display combined results
for model in "${MODELS[@]}"; do
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    OUTPUT_FILE="$OUTPUT_DIR/$SAFE_NAME.md"

    if [ -f "$OUTPUT_FILE" ]; then
        echo ""
        echo "============================================"
        cat "$OUTPUT_FILE"
    fi
done

echo ""
echo "=== Summary ==="
echo "Output files saved to: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"

# Create symlinks from review structure for easy discovery
DATE=$(date +%Y-%m-%d)
FOCUS_SLUG=$(echo "$FOCUS" | tr ' ' '_' | tr -cd '[:alnum:]_-' | cut -c1-30)
BY_DATE_DIR="$REVIEWS_DIR/by-date/$DATE"
BY_FOCUS_DIR="$REVIEWS_DIR/by-focus/$FOCUS_SLUG"

mkdir -p "$BY_DATE_DIR" "$BY_FOCUS_DIR"

# Create symlinks for each model's output
for model in "${MODELS[@]}"; do
    SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
    SOURCE_FILE="$OUTPUT_DIR/$SAFE_NAME.md"

    if [ -f "$SOURCE_FILE" ]; then
        # Create symlinks in index directories
        ln -sf "../../../droid-outputs/parallel-reviews/$TIMESTAMP/$SAFE_NAME.md" "$BY_DATE_DIR/${SAFE_NAME}.md" 2>/dev/null || true
        ln -sf "../../../droid-outputs/parallel-reviews/$TIMESTAMP/$SAFE_NAME.md" "$BY_FOCUS_DIR/${SAFE_NAME}.md" 2>/dev/null || true
        ln -sf "../../../droid-outputs/parallel-reviews/$TIMESTAMP/$SAFE_NAME.md" "$REVIEWS_DIR/by-model/$model/$SAFE_NAME.md" 2>/dev/null || true
    fi
done

# Create master index for this parallel run
PARALLEL_INDEX="$OUTPUT_DIR/INDEX.md"
{
    echo "# Parallel Droid Audit Report"
    echo ""
    echo "**Date**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Focus**: $FOCUS"
    echo "**Directory**: $WORKDIR"
    echo ""
    echo "## Models Reviewed"
    echo ""
    for model in "${MODELS[@]}"; do
        echo "- **$model**"
    done
    echo ""
    echo "## Results"
    echo ""
    for model in "${MODELS[@]}"; do
        echo "### $model"
        SAFE_NAME=$(echo "$model" | tr -cd '[:alnum:]-_')
        OUTPUT_FILE="$OUTPUT_DIR/$SAFE_NAME.md"
        if [ -f "$OUTPUT_FILE" ]; then
            echo "\`\`\`"
            head -20 "$OUTPUT_FILE"
            echo "... (see full report for details)"
            echo "\`\`\`"
            echo ""
        fi
    done
} > "$PARALLEL_INDEX"

# Emit knowledge event
if command -v ~/.claude/scripts/knowledge-events.py &>/dev/null; then
    ~/.claude/scripts/knowledge-events.py emit "knowledge:parallel_droid_review" \
        --models "${MODELS[*]}" \
        --focus "$FOCUS" \
        --path "$OUTPUT_DIR" \
        --timestamp "$(date +%s)" 2>/dev/null || true
fi

echo ""
echo "=== Auto-Save Details ==="
echo "Project Location: $CLAUDE_DIR"
echo "Reviews stored in: $OUTPUT_DIR"
echo "Master index: $PARALLEL_INDEX"

# Log parallel audit complete
type log_debug &>/dev/null && log_debug "droid" "parallel_complete" "models=${MODELS[*]}" "output=$OUTPUT_DIR" "failed=$FAILED"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "WARNING: $FAILED model(s) failed"
    exit 1
fi
