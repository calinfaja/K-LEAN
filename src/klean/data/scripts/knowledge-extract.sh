#!/usr/bin/env bash
#
# Knowledge Extract - Use Claude Haiku to extract structured knowledge
#
# Usage:
#   knowledge-extract.sh <url_or_content> [instructions]
#
# This script:
# 1. Takes URL or content
# 2. Calls Claude Haiku to extract structured knowledge
# 3. Returns JSON suitable for knowledge-db
#
# Can be called from:
# - GoodJob hook (manual trigger)
# - Auto-capture hook (automatic)
# - Task tool subagent (from Claude session)
#

set -e

CONTENT="$1"
INSTRUCTIONS="${2:-Extract the key knowledge from this content}"

# Find project root (for context)
find_project_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.serena" ] || [ -d "$dir/.claude" ] || [ -d "$dir/.knowledge-db" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo "$PWD"
}

PROJECT_ROOT=$(find_project_root)

# Check if content is URL
if [[ "$CONTENT" =~ ^https?:// ]]; then
    URL="$CONTENT"
    # Fetch URL content (basic)
    PAGE_CONTENT=$(curl -sL --max-time 10 "$URL" 2>/dev/null | head -c 10000 || echo "")
    CONTENT="URL: $URL

Content:
$PAGE_CONTENT"
fi

# Extraction prompt for Haiku
EXTRACTION_PROMPT="You are a knowledge extraction assistant. Extract structured information from the following content.

USER INSTRUCTIONS: $INSTRUCTIONS

CONTENT:
$CONTENT

---

Extract and return ONLY valid JSON in this exact format:
{
    \"title\": \"Short descriptive title (max 60 chars)\",
    \"summary\": \"2-3 sentence summary of what this content contains\",
    \"type\": \"web|code|solution|lesson\",
    \"problem_solved\": \"What problem does this solve? (if applicable)\",
    \"key_concepts\": [\"keyword1\", \"keyword2\", \"keyword3\"],
    \"relevance_score\": 0.0 to 1.0,
    \"what_worked\": \"For solutions: what specifically worked (if applicable)\",
    \"constraints\": \"Any limitations or caveats (if applicable)\"
}

Rules:
- relevance_score: 0.9+ for directly useful solutions, 0.7-0.9 for helpful references, 0.5-0.7 for tangentially related, <0.5 for low value
- key_concepts: 3-7 searchable terms
- Be concise but capture the essential knowledge
- If content is not useful, set relevance_score < 0.3

Return ONLY the JSON, no other text."

# Call Claude with Haiku model
# Method A: Claude CLI (for headless/scripts)
if command -v claude &> /dev/null; then
    RESULT=$(echo "$EXTRACTION_PROMPT" | claude --model haiku --print 2>/dev/null || echo '{"error": "Claude CLI failed"}')
else
    # Fallback: output error
    RESULT='{"error": "Claude CLI not available"}'
fi

# Extract just the JSON (in case there's extra text)
JSON_RESULT=$(echo "$RESULT" | grep -o '{.*}' | head -1 || echo "$RESULT")

echo "$JSON_RESULT"
