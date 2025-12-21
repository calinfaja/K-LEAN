#!/usr/bin/env bash
#
# Auto-Capture Hook - Automatically capture valuable web findings
#
# Triggered by PostToolUse hook after WebFetch/WebSearch
#
# This script runs in background, non-blocking, to:
# 1. Check if content is worth storing (quick heuristics)
# 2. Call Haiku to extract and score
# 3. Store if relevance > threshold
#
# Hook input (JSON via stdin or $1):
# {
#   "tool": "WebFetch",
#   "result": "...",
#   "url": "..."
# }
#

# Source kb-root.sh for paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true

SCRIPTS_DIR="${KB_SCRIPTS_DIR:-$HOME/.claude/scripts}"
PYTHON="${KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"

# Read hook input
if [ -n "$1" ]; then
    HOOK_INPUT="$1"
else
    HOOK_INPUT=$(cat)
fi

# Parse tool and result
TOOL=$(echo "$HOOK_INPUT" | jq -r '.tool // ""')
RESULT=$(echo "$HOOK_INPUT" | jq -r '.result // ""')
URL=$(echo "$HOOK_INPUT" | jq -r '.url // ""')

# Only process web-related tools
case "$TOOL" in
    WebFetch|WebSearch|mcp__*fetch*|mcp__*search*)
        ;;
    *)
        # Not a web tool, skip
        exit 0
        ;;
esac

# Quick heuristics - is this worth processing?
# Skip if result is too short or looks like an error
RESULT_LENGTH=${#RESULT}

if [ $RESULT_LENGTH -lt 200 ]; then
    exit 0  # Too short, probably not useful
fi

if echo "$RESULT" | grep -qi "error\|failed\|not found\|403\|404\|500"; then
    exit 0  # Looks like an error
fi

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
    exit 0  # Not in a project, skip
fi

# Truncate result for extraction (save tokens)
TRUNCATED_RESULT=$(echo "$RESULT" | head -c 5000)

# Prepare content for extraction
if [ -n "$URL" ]; then
    CONTENT="URL: $URL

Content:
$TRUNCATED_RESULT"
else
    CONTENT="$TRUNCATED_RESULT"
fi

# Call Haiku extraction (this is the expensive part)
JSON=$("$SCRIPTS_DIR/knowledge-extract.sh" "$CONTENT" "Extract key technical knowledge. Focus on: solutions, patterns, APIs, configurations, best practices.")

# Validate JSON
if ! echo "$JSON" | jq . > /dev/null 2>&1; then
    exit 0  # Invalid JSON, skip
fi

# Check relevance score - only store if > 0.5
SCORE=$(echo "$JSON" | jq -r '.relevance_score // 0')
if (( $(echo "$SCORE < 0.5" | bc -l 2>/dev/null || echo "1") )); then
    exit 0  # Not relevant enough
fi

# Add URL if available
if [ -n "$URL" ]; then
    JSON=$(echo "$JSON" | jq --arg url "$URL" '. + {url: $url, source_type: "web"}')
fi

# Store in knowledge-db (silently)
"$PYTHON" "$SCRIPTS_DIR/knowledge-db.py" add "$JSON" > /dev/null 2>&1

exit 0
