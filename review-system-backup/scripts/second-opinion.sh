#!/bin/bash
#
# Second Opinion - Single model with full context
# With health check + fallback to next available model
#
# Usage: second-opinion.sh <model> "<question>" [working_dir]
#

MODEL="${1:-qwen}"
QUESTION="${2:-Is this implementation correct?}"
WORK_DIR="${3:-$(pwd)}"

# Session-based output directory (each Claude instance gets its own folder)
source ~/.claude/scripts/session-helper.sh
OUTPUT_DIR="$SESSION_DIR"
TIME_STAMP=$(date +%H%M%S)

# Model priority order for fallback
MODELS_PRIORITY="coding-qwen architecture-deepseek tools-glm"

# Map model aliases to LiteLLM names
get_litellm_model() {
    case "$1" in
        qwen) echo "coding-qwen" ;;
        deepseek) echo "architecture-deepseek" ;;
        glm) echo "tools-glm" ;;
        *) echo "coding-qwen" ;;
    esac
}

# Check if specific model is healthy (quick test call)
check_model_health() {
    local model="$1"
    local response=$(curl -s --max-time 5 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}],
            \"max_tokens\": 5
        }" 2>/dev/null)

    # Check if we got a valid response (has choices)
    if echo "$response" | jq -e '.choices[0]' > /dev/null 2>&1; then
        return 0  # healthy
    else
        return 1  # unhealthy
    fi
}

# Find first healthy model
find_healthy_model() {
    local preferred="$1"

    # Try preferred model first
    if check_model_health "$preferred"; then
        echo "$preferred"
        return 0
    fi

    echo "⚠️  $preferred unhealthy, trying fallback..." >&2

    # Try others in priority order
    for model in $MODELS_PRIORITY; do
        if [ "$model" != "$preferred" ]; then
            if check_model_health "$model"; then
                echo "✓ Falling back to $model" >&2
                echo "$model"
                return 0
            fi
        fi
    done

    echo ""  # No healthy model
    return 1
}

# Check LiteLLM proxy is running
if ! curl -s --max-time 3 http://localhost:4000/models > /dev/null 2>&1; then
    echo "ERROR: LiteLLM proxy not running on localhost:4000"
    echo "Start with: start-nano-proxy"
    exit 1
fi

# Get preferred model and find healthy one
PREFERRED_MODEL=$(get_litellm_model "$MODEL")
LITELLM_MODEL=$(find_healthy_model "$PREFERRED_MODEL")

if [ -z "$LITELLM_MODEL" ]; then
    echo "ERROR: No healthy models available"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "SECOND OPINION - $LITELLM_MODEL"
echo "═══════════════════════════════════════════════════════════════"
echo "Question: $QUESTION"
echo "Directory: $WORK_DIR"
echo "═══════════════════════════════════════════════════════════════"

cd "$WORK_DIR"

# Search knowledge-db for relevant context
KNOWLEDGE_CONTEXT=""
PYTHON="$HOME/.venvs/knowledge-db/bin/python"
if [ -x "$PYTHON" ] && [ -f "$HOME/.claude/scripts/knowledge-search.py" ]; then
    if [ -d ".knowledge-db" ] || [ -d "../.knowledge-db" ]; then
        KNOWLEDGE_CONTEXT=$("$PYTHON" "$HOME/.claude/scripts/knowledge-search.py" "$QUESTION" --format inject --limit 3 2>/dev/null || echo "")
    fi
fi

# Gather context
DIFF=$(git diff HEAD~3..HEAD 2>/dev/null | head -500)
[ -z "$DIFF" ] && DIFF=$(git diff 2>/dev/null | head -500)

FILES=$(git diff --name-only HEAD~3..HEAD 2>/dev/null | head -20)

PROJECT_CONFIG=""
[ -f "CMakeLists.txt" ] && PROJECT_CONFIG=$(head -50 CMakeLists.txt)
[ -f "package.json" ] && PROJECT_CONFIG=$(cat package.json)

CONTEXT="PROJECT CONTEXT:
Modified Files: $FILES

Recent Diff:
$DIFF

Project Config:
$PROJECT_CONFIG

YOUR QUESTION: $QUESTION

Provide your honest, independent assessment. Be specific."

# Build system prompt with optional knowledge context
SYSTEM_PROMPT="You provide independent technical opinions. Be direct and specific."
if [ -n "$KNOWLEDGE_CONTEXT" ] && [ "$KNOWLEDGE_CONTEXT" != "No relevant prior knowledge found." ]; then
    SYSTEM_PROMPT="You provide independent technical opinions. Be direct and specific.

$KNOWLEDGE_CONTEXT

Consider this prior knowledge in your assessment if relevant."
    echo "📚 Found relevant prior knowledge"
fi

# Make the actual request (with timeout)
RESPONSE=$(curl -s --max-time 60 http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$LITELLM_MODEL\",
    \"messages\": [
      {\"role\": \"system\", \"content\": $(echo "$SYSTEM_PROMPT" | jq -Rs .)},
      {\"role\": \"user\", \"content\": $(echo "$CONTEXT" | jq -Rs .)}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 2000
  }")

# Save and display
echo "$RESPONSE" > "$OUTPUT_DIR/opinion-$LITELLM_MODEL-$TIME_STAMP.json"

# Handle both regular and thinking models
CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // empty')
[ -z "$CONTENT" ] && CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.reasoning_content // empty')

if [ -z "$CONTENT" ]; then
    echo ""
    echo "ERROR: No response from model"
    echo "Raw response: $RESPONSE"
else
    echo ""
    echo "$CONTENT"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Result saved to: $OUTPUT_DIR/opinion-$LITELLM_MODEL-$TIME_STAMP.json"
echo "═══════════════════════════════════════════════════════════════"
