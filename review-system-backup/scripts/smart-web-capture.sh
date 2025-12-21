#!/usr/bin/env bash
#
# Smart Web Capture - Context-Aware AI Evaluation
#
# Called by post-web-handler.sh after WebFetch/WebSearch/Tavily tool use.
# Uses LiteLLM (qwen3-coder) to evaluate if content is worth saving to knowledge DB.
#
# FEATURES:
#   - Project context: Queries recent knowledge DB entries for relevance
#   - Smart deduplication: URL-based fast check + LLM semantic dedup
#   - Task-aware: Evaluates relevance to current project work
#   - Low cost: ~$0.001 per evaluation via NanoGPT (qwen3-coder)
#
# Usage:
#   smart-web-capture.sh "<content>" "<url>" "<query>" "<source_type>" [working_dir]
#
# Threshold: Only saves if relevance_score >= 0.7 AND not duplicate (URL or semantic)
#

# Don't use set -e - we handle errors explicitly
# set -e

# Source kb-root.sh for paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true

CONTENT="$1"
URL="$2"
QUERY="$3"
SOURCE_TYPE="$4"
WORK_DIR="${5:-$(pwd)}"

# Skip if content is too short (< 100 chars)
if [ ${#CONTENT} -lt 100 ]; then
    exit 0
fi

# Skip common non-valuable content patterns
if echo "$CONTENT" | grep -qiE "^(error|404|not found|access denied|login required)"; then
    exit 0
fi

# Find project root
find_project_root() {
    local dir="$WORK_DIR"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.knowledge-db" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$WORK_DIR"
}

PROJECT_ROOT=$(find_project_root)

# Use paths from kb-root.sh
PYTHON="${KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
KNOWLEDGE_DB="${KB_SCRIPTS_DIR:-$HOME/.claude/scripts}/knowledge_db.py"
KNOWLEDGE_DIR="$PROJECT_ROOT/.knowledge-db"
TIMELINE_FILE="$KNOWLEDGE_DIR/timeline.txt"

# Check if knowledge system is available
if [ ! -x "$PYTHON" ] || [ ! -f "$KNOWLEDGE_DB" ]; then
    exit 0
fi

mkdir -p "$KNOWLEDGE_DIR"

# Truncate content to save tokens (max 2000 chars)
TRUNCATED=$(echo "$CONTENT" | head -c 2000)

#------------------------------------------------------------------------------
# STEP 1: Get Recent Project Context from Timeline (fast, no DB loading)
#------------------------------------------------------------------------------
RECENT_CONTEXT=""
if [ -f "$TIMELINE_FILE" ]; then
    # Use timeline for fast context (no model loading needed)
    RECENT_CONTEXT=$(grep -E "smart-web|commit|lesson" "$TIMELINE_FILE" 2>/dev/null | tail -5)
fi

#------------------------------------------------------------------------------
# STEP 2: Simple URL-based Deduplication (fast, no DB query needed)
#------------------------------------------------------------------------------
if [ -n "$URL" ] && [ "$URL" != "null" ] && [ -f "$KNOWLEDGE_DIR/entries.jsonl" ]; then
    # Check if exact URL already exists in entries
    if grep -qF "\"$URL\"" "$KNOWLEDGE_DIR/entries.jsonl" 2>/dev/null; then
        TIMESTAMP=$(date '+%m-%d %H:%M')
        echo "$TIMESTAMP | skip-dup | URL exists: $URL" >> "$TIMELINE_FILE"
        exit 0
    fi
fi

#------------------------------------------------------------------------------
# STEP 3: Semantic Dedup - Query Similar Existing Entries
#------------------------------------------------------------------------------
EXISTING_ENTRIES=""
KNOWLEDGE_QUERY="${KB_SCRIPTS_DIR:-$HOME/.claude/scripts}/knowledge-query.sh"

if [ -x "$KNOWLEDGE_QUERY" ]; then
    # Build search key from URL domain or content snippet
    if [ -n "$URL" ] && [ "$URL" != "null" ]; then
        # Extract domain and path keywords for search
        SEARCH_KEY=$(echo "$URL" | sed 's|https\?://||' | cut -d'/' -f1-3 | tr '/' ' ')
    else
        # Use first 80 chars of content as search key
        SEARCH_KEY=$(echo "$CONTENT" | head -c 80 | tr '\n' ' ' | sed 's/[^a-zA-Z0-9 ]/ /g')
    fi

    # Query knowledge DB for similar entries (5 second timeout)
    if [ -n "$SEARCH_KEY" ]; then
        EXISTING_ENTRIES=$(timeout 5 "$KNOWLEDGE_QUERY" "$SEARCH_KEY" 2>/dev/null | head -8)
    fi
fi

#------------------------------------------------------------------------------
# STEP 4: Build Context Strings for Haiku
#------------------------------------------------------------------------------
URL_CONTEXT=""
if [ -n "$URL" ] && [ "$URL" != "null" ]; then
    URL_CONTEXT="URL: $URL"
fi

SEARCH_CONTEXT=""
if [ -n "$QUERY" ] && [ "$QUERY" != "null" ]; then
    SEARCH_CONTEXT="Search/Prompt: $QUERY"
fi

PROJECT_CONTEXT=""
if [ -n "$RECENT_CONTEXT" ]; then
    PROJECT_CONTEXT="RECENT PROJECT KNOWLEDGE (what user has been working on):
$RECENT_CONTEXT"
fi

#------------------------------------------------------------------------------
# STEP 5: Haiku Evaluation with Full Context + Dedup Check
#------------------------------------------------------------------------------
# Build context for existing entries (for dedup)
DEDUP_CONTEXT=""
if [ -n "$EXISTING_ENTRIES" ]; then
    DEDUP_CONTEXT="
EXISTING SIMILAR ENTRIES (check for duplicates):
$EXISTING_ENTRIES
"
fi

# Build simple prompt - Haiku knows JSON format
EVAL_PROMPT="Evaluate this web content for a developer knowledge DB. Return ONLY valid JSON.

$URL_CONTEXT
$SEARCH_CONTEXT
Content: $TRUNCATED
$DEDUP_CONTEXT
Criteria: Is it reusable? Took effort to find? Adds NEW info not in existing entries? Skip generic overviews. Mark is_duplicate=true if same topic/library/concept already exists above.

Return JSON: {\"worth_saving\": bool, \"relevance_score\": 0-1, \"is_duplicate\": bool, \"duplicate_of\": \"title if dup\", \"reason\": \"1 sentence\", \"fact\": {\"title\": \"\", \"summary\": \"\", \"type\": \"web|solution|lesson\", \"key_concepts\": [], \"tags\": []}}"

#------------------------------------------------------------------------------
# STEP 6: Call LiteLLM for Evaluation (qwen3-coder via NanoGPT - fast & cheap)
#------------------------------------------------------------------------------
LITELLM_URL="http://localhost:4000/v1/chat/completions"
PROMPT_ESCAPED=$(echo "$EVAL_PROMPT" | jq -Rs .)

RESPONSE=$(curl -s --max-time 25 "$LITELLM_URL" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"qwen3-coder\",\"messages\":[{\"role\":\"system\",\"content\":\"Return ONLY valid JSON. Be strict: if same topic exists in EXISTING ENTRIES, set is_duplicate=true.\"},{\"role\":\"user\",\"content\":$PROMPT_ESCAPED}],\"temperature\":0.1,\"max_tokens\":500}" 2>/dev/null)

RESULT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content // ""' 2>/dev/null)

# Final fallback
if [ -z "$RESULT" ] || [ "$RESULT" = "null" ]; then
    RESULT='{"worth_saving": false}'
fi

# Extract JSON from response (handle multiline and code blocks)
# First try: parse the whole result as JSON
JSON=$(echo "$RESULT" | jq -c '.' 2>/dev/null)
if [ -z "$JSON" ] || [ "$JSON" = "null" ]; then
    # Second try: extract from markdown code block
    JSON=$(echo "$RESULT" | sed -n '/```json/,/```/p' | grep -v '```' | jq -sc '.[0]' 2>/dev/null)
fi
if [ -z "$JSON" ] || [ "$JSON" = "null" ]; then
    # Third try: find JSON object in text (handles multiline)
    JSON=$(echo "$RESULT" | tr '\n' ' ' | grep -oP '\{[^{}]*\}' | head -1 | jq -c '.' 2>/dev/null)
fi

# Validate JSON
if ! echo "$JSON" | jq . > /dev/null 2>&1; then
    exit 0
fi

# Check if worth saving
WORTH=$(echo "$JSON" | jq -r '.worth_saving // false')
SCORE=$(echo "$JSON" | jq -r '.relevance_score // 0')
REASON=$(echo "$JSON" | jq -r '.reason // "No reason provided"')
IS_DUPLICATE=$(echo "$JSON" | jq -r '.is_duplicate // false')
DUPLICATE_OF=$(echo "$JSON" | jq -r '.duplicate_of // ""')

# Skip if semantic duplicate detected by Haiku
if [ "$IS_DUPLICATE" = "true" ]; then
    TIMESTAMP=$(date '+%m-%d %H:%M')
    if [ -n "$DUPLICATE_OF" ] && [ "$DUPLICATE_OF" != "null" ]; then
        echo "$TIMESTAMP | skip-dup | Semantic duplicate of: $DUPLICATE_OF" >> "$TIMELINE_FILE"
    else
        echo "$TIMESTAMP | skip-dup | Semantic duplicate detected" >> "$TIMELINE_FILE"
    fi
    exit 0
fi

if [ "$WORTH" != "true" ]; then
    # Log rejection to timeline (optional, for debugging)
    # TIMESTAMP=$(date '+%m-%d %H:%M')
    # echo "$TIMESTAMP | skip-low | Score: $SCORE - $REASON" >> "$TIMELINE_FILE"
    exit 0
fi

# Threshold: 0.7 for web content
THRESHOLD_CHECK=$(echo "$SCORE < 0.7" | bc -l 2>/dev/null || echo "1")
if [ "$THRESHOLD_CHECK" = "1" ]; then
    exit 0
fi

#------------------------------------------------------------------------------
# STEP 7: Build Entry and Save to Knowledge DB
#------------------------------------------------------------------------------
FACT=$(echo "$JSON" | jq \
    --arg score "$SCORE" \
    --arg date "$(date -Iseconds)" \
    --arg url "$URL" \
    --arg query "$QUERY" \
    --arg source_type "$SOURCE_TYPE" \
    --arg reason "$REASON" \
    '.fact + {
        relevance_score: ($score | tonumber),
        found_date: $date,
        url: (if $url != "" and $url != "null" then $url else null end),
        search_context: (if $query != "" and $query != "null" then $query else null end),
        source: ("smart-" + $source_type),
        save_reason: $reason,
        auto_captured: true,
        source_quality: "medium",
        confidence_score: 0.8
    }')

# Validate the constructed entry
if ! echo "$FACT" | jq . > /dev/null 2>&1; then
    exit 0
fi

# Store in knowledge DB
cd "$PROJECT_ROOT"
FACT_COMPACT=$(echo "$FACT" | jq -c '.')
ENTRIES_FILE="$KNOWLEDGE_DIR/entries.jsonl"
SAVED=false

# Try Python add first (fast if server not running)
if "$PYTHON" "$KNOWLEDGE_DB" add "$FACT_COMPACT" 2>/dev/null; then
    SAVED=true
else
    # Fallback: append to entries.jsonl directly (server will reindex on restart)
    # Add unique ID if not present
    FACT_WITH_ID=$(echo "$FACT_COMPACT" | jq --arg id "$(date +%s)-$$" '. + {id: $id}')
    echo "$FACT_WITH_ID" >> "$ENTRIES_FILE"
    SAVED=true
fi

if [ "$SAVED" = "true" ]; then
    TITLE=$(echo "$FACT" | jq -r '.title // "Untitled"')
    TAGS=$(echo "$FACT" | jq -r '.tags // [] | join(", ")' 2>/dev/null || echo "")

    # Log to timeline with tags
    TIMESTAMP=$(date '+%m-%d %H:%M')
    if [ -n "$TAGS" ]; then
        echo "$TIMESTAMP | smart-web | $TITLE [$TAGS] (score: $SCORE)" >> "$TIMELINE_FILE"
    else
        echo "$TIMESTAMP | smart-web | $TITLE (score: $SCORE)" >> "$TIMELINE_FILE"
    fi

    # Emit event if available
    EVENTS_SCRIPT="${KB_SCRIPTS_DIR:-$HOME/.claude/scripts}/knowledge-events.py"
    if [ -x "$EVENTS_SCRIPT" ]; then
        "$PYTHON" "$EVENTS_SCRIPT" emit "knowledge:smart-captured" \
            "{\"source\": \"$SOURCE_TYPE\", \"url\": \"$URL\", \"score\": $SCORE, \"title\": \"$TITLE\", \"reason\": \"$REASON\"}" 2>/dev/null &
    fi
fi

exit 0
