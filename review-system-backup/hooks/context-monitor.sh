#!/bin/bash
#
# K-LEAN Context Monitor Hook - PostToolUse (All Tools)
# Warns at 85% and 95% context usage
#
# Since Claude doesn't expose context % directly, we estimate
# based on tool call count in the session.
#
# Thresholds are calibrated for typical Claude Code sessions:
# - ~60 tool calls ≈ 85% context for complex operations
# - ~80 tool calls ≈ 95% context
#

INPUT=$(cat)

# Session tracking - use a consistent file per terminal session
# We use PPID (parent PID) since each tool call is a subprocess
SESSION_ID="${CLAUDE_SESSION_ID:-$PPID}"
SESSION_FILE="/tmp/claude-context-monitor-$SESSION_ID"

# Read or initialize counter
if [ -f "$SESSION_FILE" ]; then
    COUNT=$(cat "$SESSION_FILE" 2>/dev/null || echo "0")
else
    COUNT=0
fi

# Increment counter
COUNT=$((COUNT + 1))
echo "$COUNT" > "$SESSION_FILE"

# Thresholds (calibrated for typical sessions)
WARN_THRESHOLD=60      # ~85% estimate
CRITICAL_THRESHOLD=80  # ~95% estimate

# Generate warnings at thresholds
if [ "$COUNT" -ge "$CRITICAL_THRESHOLD" ]; then
    # Critical warning - show every 10 calls after threshold
    if [ $((COUNT % 10)) -eq 0 ] || [ "$COUNT" -eq "$CRITICAL_THRESHOLD" ]; then
        echo "{\"systemMessage\": \"🚨 CRITICAL: ~${COUNT} tool calls. Context likely near limit!\\n→ Run /compact to compress context\\n→ Or /kln:remember then /clear to save & reset\"}"
    fi
elif [ "$COUNT" -ge "$WARN_THRESHOLD" ]; then
    # Warning - show at threshold and every 10 calls after
    if [ $((COUNT % 10)) -eq 0 ] || [ "$COUNT" -eq "$WARN_THRESHOLD" ]; then
        echo "{\"systemMessage\": \"⚠️ Context Monitor: ~${COUNT} tool calls (~85% estimate).\\n→ Consider /compact soon or plan for /clear\"}"
    fi
fi

# Always exit 0 - never block tool execution
exit 0
