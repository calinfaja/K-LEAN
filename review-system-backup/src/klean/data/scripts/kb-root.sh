#!/usr/bin/env bash
#
# K-LEAN kb-root.sh - Unified Project Root Detection & Path Configuration
# ========================================================================
# Single source of truth for project detection and paths across ALL scripts.
# Source this file in any script that needs project root or path detection.
#
# Usage:
#   source ~/.claude/scripts/kb-root.sh
#   PROJECT_ROOT=$(find_kb_project_root)
#   SOCKET=$(get_kb_socket_path "$PROJECT_ROOT")
#   $KB_PYTHON script.py  # Uses configured Python
#
# Environment Variables (override defaults):
#   KLEAN_KB_PYTHON    - Python interpreter for knowledge DB
#   KLEAN_SCRIPTS_DIR  - K-LEAN scripts directory
#   KLEAN_SOCKET_DIR   - Directory for Unix sockets
#
# Priority order for project detection:
#   1. CLAUDE_PROJECT_DIR environment variable
#   2. .knowledge-db directory (walk up)
#   3. .serena directory (walk up)
#   4. .claude directory (walk up)
#   5. .git directory (walk up)
#

# =============================================================================
# Path Configuration (with environment variable overrides)
# =============================================================================

# Knowledge DB Python - check multiple locations
if [ -n "$KLEAN_KB_PYTHON" ] && [ -x "$KLEAN_KB_PYTHON" ]; then
    KB_PYTHON="$KLEAN_KB_PYTHON"
elif [ -x "$HOME/.venvs/knowledge-db/bin/python" ]; then
    KB_PYTHON="$HOME/.venvs/knowledge-db/bin/python"
elif [ -x "$HOME/.local/share/klean/venv/bin/python" ]; then
    KB_PYTHON="$HOME/.local/share/klean/venv/bin/python"
elif command -v python3 &>/dev/null; then
    KB_PYTHON="python3"  # Fallback to system python
else
    KB_PYTHON=""
fi

# Scripts directory
KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"

# Socket directory (must be writable, /tmp works on all Unix)
KB_SOCKET_DIR="${KLEAN_SOCKET_DIR:-/tmp}"

# Export for use in subshells
export KB_PYTHON KB_SCRIPTS_DIR KB_SOCKET_DIR

# Find project root by walking up directory tree
# Returns: project root path, or empty string if not found
find_kb_project_root() {
    local start_dir="${1:-$(pwd)}"
    local dir="$start_dir"

    # Priority 1: Environment variable (Claude sets this)
    if [ -n "$CLAUDE_PROJECT_DIR" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        echo "$CLAUDE_PROJECT_DIR"
        return 0
    fi

    # Priority 2-5: Walk up looking for markers in priority order
    while [ "$dir" != "/" ]; do
        for marker in ".knowledge-db" ".serena" ".claude" ".git"; do
            if [ -d "$dir/$marker" ]; then
                echo "$dir"
                return 0
            fi
        done
        dir=$(dirname "$dir")
    done

    # Not found
    return 1
}

# Calculate MD5 hash of project path (first 8 chars)
# Used for unique socket/pid file naming per project
get_kb_project_hash() {
    local root="$1"
    if [ -z "$root" ]; then
        return 1
    fi
    # Resolve to absolute path for consistent hashing
    local abs_path=$(cd "$root" 2>/dev/null && pwd)
    # macOS uses 'md5', Linux uses 'md5sum'
    if command -v md5sum &>/dev/null; then
        echo -n "$abs_path" | md5sum | cut -c1-8
    elif command -v md5 &>/dev/null; then
        echo -n "$abs_path" | md5 | cut -c1-8
    else
        # Fallback to Python
        echo -n "$abs_path" | python3 -c "import sys,hashlib; print(hashlib.md5(sys.stdin.read().encode()).hexdigest()[:8])"
    fi
}

# Get socket path for project's knowledge server
get_kb_socket_path() {
    local root="$1"
    local hash=$(get_kb_project_hash "$root")
    if [ -z "$hash" ]; then
        return 1
    fi
    echo "${KB_SOCKET_DIR:-/tmp}/kb-${hash}.sock"
}

# Get PID file path for project's knowledge server
get_kb_pid_path() {
    local root="$1"
    local hash=$(get_kb_project_hash "$root")
    if [ -z "$hash" ]; then
        return 1
    fi
    echo "${KB_SOCKET_DIR:-/tmp}/kb-${hash}.pid"
}

# Check if knowledge DB is initialized for project
is_kb_initialized() {
    local root="$1"
    [ -d "$root/.knowledge-db" ]
}

# Check if knowledge server is running and responsive
is_kb_server_running() {
    local root="$1"
    local socket=$(get_kb_socket_path "$root")

    # Socket must exist
    if [ ! -S "$socket" ]; then
        return 1
    fi

    # Try to ping server
    local response
    if command -v socat &> /dev/null; then
        response=$(echo '{"cmd":"ping"}' | timeout 2 socat - UNIX-CONNECT:"$socket" 2>/dev/null)
    elif command -v nc &> /dev/null; then
        response=$(echo '{"cmd":"ping"}' | timeout 2 nc -U "$socket" 2>/dev/null)
    else
        # Python fallback
        response=$(python3 -c "
import socket
import sys
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect('$socket')
    s.sendall(b'{\"cmd\":\"ping\"}')
    print(s.recv(1024).decode())
    s.close()
except:
    sys.exit(1)
" 2>/dev/null)
    fi

    # Check for pong response
    echo "$response" | grep -q '"pong"' 2>/dev/null
}

# Clean stale socket if server is not responsive
clean_kb_stale_socket() {
    local root="$1"
    local socket=$(get_kb_socket_path "$root")
    local pid_file=$(get_kb_pid_path "$root")

    if [ -S "$socket" ]; then
        if ! is_kb_server_running "$root"; then
            rm -f "$socket" "$pid_file" 2>/dev/null
            return 0  # Cleaned
        fi
    fi
    return 1  # Nothing to clean
}

# Get knowledge DB directory path
get_kb_dir() {
    local root="$1"
    if [ -n "$root" ]; then
        echo "$root/.knowledge-db"
    fi
}

# Export functions for use in subshells
export -f find_kb_project_root
export -f get_kb_project_hash
export -f get_kb_socket_path
export -f get_kb_pid_path
export -f is_kb_initialized
export -f is_kb_server_running
export -f clean_kb_stale_socket
export -f get_kb_dir
