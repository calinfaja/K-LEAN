#!/usr/bin/env bash
#
# Async Review Dispatcher
# Intercepts user prompts, runs reviews in background, BLOCKS the prompt
# so Claude doesn't try to respond to it - user can immediately continue coding
#

# Source kb-root.sh for unified paths
SCRIPT_DIR="$(dirname "$0")"
if [ -f "$SCRIPT_DIR/kb-root.sh" ]; then
    source "$SCRIPT_DIR/kb-root.sh"
else
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
    KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
fi

# Session-based output directory
source "$KB_SCRIPTS_DIR/session-helper.sh"
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

# Auto-initialize knowledge-db for this project (runs once, silent if exists)
"$KB_SCRIPTS_DIR/kb-init.sh" "$WORK_DIR" > /dev/null 2>&1 &

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
    for model in qwen3-coder deepseek-v3-thinking glm-4.6-thinking minimax-m2 kimi-k2-thinking hermes-4-70b; do
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
if echo "$PROMPT" | grep -qi "asyncDeepAudit\|asyncQuickCompare\|asyncQuickReview\|asyncQuickConsult"; then
    if ! check_proxy_health; then
        block_with_message "❌ LiteLLM proxy not running. Start it first: start-nano-proxy"
    fi
fi

# asyncDeepAudit - 3 models with full tools (CLI)
if echo "$PROMPT" | grep -qi "asyncDeepAudit"; then
    FOCUS=$(echo "$PROMPT" | sed 's/.*asyncDeepAudit[[:space:]]*//')
    [ -z "$FOCUS" ] && FOCUS="General code review"
    nohup "$KB_SCRIPTS_DIR/parallel-deep-review.sh" "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/deep-audit-latest.log" 2>&1 &
    block_with_message "🚀 Deep audit started (3 models, CLI). Results: $OUTPUT_DIR/deep-audit-latest.log"
fi

# asyncQuickCompare - 3 models via curl (API)
if echo "$PROMPT" | grep -qi "asyncQuickCompare"; then
    FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickCompare[[:space:]]*//')
    [ -z "$FOCUS" ] && FOCUS="General code review"
    nohup "$KB_SCRIPTS_DIR/consensus-review.sh" "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-compare-latest.log" 2>&1 &
    block_with_message "🚀 Quick compare started (3 models, API). Results: $OUTPUT_DIR/quick-compare-latest.log"
fi

# asyncQuickReview with model (API)
if echo "$PROMPT" | grep -qi "asyncQuickReview"; then
    if echo "$PROMPT" | grep -qi "qwen"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickReview[[:space:]]*qwen[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="General review"
        nohup "$KB_SCRIPTS_DIR/quick-review.sh" qwen "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-review-qwen-latest.log" 2>&1 &
        block_with_message "🚀 Quick review started (qwen, API). Results: $OUTPUT_DIR/quick-review-qwen-latest.log"
    elif echo "$PROMPT" | grep -qi "deepseek"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickReview[[:space:]]*deepseek[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="General review"
        nohup "$KB_SCRIPTS_DIR/quick-review.sh" deepseek "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-review-deepseek-latest.log" 2>&1 &
        block_with_message "🚀 Quick review started (deepseek, API). Results: $OUTPUT_DIR/quick-review-deepseek-latest.log"
    elif echo "$PROMPT" | grep -qi "glm"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickReview[[:space:]]*glm[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="General review"
        nohup "$KB_SCRIPTS_DIR/quick-review.sh" glm "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-review-glm-latest.log" 2>&1 &
        block_with_message "🚀 Quick review started (glm, API). Results: $OUTPUT_DIR/quick-review-glm-latest.log"
    fi
fi

# asyncQuickConsult with model (API)
if echo "$PROMPT" | grep -qi "asyncQuickConsult"; then
    if echo "$PROMPT" | grep -qi "qwen"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickConsult[[:space:]]*qwen[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="Is this implementation correct?"
        nohup "$KB_SCRIPTS_DIR/second-opinion.sh" qwen "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-consult-qwen-latest.log" 2>&1 &
        block_with_message "🚀 Quick consult started (qwen, API). Results: $OUTPUT_DIR/quick-consult-qwen-latest.log"
    elif echo "$PROMPT" | grep -qi "deepseek"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickConsult[[:space:]]*deepseek[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="Is this implementation correct?"
        nohup "$KB_SCRIPTS_DIR/second-opinion.sh" deepseek "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-consult-deepseek-latest.log" 2>&1 &
        block_with_message "🚀 Quick consult started (deepseek, API). Results: $OUTPUT_DIR/quick-consult-deepseek-latest.log"
    elif echo "$PROMPT" | grep -qi "glm"; then
        FOCUS=$(echo "$PROMPT" | sed 's/.*asyncQuickConsult[[:space:]]*glm[[:space:]]*//')
        [ -z "$FOCUS" ] && FOCUS="Is this implementation correct?"
        nohup "$KB_SCRIPTS_DIR/second-opinion.sh" glm "$FOCUS" "$WORK_DIR" > "$OUTPUT_DIR/quick-consult-glm-latest.log" 2>&1 &
        block_with_message "🚀 Quick consult started (glm, API). Results: $OUTPUT_DIR/quick-consult-glm-latest.log"
    fi
fi

# FindKnowledge - search knowledge base
if echo "$PROMPT" | grep -qi "^findknowledge\|^searchknowledge"; then
    QUERY=$(echo "$PROMPT" | sed -E 's/^(find|search)knowledge[[:space:]]*//i')
    if [ -n "$QUERY" ]; then
        RESULTS=$("$KB_PYTHON" "$KB_SCRIPTS_DIR/knowledge-search.py" "$QUERY" --format inject 2>&1)
        block_with_message "$RESULTS"
    else
        block_with_message "Usage: FindKnowledge <query>"
    fi
fi

# No async keyword found - continue normally (no output, exit 0)
exit 0
