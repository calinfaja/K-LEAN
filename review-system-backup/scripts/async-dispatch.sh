#!/bin/bash
#
# Async Review Dispatcher
# Intercepts user prompts, runs reviews in background, BLOCKS the prompt
# so Claude doesn't try to respond to it - user can immediately continue coding
#

# Session-based output directory
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR="$SESSION_DIR"

# Read JSON input from stdin
INPUT=$(cat)

# Extract the prompt text from JSON
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)

# If no prompt extracted, try raw input
if [ -z "$PROMPT" ]; then
    PROMPT="$INPUT"
fi

# Get working directory
WORK_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Helper function to block prompt and show message
block_with_message() {
    local msg="$1"
    echo "{\"decision\": \"block\", \"reason\": \"$msg\"}"
    exit 0
}

# Quick health check function (use /models - faster than /health)
check_proxy_health() {
    curl -s --max-time 5 http://localhost:4000/models > /dev/null 2>&1
}

# Full model health check
check_all_models() {
    local results=""
    for model in coding-qwen architecture-deepseek tools-glm research-minimax agent-kimi scripting-hermes; do
        local resp=$(curl -s --max-time 10 http://localhost:4000/chat/completions \
            -H "Content-Type: application/json" \
            -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)
        local content=$(echo "$resp" | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content // empty' 2>/dev/null)
        if [ -n "$content" ]; then
            results="$results ✅ $model"
        else
            results="$results ❌ $model"
        fi
    done
    echo "$results"
}

# Health check keyword - run full model check
if echo "$PROMPT" | grep -qi "^healthcheck$\|^health check$\|^checkhealth$"; then
    if ! check_proxy_health; then
        block_with_message "❌ LiteLLM proxy not running on localhost:4000. Run: start-nano-proxy"
    fi
    RESULTS=$(check_all_models)
    block_with_message "Model Health:$RESULTS"
fi

# Pre-check: If any async keyword detected, verify proxy is up first
if echo "$PROMPT" | grep -qi "asyncDeepReview\|asyncConsensus\|asyncReview\|asyncSecondOpinion"; then
    if ! check_proxy_health; then
        block_with_message "❌ LiteLLM proxy not running. Start it first: start-nano-proxy"
    fi
fi

# asyncDeepReview - 3 models with full tools
if echo "$PROMPT" | grep -qi "asyncDeepReview"; then
    FOCUS=$(echo "$PROMPT" | sed 's/.*asyncDeepReview[[:space:]]*//')
    [ -z "$FOCUS" ] && FOCUS="General code review"
    nohup ~/.claude/scripts/parallel-deep-review.sh "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/deep-review-latest.log" 2>&1 &
    block_with_message "🚀 Deep review started (3 models). Results: $OUTPUT_DIR/deep-review-latest.log"
fi

# asyncConsensus - 3 models via curl
if echo "$PROMPT" | grep -qi "asyncConsensus"; then
    FOCUS=$(echo "$PROMPT" | sed 's/.*asyncConsensus[[:space:]]*//')
    [ -z "$FOCUS" ] && FOCUS="General code review"
    nohup ~/.claude/scripts/consensus-review.sh "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/consensus-latest.log" 2>&1 &
    block_with_message "🚀 Consensus review started (3 models). Results: $OUTPUT_DIR/consensus-latest.log"
fi

# asyncReview with model
if echo "$PROMPT" | grep -qi "asyncReview"; then
    if echo "$PROMPT" | grep -qi "qwen"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncReview[[:space:]]*qwen[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="General review"
        nohup ~/.claude/scripts/quick-review.sh qwen "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/review-qwen-latest.log" 2>&1 &
        block_with_message "🚀 Quick review started (qwen). Results: $OUTPUT_DIR/review-qwen-latest.log"
    elif echo "$PROMPT" | grep -qi "deepseek"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncReview[[:space:]]*deepseek[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="General review"
        nohup ~/.claude/scripts/quick-review.sh deepseek "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/review-deepseek-latest.log" 2>&1 &
        block_with_message "🚀 Quick review started (deepseek). Results: $OUTPUT_DIR/review-deepseek-latest.log"
    elif echo "$PROMPT" | grep -qi "glm"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncReview[[:space:]]*glm[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="General review"
        nohup ~/.claude/scripts/quick-review.sh glm "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/review-glm-latest.log" 2>&1 &
        block_with_message "🚀 Quick review started (glm). Results: $OUTPUT_DIR/review-glm-latest.log"
    fi
fi

# asyncSecondOpinion with model
if echo "$PROMPT" | grep -qi "asyncSecondOpinion"; then
    if echo "$PROMPT" | grep -qi "qwen"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncSecondOpinion[[:space:]]*qwen[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="Is this implementation correct?"
        nohup ~/.claude/scripts/second-opinion.sh qwen "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/opinion-qwen-latest.log" 2>&1 &
        block_with_message "🚀 Second opinion started (qwen). Results: $OUTPUT_DIR/opinion-qwen-latest.log"
    elif echo "$PROMPT" | grep -qi "deepseek"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncSecondOpinion[[:space:]]*deepseek[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="Is this implementation correct?"
        nohup ~/.claude/scripts/second-opinion.sh deepseek "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/opinion-deepseek-latest.log" 2>&1 &
        block_with_message "🚀 Second opinion started (deepseek). Results: $OUTPUT_DIR/opinion-deepseek-latest.log"
    elif echo "$PROMPT" | grep -qi "glm"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncSecondOpinion[[:space:]]*glm[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="Is this implementation correct?"
        nohup ~/.claude/scripts/second-opinion.sh glm "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/opinion-glm-latest.log" 2>&1 &
        block_with_message "🚀 Second opinion started (glm). Results: $OUTPUT_DIR/opinion-glm-latest.log"
    fi
fi

# No async keyword found - continue normally (no output, exit 0)
exit 0
