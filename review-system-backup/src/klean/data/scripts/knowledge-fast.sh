#!/bin/bash
#
# Knowledge Fast Search - Uses daemon if available, falls back to direct
#
# Usage:
#   knowledge-fast.sh "<query>" [limit]
#
# If knowledge-server.py is running: ~50ms search
# If not running: ~20s (falls back to knowledge-search.py)
#

QUERY="${1:-}"
LIMIT="${2:-5}"

if [ -z "$QUERY" ]; then
    echo "Usage: knowledge-fast.sh <query> [limit]"
    exit 1
fi

SOCKET="/tmp/knowledge-server.sock"
PYTHON="$HOME/.venvs/knowledge-db/bin/python"
SERVER="$HOME/.claude/scripts/knowledge-server.py"
SEARCH="$HOME/.claude/scripts/knowledge-search.py"

# Try daemon first (fast path)
if [ -S "$SOCKET" ]; then
    RESULT=$("$PYTHON" "$SERVER" search "$QUERY" "$LIMIT" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$RESULT" ]; then
        echo "$RESULT"
        exit 0
    fi
fi

# Fallback to direct search (slow path)
echo "⏳ Server not running, using direct search (slow)..."
echo "   Tip: Start server with: knowledge-server.py start"
"$PYTHON" "$SEARCH" "$QUERY" --format compact --limit "$LIMIT"
