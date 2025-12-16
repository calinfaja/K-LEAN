#!/bin/bash
#
# GoodJob Dispatch - Manual knowledge capture hook
#
# Triggered by UserPromptSubmit hook when user types:
#   "GoodJob <url>"
#   "GoodJob <url> <instructions>"
#   "SaveThis <description>"
#
# This script:
# 1. Parses the trigger command
# 2. Calls Haiku extraction
# 3. Stores result in knowledge-db
# 4. Returns confirmation to Claude
#

PROMPT="$1"
SCRIPTS_DIR="$HOME/.claude/scripts"
PYTHON="$HOME/.venvs/knowledge-db/bin/python"

# Find project root
find_project_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.serena" ] || [ -d "$dir/.claude" ] || [ -d "$dir/.knowledge-db" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo ""
}

PROJECT_ROOT=$(find_project_root)

if [ -z "$PROJECT_ROOT" ]; then
    echo "ERROR: Not in a project directory (no .serena, .claude, or .knowledge-db found)"
    exit 1
fi

# Parse the prompt
# GoodJob https://example.com
# GoodJob https://example.com focus on security aspects
# SaveThis learned that X works better than Y

if echo "$PROMPT" | grep -qi "^goodjob"; then
    # Extract URL and optional instructions
    # Remove "GoodJob " prefix (case insensitive)
    CONTENT=$(echo "$PROMPT" | sed -E 's/^[Gg]ood[Jj]ob[[:space:]]+//')

    # Check if first part is URL
    if [[ "$CONTENT" =~ ^https?:// ]]; then
        # Extract URL (first word)
        URL=$(echo "$CONTENT" | awk '{print $1}')
        # Rest is instructions
        INSTRUCTIONS=$(echo "$CONTENT" | sed "s|$URL||" | xargs)
        [ -z "$INSTRUCTIONS" ] && INSTRUCTIONS="Extract key knowledge from this page"

        echo "Capturing knowledge from: $URL"
        echo "Instructions: $INSTRUCTIONS"

        # Call extraction
        JSON=$("$SCRIPTS_DIR/knowledge-extract.sh" "$URL" "$INSTRUCTIONS")

        # Add URL to JSON
        JSON=$(echo "$JSON" | jq --arg url "$URL" '. + {url: $url}')

    else
        # Not a URL, treat entire content as description
        INSTRUCTIONS="$CONTENT"
        echo "Capturing knowledge: $INSTRUCTIONS"

        JSON=$("$SCRIPTS_DIR/knowledge-extract.sh" "$CONTENT" "Extract and structure this information")
    fi

elif echo "$PROMPT" | grep -qi "^savethis"; then
    # SaveThis <description>
    DESCRIPTION=$(echo "$PROMPT" | sed -E 's/^[Ss]ave[Tt]his[[:space:]]+//')

    echo "Saving lesson learned: $DESCRIPTION"

    # For SaveThis, we create a lesson entry directly
    JSON=$(cat <<EOF
{
    "title": "$(echo "$DESCRIPTION" | head -c 60)",
    "summary": "$DESCRIPTION",
    "type": "lesson",
    "key_concepts": [],
    "relevance_score": 0.8
}
EOF
)
else
    echo "ERROR: Unknown command. Use 'GoodJob <url>' or 'SaveThis <description>'"
    exit 1
fi

# Validate JSON
if ! echo "$JSON" | jq . > /dev/null 2>&1; then
    echo "ERROR: Extraction failed - invalid JSON"
    echo "Raw output: $JSON"
    exit 1
fi

# Check relevance score
SCORE=$(echo "$JSON" | jq -r '.relevance_score // 0')
if (( $(echo "$SCORE < 0.1" | bc -l) )); then
    echo "SKIPPED: Content scored too low on relevance ($SCORE)"
    exit 0
fi

# Add to knowledge-db
echo "Storing in knowledge-db..."
ENTRY_ID=$("$PYTHON" "$SCRIPTS_DIR/knowledge_db.py" add "$JSON" 2>&1)

if [ $? -eq 0 ]; then
    TITLE=$(echo "$JSON" | jq -r '.title')
    echo ""
    echo "SUCCESS: Knowledge captured"
    echo "Title: $TITLE"
    echo "Score: $SCORE"
    echo "ID: $ENTRY_ID"
else
    echo "ERROR: Failed to store in knowledge-db"
    echo "$ENTRY_ID"
    exit 1
fi
