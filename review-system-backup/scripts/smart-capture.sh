#!/usr/bin/env bash
#
# Smart Capture - Automatically capture valuable conversation insights
# Uses Claude Haiku to evaluate relevance and quality
#
# Usage:
#   smart-capture.sh "<content>" [working_dir]
#   echo "<content>" | smart-capture.sh - [working_dir]
#
# Designed to be called by hooks or manually
# Runs in background, non-blocking
#

# Source kb-root.sh for paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true

CONTENT="$1"
WORK_DIR="${2:-$(pwd)}"

# If content is "-", read from stdin
if [ "$CONTENT" = "-" ]; then
    CONTENT=$(cat)
fi

# Skip if content is too short (< 50 chars)
if [ ${#CONTENT} -lt 50 ]; then
    exit 0
fi

# Skip common non-valuable content
if echo "$CONTENT" | grep -qiE "^(yes|no|ok|thanks|done|good|sure|hello|hi)$"; then
    exit 0
fi

# Find project root
find_project_root() {
    local dir="$WORK_DIR"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ]; then
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

# Check if knowledge system is available
if [ ! -x "$PYTHON" ] || [ ! -f "$KNOWLEDGE_DB" ]; then
    exit 0
fi

mkdir -p "$PROJECT_ROOT/.knowledge-db"

# Truncate to save tokens (max 2000 chars)
TRUNCATED=$(echo "$CONTENT" | head -c 2000)

# Build evaluation prompt
EVAL_PROMPT="Evaluate if this content contains knowledge worth saving for future reference.

CONTENT:
$TRUNCATED

Score criteria:
- Is this a reusable pattern, solution, or lesson? (not just task-specific)
- Would this help in future development sessions?
- Is it specific enough to be actionable?
- Is it something that took effort to discover/figure out?

Return ONLY a JSON object:
{
  \"worth_saving\": true,
  \"relevance_score\": 0.8,
  \"reason\": \"Why this is valuable (1 sentence)\",
  \"fact\": {
    \"title\": \"Short title (max 60 chars)\",
    \"summary\": \"What to remember (2-3 sentences)\",
    \"type\": \"lesson\",
    \"key_concepts\": [\"keyword1\", \"keyword2\"],
    \"tags\": [\"category1\"]
  }
}

Types: lesson, gotcha, pattern, solution, insight, tip
Set worth_saving=false if:
- It's just task execution (\"done\", \"fixed\", \"updated\")
- It's project-specific without reusable insight
- It's obvious/trivial
- It's a question without an answer"

# Run in background
(
    cd "$PROJECT_ROOT"

    # Call Claude Haiku
    RESULT=$(claude --model haiku --print "$EVAL_PROMPT" 2>/dev/null)

    # Parse JSON
    JSON=$(echo "$RESULT" | grep -o '{.*}' | head -1)
    if ! echo "$JSON" | jq . > /dev/null 2>&1; then
        JSON=$(echo "$RESULT" | sed -n '/```json/,/```/p' | grep -v '```' | tr -d '\n')
    fi

    if ! echo "$JSON" | jq . > /dev/null 2>&1; then
        exit 0
    fi

    # Check if worth saving
    WORTH=$(echo "$JSON" | jq -r '.worth_saving // false')
    SCORE=$(echo "$JSON" | jq -r '.relevance_score // 0')

    if [ "$WORTH" != "true" ]; then
        exit 0
    fi

    # Threshold: 0.7 for conversation capture (higher than reviews)
    if [ "$(echo "$SCORE < 0.7" | bc -l 2>/dev/null || echo "1")" = "1" ]; then
        exit 0
    fi

    # Build fact with metadata
    FACT=$(echo "$JSON" | jq --arg score "$SCORE" --arg date "$(date -Iseconds)" \
        '.fact + {relevance_score: ($score | tonumber), found_date: $date, source: "conversation", auto_captured: true}')

    # Store
    if echo "$FACT" | "$PYTHON" "$KNOWLEDGE_DB" add - 2>/dev/null; then
        TITLE=$(echo "$FACT" | jq -r '.title')
        echo "$(date '+%m-%d %H:%M') | auto | $TITLE (score: $SCORE)" >> "$PROJECT_ROOT/.knowledge-db/timeline.txt"
    fi

) &

exit 0
