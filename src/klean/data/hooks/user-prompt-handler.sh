#!/bin/bash
#
# K-LEAN UserPromptSubmit Hook Handler
# Intercepts user prompts and dispatches to appropriate handlers
#
# Keywords handled:
#   - InitKB              → Initialize knowledge DB for project
#   - SaveThis <lesson>   → Save lesson learned directly (no AI eval)
#   - SaveInfo <url>      → Smart save with LLM evaluation
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

# Get project directory and source kb-root.sh if available
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
if [ -f "$_SCRIPTS_DIR/kb-root.sh" ]; then
    source "$_SCRIPTS_DIR/kb-root.sh"
    SCRIPTS_DIR="$KB_SCRIPTS_DIR"
    PYTHON_BIN="${KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
else
    SCRIPTS_DIR="$_SCRIPTS_DIR"
    PYTHON_BIN="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
fi
REVIEWS_DIR="/tmp/claude-reviews"
mkdir -p "$REVIEWS_DIR"

# Session ID for output files
SESSION_ID=$(date +%Y%m%d-%H%M%S)

#------------------------------------------------------------------------------
# INITKB - Initialize Knowledge DB for project
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^InitKB$\|^InitKB "; then
    echo "🚀 Initializing Knowledge DB..." >&2

    KB_INIT_SCRIPT="$SCRIPTS_DIR/kb-init.sh"

    if [ -x "$KB_INIT_SCRIPT" ]; then
        cd "$PROJECT_DIR"
        RESULT=$("$KB_INIT_SCRIPT" "$PROJECT_DIR" 2>&1)
        EXIT_CODE=$?

        RESULT_ESCAPED=$(echo "$RESULT" | jq -Rs .)
        if [ $EXIT_CODE -eq 0 ]; then
            echo "{\"systemMessage\": $RESULT_ESCAPED}"
        else
            echo "{\"systemMessage\": \"❌ InitKB failed:\\n\"$RESULT_ESCAPED}"
        fi
    else
        echo "{\"systemMessage\": \"⚠️ kb-init.sh not found at $KB_INIT_SCRIPT\"}"
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# SAVETHIS <lesson> [--type TYPE] [--tags TAGS] [--priority LEVEL]
# Direct save using knowledge-capture.py
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^SaveThis "; then
    # Extract the full argument string after SaveThis
    ARGS=$(echo "$USER_PROMPT" | sed -E 's/^SaveThis[[:space:]]+//i')

    if [ -z "$ARGS" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: SaveThis <lesson> [--type TYPE] [--tags TAG1,TAG2] [--priority LEVEL]\\nTypes: lesson, finding, solution, pattern, warning, best-practice\\nPriority: low, medium, high, critical\"}"
        exit 0
    fi

    echo "💾 Saving to knowledge DB..." >&2

    # Use knowledge-capture.py with proper interface
    CAPTURE_SCRIPT="$SCRIPTS_DIR/knowledge-capture.py"

    if [ -f "$CAPTURE_SCRIPT" ] && [ -x "$PYTHON_BIN" ]; then
        # Strip surrounding quotes from user input
        CONTENT=$(echo "$ARGS" | sed 's/^["'"'"']//' | sed 's/["'"'"']$//')
        cd "$PROJECT_DIR"
        RESULT=$($PYTHON_BIN "$CAPTURE_SCRIPT" "$CONTENT" 2>&1)
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            RESULT_ESCAPED=$(echo "$RESULT" | jq -Rs .)
            echo "{\"systemMessage\": $RESULT_ESCAPED}"
        else
            echo "{\"systemMessage\": \"❌ Error: $RESULT\"}"
        fi
    else
        # Fallback to simple append if script not available
        LESSON=$(echo "$ARGS" | sed -E 's/[[:space:]]*--[a-z]+[[:space:]]+[^[:space:]]+//g')
        KNOWLEDGE_DIR="$PROJECT_DIR/.knowledge-db"
        mkdir -p "$KNOWLEDGE_DIR"

        # Build compact JSONL entry (single line, properly escaped)
        ENTRY=$(jq -nc \
            --arg title "Lesson Learned" \
            --arg summary "$LESSON" \
            --arg date "$(date -Iseconds)" \
            '{
                title: $title,
                summary: $summary,
                type: "lesson",
                source: "manual",
                found_date: $date,
                relevance_score: 0.9,
                key_concepts: ["lesson"]
            }')
        echo "$ENTRY" >> "$KNOWLEDGE_DIR/entries.jsonl"
        echo "{\"systemMessage\": \"✅ Lesson saved (fallback mode)\"}"
    fi
    exit 0
fi

#------------------------------------------------------------------------------
# SAVEINFO <url> [--search-context "context"] - Smart save with LLM evaluation
#------------------------------------------------------------------------------
if echo "$USER_PROMPT" | grep -qi "^SaveInfo "; then
    # Extract the URL/content
    CONTENT=$(echo "$USER_PROMPT" | sed -E 's/^SaveInfo[[:space:]]+//i')

    if [ -z "$CONTENT" ]; then
        echo "{\"systemMessage\": \"⚠️ Usage: SaveInfo <url> [--search-context \\\"context\\\"]\\n\\nEvaluates URL content with LiteLLM and saves if relevant.\"}"
        exit 0
    fi

    echo "🤖 Evaluating content with LLM..." >&2

    SMART_CAPTURE="$SCRIPTS_DIR/smart-capture.py"

    if [ -f "$SMART_CAPTURE" ] && [ -x "$PYTHON_BIN" ]; then
        # Check if it's a URL
        if echo "$CONTENT" | grep -q "^https\?://"; then
            # Run smart capture with URL (in background for faster response)
            cd "$PROJECT_DIR"
            RESULT=$($PYTHON_BIN "$SMART_CAPTURE" "$CONTENT" --json 2>&1)

            # Parse result
            if echo "$RESULT" | jq -e '.saved == true' >/dev/null 2>&1; then
                TITLE=$(echo "$RESULT" | jq -r '.title')
                INSIGHT=$(echo "$RESULT" | jq -r '.atomic_insight // ""')
                echo "{\"systemMessage\": \"✅ Saved: $TITLE\\n💡 $INSIGHT\"}"
            elif echo "$RESULT" | jq -e '.saved == false' >/dev/null 2>&1; then
                REASON=$(echo "$RESULT" | jq -r '.reason')
                echo "{\"systemMessage\": \"ℹ️ Not saved: $REASON\"}"
            else
                echo "{\"systemMessage\": \"⚠️ Evaluation result: $RESULT\"}"
            fi
        else
            echo "{\"systemMessage\": \"⚠️ SaveInfo expects a URL. For lessons, use SaveThis instead.\"}"
        fi
    else
        echo "{\"systemMessage\": \"⚠️ smart-capture.py not found or Python not available\"}"
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
    if [ -f "$SCRIPTS_DIR/knowledge-hybrid-search.py" ]; then
        # Use hybrid search engine (semantic + keyword + tag fallback)
        RESULT=$("$PYTHON_BIN" "$SCRIPTS_DIR/knowledge-hybrid-search.py" "$QUERY" --strategy hybrid --verbose 2>&1)

        # Emit search event (Phase 4)
        if [ -f "$SCRIPTS_DIR/knowledge-events.py" ]; then
            "$PYTHON_BIN" "$SCRIPTS_DIR/knowledge-events.py" emit "knowledge:search" "{\"query\": \"$QUERY\", \"strategy\": \"hybrid\"}" 2>/dev/null &
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
        PID=$!
        sleep 0.1
        if kill -0 $PID 2>/dev/null; then
            echo "{\"systemMessage\": \"🚀 Deep review started (PID: $PID)\\n📁 Focus: $FOCUS\\n📋 Log: $LOG_FILE\"}"
        else
            echo "{\"systemMessage\": \"❌ Deep review failed to start. Check: $LOG_FILE\"}"
        fi
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
        PID=$!
        sleep 0.1
        if kill -0 $PID 2>/dev/null; then
            echo "{\"systemMessage\": \"🚀 Consensus review started (PID: $PID)\\n📁 Focus: $FOCUS\\n📋 Log: $LOG_FILE\"}"
        else
            echo "{\"systemMessage\": \"❌ Consensus review failed to start. Check: $LOG_FILE\"}"
        fi
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
        PID=$!
        sleep 0.1
        if kill -0 $PID 2>/dev/null; then
            echo "{\"systemMessage\": \"🚀 Review started with $MODEL (PID: $PID)\\n📁 Focus: $FOCUS\\n📋 Log: $LOG_FILE\"}"
        else
            echo "{\"systemMessage\": \"❌ Review with $MODEL failed to start. Check: $LOG_FILE\"}"
        fi
    else
        echo "{\"systemMessage\": \"⚠️ quick-review.sh not found\"}"
    fi
    exit 0
fi

# No keyword matched - let prompt continue normally
exit 0
