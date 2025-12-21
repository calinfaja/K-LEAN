#!/usr/bin/env bash
#
# Fact Extraction - Extract reusable knowledge from reviews/commits
# Uses native Claude Haiku for fast, cheap extraction
#
# Usage:
#   fact-extract.sh "<content>" "<source_type>" "<focus>" [working_dir]
#   echo "<content>" | fact-extract.sh - "<source_type>" "<focus>" [working_dir]
#
# Source types: review, commit
#
# Runs in background, non-blocking
#

# Source kb-root.sh for paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true

CONTENT="$1"
SOURCE_TYPE="${2:-review}"
FOCUS="${3:-general}"
WORK_DIR="${4:-$(pwd)}"

# If content is "-", read from stdin
if [ "$CONTENT" = "-" ]; then
    CONTENT=$(cat)
fi

# Skip if content is too short
if [ ${#CONTENT} -lt 100 ]; then
    exit 0
fi

# Find project root for knowledge-db
find_project_root() {
    local dir="$WORK_DIR"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.knowledge-db" ] || [ -d "$dir/.serena" ] || [ -d "$dir/.claude" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo ""
}

PROJECT_ROOT=$(find_project_root)
if [ -z "$PROJECT_ROOT" ]; then
    # No project found, skip extraction
    exit 0
fi

# Use paths from kb-root.sh
PYTHON="${KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
KNOWLEDGE_DB="${KB_SCRIPTS_DIR:-$HOME/.claude/scripts}/knowledge_db.py"

# Check if knowledge system is available
if [ ! -x "$PYTHON" ] || [ ! -f "$KNOWLEDGE_DB" ]; then
    exit 0
fi

# Ensure knowledge-db directory exists
mkdir -p "$PROJECT_ROOT/.knowledge-db"

# Log to timeline (chronological event tracking)
log_timeline() {
    echo "$(date '+%m-%d %H:%M') | $1 | $2" >> "$PROJECT_ROOT/.knowledge-db/timeline.txt"
}

# Truncate content to save tokens (max 3000 chars)
TRUNCATED_CONTENT=$(echo "$CONTENT" | head -c 3000)

# Build extraction prompt based on source type
if [ "$SOURCE_TYPE" = "commit" ]; then
    EXTRACT_PROMPT="Extract reusable lessons from this git commit.

COMMIT INFO:
$TRUNCATED_CONTENT

Extract ONLY information useful for FUTURE development sessions:
- Bug fixes: what was broken, how it was fixed
- Patterns: reusable approaches discovered
- Gotchas: pitfalls to avoid (don't do X because Y)
- Decisions: architectural choices made and why

Return ONLY valid JSON (no markdown, no explanation):
{
  \"should_store\": true,
  \"relevance_score\": 0.7,
  \"facts\": [
    {
      \"title\": \"Short descriptive title (max 60 chars)\",
      \"summary\": \"What was learned in 2-3 sentences\",
      \"type\": \"gotcha\",
      \"key_concepts\": [\"keyword1\", \"keyword2\"],
      \"problem_solved\": \"What problem this addresses\",
      \"source\": \"commit\"
    }
  ]
}

Types: gotcha, pattern, solution, decision, lesson
Set should_store=false and relevance_score=0 if nothing worth storing.
Return empty facts array if nothing valuable."

else
    EXTRACT_PROMPT="Extract reusable knowledge from this code review.

REVIEW FOCUS: $FOCUS

REVIEW CONTENT:
$TRUNCATED_CONTENT

Extract ONLY findings useful for FUTURE reviews:
- Critical issues found (with file:line if available)
- Patterns that indicate bugs
- Common mistakes in this codebase
- Solutions that worked

Return ONLY valid JSON (no markdown, no explanation):
{
  \"should_store\": true,
  \"relevance_score\": 0.7,
  \"facts\": [
    {
      \"title\": \"Short descriptive title (max 60 chars)\",
      \"summary\": \"What was found in 2-3 sentences\",
      \"type\": \"gotcha\",
      \"key_concepts\": [\"keyword1\", \"keyword2\"],
      \"problem_solved\": \"What problem this addresses\",
      \"source\": \"review_$FOCUS\"
    }
  ]
}

Types: gotcha, pattern, solution, insight
Set should_store=false and relevance_score=0 if nothing worth storing.
Return empty facts array if nothing valuable."
fi

# Run extraction in background
(
    cd "$PROJECT_ROOT"

    # Call native Claude Haiku for extraction
    RESULT=$(claude --model haiku --print "$EXTRACT_PROMPT" 2>/dev/null)

    # Try to parse JSON from result (might have markdown wrapper)
    JSON=$(echo "$RESULT" | grep -o '{.*}' | head -1)

    # Validate JSON
    if ! echo "$JSON" | jq . > /dev/null 2>&1; then
        # Try extracting JSON from code block
        JSON=$(echo "$RESULT" | sed -n '/```json/,/```/p' | grep -v '```' | tr -d '\n')
        if ! echo "$JSON" | jq . > /dev/null 2>&1; then
            exit 0
        fi
    fi

    # Check if we should store
    SHOULD_STORE=$(echo "$JSON" | jq -r '.should_store // false')
    SCORE=$(echo "$JSON" | jq -r '.relevance_score // 0')

    if [ "$SHOULD_STORE" != "true" ]; then
        exit 0
    fi

    # Check score threshold (0.6)
    if [ "$(echo "$SCORE < 0.6" | bc -l 2>/dev/null || echo "1")" = "1" ]; then
        exit 0
    fi

    # Extract and store each fact
    FACT_COUNT=$(echo "$JSON" | jq '.facts | length')
    STORED=0

    for i in $(seq 0 $((FACT_COUNT - 1))); do
        FACT=$(echo "$JSON" | jq ".facts[$i]")

        # Add metadata
        FACT=$(echo "$FACT" | jq --arg score "$SCORE" --arg date "$(date -Iseconds)" \
            '. + {relevance_score: ($score | tonumber), found_date: $date, auto_extracted: true}')

        # Store in knowledge-db
        if echo "$FACT" | "$PYTHON" "$KNOWLEDGE_DB" add - 2>/dev/null; then
            STORED=$((STORED + 1))
        fi
    done

    # Log to timeline if facts were stored
    if [ $STORED -gt 0 ]; then
        log_timeline "$SOURCE_TYPE" "$FOCUS ($STORED facts, score: $SCORE)"
    fi

) &

exit 0
