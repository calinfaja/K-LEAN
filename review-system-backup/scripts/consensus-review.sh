#!/bin/bash
#
# Consensus Review - 3 models in parallel with health check
# Skips unhealthy models, runs what's available
#
# Usage: consensus-review.sh "<focus>" [working_dir]
#

FOCUS="${1:-General code review}"
WORK_DIR="${2:-$(pwd)}"

# Session-based output directory (each Claude instance gets its own folder)
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR="$SESSION_DIR"
TIME_STAMP=$(date +%H%M%S)

# Health check
check_model_health() {
    local resp=$(curl -s --max-time 5 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$1\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)
    echo "$resp" | jq -e '.choices[0]' > /dev/null 2>&1
}

# Check proxy
curl -s --max-time 3 http://localhost:4000/health > /dev/null 2>&1 || { echo "ERROR: LiteLLM not running"; exit 1; }

echo "═══════════════════════════════════════════════════════════════"
echo "CONSENSUS REVIEW - Checking model health..."
echo "═══════════════════════════════════════════════════════════════"

# Check which models are healthy
HEALTHY_MODELS=""
for model in coding-qwen architecture-deepseek tools-glm; do
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

DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)
[ -z "$DIFF" ] && DIFF=$(git diff 2>/dev/null | head -300)
[ -z "$DIFF" ] && DIFF="No git changes found."

PROMPT="Review this code for: $FOCUS

CODE:
$DIFF

Provide: Grade (A-F), Risk, Top 3 Issues, Verdict"

echo "Starting parallel reviews..."

# Launch healthy models in parallel
PIDS=""

if echo "$HEALTHY_MODELS" | grep -q "coding-qwen"; then
    curl -s --max-time 60 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"coding-qwen\", \"messages\": [{\"role\": \"system\", \"content\": \"Code reviewer: bugs, memory safety.\"}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$OUTPUT_DIR/consensus-qwen-$TIME_STAMP.json" &
    PID_QWEN=$!
    PIDS="$PIDS $PID_QWEN"
fi

if echo "$HEALTHY_MODELS" | grep -q "architecture-deepseek"; then
    curl -s --max-time 60 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"architecture-deepseek\", \"messages\": [{\"role\": \"system\", \"content\": \"Architect: design, coupling.\"}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$OUTPUT_DIR/consensus-deepseek-$TIME_STAMP.json" &
    PID_DEEPSEEK=$!
    PIDS="$PIDS $PID_DEEPSEEK"
fi

if echo "$HEALTHY_MODELS" | grep -q "tools-glm"; then
    curl -s --max-time 60 http://localhost:4000/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"tools-glm\", \"messages\": [{\"role\": \"system\", \"content\": \"Compliance: MISRA, standards.\"}, {\"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .)}], \"temperature\": 0.3, \"max_tokens\": 1500}" \
      > "$OUTPUT_DIR/consensus-glm-$TIME_STAMP.json" &
    PID_GLM=$!
    PIDS="$PIDS $PID_GLM"
fi

# Wait for all
for pid in $PIDS; do
    wait $pid
done

# Display results for healthy models only
# Helper to extract content from regular or thinking models
get_response() {
    jq -r '.choices[0].message.content // .choices[0].message.reasoning_content // "No response"' "$1"
}

if [ -f "$OUTPUT_DIR/consensus-qwen-$TIME_STAMP.json" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "QWEN (Code Quality)"
    echo "═══════════════════════════════════════════════════════════════"
    get_response "$OUTPUT_DIR/consensus-qwen-$TIME_STAMP.json"
fi

if [ -f "$OUTPUT_DIR/consensus-deepseek-$TIME_STAMP.json" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "DEEPSEEK (Architecture)"
    echo "═══════════════════════════════════════════════════════════════"
    get_response "$OUTPUT_DIR/consensus-deepseek-$TIME_STAMP.json"
fi

if [ -f "$OUTPUT_DIR/consensus-glm-$TIME_STAMP.json" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "GLM (Standards)"
    echo "═══════════════════════════════════════════════════════════════"
    get_response "$OUTPUT_DIR/consensus-glm-$TIME_STAMP.json"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Results saved to: $OUTPUT_DIR/consensus-*-$TIME_STAMP.json"
echo "═══════════════════════════════════════════════════════════════"
