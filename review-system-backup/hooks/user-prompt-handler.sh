#!/bin/bash
#
# K-LEAN UserPromptSubmit Hook Handler
# Intercepts user prompts and dispatches to appropriate handlers
#
# Keywords handled:
#   - healthcheck         → Run health check on all 6 models
#   - GoodJob <url>       → Capture URL to knowledge DB
#   - SaveThis <lesson>   → Save lesson learned directly (no AI eval)
#   - SaveInfo <content>  → Smart save with AI relevance evaluation
#   - FindKnowledge <q>   → Search knowledge DB
#   - asyncDeepReview     → 3 models with tools (background)
#   - asyncConsensus      → 3 models quick review (background)
#   - asyncReview         → Single model quick review (background)
#

# Read JSON input from stdin
INPUT=$(cat)

# Extract the user prompt from the hook input
# The prompt comes in different fields depending on context
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // .message // .content // ""' 2>/dev/null)

# If empty, try alternate extraction
if [ -z "$USER_PROMPT" ] || [ "$USER_PROMPT" = "null" ]; then
    USER_PROMPT=$(echo "$INPUT" | jq -r 'if type == "string" then . else .user_prompt // "" end' 2>/dev/null)
fi

# Exit silently if no prompt found
if [ -z "$USER_PROMPT" ] || [ "$USER_PROMPT" = "null" ]; then
    exit 0
fi

# Get project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SCRIPTS_DIR="$HOME/.claude/scripts"
REVIEWS_DIR="/tmp/claude-reviews"
mkdir -p "$REVIEWS_DIR"

# Session ID for output files
SESSION_ID=$(date +%Y%m%d-%H%M%S)

#------------------------------------------------------------------------------
# HEALTHCHECK
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^healthcheck$\|^health check$\|^health-check$"; then
    echo "🏥 Running health check on all models..." >&2

    if [ -x "$SCRIPTS_DIR/health-check.sh" ]; then
        RESULT=$("$SCRIPTS_DIR/health-check.sh" 2>&1)

        # Output as system message
        echo "{\"systemMessage\": \"Health Check Results:\\n$RESULT\"}"
        exit 0
    else
        echo "{\"systemMessage\": \"⚠️ health-check.sh not found at $SCRIPTS_DIR/health-check.sh\"}"
        exit 0
    fi
fi

