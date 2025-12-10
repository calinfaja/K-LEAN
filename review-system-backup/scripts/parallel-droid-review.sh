#!/bin/bash
# Parallel Factory Droid review - runs 3 models simultaneously
# Usage: parallel-droid-review.sh "[focus]" [working_dir]

set -e

FOCUS="${1:-Comprehensive code review for bugs, security, architecture, and best practices}"
WORKDIR="${2:-$(pwd)}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/tmp/droid-audit-$TIMESTAMP"

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

# Create output directory
mkdir -p "$OUTPUT_DIR"

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

if [ $FAILED -gt 0 ]; then
    echo ""
    echo "WARNING: $FAILED model(s) failed"
    exit 1
fi
