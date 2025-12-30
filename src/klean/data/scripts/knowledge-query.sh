#!/usr/bin/env bash
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/knowledge-server.py"

# Source kb-root.sh for KB_PYTHON and other paths
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true
PYTHON="${KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"

if [ -z "$QUERY" ]; then
    echo "Usage: knowledge-query.sh <query> [limit]"
    echo ""
    echo "Searches the knowledge DB for the current project."
    echo "Server auto-starts if not running (~15s first time)."
    exit 1
fi

# Source unified project detection
if [ -f "$SCRIPT_DIR/kb-root.sh" ]; then
    source "$SCRIPT_DIR/kb-root.sh"
else
    # Fallback inline functions
    find_kb_project_root() {
        local dir="$PWD"
        while [ "$dir" != "/" ]; do
            for marker in ".knowledge-db" ".serena" ".claude" ".git"; do
                if [ -d "$dir/$marker" ]; then
                    echo "$dir"
                    return 0
                fi
            done
            dir="$(dirname "$dir")"
        done
        return 1
    }
    get_kb_socket_path() {
        local project="$1"
        local abs_path=$(cd "$project" 2>/dev/null && pwd)
        local hash=$(echo -n "$abs_path" | md5sum | cut -c1-8)
        echo "/tmp/kb-${hash}.sock"
    }
fi

# Find project
PROJECT_ROOT=$(find_kb_project_root)
if [ -z "$PROJECT_ROOT" ]; then
    echo "[ERROR] No project root found"
    echo "   Run from a project directory with .knowledge-db, .claude, .serena, or .git"
    exit 1
fi

# Check if knowledge DB is initialized
if [ ! -d "$PROJECT_ROOT/.knowledge-db" ]; then
    echo "[ERROR] Knowledge DB not initialized for $(basename "$PROJECT_ROOT")"
    echo "   Run: InitKB"
    exit 1
fi

SOCKET=$(get_kb_socket_path "$PROJECT_ROOT")

# Auto-start server if not running
if [ ! -S "$SOCKET" ]; then
    echo "⏳ Starting knowledge server for $(basename "$PROJECT_ROOT")..."

    # Start server in background
    cd "$PROJECT_ROOT" && nohup "$PYTHON" "$SERVER_SCRIPT" start > /tmp/kb-startup.log 2>&1 &
    SERVER_PID=$!

    # Wait for socket (up to 60s for index loading)
    for i in {1..60}; do
        if [ -S "$SOCKET" ]; then
            echo "[OK] Server ready (${i}s)"
            break
        fi
        sleep 1
    done

    if [ ! -S "$SOCKET" ]; then
        echo "[ERROR] Server failed to start. Check /tmp/kb-startup.log"
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
    echo "[ERROR] No response from server"
    exit 1
fi

# Parse and display results
echo "$RESPONSE" | jq -r '
if .error then
    "[ERROR] Error: \(.error)"
else
    " Search time: \(.search_time_ms)ms",
    "",
    (.results[] | "[\(.score | . * 100 | floor / 100)] \(.title // .text // .id)")
end
' 2>/dev/null || echo "$RESPONSE"