#------------------------------------------------------------------------------
# GOODJOB <url> [instructions]
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^GoodJob "; then
    # Extract URL and optional instructions
    URL=$(echo "$USER_PROMPT" | sed -E 's/^GoodJob[[:space:]]+([^[:space:]]+).*/\1/i')
    INSTRUCTIONS=$(echo "$USER_PROMPT" | sed -E 's/^GoodJob[[:space:]]+[^[:space:]]+[[:space:]]*(.*)/\1/i')

    if [ -z "$URL" ] || [ "$URL" = "$USER_PROMPT" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: GoodJob <url> [instructions]\"}"
        exit 0
    fi

    echo "📥 Capturing URL to knowledge DB: $URL" >&2

    if [ -x "$SCRIPTS_DIR/goodjob-dispatch.sh" ]; then
        RESULT=$("$SCRIPTS_DIR/goodjob-dispatch.sh" "$URL" "$INSTRUCTIONS" "$PROJECT_DIR" 2>&1)
        echo "{\"systemMessage\": \"$RESULT\"}"
    else
        echo "{\"systemMessage\": \"⚠️ goodjob-dispatch.sh not found\"}"
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# SAVETHIS <lesson> - Direct save (no AI evaluation)
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^SaveThis "; then
    # Extract the lesson
    LESSON=$(echo "$USER_PROMPT" | sed -E 's/^SaveThis[[:space:]]+//i')

    if [ -z "$LESSON" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: SaveThis <lesson learned>\"}"
        exit 0
    fi

    echo "💾 Saving lesson to knowledge DB..." >&2

    # Create knowledge entry
    ENTRY=$(cat <<EOF
{
  "title": "Lesson Learned",
  "summary": "$LESSON",
  "type": "lesson",
  "source": "manual",
  "found_date": "$(date -Iseconds)",
  "relevance_score": 0.9,
  "key_concepts": ["lesson", "learned", "tip"]
}
EOF
)

    # Append to knowledge DB
    KNOWLEDGE_DIR="$PROJECT_DIR/.knowledge-db"
    mkdir -p "$KNOWLEDGE_DIR"
    echo "$ENTRY" >> "$KNOWLEDGE_DIR/entries.jsonl"

    echo "{\"systemMessage\": \"✅ Lesson saved to knowledge DB\"}"
    exit 0
fi

#------------------------------------------------------------------------------
# SAVEINFO <content> - Smart save with AI relevance evaluation
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^SaveInfo "; then
    # Extract the content
    CONTENT=$(echo "$USER_PROMPT" | sed -E 's/^SaveInfo[[:space:]]+//i')

    if [ -z "$CONTENT" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: SaveInfo <content to evaluate and save>\"}"
        exit 0
    fi

    echo "🤖 Evaluating content for knowledge capture..." >&2

    if [ -x "$SCRIPTS_DIR/smart-capture.sh" ]; then
        # Run smart capture (uses Haiku to evaluate relevance)
        "$SCRIPTS_DIR/smart-capture.sh" "$CONTENT" "$PROJECT_DIR" &

        echo "{\"systemMessage\": \"🤖 Evaluating content with AI...\\nIf relevant (score ≥ 0.7), it will be saved automatically.\\nCheck timeline: ~/.claude/scripts/timeline-query.sh today\"}"
    else
        echo "{\"systemMessage\": \"⚠️ smart-capture.sh not found at $SCRIPTS_DIR\"}"
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# FINDKNOWLEDGE <query> - Now uses hybrid search (Phase 2)
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^FindKnowledge "; then
    # Extract the query
    QUERY=$(echo "$USER_PROMPT" | sed -E 's/^FindKnowledge[[:space:]]+//i')

    if [ -z "$QUERY" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: FindKnowledge <query>\"}"
        exit 0
    fi

    echo "🔍 Searching knowledge DB with hybrid search: $QUERY" >&2

    # PHASE 2: Use hybrid search (semantic + keyword + tag)
    if [ -x "$SCRIPTS_DIR/knowledge-hybrid-search.py" ]; then
        # Use hybrid search engine (semantic + keyword + tag fallback)
        RESULT=$(/home/calin/.venvs/knowledge-db/bin/python "$SCRIPTS_DIR/knowledge-hybrid-search.py" "$QUERY" --strategy hybrid --verbose 2>&1)

        # Emit search event (Phase 4)
        if [ -x "$SCRIPTS_DIR/knowledge-events.py" ]; then
            /home/calin/.venvs/knowledge-db/bin/python "$SCRIPTS_DIR/knowledge-events.py" emit "knowledge:search" "{\"query\": \"$QUERY\", \"strategy\": \"hybrid\"}" 2>/dev/null &
        fi

        # Escape for JSON
        RESULT_ESCAPED=$(echo "$RESULT" | jq -Rs .)
        echo "{\"systemMessage\": $RESULT_ESCAPED}"
    elif [ -x "$SCRIPTS_DIR/knowledge-query.sh" ]; then
        # Fallback to old search
        RESULT=$("$SCRIPTS_DIR/knowledge-query.sh" "$QUERY" 2>&1)
        RESULT_ESCAPED=$(echo "$RESULT" | jq -Rs .)
        echo "{\"systemMessage\": $RESULT_ESCAPED}"
    else
        # Fallback to direct search
        KNOWLEDGE_DIR="$PROJECT_DIR/.knowledge-db"
        if [ -f "$KNOWLEDGE_DIR/entries.jsonl" ]; then
            RESULT=$(grep -i "$QUERY" "$KNOWLEDGE_DIR/entries.jsonl" | head -5)
            if [ -n "$RESULT" ]; then
                echo "{\"systemMessage\": \"Found entries:\\n$RESULT\"}"
            else
                echo "{\"systemMessage\": \"No entries found for: $QUERY\"}"
            fi
        else
            echo "{\"systemMessage\": \"Knowledge DB not found at $KNOWLEDGE_DIR\"}"
        fi
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# ASYNCDEEPREVIEW <focus>
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^asyncDeepReview\|^async.*deep.*review"; then
    # Extract focus
    FOCUS=$(echo "$USER_PROMPT" | sed -E 's/^(asyncDeepReview|async[[:space:]]*deep[[:space:]]*review)[[:space:]]*//i')

    if [ -z "$FOCUS" ]; then
        FOCUS="General code review"
    fi

    echo "🚀 Starting async deep review: $FOCUS" >&2

    if [ -x "$SCRIPTS_DIR/parallel-deep-review.sh" ]; then
        LOG_FILE="$REVIEWS_DIR/deep-review-$SESSION_ID.log"
        nohup "$SCRIPTS_DIR/parallel-deep-review.sh" "$FOCUS" "$PROJECT_DIR" > "$LOG_FILE" 2>&1 &

        echo "{\"systemMessage\": \"🚀 Deep review started in background\\n📁 Focus: $FOCUS\\n📋 Log: $LOG_FILE\"}"
    else
        echo "{\"systemMessage\": \"⚠️ parallel-deep-review.sh not found\"}"
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# ASYNCCONSENSUS <focus>
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^asyncConsensus\|^async.*consensus"; then
    # Extract focus
    FOCUS=$(echo "$USER_PROMPT" | sed -E 's/^(asyncConsensus|async[[:space:]]*consensus)[[:space:]]*//i')

    if [ -z "$FOCUS" ]; then
        FOCUS="General code review"
    fi

    echo "🚀 Starting async consensus review: $FOCUS" >&2

    if [ -x "$SCRIPTS_DIR/consensus-review.sh" ]; then
        LOG_FILE="$REVIEWS_DIR/consensus-$SESSION_ID.log"
        nohup "$SCRIPTS_DIR/consensus-review.sh" "$FOCUS" > "$LOG_FILE" 2>&1 &

        echo "{\"systemMessage\": \"🚀 Consensus review started (3 models)\\n📁 Focus: $FOCUS\\n📋 Log: $LOG_FILE\"}"
    else
        echo "{\"systemMessage\": \"⚠️ consensus-review.sh not found\"}"
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# ASYNCREVIEW <model> <focus>
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^asyncReview "; then
    # Extract model and focus
    MODEL=$(echo "$USER_PROMPT" | sed -E 's/^asyncReview[[:space:]]+([^[:space:]]+).*/\1/i')
    FOCUS=$(echo "$USER_PROMPT" | sed -E 's/^asyncReview[[:space:]]+[^[:space:]]+[[:space:]]*(.*)/\1/i')

    if [ -z "$MODEL" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: asyncReview <model> <focus>\\nModels: qwen, deepseek, glm, minimax, kimi, hermes\"}"
        exit 0
    fi

    if [ -z "$FOCUS" ]; then
        FOCUS="General code review"
    fi

    echo "🚀 Starting async review with $MODEL: $FOCUS" >&2

    if [ -x "$SCRIPTS_DIR/quick-review.sh" ]; then
        LOG_FILE="$REVIEWS_DIR/review-$MODEL-$SESSION_ID.log"
        nohup "$SCRIPTS_DIR/quick-review.sh" "$MODEL" "$FOCUS" > "$LOG_FILE" 2>&1 &

        echo "{\"systemMessage\": \"🚀 Review started with $MODEL\\n📁 Focus: $FOCUS\\n📋 Log: $LOG_FILE\"}"
    else
        echo "{\"systemMessage\": \"⚠️ quick-review.sh not found\"}"
    fi
    exit 0
fi

# No keyword matched - let prompt continue normally
exit 0
