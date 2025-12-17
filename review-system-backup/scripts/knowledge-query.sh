#!/bin/bash
#
# Knowledge Query - Fast per-project search via Unix socket
#
# Usage:
#   knowledge-query.sh "<query>" [limit]
#
# Each project has its own server. Auto-starts if not running.
# Socket: /tmp/kb-{project_hash}.sock
#

QUERY="${1:-}"
LIMIT="${2:-5}"
PYTHON="$HOME/.venvs/knowledge-db/bin/python"
SERVER_SCRIPT="$HOME/.claude/scripts/knowledge-server.py"

if [ -z "$QUERY" ]; then
    echo "Usage: knowledge-query.sh <query> [limit]"
    echo ""
    echo "Searches the knowledge DB for the current project."
    echo "Server auto-starts if not running (~15s first time)."
    exit 1
fi

# Find project root (walk up looking for .knowledge-db)
find_project_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.knowledge-db" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Get socket path for project (must match Python's get_socket_path)
get_socket_path() {
    local project="$1"
    local hash=$(echo -n "$project" | md5sum | cut -c1-8)
    echo "/tmp/kb-${hash}.sock"
}

# Find project
PROJECT_ROOT=$(find_project_root)
if [ -z "$PROJECT_ROOT" ]; then
    echo "❌ No .knowledge-db found in current directory tree"
    echo "   Run from a project directory with knowledge DB"
    exit 1
fi

SOCKET=$(get_socket_path "$PROJECT_ROOT")

# Auto-start server if not running
if [ ! -S "$SOCKET" ]; then
    echo "⏳ Starting knowledge server for $(basename "$PROJECT_ROOT")..."

    # Start server in background
    cd "$PROJECT_ROOT" && nohup "$PYTHON" "$SERVER_SCRIPT" start > /tmp/kb-startup.log 2>&1 &
    SERVER_PID=$!

    # Wait for socket (up to 60s for index loading)
    for i in {1..60}; do
        if [ -S "$SOCKET" ]; then
            echo "✓ Server ready (${i}s)"
            break
        fi
        sleep 1
    done

    if [ ! -S "$SOCKET" ]; then
        echo "❌ Server failed to start. Check /tmp/kb-startup.log"
        exit 1
    fi
fi

# Send query via socket
REQUEST="{\"cmd\":\"search\",\"query\":\"$QUERY\",\"limit\":$LIMIT}"

if command -v socat &> /dev/null; then
    RESPONSE=$(echo "$REQUEST" | socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null)
elif command -v nc &> /dev/null; then
    RESPONSE=$(echo "$REQUEST" | nc -U "$SOCKET" 2>/dev/null)
else
    # Fallback to Python
    RESPONSE=$("$PYTHON" -c "
import socket, json
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('$SOCKET')
s.sendall(b'$REQUEST')
print(s.recv(65536).decode())
s.close()
" 2>/dev/null)
fi

if [ -z "$RESPONSE" ]; then
    echo "❌ No response from server"
    exit 1
fi

# Parse and display results
echo "$RESPONSE" | jq -r '
if .error then
    "❌ Error: \(.error)"
else
    "⚡ Search time: \(.search_time_ms)ms",
    "",
    (.results[] | "[\(.score | . * 100 | floor / 100)] \(.title // .text // .id)")
end
' 2>/dev/null || echo "$RESPONSE"
