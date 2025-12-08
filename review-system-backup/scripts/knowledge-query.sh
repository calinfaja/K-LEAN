#!/bin/bash
#
# Knowledge Query - Fast search via Unix socket (pure bash, no Python import)
#
# Usage:
#   knowledge-query.sh "<query>" [limit]
#
# Requires knowledge-server.py running in background.
#

QUERY="${1:-}"
LIMIT="${2:-5}"
SOCKET="/tmp/knowledge-server.sock"

if [ -z "$QUERY" ]; then
    echo "Usage: knowledge-query.sh <query> [limit]"
    echo ""
    echo "Start server first: knowledge-server.py start &"
    exit 1
fi

if [ ! -S "$SOCKET" ]; then
    echo "❌ Server not running. Start with:"
    echo "   cd ~/claudeAgentic && ~/.claude/scripts/knowledge-server.py start &"
    exit 1
fi

# Send query via netcat/socat (pure socket, no Python)
REQUEST="{\"cmd\":\"search\",\"query\":\"$QUERY\",\"limit\":$LIMIT}"

if command -v socat &> /dev/null; then
    RESPONSE=$(echo "$REQUEST" | socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null)
elif command -v nc &> /dev/null; then
    RESPONSE=$(echo "$REQUEST" | nc -U "$SOCKET" 2>/dev/null)
else
    # Fallback to Python (slower)
    RESPONSE=$("$HOME/.venvs/knowledge-db/bin/python" -c "
import socket, json, sys
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
