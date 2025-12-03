#!/bin/bash
#
# Session Helper - Provides consistent session ID for all review scripts
#
# Usage: source this file, then use $SESSION_DIR
#
# Each Claude instance gets its own session folder based on PPID

# Find the Claude parent process (walk up the process tree)
get_claude_pid() {
    local pid=$$
    while [ "$pid" != "1" ]; do
        local cmdline=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
        if echo "$cmdline" | grep -q "claude"; then
            echo "$pid"
            return 0
        fi
        pid=$(ps -o ppid= -p $pid 2>/dev/null | tr -d ' ')
    done
    # Fallback to PPID if claude not found
    echo "$PPID"
}

CLAUDE_PID=$(get_claude_pid)
SESSION_FILE="/tmp/claude-session-$CLAUDE_PID"

# Create session ID if doesn't exist
if [ ! -f "$SESSION_FILE" ]; then
    echo "$(date +%Y-%m-%d-%H%M%S)" > "$SESSION_FILE"
fi

# Read session ID
SESSION_ID=$(cat "$SESSION_FILE")

# Set session directory
SESSION_DIR="/tmp/claude-reviews/$SESSION_ID"
mkdir -p "$SESSION_DIR"

# Export for use in scripts
export SESSION_ID
export SESSION_DIR
